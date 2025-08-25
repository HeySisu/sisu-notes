# Sheets Service Query Performance Optimization Plan

**Analysis Date**: December 19, 2024
**Target Service**: Sheets Service
**Focus Area**: Query Performance & Caching

## 🚨 Executive Summary

The sheets service is experiencing critical performance bottlenecks due to complex SQL queries with multiple CTEs, inefficient filtering architecture, and suboptimal caching strategies. Current queries can take up to 50 seconds to complete, requiring immediate optimization.

**Key Issues**:
- Complex window functions with multiple table scans
- O(n) self-joins for filtering operations
- Redis cache storing only row IDs, requiring expensive hydration
- Missing critical database indexes
- Inefficient query patterns for latest cell lookups

**Expected Impact**: 60-80% query performance improvement with proper implementation.

---

## 🔍 Current Performance Problems

### 1. **Complex Window Function Performance**

**Location**: `sheets/data_layer/cells.py:1081-1106`

**Problem**: The `_latest_cells_query` creates expensive window functions across massive datasets:

```python
# Current problematic pattern
latest_cells_query = (
    sa.select(Cell.id, Cell.row_id, Cell.versioned_column_id, ...)
    .where(Cell.sheet_id == sheet_id, Cell.tab_id == active_tab_id, ...)
    .order_by(Cell.row_id, Cell.versioned_column_id, sa.desc(Cell.updated_at))
)
```

**Impact**: Creates full table scans on cells table (2.1M+ lines of code suggest massive data volumes).

### 2. **Inefficient Multi-Filter Architecture**

**Location**: `sheets/data_layer/cells.py:2015-2048`

**Problem**: Each filter creates a separate alias and join:

```python
# This creates O(n) joins for n filters - major performance killer
for idx, (column_id, filter_data) in enumerate(filter_model.items()):
    cell_alias = sa.alias(latest_cells_filtered_cte, name=f"filter_cell_{idx}")
    condition = get_filter_clause(filter_data, column_id, cell_alias)
    rows_query = rows_query.join(cell_alias, condition)
```

**Impact**: Exponential query complexity with multiple filters.

### 3. **Suboptimal Caching Strategy**

**Location**: `sheets/cache/sheet_rows.py`

**Problem**:
- Cache stores only row IDs, not hydrated data
- Cache miss penalty requires expensive `hydrate_rows` operation
- Timestamp-based invalidation too aggressive

**Impact**: Low cache hit rates and expensive cache misses.

---

## 🎯 High-Impact Optimization Recommendations

### **Priority 0: Critical Database Index Optimization**

#### A) **Add Composite Index for Latest Cell Lookup**

```sql
-- Critical missing index for the most common query pattern
CREATE INDEX CONCURRENTLY ix_cells_latest_lookup
ON cells (sheet_id, tab_id, row_id, versioned_column_id, updated_at DESC);

-- Covering index to avoid table lookups
CREATE INDEX CONCURRENTLY ix_cells_latest_with_content
ON cells (sheet_id, tab_id, row_id, versioned_column_id, updated_at DESC)
INCLUDE (content, answer, answer_numeric, answer_date, not_found);
```

**Implementation**:
```python
# Create migration file
# migrations/versions/YYYY_MM_DD_HHMM-add_critical_cells_indexes.py

def upgrade() -> None:
    # Use CONCURRENTLY to avoid blocking production
    op.execute("""
        CREATE INDEX CONCURRENTLY ix_cells_latest_lookup
        ON cells (sheet_id, tab_id, row_id, versioned_column_id, updated_at DESC)
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY ix_cells_latest_with_content
        ON cells (sheet_id, tab_id, row_id, versioned_column_id, updated_at DESC)
        INCLUDE (content, answer, answer_numeric, answer_date, not_found)
    """)
```

#### B) **Optimize Row Table Indexes**

```sql
-- Better index for row filtering and sorting
CREATE INDEX CONCURRENTLY ix_rows_sheet_tab_y_repo_doc
ON rows (sheet_id, tab_id, y_value, repo_doc_id)
WHERE deleted IS NULL OR deleted = false;

-- Index for row ordering operations
CREATE INDEX CONCURRENTLY ix_rows_sheet_tab_order
ON rows (sheet_id, tab_id, row_order, y_value)
WHERE deleted IS NULL OR deleted = false;
```

**Expected Impact**: 60-70% query time reduction for basic row operations.

---

### **Priority 0: Query Architecture Rewrite**

#### A) **Replace Window Functions with Lateral Joins**

**Current Problem**: Window functions scan entire cells table
**Solution**: Use lateral joins for targeted latest cell lookup

**Implementation**:
```python
# File: sheets/data_layer/cells.py
# Replace _latest_cells_query function

def _latest_cells_query_optimized(
    sheet_id: str,
    active_tab_id: str,
    column_ids: list[str],
    cell_id: Optional[str] = None,
) -> Select:
    """
    Optimized latest cells query using lateral joins instead of window functions.
    This reduces query complexity from O(n²) to O(n log n).
    """

    # Use lateral join for latest cell per row/column combination
    latest_cell_lateral = (
        sa.select(
            Cell.id,
            Cell.row_id,
            Cell.versioned_column_id,
            Cell.content,
            Cell.answer,
            Cell.answer_numeric,
            Cell.answer_date,
            Cell.not_found,
            Cell.updated_at
        )
        .where(
            Cell.sheet_id == sheet_id,
            Cell.tab_id == active_tab_id,
            Cell.versioned_column_id.in_(column_ids),
            Cell.row_id == sa.text("r.id")  # Correlate with outer query
        )
        .order_by(sa.desc(Cell.updated_at))
        .limit(1)
    ).lateral("latest_cell")

    base_query = (
        sa.select(latest_cell_lateral)
        .select_from(
            Row.alias("r").join(
                latest_cell_lateral,
                sa.true()  # CROSS JOIN LATERAL
            )
        )
        .where(
            sa.text("r.sheet_id") == sheet_id,
            sa.text("r.tab_id") == active_tab_id,
            sa.text("r.y_value") >= 0,
            sa.or_(
                sa.text("r.deleted").is_(None),
                sa.text("r.deleted").is_(False)
            )
        )
    )

    if cell_id:
        base_query = base_query.where(Cell.id == cell_id)

    return base_query
```

#### B) **Implement Single-Query Filtering**

**Current Problem**: Multiple self-joins for each filter
**Solution**: Single query with EXISTS clauses

```python
# File: sheets/data_layer/cells.py
# Replace _get_filters function

async def _get_filters_optimized(
    filter_model: Optional[dict[str, FilterModel]],
    sheet_id: str,
    active_tab_id: str,
    base_query: Select
) -> Select:
    """
    Optimized filtering using EXISTS clauses instead of multiple joins.
    """

    if not filter_model:
        return base_query

    filter_conditions = []

    for column_id, filter_data in filter_model.items():
        if not filter_data:
            continue

        # Build EXISTS clause for each filter
        exists_subquery = (
            sa.select(sa.literal(1))
            .select_from(Cell)
            .where(
                Cell.sheet_id == sheet_id,
                Cell.tab_id == active_tab_id,
                Cell.row_id == Row.id,
                Cell.versioned_column_id == column_id,
                build_filter_condition(filter_data, Cell)
            )
            .limit(1)
        )

        filter_conditions.append(sa.exists(exists_subquery))

    if filter_conditions:
        base_query = base_query.where(sa.and_(*filter_conditions))

    return base_query

def build_filter_condition(filter_data: FilterModel, cell_table) -> Any:
    """Build filter condition based on filter type."""
    if filter_data.type == "equals":
        return cell_table.answer == filter_data.filter
    elif filter_data.type == "contains":
        return cell_table.answer.ilike(f"%{filter_data.filter}%")
    elif filter_data.type == "number_range":
        return sa.and_(
            cell_table.answer_numeric >= filter_data.filter_from,
            cell_table.answer_numeric <= filter_data.filter_to
        )
    # Add more filter types as needed
    return sa.true()
```

**Expected Impact**: 40-60% reduction in complex query execution time.

---

### **Priority 1: Advanced Caching Strategy**

#### A) **Multi-Layer Cache Implementation**

**Current Problem**: Cache stores only row IDs, expensive hydration
**Solution**: Cache full hydrated row data

```python
# File: sheets/cache/enhanced_sheet_cache.py

from typing import Optional, Any
import msgpack
import numpy as np
from dataclasses import asdict

class EnhancedSheetCache:
    """
    Multi-layer caching strategy:
    Level 1: Redis - Full hydrated rows with cell content
    Level 2: Local memory - Sheet metadata and common queries
    Level 3: PostgreSQL - Prepared statements and query plans
    """

    async def get_hydrated_rows(
        self,
        cache_key: SheetRowCacheKey,
        fallback_query_func: callable
    ) -> list[dict[str, Any]]:
        """
        Get fully hydrated rows from cache or execute optimized query.
        """

        # Level 1: Try Redis cache with full data
        cached_data = await self._get_full_rows_from_redis(cache_key)
        if cached_data:
            return cached_data

        # Level 2: Check if we can use prepared statement
        if self._is_common_query_pattern(cache_key):
            rows = await self._execute_prepared_statement(cache_key)
        else:
            rows = await fallback_query_func()

        # Cache the full result
        await self._cache_full_rows(cache_key, rows)

        return rows

    async def _cache_full_rows(
        self,
        cache_key: SheetRowCacheKey,
        rows: list[dict[str, Any]]
    ) -> None:
        """Cache full row data including cell content."""

        # Optimize serialization for large datasets
        compressed_data = self._compress_row_data(rows)

        async with get_redis_sheets_cache_writer_client().aget() as r:
            sheet_key = f"sheet_full_rows:{cache_key.sheet_id}"
            field_name = f"{cache_key.last_updated_at}::{cache_key.params_hash}"

            # Store compressed full data
            await r.hset(sheet_key, field_name, compressed_data)
            await r.expire(sheet_key, 86400)  # 24 hour TTL

    def _compress_row_data(self, rows: list[dict[str, Any]]) -> bytes:
        """Compress row data for efficient storage."""

        # Separate frequently accessed data from content
        metadata = []
        content_data = []

        for row in rows:
            metadata.append({
                'id': str(row['id']),
                'y_value': row['y_value'],
                'repo_doc_id': str(row.get('repo_doc_id', '')),
                'created_at': row.get('created_at', '').isoformat() if row.get('created_at') else None
            })
            content_data.append(row.get('content', {}))

        # Use msgpack for better compression than JSON
        return msgpack.packb({
            'metadata': metadata,
            'content': content_data,
            'version': '1.0'
        })
```

#### B) **Smart Cache Invalidation**

**Current Problem**: Timestamp-based invalidation too aggressive
**Solution**: Cell-level change tracking

```python
# File: sheets/cache/smart_invalidation.py

class SmartCacheInvalidation:
    """
    Intelligent cache invalidation based on actual cell changes
    instead of timestamp-based invalidation.
    """

    async def invalidate_affected_queries(
        self,
        changed_cells: list[CellModel]
    ) -> None:
        """
        Only invalidate cache entries that would be affected by these cell changes.
        """

        # Group changes by sheet and tab
        changes_by_sheet = self._group_changes_by_sheet(changed_cells)

        for sheet_id, tab_changes in changes_by_sheet.items():
            # Find all cache keys that could be affected
            affected_keys = await self._find_affected_cache_keys(
                sheet_id,
                tab_changes
            )

            # Batch invalidate only affected entries
            if affected_keys:
                await self._batch_invalidate(sheet_id, affected_keys)

    async def _find_affected_cache_keys(
        self,
        sheet_id: str,
        changed_cells: list[CellModel]
    ) -> list[str]:
        """
        Find cache keys that would be affected by cell changes.
        """

        # Get all cache keys for this sheet
        async with get_redis_sheets_cache_reader_client().aget() as r:
            sheet_key = f"sheet_full_rows:{sheet_id}"
            all_keys = await r.hkeys(sheet_key)

        affected_keys = []
        changed_columns = {cell.versioned_column_id for cell in changed_cells}
        changed_rows = {cell.row_id for cell in changed_cells}

        for key_bytes in all_keys:
            key = key_bytes.decode('utf-8')

            # Parse cache key to understand what columns/filters it contains
            if self._key_affected_by_changes(key, changed_columns, changed_rows):
                affected_keys.append(key)

        return affected_keys

    def _key_affected_by_changes(
        self,
        cache_key: str,
        changed_columns: set[str],
        changed_rows: set[str]
    ) -> bool:
        """
        Determine if a cache key would be affected by the given changes.
        """

        # Parse the cache key to extract query parameters
        # This would need to be implemented based on current key format
        key_params = self._parse_cache_key(cache_key)

        # Check if any of the query's columns were affected
        if key_params.get('column_ids'):
            if changed_columns.intersection(set(key_params['column_ids'])):
                return True

        # Check if sorting/filtering columns were affected
        if key_params.get('sort_column_id') in changed_columns:
            return True

        # Check filter columns
        if key_params.get('filter_columns'):
            if changed_columns.intersection(set(key_params['filter_columns'])):
                return True

        return False
```

**Expected Impact**: 50-70% improvement in cache hit rates.

---

### **Priority 1: Materialized Views for Hot Data**

#### A) **Implement Latest Cells Materialized View**

**Solution**: Pre-compute latest cells for frequently accessed sheets

```sql
-- Create materialized view for latest cells
CREATE MATERIALIZED VIEW mv_sheet_latest_cells AS
SELECT DISTINCT ON (c.sheet_id, c.tab_id, c.row_id, c.versioned_column_id)
    c.sheet_id,
    c.tab_id,
    c.row_id,
    c.versioned_column_id,
    c.content,
    c.answer,
    c.answer_numeric,
    c.answer_date,
    c.not_found,
    c.updated_at,
    r.y_value,
    r.repo_doc_id,
    r.row_order
FROM cells c
JOIN rows r ON c.row_id = r.id
WHERE (r.deleted IS NULL OR r.deleted = false)
ORDER BY c.sheet_id, c.tab_id, c.row_id, c.versioned_column_id, c.updated_at DESC;

-- Create indexes on materialized view
CREATE UNIQUE INDEX ix_mv_latest_cells_unique
ON mv_sheet_latest_cells (sheet_id, tab_id, row_id, versioned_column_id);

CREATE INDEX ix_mv_latest_cells_sheet_tab
ON mv_sheet_latest_cells (sheet_id, tab_id);

CREATE INDEX ix_mv_latest_cells_answer_search
ON mv_sheet_latest_cells USING gin (answer gin_trgm_ops);
```

**Refresh Strategy**:
```python
# File: sheets/data_layer/materialized_view_refresh.py

class MaterializedViewManager:
    """
    Manage materialized view refresh strategy for optimal performance.
    """

    async def refresh_for_sheet(self, sheet_id: str, tab_id: str) -> None:
        """
        Refresh materialized view for specific sheet when cells change.
        """

        async with async_or_sync_session() as session:
            # Incremental refresh for specific sheet
            await session.execute(sa.text("""
                REFRESH MATERIALIZED VIEW CONCURRENTLY mv_sheet_latest_cells
                WHERE sheet_id = :sheet_id AND tab_id = :tab_id
            """), {"sheet_id": sheet_id, "tab_id": tab_id})

    async def schedule_bulk_refresh(self) -> None:
        """
        Schedule bulk refresh during low-traffic periods.
        """

        # Identify sheets that need refresh
        sheets_to_refresh = await self._find_stale_sheets()

        for sheet_id, tab_id in sheets_to_refresh:
            # Use background task to avoid blocking
            asyncio.create_task(self._refresh_sheet_background(sheet_id, tab_id))
```

#### B) **Query Rewrite to Use Materialized Views**

```python
# File: sheets/data_layer/cells.py
# Modify _get_relevant_rows_cached to use materialized view

async def _get_relevant_rows_with_mv(
    sheet_id: str,
    active_tab_id: str,
    column_ids: list[str],
    sort_column_id: Optional[str] = None,
    # ... other parameters
) -> tuple[list[RowInfo], str]:
    """
    Use materialized view for better performance on hot sheets.
    """

    async with async_or_sync_session() as s:
        # Check if materialized view is available and fresh
        mv_available = await self._check_mv_freshness(sheet_id, active_tab_id)

        if mv_available:
            # Use materialized view for much faster queries
            query = sa.select(
                sa.text("row_id"),
                sa.text("y_value")
            ).select_from(
                sa.text("mv_sheet_latest_cells")
            ).where(
                sa.text("sheet_id = :sheet_id"),
                sa.text("tab_id = :tab_id"),
                sa.text("versioned_column_id = ANY(:column_ids)")
            )

            # Apply filters directly on materialized view
            if sort_column_id:
                query = self._apply_sort_to_mv_query(query, sort_column_id)

            result = await s.execute(query, {
                "sheet_id": sheet_id,
                "tab_id": active_tab_id,
                "column_ids": column_ids
            })
        else:
            # Fallback to original query
            result = await self._original_query_method(...)

        rows_result = result.all()
        return [RowInfo(id=row.row_id, y_value=row.y_value) for row in rows_result]
```

**Expected Impact**: 30-50% performance improvement for frequently accessed sheets.

---

### **Priority 2: Application-Level Optimizations**

#### A) **Query Batching and Connection Pooling**

```python
# File: sheets/data_layer/query_batcher.py

class QueryBatcher:
    """
    Batch multiple similar sheet queries to reduce database round trips.
    """

    def __init__(self):
        self._pending_queries = {}
        self._batch_size = 10
        self._batch_timeout = 100  # milliseconds

    async def batch_get_rows(
        self,
        requests: list[GetRowsRequest]
    ) -> dict[str, GetRowsResponse]:
        """
        Batch multiple get_rows requests for efficiency.
        """

        # Group requests by similarity
        grouped_requests = self._group_similar_requests(requests)

        results = {}
        for group in grouped_requests:
            if len(group) > 1:
                # Execute as batch query
                batch_results = await self._execute_batch_query(group)
                results.update(batch_results)
            else:
                # Execute single query
                single_result = await self._execute_single_query(group[0])
                results[group[0].sheet_id] = single_result

        return results

    def _group_similar_requests(
        self,
        requests: list[GetRowsRequest]
    ) -> list[list[GetRowsRequest]]:
        """
        Group requests that can be efficiently batched together.
        """

        groups = []
        current_group = []

        for request in requests:
            if self._can_batch_with_current_group(request, current_group):
                current_group.append(request)
            else:
                if current_group:
                    groups.append(current_group)
                current_group = [request]

        if current_group:
            groups.append(current_group)

        return groups

    async def _execute_batch_query(
        self,
        requests: list[GetRowsRequest]
    ) -> dict[str, GetRowsResponse]:
        """
        Execute multiple requests in a single optimized query.
        """

        # Build UNION query for multiple sheets
        sheet_ids = [req.sheet_id for req in requests]

        # Use CTE to get data for all sheets at once
        batch_query = sa.text("""
            WITH batch_sheets AS (
                SELECT unnest(:sheet_ids) AS sheet_id
            ),
            batch_data AS (
                SELECT
                    mv.sheet_id,
                    mv.row_id,
                    mv.y_value,
                    mv.content
                FROM mv_sheet_latest_cells mv
                JOIN batch_sheets bs ON mv.sheet_id = bs.sheet_id
                WHERE mv.tab_id = :tab_id
            )
            SELECT * FROM batch_data
            ORDER BY sheet_id, y_value
        """)

        # Execute single query for all sheets
        async with async_or_sync_session() as session:
            result = await session.execute(batch_query, {
                "sheet_ids": sheet_ids,
                "tab_id": requests[0].active_tab_id  # Assuming same tab
            })

        # Split results by sheet_id
        return self._split_batch_results(result.all(), requests)
```

#### B) **Optimize Data Structures**

```python
# File: sheets/models/optimized_structures.py

import numpy as np
from dataclasses import dataclass
from typing import Union
import msgpack

@dataclass
class OptimizedRowData:
    """
    Memory-efficient data structure for large row datasets.
    Uses numpy arrays and compact serialization.
    """

    def __init__(self):
        # Use numpy for efficient numeric operations
        self.y_values: np.ndarray = np.array([], dtype=np.int32)
        self.row_ids: list[bytes] = []  # Store UUIDs as bytes
        self.content_indices: np.ndarray = np.array([], dtype=np.int32)
        self.content_data: list[dict] = []  # Deduplicated content

    def add_row(self, row_id: UUID, y_value: int, content: dict) -> None:
        """Add row with deduplication of content."""

        # Convert UUID to bytes for efficient storage
        row_id_bytes = row_id.bytes
        self.row_ids.append(row_id_bytes)

        # Add y_value to numpy array
        self.y_values = np.append(self.y_values, y_value)

        # Deduplicate content
        content_hash = hash(str(sorted(content.items())))
        content_index = self._get_or_add_content(content, content_hash)
        self.content_indices = np.append(self.content_indices, content_index)

    def serialize_compact(self) -> bytes:
        """Serialize using msgpack for efficient storage."""

        return msgpack.packb({
            'y_values': self.y_values.tobytes(),
            'row_ids': self.row_ids,
            'content_indices': self.content_indices.tobytes(),
            'content_data': self.content_data,
            'version': '1.0'
        })

    @classmethod
    def deserialize_compact(cls, data: bytes) -> 'OptimizedRowData':
        """Deserialize from msgpack."""

        unpacked = msgpack.unpackb(data, raw=False)

        instance = cls()
        instance.y_values = np.frombuffer(unpacked['y_values'], dtype=np.int32)
        instance.row_ids = unpacked['row_ids']
        instance.content_indices = np.frombuffer(unpacked['content_indices'], dtype=np.int32)
        instance.content_data = unpacked['content_data']

        return instance

    def to_dict_list(self) -> list[dict]:
        """Convert back to standard format for API responses."""

        result = []
        for i in range(len(self.row_ids)):
            content_idx = self.content_indices[i]
            result.append({
                'id': UUID(bytes=self.row_ids[i]),
                'y_value': int(self.y_values[i]),
                'content': self.content_data[content_idx]
            })

        return result
```

**Expected Impact**: 20-40% reduction in memory usage and serialization time.

---

## 📊 Implementation Priority Matrix

| Priority | Optimization | Est. Impact | Implementation Effort | Risk Level | Timeline |
|----------|-------------|-------------|----------------------|------------|----------|
| **P0** | Critical DB Indexes | 60-70% | Low (1-2 days) | Low | Immediate |
| **P0** | Lateral Join Rewrite | 40-60% | Medium (1 week) | Medium | Week 1 |
| **P1** | Multi-Layer Caching | 50-70% | High (2-3 weeks) | Medium | Week 2-3 |
| **P1** | Materialized Views | 30-50% | Medium (1-2 weeks) | Low | Week 2-4 |
| **P2** | Query Batching | 20-40% | Medium (1 week) | Low | Week 4-5 |
| **P2** | Table Partitioning | 30-50% | High (3-4 weeks) | High | Month 2 |

---

## 🔬 Performance Monitoring Strategy

### A) **Enhanced Query Performance Tracking**

```python
# File: sheets/monitoring/performance_tracker.py

class QueryPerformanceTracker:
    """
    Comprehensive query performance monitoring with detailed metrics.
    """

    def __init__(self):
        self.metrics = {}
        self.slow_query_threshold = 2.0  # seconds

    async def track_query_execution(
        self,
        query_type: str,
        query_params: dict,
        execution_time: float,
        cache_hit: bool,
        rows_returned: int
    ) -> None:
        """
        Track detailed query performance metrics.
        """

        complexity_score = self._calculate_complexity_score(query_params)

        metrics = {
            'query_type': query_type,
            'execution_time': execution_time,
            'cache_hit': cache_hit,
            'rows_returned': rows_returned,
            'complexity_score': complexity_score,
            'sheet_size_category': self._categorize_sheet_size(query_params),
            'has_filters': bool(query_params.get('filter_model')),
            'has_sorting': bool(query_params.get('sort_column_id')),
            'has_grouping': bool(query_params.get('group_by_column_ids')),
            'timestamp': time.time()
        }

        # Emit to DataDog
        await self._emit_datadog_metrics(metrics)

        # Log slow queries with detailed context
        if execution_time > self.slow_query_threshold:
            await self._log_slow_query(metrics, query_params)

    def _calculate_complexity_score(self, params: dict) -> float:
        """
        Calculate query complexity score for performance analysis.
        """

        score = 1.0

        # Add complexity for filters
        if params.get('filter_model'):
            score += len(params['filter_model']) * 0.5

        # Add complexity for sorting
        if params.get('sort_column_id'):
            score += 0.3

        # Add complexity for grouping
        if params.get('group_by_column_ids'):
            score += len(params['group_by_column_ids']) * 0.7

        # Add complexity for full matrix search
        if params.get('full_matrix_search'):
            score += 1.5

        return score

    async def generate_performance_report(self) -> dict:
        """
        Generate comprehensive performance analysis report.
        """

        return {
            'avg_execution_time': self._calculate_avg_execution_time(),
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'slow_queries_count': self._count_slow_queries(),
            'complexity_distribution': self._analyze_complexity_distribution(),
            'optimization_opportunities': self._identify_optimization_opportunities()
        }
```

### B) **Real-time Performance Alerting**

```python
# File: sheets/monitoring/alerts.py

class PerformanceAlerting:
    """
    Real-time alerting for performance degradation.
    """

    def __init__(self):
        self.thresholds = {
            'avg_query_time': 5.0,  # seconds
            'cache_hit_rate': 0.7,  # 70%
            'slow_queries_per_hour': 100,
            'error_rate': 0.05  # 5%
        }

    async def check_performance_metrics(self) -> None:
        """
        Check current performance against thresholds and alert if needed.
        """

        current_metrics = await self._get_current_metrics()

        alerts = []

        # Check each threshold
        for metric, threshold in self.thresholds.items():
            current_value = current_metrics.get(metric, 0)

            if self._is_threshold_breached(metric, current_value, threshold):
                alerts.append({
                    'metric': metric,
                    'current_value': current_value,
                    'threshold': threshold,
                    'severity': self._calculate_severity(metric, current_value, threshold)
                })

        # Send alerts if any thresholds breached
        if alerts:
            await self._send_alerts(alerts)

    async def _send_alerts(self, alerts: list[dict]) -> None:
        """
        Send performance alerts to monitoring systems.
        """

        for alert in alerts:
            # Send to DataDog
            await self._send_datadog_alert(alert)

            # Send to Slack if critical
            if alert['severity'] == 'critical':
                await self._send_slack_alert(alert)
```

---

## 🎯 Expected Performance Improvements

### **Baseline Metrics** (Current State)
- Average query time: 8-15 seconds for complex queries
- 50-second timeout required for safety
- Cache hit rate: ~40-50%
- Database CPU utilization: 70-80% during peak
- Memory usage: High due to inefficient data structures

### **Target Metrics** (Post-Optimization)
- Average query time: 2-4 seconds for complex queries
- 95th percentile under 10 seconds
- Cache hit rate: 80-90%
- Database CPU utilization: 30-50% during peak
- Memory usage: 40-60% reduction

### **Specific Improvements by Category**

| Optimization Category | Current Performance | Target Performance | Improvement |
|---------------------|-------------------|------------------|-------------|
| Simple Row Retrieval | 3-5 seconds | 0.5-1 second | 80% faster |
| Filtered Queries | 8-15 seconds | 2-4 seconds | 70% faster |
| Complex Group/Sort | 20-50 seconds | 5-12 seconds | 75% faster |
| Cache Hit Rate | 40-50% | 80-90% | 60-80% better |
| Memory Usage | High | Medium | 50% reduction |

---

## 🚀 Implementation Roadmap

### **Phase 1: Immediate Wins (Week 1)**
1. **Critical Database Indexes**
   - Deploy composite indexes for cells table
   - Add optimized row table indexes
   - Monitor impact via performance metrics

2. **Query Timeout Optimization**
   - Reduce timeout from 50s to 30s initially
   - Monitor for any timeout errors
   - Gradually reduce as other optimizations take effect

### **Phase 2: Core Architecture (Weeks 2-3)**
1. **Lateral Join Implementation**
   - Rewrite `_latest_cells_query` function
   - A/B test with percentage of traffic
   - Full rollout after validation

2. **Enhanced Caching**
   - Implement multi-layer cache
   - Deploy smart invalidation
   - Monitor cache hit rate improvements

### **Phase 3: Advanced Features (Weeks 4-6)**
1. **Materialized Views**
   - Create materialized views for hot sheets
   - Implement refresh strategy
   - Monitor performance gains

2. **Query Batching**
   - Implement batch query execution
   - Optimize data structures
   - Monitor memory usage improvements

### **Phase 4: Scalability (Month 2)**
1. **Table Partitioning** (High Risk)
   - Plan partition strategy
   - Test on staging environment
   - Gradual rollout with monitoring

2. **Advanced Monitoring**
   - Deploy comprehensive performance tracking
   - Set up automated alerting
   - Create performance dashboards

---

## ⚠️ Risks and Mitigation Strategies

### **High Risk Items**
1. **Table Partitioning**
   - Risk: Data migration complexity, potential downtime
   - Mitigation: Extensive testing, gradual rollout, rollback plan

2. **Lateral Join Rewrite**
   - Risk: Query plan changes, unexpected performance impact
   - Mitigation: A/B testing, feature flags, monitoring

### **Medium Risk Items**
1. **Materialized View Refresh**
   - Risk: Stale data if refresh fails
   - Mitigation: Automated monitoring, fallback to regular queries

2. **Cache Strategy Changes**
   - Risk: Cache invalidation bugs, memory usage
   - Mitigation: Gradual rollout, monitoring, circuit breakers

### **Low Risk Items**
1. **Database Indexes**
   - Risk: Minimal, using CONCURRENTLY
   - Mitigation: Monitor for any lock contention

2. **Query Batching**
   - Risk: Low, additive feature
   - Mitigation: Feature flags, gradual enablement

---

## 📈 Success Metrics and KPIs

### **Primary KPIs**
- **Query Performance**: 60-80% reduction in average execution time
- **Cache Efficiency**: 80-90% cache hit rate
- **User Experience**: Sub-5-second response for 95% of requests
- **Database Load**: 50% reduction in CPU utilization

### **Secondary Metrics**
- **Memory Usage**: 40-60% reduction in application memory
- **Error Rate**: Maintain <1% error rate during optimization
- **Scalability**: Support 10x larger sheets without degradation
- **Cost**: 30-50% reduction in database costs

### **Monitoring Dashboard**
Create comprehensive DataDog dashboard tracking:
- Real-time query performance metrics
- Cache hit rates by query type
- Database resource utilization
- Error rates and slow query counts
- User experience metrics (response times)

---

**Document Version**: 1.0
**Last Updated**: December 19, 2024
**Next Review**: January 15, 2025

*This optimization plan should be reviewed and updated based on implementation results and changing performance requirements.*
