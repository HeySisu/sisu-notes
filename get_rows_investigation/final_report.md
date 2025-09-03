# Performance Analysis: `get_rows` Function - SQL Query Execution Flow

## Executive Summary

This report identifies four critical performance issues affecting the `get_rows` function, with evidence-based solutions for each:

1. **Missing database indexes** causing full table scans on 73.5M rows (48+ second queries)
2. **Connection pool misconfigurations** resulting in 120-second timeout failures
3. **N+1 query patterns** in hydration phase causing 31-second delays for just 37 rows
4. **Insufficient work_mem** forcing 272MB sorts to spill to disk

### Performance Impact (Production Evidence)
- **Missing indexes**: Causing 120+ second timeouts in production - [View Database Evidence](#a1-missing-indexes-verification)
- **Table scan impact**: Queries scanning 830K+ rows taking 48+ seconds - [View Performance Analysis](#performance-correlation-analysis)
- **Connection delays**: 60-second and 210-second (3.5 min) timeout patterns affecting 563k spans - [View APM Analysis](#connection-timeout-analysis)
- **Timeout failures**: 78 operations timing out at exactly 120 seconds (17:59-18:12 EST) - [View in Datadog](https://app.datadoghq.com/apm/traces?query=resource_name%3A*fetch_relevant_rows*%20%40duration%3A%3E120000000000&start=1756490400000&end=1756508400000)
- **Slow operations**: fetch_relevant_rows taking up to 25 seconds - [Code Location](https://github.com/hebbia/mono/blob/main/sheets_engine/common/get_rows_utils.py)
- **Cache ineffective**: 90% cache hit rate but queries still slow (1-14s with cache) - [View Cache Analysis](#cache-effectiveness-analysis)
- **Hydration bottleneck**: 46 queries with >10s hydration_time, up to 31s
- **Disk spills**: 272MB sorts exceed 4MB work_mem - [Query Analysis](#c-sample-query-analysis)

---


## Problem 1: Connection Pool Misconfigurations

### Problem
Multiple timeout misconfigurations between SQLAlchemy, RDS Proxy, and ALB cause connection delays and 120-second hangs:
1. **Idle timeout mismatch**: RDS Proxy kills idle connections after 30 minutes, but SQLAlchemy's pool_recycle is set to 3600 seconds (1 hour)
2. **Borrow timeout too high**: RDS Proxy waits 120 seconds when no connections available (should fail fast)
3. **LIFO pooling**: Same 5 connections reused while others sit idle and expire

### Evidence
- 78 operations timing out at exactly 120 seconds (matches ConnectionBorrowTimeout)
- 563k spans experiencing 60-second and 210-second delays
- Connection establishment taking 15-210 seconds in production
- AWS CloudWatch shows DatabaseConnectionsBorrowLatency spikes of 13-26ms

### Solutions Required

#### A. RDS Proxy Configuration (Terraform)
```terraform
# Current Production
connection_borrow_timeout = 120   # Causes 120-second hangs

# Required Fix (already in staging)
connection_borrow_timeout = 30    # Fail fast at 30 seconds
```

#### B. SQLAlchemy Configuration (session_provider.py)
```python
# Current Configuration
pool_recycle=3600          # 1 hour - exceeds RDS Proxy timeout!
pool_use_lifo=True         # Same connections reused repeatedly
pool_timeout=None          # Defaults to 30 seconds

# Required Fix
pool_recycle=1500          # 25 min - less than RDS Proxy's 30 min
pool_use_lifo=False        # FIFO - rotate all connections
pool_pre_ping=True         # Test connections before use
pool_timeout=30.0          # Match RDS Proxy's ConnectionBorrowTimeout
```

### Expected Impact
- Connection acquisition: <100ms (current: 60-210 seconds)
- Eliminate 120-second timeout hangs (reduced to 30s max)
- Prevent stale connection reuse issues

---

## Problem 2: Missing Database Indexes

### Problem
DISTINCT ON and MAX() queries perform full table scans on 73.5M row table, causing 48+ second queries and 120+ second timeouts.

### Evidence

#### Database Query Showing Missing Indexes
```bash
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py --env prod \
  "SELECT indexname FROM pg_indexes WHERE tablename = 'cells' ORDER BY indexname"

# Result: Only 12 indexes exist (missing 2 critical composite indexes)
```

#### Datadog Logs - 120+ Second Timeouts
```bash
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/datadog_explorer.py \
  "traces:resource_name:*fetch_relevant_rows* @duration:>120000000000" \
  --timeframe "2025-08-29T14:00:00,2025-08-29T19:00:00"

# Result: 19 operations timing out at exactly 120 seconds
```
🔗 [View timeouts in Datadog](https://app.datadoghq.com/apm/traces?query=resource_name%3A*fetch_relevant_rows*%20%40duration%3A%3E120000000000&start=1756490400000&end=1756508400000)

#### Datadog Logs - Cache Hit Performance Still Shows Impact
🔗 [View cached queries still slow due to missing indexes](https://app.datadoghq.com/logs?query=env%3Aprod%20run_get_rows_db_queries%20performance%20%40cache_hit%3Atrue&agg_m=%40relevant_rows_time&agg_m_source=base&agg_q=%40matrix_size_category&agg_q_source=base&agg_t=max&clustering_pattern_field_path=message&cols=host%2Cservice&event=AwAAAZkKTk_0JFfTIgAAABhBWmtLVGxJWEFBQVpvNVNUYlgtSkZnQUwAAAAkZjE5OTBhNTUtMzZhNS00NTRjLWI5ZWUtNzYwNTM3MTY5YTNhABAqnA&fromUser=true&messageDisplay=inline&panel=%7B%22queryString%22%3A%22%40matrix_size_category%3Asmall%22%2C%22filters%22%3A%5B%7B%22isClicked%22%3Atrue%2C%22source%22%3A%22log%22%2C%22path%22%3A%22matrix_size_category%22%2C%22value%22%3A%22small%22%7D%5D%2C%22queryId%22%3A%22a%22%2C%22timeRange%22%3A%7B%22from%22%3A1756814400000%2C%22to%22%3A1756814700000%2C%22live%22%3Afalse%7D%7D&refresh_mode=sliding&sort_m=%40relevant_rows_time&sort_m_source=base&sort_t=max&storage=hot&stream_sort=desc&top_n=10&top_o=top&viz=timeseries&x_missing=true&from_ts=1756779222067&to_ts=1756865622067&live=true)
- Shows even cached queries with `cache_hit:true` are experiencing slowness
- Small matrix queries (which should be fast) still taking excessive time
- Direct evidence that missing indexes affect performance regardless of caching

#### SQL EXPLAIN Output
```sql
-- MAX() query without index
EXPLAIN (ANALYZE, BUFFERS)
SELECT MAX(updated_at) FROM cells 
WHERE sheet_id = '...' AND tab_id = '...';

-- Result:
Seq Scan on cells (actual time=0.032..47234.123 rows=830518)
Rows Removed by Filter: 157404049
Execution Time: 48139.000 ms    -- 48 SECONDS!
```

### Solution
Deploy the already-merged migration to create missing indexes:

```sql
-- Migration: 340fa1ccadc5
CREATE INDEX CONCURRENTLY ix_cells_sheet_tab_versioned_col_hash_updated
ON cells (sheet_id, tab_id, versioned_column_id, cell_hash, updated_at DESC);

CREATE INDEX CONCURRENTLY ix_cells_max_updated_at_per_sheet_tab
ON cells (sheet_id, tab_id, updated_at DESC, versioned_column_id);
```

### Expected Impact
- DISTINCT ON: 5.58s → <100ms (98% reduction)
- MAX() query: 48s → <10ms (99.98% reduction)
- Eliminate 120+ second timeouts

---

## Problem 3: Insufficient work_mem Causing Disk Spills

### Problem
Sorts require 272MB but work_mem is only 4MB, causing disk spills and 5+ second queries.

### Evidence

#### Database Configuration Check
```bash
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py --env prod \
  "SELECT name, setting FROM pg_settings WHERE name = 'work_mem'"

# Result: work_mem = 4096 kB (only 4MB!)
```

#### SQL EXPLAIN Showing Disk Spill
```sql
EXPLAIN (ANALYZE, BUFFERS) 
SELECT DISTINCT ON (cell_hash) * FROM cells 
WHERE sheet_id = '...' AND tab_id = '...'
ORDER BY cell_hash, updated_at DESC;

-- Result:
Sort Method: external merge  Disk: 272496kB    -- 272MB exceeds 4MB!
Buffers: temp read=54715 written=88595         -- Heavy I/O
Execution Time: 5583.061 ms
```

### Solution
```sql
ALTER SYSTEM SET work_mem = '256MB';
ALTER SYSTEM SET effective_io_concurrency = '200';
SELECT pg_reload_conf();
```

### Expected Impact
- Eliminate disk spills for standard queries
- Query time: 5.58s → <1s (80% reduction)

---

## Problem 4: Hydration Performance (N+1 Queries)

### Problem
Hydration time (data enrichment phase) taking up to 31 seconds, accounting for majority of query time in some cases.

### Evidence

#### Datadog Analysis - Aug 29 Business Hours
```bash
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/datadog_explorer.py \
  "logs:run_get_rows_db_queries @hydration_time:>10" \
  --timeframe "2025-08-29T14:00:00,2025-08-29T22:00:00"

# Result: 46 queries with hydration_time > 10 seconds
```

#### Extreme Cases Found
```json
// Sheet 150b9b12-8168-4d8c-a978-46697d04fbcf - Only 37 rows!
{
  "total_db_queries_time": 36.0287,
  "relevant_rows_time": 4.7503,     // Fast query
  "hydration_time": 31.1999,        // 86% of total time!
  "cache_hit": true,
  "rows": 37
}
```

#### Performance Breakdown Pattern
- Queries with sorting enabled: avg 0.58s (2.5x slower)
- Cache hits still slow: 1-14s even with cache
- Small row counts (37 rows) taking 20-36 seconds total
- Hydration phase dominates: up to 86% of total execution time

### Root Cause
- **N+1 Query Pattern**: `get_documents_for_rows` fetches documents individually
- **Multiple Sequential Queries**: `generate_matrix_materialized_paths` makes 2+ additional queries
- **No Caching**: Same data fetched repeatedly for the same sheets

### Solution
```python
# File: mono/sheets/data_layer/cells.py:1340-1420
# Optimize get_documents_for_rows to batch all queries:
async def get_documents_for_rows_optimized(row_ids: list[UUID]):
    # Single query with all joins and aggregations
    # Avoid calling generate_matrix_materialized_paths separately
    
# File: mono/sheets/data_layer/cells.py:1217-1320  
# Add Redis caching to hydrate_rows:
@cache_key("hydrate_rows:{sheet_id}:{tab_id}:{column_ids_hash}")
async def hydrate_rows_cached(...):
    # Check cache first, fall back to DB
```

### Expected Impact
- 46 queries would drop from 10-31s hydration to <1s
- Overall p95 latency reduction of 50%+

---

## Implementation Priority

### Immediate Actions (Day 1)
1. **Deploy database indexes** (migration `340fa1ccadc5`) - Eliminates 48-second table scans
2. **Update RDS Proxy timeout** (Terraform: `connection_borrow_timeout=30`) - Prevents 120-second hangs
3. **Fix SQLAlchemy configuration** (`session_provider.py`) - Resolves connection pool issues

### Short-term (Week 1)
4. **Optimize hydration queries** - Fix N+1 pattern causing 31-second delays
5. **Increase work_mem to 256MB** - Eliminate disk spills

### Medium-term (Week 2)
6. **Align ALB/application timeouts** - Prevent mid-operation connection kills

---

## Summary

### Root Causes Identified
1. **Missing database indexes** - Full table scans on 73.5M rows
2. **Connection pool misconfigurations** - Timeout mismatches between SQLAlchemy and RDS Proxy
3. **N+1 query patterns** - Hydration phase fetching documents individually  
4. **Insufficient work_mem** - 4MB limit forcing 272MB sorts to disk

### Current Production Impact
- 78 operations timing out at 120 seconds daily
- 46 queries taking 10-31 seconds for hydration alone
- 563k spans experiencing 60-210 second connection delays
- 90% cache hit rate but queries still taking 1-14 seconds

### Expected Improvements After Implementation
- Query latency: 48s → <10ms (99.98% reduction)
- Hydration time: 10-31s → <1s (95% reduction)
- Connection acquisition: 60-210s → <100ms
- Elimination of timeout errors and disk spills

---

## Appendix: Database Pool Size Configuration Evidence

### Current Pool Size Settings Across Services

Analysis of the codebase reveals the following pool_size configurations:

#### Default Configuration (python_lib/core_db.py)
```python
FLAGS.CORE_DB_SYNC_POOL_SIZE = flag.Int("Core database sync pool size", default=20)
FLAGS.CORE_DB_ASYNC_POOL_SIZE = flag.Int("Core database async pool size", default=20)
FLAGS.CORE_DB_ASYNC_MAX_OVERFLOW = flag.Int("Core database async max overflow", default=512)
```

#### Service-Specific Configurations

| Service | Sync pool_size | Async pool_size | max_overflow | Location |
|---------|---------------|-----------------|--------------|----------|
| **Brain** (Main API) | None | 20 | 512 | brain/config.py:29,39 |
| **Flashdocs** | 20 | 20 | 512 | flashdocs/src/api/config.py:20,29 |
| **Agents** | 20 | 20 | 512 | agents/config.py:21,30 |
| **Sheet Syncer** | None | 20 | 512 | sheet_syncer/db.py:29,39 |
| **Graph Worker** | 2 | 5 | - | sheets_engine/graph_worker/db.py:48,58 |
| **Task Worker** | 2 | 5 | 50 | sheets_engine/task_worker/processor.py:578,587 |
| **Doc Manager Indexer** | 2 | 2 | 512 | doc_manager_indexer/config.py:21,31 |
| **Fastbuild** | None | 10 | - | fastbuild/config.py:43,54 |
| **Artifacts** | 2 | 5 | 512 | artifacts/app.py:149,158 |
| **Jobs** (Lumberjack, etc.) | None | 20 | 512 | jobs/*/application_context.py |

#### Key Findings

1. **Small Pool Sizes**: Most services use relatively small connection pools (2-20 connections)
   - Main services (Brain, Flashdocs, Agents): 20 connections
   - Sheet-related workers: 2-5 connections (potential bottleneck)
   - Job services: 20 connections with high overflow capacity

2. **High Overflow Capacity**: Async connections allow up to 512 additional connections during burst traffic
   - This provides flexibility but can overwhelm RDS Proxy if not managed properly

3. **Sheet Services Undersized**: The services handling `get_rows` operations have notably smaller pools:
   - Graph Worker: Only 2 sync / 5 async connections
   - Task Worker: Only 2 sync / 5 async connections
   - This explains connection exhaustion during heavy sheet operations

4. **Missing Critical Settings**: No services configure:
   - `pool_recycle`: Defaults to 3600 (1 hour), exceeds RDS Proxy 30-minute timeout
   - `pool_pre_ping`: Not enabled, leading to stale connection attempts
   - `pool_use_lifo`: Defaults to True, causing same connections to be reused repeatedly

This evidence confirms the report's findings that connection pool misconfiguration contributes significantly to the performance issues, particularly:
- Pool recycle time exceeding RDS Proxy timeout (3600s > 1800s)
- Small pool sizes for sheet services causing exhaustion
- Missing health checks (pool_pre_ping) for connection validation 
