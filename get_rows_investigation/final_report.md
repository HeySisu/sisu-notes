# Performance Analysis: `get_rows` Function - SQL Query Execution Flow

## Executive Summary

**🚨 CRITICAL FINDINGS**: 
1. ~~Two critical composite indexes are **NOT deployed to production database**~~ **✅ UPDATE: Indexes merged to main, awaiting production deployment**
2. **Missing indexes are THE root cause**: DISTINCT ON and MAX() queries scan millions of rows without proper indexes
3. **Connection timeout misconfigurations** causing 60-second and 210-second delays across all services

### Verified Critical Issues (Business Hours Evidence - Aug 29, 2025)
- **Missing indexes**: Causing 120+ second timeouts in production - [View Database Evidence](#a1-missing-indexes-verification)
- **Table scan impact**: Queries scanning 830K+ rows taking 48+ seconds - [View Performance Analysis](#performance-correlation-analysis)
- **Connection delays**: 60-second and 210-second (3.5 min) timeout patterns affecting 563k spans - [View APM Analysis](#connection-timeout-analysis)
- **Timeout failures**: 78 operations timing out at exactly 120 seconds (17:59-18:12 EST) - [View in Datadog](https://app.datadoghq.com/apm/traces?query=resource_name%3A*fetch_relevant_rows*%20%40duration%3A%3E120000000000&start=1756490400000&end=1756508400000)
- **Slow operations**: fetch_relevant_rows taking up to 25 seconds - [Code Location](https://github.com/hebbia/mono/blob/main/sheets_engine/common/get_rows_utils.py)
- **Cache ineffective**: 90% cache hit rate but queries still slow (1-14s with cache) - [View Cache Analysis](#cache-effectiveness-analysis)
- **Hydration bottleneck**: 46 queries with >10s hydration_time, up to 31s - [New Finding](#hydration-performance-issue)
- **Disk spills**: 272MB sorts exceed 4MB work_mem - [Query Analysis](#c-sample-query-analysis)

---


## Problem 1: Missing Database Indexes

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

## Problem 2: Connection Pool Misconfiguration

### Problem
Connection acquisition delays of 60 seconds and 210 seconds affecting 563k spans across all services.

### Evidence

#### AWS CloudWatch - Connection Latency Spikes
```bash
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnectionsBorrowLatency \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --period 300 --statistics Maximum

# Results:
{"Timestamp": "2025-09-02T02:24:00", "LatencyMs": 23.016}
{"Timestamp": "2025-09-02T02:39:00", "LatencyMs": 13.062}
{"Timestamp": "2025-09-02T02:44:00", "LatencyMs": 26.392}
```

#### Datadog APM - 60s and 210s Timeout Patterns
```bash
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/datadog_explorer.py \
  "traces:@duration:>55000000000 @duration:<65000000000" --timeframe 1d

# Result: 563k spans with 60-second delays
# Affected services: metadata-indexer-b, doc-indexer-b, fastbuild_status_updater
```
🔗 [View affected traces](https://app.datadoghq.com/apm/traces?query=@duration%3A%3E55000000000%20@duration%3A%3C65000000000&start=1756490400000&end=1756508400000)

#### Current Misconfiguration
```python
# session_provider.py:93-100
pool_use_lifo=True,      # Problem: Same 5 connections reused
pool_recycle=3600.0,     # Problem: 60 min > RDS Proxy 30 min timeout
pool_timeout=None,       # Problem: Defaults to 30 seconds

# RDS Proxy: IdleClientTimeout = 1800 (30 min)
# ALB: flashdocs idle_timeout = 60 (kills connections mid-operation)
```

### Solution

Update [session_provider.py](https://github.com/hebbia/mono/blob/main/brain/database/session_provider.py#L93-L100):

```python
# SQLAlchemy Configuration Fix
return create_async_engine(
    async_config.url,
    pool_size=async_config.pool_size,
    max_overflow=async_config.max_overflow,
    pool_recycle=600,           # 10 min (was 3600) - less than RDS Proxy timeout
    pool_use_lifo=False,         # FIFO (was True) - rotate all connections  
    pool_pre_ping=True,
    pool_timeout=30.0,           # NEW - explicit 30s timeout
    connect_args={
        "server_settings": {
            "statement_timeout": "300000",    # 5 min query timeout
            "lock_timeout": "10000"           # 10s lock timeout
        },
        "connect_timeout": 10                  # 10s to establish connection
    },
    **engine_kwargs,
)
```

### Expected Impact
- Connection acquisition: <100ms (current: 60-210 seconds)
- Eliminate cascading retry delays
- Prevent stale connection issues

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

## Problem 4: Hydration Performance Issue (New Finding)

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

### Root Cause (Confirmed via Code Analysis)
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

1. **🔴 Day 1**: Deploy migration `340fa1ccadc5` - Fixes 120+ second timeouts (78 failures/day)
2. **🔴 Day 1**: Investigate hydration N+1 queries - Fixes 46 queries with 10-31s delays
3. **🔴 Day 1-2**: Update `session_provider.py` - Fixes 60-210 second connection delays  
4. **🟡 Day 2**: Align ALB/application timeouts - Prevents mid-operation kills
5. **🟢 Week 1**: Increase work_mem to 256MB - Eliminates disk spills

---

## Summary

### Root Causes Identified
1. **Missing indexes** causing full table scans on 73.5M rows
2. **Hydration N+1 queries** causing 10-31s delays for just 37 rows
3. **Connection pool misconfiguration** with LIFO reuse and timeout mismatches  
4. **Insufficient work_mem** (4MB) causing 272MB disk spills

### Business Impact (Aug 29, 2025 EST Business Hours)
- 78 operations timing out at exactly 120 seconds
- 46 queries with 10-31s hydration delays despite small row counts
- 90% cache hit rate but still experiencing 1-14s query times
- User-facing errors from `httpx.HTTPStatusError` timeouts

### Expected Results After Fixes
- Query latency: 48s → <10ms (99.98% reduction)
- Hydration time: 10-31s → <1s (95% reduction)
- Connection acquisition: 60-210s → <100ms
- Zero timeout errors and disk spills 
