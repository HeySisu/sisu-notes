# Hydration Performance Optimization Plan

## Root Cause Analysis

The hydration phase (`hydration_time`) is taking 10-31 seconds for queries with as few as 37 rows. After analyzing the code, I've identified several performance bottlenecks:

### 1. Missing Database Indexes (Already Addressed)
**Status**: ✅ Migration already created (`340fa1ccadc5`)

The DISTINCT ON query pattern needs these indexes:
```sql
-- Already in migration, needs deployment
CREATE INDEX ix_cells_sheet_tab_versioned_col_hash_updated 
ON cells (sheet_id, tab_id, versioned_column_id, cell_hash, updated_at DESC);

CREATE INDEX ix_cells_max_updated_at_per_sheet_tab
ON cells (sheet_id, tab_id, updated_at DESC, versioned_column_id);
```

### 2. N+1 Query Pattern in Document Fetching
**Location**: `mono/sheets/data_layer/cells.py:1340-1420`

The `get_documents_for_rows` function has several inefficiencies:
1. Fetches documents one at a time for each row
2. Calls `generate_matrix_materialized_paths` which makes additional queries:
   - Query for all document titles
   - Query for all folder names
3. Processes paths sequentially instead of batching

### 3. Inefficient Hydrate Rows Query
**Location**: `mono/sheets/data_layer/cells.py:1217-1320`

The `hydrate_rows` function uses a complex CTE with DISTINCT ON that:
- Scans all cells for the sheet/tab combination
- Sorts by cell_hash and updated_at DESC
- Applies DISTINCT ON cell_hash
- This happens even for small datasets (37 rows taking 31s)

## Optimization Recommendations

### Priority 1: Deploy Existing Index Migration (Immediate)
```bash
# Deploy migration 340fa1ccadc5 to production
# This will help with the DISTINCT ON query performance
```

### Priority 2: Optimize Document Fetching (1-2 days)

#### Current Code (N+1 Pattern):
```python
# get_documents_for_rows makes multiple queries
documents_query = (
    get_documents_with_v2_base_query()
    .join(Row, Row.repo_doc_id == Document.id)
    .outerjoin(DocumentListDocument, ...)
    .outerjoin(DocumentList, ...)
    .where(Row.id.in_(row_ids))
)
# Then calls generate_matrix_materialized_paths which makes more queries
```

#### Optimized Approach:
```python
async def get_documents_for_rows_optimized(
    row_ids: list[UUID],
) -> dict[str, dict[str, Any]]:
    # Batch fetch all data in a single query with proper joins
    async with async_or_sync_session() as s:
        # Use a single optimized query with all necessary joins
        documents_query = (
            select(
                Document,
                DocumentV2,
                DocumentListDocument.path,
                DocumentList.name,
                # Pre-fetch folder context in the same query
                func.array_agg(
                    func.json_build_object(
                        'folder_id', DocumentListDocument.id,
                        'folder_name', DocumentListDocument.name
                    )
                ).label('folder_context')
            )
            .join(Row, Row.repo_doc_id == Document.id)
            .outerjoin(DocumentListDocument, ...)
            .outerjoin(DocumentList, ...)
            .where(Row.id.in_(row_ids))
            .group_by(Document.id, DocumentV2.id, DocumentListDocument.path, DocumentList.name)
        )
        
        result = await s.execute(documents_query)
        # Process results once without additional queries
        return process_documents_batch(result)
```

### Priority 3: Add Caching Layer for Hydration (3-5 days)

Since the same sheets are often queried multiple times, add a Redis cache:

```python
@cache_key("hydrate_rows:{sheet_id}:{tab_id}:{column_ids_hash}:{row_ids_hash}")
async def hydrate_rows_cached(
    sheet_id: str,
    active_tab_id: str,
    column_ids: list[str],
    row_ids: list[UUID],
    user_id: Optional[str] = None,
) -> list[dict[str, Any]]:
    # Check Redis cache first
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Fall back to database query
    result = await hydrate_rows_original(...)
    
    # Cache for 5 minutes
    await redis_client.setex(cache_key, 300, json.dumps(result))
    return result
```

### Priority 4: Connection Pool Tuning (Already Documented)

Update `mono/brain/database/session_provider.py`:
```python
pool_recycle=600,           # 10 min (was 3600)
pool_use_lifo=False,        # FIFO (was True)
pool_pre_ping=True,
pool_timeout=30.0,          # Explicit timeout
```

## Expected Performance Improvements

### With Index Deployment Only:
- DISTINCT ON query: 245ms → ~50ms (80% reduction)
- Overall hydration: 10-31s → 8-25s (modest improvement)

### With All Optimizations:
- Document fetching: 5-20s → <1s (95% reduction)
- Hydration caching: 0ms for cache hits
- Overall hydration: 10-31s → <1s for most queries (95%+ reduction)

## Implementation Steps

1. **Day 1**: Deploy migration `340fa1ccadc5`
2. **Day 1-2**: Implement document fetching optimization
3. **Day 2-3**: Add Redis caching for hydration
4. **Day 3**: Update connection pool settings
5. **Day 4**: Monitor and tune based on metrics

## Validation Queries

```bash
# Check if indexes are deployed
.venv/bin/python tools/db_explorer.py --env prod \
  "SELECT indexname FROM pg_indexes WHERE tablename = 'cells' AND indexname LIKE '%hash_updated%'"

# Monitor hydration performance
.venv/bin/python tools/datadog_explorer.py \
  "logs:run_get_rows_db_queries @hydration_time:>5" \
  --timeframe "2025-08-30T14:00:00,2025-08-30T22:00:00"

# Check specific slow sheet performance
.venv/bin/python tools/db_explorer.py --env prod \
  "EXPLAIN (ANALYZE, BUFFERS) SELECT DISTINCT ON (cell_hash) * FROM cells \
   WHERE sheet_id = '150b9b12-8168-4d8c-a978-46697d04fbcf' \
   AND tab_id = '605c9092-646e-4c9a-b699-515c5ada192c' \
   ORDER BY cell_hash, updated_at DESC LIMIT 100"
```

## Code Changes Required

### File: `mono/sheets/data_layer/cells.py`
- Optimize `get_documents_for_rows` function (lines 1340-1420)
- Add caching to `hydrate_rows` function (lines 1217-1320)

### File: `mono/doc_manager/data_layer/utils.py`
- Optimize `generate_matrix_materialized_paths` (lines 249-267)
- Batch queries in `get_doc_folder_context` (lines 202-246)

### File: `mono/brain/database/session_provider.py`
- Update connection pool settings (lines 93-100)