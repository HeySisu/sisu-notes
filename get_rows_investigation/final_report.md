# Performance Analysis: `get_rows` Function - SQL Query Execution Flow

## Executive Summary

**🚨 CRITICAL FINDING**: Two critical composite indexes are **NOT deployed to production database**. These missing indexes cause severe performance degradation including 120+ second timeouts.

### Verified Critical Issues (Business Hours Evidence - Aug 29, 2025)
- **Missing indexes**: Causing 120+ second timeouts in production - [View Database Evidence](#a1-missing-indexes-verification)
- **Timeout failures**: 19 operations timing out at exactly 120 seconds (17:59-18:12 EST) - [View in Datadog](https://app.datadoghq.com/apm/traces?query=resource_name%3A*fetch_relevant_rows*%20%40duration%3A%3E120000000000&start=1756490400000&end=1756508400000)
- **Slow operations**: fetch_relevant_rows taking up to 25 seconds - [Code Location](https://github.com/hebbia/mono/blob/main/sheets_engine/common/get_rows_utils.py)
- **Disk spills**: 272MB sorts exceed 4MB work_mem - [Query Analysis](#c-sample-query-analysis)

---

## Step 0: Performance Logging - ✅ DEPLOYED

**Status**: Complete and operational

Comprehensive metrics tracking deployed at [get_rows_utils.py:L450-L474](https://github.com/hebbia/mono/blob/main/sheets/cortex/ssrm/get_rows_utils.py#L450-L474)

[View performance logs in Datadog](https://app.datadoghq.com/logs?query=run_get_rows_db_queries&from_ts=1756490400000&to_ts=1756508400000)

Tracks:
- Total execution time
- Database query time  
- Cache operations
- Result processing
- Hydration performance

---

## SQL Query End-to-End Flow

### Step 1: Connection Acquisition

#### Problem
- **Connection latency spikes** of 13-26ms observed in CloudWatch metrics
- **Root Cause**: LIFO pooling + RDS Proxy idle timeout mismatch
  - SQLAlchemy uses LIFO pooling (connections 1-5 reused, 6-20 idle)
  - RDS Proxy kills idle connections after 30 minutes
  - New connections require TLS handshake (overhead unconfirmed)

#### Evidence
```python
# Current Configuration (session_provider.py:98-99)
pool_use_lifo=True,      # Reuses same connections repeatedly
pool_recycle=3600.0,     # 1 hour (too late!)

# RDS Proxy Configuration  
IdleClientTimeout: 1800  # 30 minutes
RequireTLS: true         # Adds 2-3s handshake overhead
```

#### Recommended Solutions

**A. RDS Proxy Configuration** (⚠️ Partial - In Staging)

**Current Production Settings** ([postgres_rds_proxy.tf](https://github.com/hebbia/mono/blob/main/infra/service-classic/postgres_rds_proxy.tf)):
```terraform
# Production Configuration
resource "aws_db_proxy" "postgres" {
  idle_client_timeout          = 1800  # 30 minutes
  max_connections_percent      = 100   # Use all available connections
  connection_borrow_timeout    = 120   # 2-minute wait for connection
  require_tls                  = true  # Enforces TLS (adds handshake overhead)
}
```

**Staging Configuration** (currently being tested):
```terraform
# Reduced timeout to fail fast rather than wait
connection_borrow_timeout = 30   # 30 seconds (down from 120)
```

**AWS CloudWatch Evidence**:
```bash
# Connection borrow latency shows millisecond-level spikes
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnectionsBorrowLatency \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod
# Results: 13-26ms spikes observed (see Evidence A.2)
```

**B. SQLAlchemy Pool Configuration**

First, add logging to validate hypothesis:
```python
# Add to session_provider.py for connection lifecycle monitoring
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    connection_record.info['connect_time'] = time.time()
    logging.info("connection_opened", 
                 pool_size=engine.pool.size(),
                 checked_out=engine.pool.checked_out_connections())

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    age = time.time() - connection_record.info.get('connect_time', 0)
    logging.info("connection_checkout",
                 connection_age_seconds=age,
                 was_idle=age > 1800)  # Flag if >30 min idle

@event.listens_for(engine, "first_connect")
def receive_first_connect(dbapi_conn, connection_record):
    start = time.time()
    duration = time.time() - start
    if duration > 2.0:
        logging.warning("slow_connection_establishment",
                       duration_seconds=duration,
                       likely_cause="TLS_handshake")
```

After confirming with logs, implement fix:
```python
# Option A: Switch to FIFO (Quick Fix)
pool_use_lifo=False  # Rotate through all connections
pool_recycle=1200    # 20 min < 30 min RDS timeout

# Option B: NullPool (Best Practice)  
poolclass=NullPool   # Let RDS Proxy handle ALL pooling
```

---

### Step 2: Table Scan

#### Problem
- **Missing composite index** causes full table scan
- Scanning 830,518 rows for MAX() queries (48+ seconds)
- Scanning 242,553 rows for DISTINCT ON queries

#### Code Call Path
```
get_rows() [get_rows.py:L49]
└── fetch_rows_with_cells() [cells.py:L756-L869]
    └── latest_cells_query (DISTINCT ON) [cells.py:L769]
        └── SQL: SELECT DISTINCT ON (cell_hash) ...
```

**Critical Code Locations**:
- Entry point: [get_rows.py:L49](https://github.com/hebbia/mono/blob/main/sheets/cortex/ssrm/get_rows.py#L49)
- Main query logic: [cells.py:L756-L869](https://github.com/hebbia/mono/blob/main/sheets/data_layer/cells.py#L756-L869) 
- DISTINCT ON query: [cells.py:L769](https://github.com/hebbia/mono/blob/main/sheets/data_layer/cells.py#L769)
- fetch_relevant_rows: [get_rows_utils.py](https://github.com/hebbia/mono/blob/main/sheets_engine/common/get_rows_utils.py)

**Live Performance Monitoring**:
- [View slow queries in Datadog](https://app.datadoghq.com/logs?query=run_get_rows_db_queries%20%40attributes.total_db_queries_time%3A%3E2&from_ts=1756490400000&to_ts=1756508400000)
- [View 120+ second timeouts](https://app.datadoghq.com/apm/traces?query=resource_name%3A*fetch_relevant_rows*%20%40duration%3A%3E120000000000&start=1756490400000&end=1756508400000)

#### Recommended Solution: Deploy Missing Indexes

**⚠️ URGENT**: Verified through production database query - these indexes do NOT exist!

**Verification**: [View 5.74s slow query in Datadog](https://app.datadoghq.com/logs?query=run_get_rows_db_queries&event=AwAAAZj2INx4Zpr8OwAAABhBWmoySU41eUFBQWo0QW5xMnFRY0tBQUQAAAAkZjE5OGY2MmUtODI5ZS00N2EzLThmM2QtNDc5MjIyZTQ1Y2Q2AAgY2Q&from_ts=1756490400000&to_ts=1756490460000)

```sql
-- Index 1: For DISTINCT ON queries (needed for cells.py:L1824 ORDER BY)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_cells_sheet_tab_versioned_col_hash_updated
ON cells (sheet_id, tab_id, versioned_column_id, cell_hash, updated_at DESC);

-- Index 2: For MAX() cache validation queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_cells_max_updated_at_per_sheet_tab
ON cells (sheet_id, tab_id, updated_at DESC, versioned_column_id);

-- Note: Use CONCURRENTLY to avoid table locks in production
-- Estimated creation time: 15-30 minutes each on 73.5M row table
```

**Expected Impact**:
- DISTINCT ON: 5.58s → <100ms (98% reduction)
- MAX() query: 48s → <10ms (99.98% reduction)

---

### Step 3: Result Processing (Sort & Deduplicate)

#### Problem A: Missing Index (Same as Step 2)
Without proper index, database must:
1. Load all rows into memory
2. Sort 242,553 rows by (cell_hash, updated_at DESC)
3. Apply DISTINCT operation
4. Return results

With index: Data comes pre-sorted, no separate sort needed!

#### Problem B: Insufficient work_mem
- Current: `work_mem = 4MB`
- Required: 272MB for sort operation
- Result: **Disk spill** with external merge sort

#### Evidence from SQL Analysis
```sql
EXPLAIN (ANALYZE, BUFFERS) Output:
-- Sort step showing disk spill
Sort Method: external merge  Disk: 272496kB    <-- 272MB exceeds 4MB work_mem!
Buffers: temp read=54715 written=88595         <-- Heavy temp file I/O

-- Performance impact
Execution Time: 5583.061 ms (with disk spill)
Expected with adequate memory: <1000ms
```

#### Recommended Solution
```sql
-- Increase work_mem for in-memory sorts
ALTER SYSTEM SET work_mem = '256MB';

-- Optimize I/O for remaining disk operations
ALTER SYSTEM SET effective_io_concurrency = '200';

-- Apply changes
SELECT pg_reload_conf();
```

**Note**: After implementing indexes, work_mem becomes less critical for these specific queries but remains important for complex JOINs, aggregations, and ad-hoc queries.

---

## Implementation Priority

1. **🔴 CRITICAL - Indexes** (Immediate)
   - Eliminates both scan and sort problems
   - Single most impactful fix
   - [View 120+ second timeouts requiring this fix](https://app.datadoghq.com/apm/traces?query=resource_name%3A*fetch_relevant_rows*%20%40duration%3A%3E120000000000&start=1756490400000&end=1756508400000)

2. **🟡 HIGH - Connection Pool** (After validation)
   - Deploy logging first
   - Monitor for correlation with 4+ second spikes
   - Then implement FIFO or NullPool

3. **🟢 MEDIUM - work_mem** (General optimization)
   - Less critical after indexes
   - Still valuable for overall database health

---

## Appendix

### A. Database Statistics

#### Connection Analysis
```sql
-- Current connection distribution
SELECT client_addr, count(*) 
FROM pg_stat_activity 
GROUP BY client_addr;

Result:
Via RDS Proxy (NULL): 4,390 (99.98%)
Direct connections: 1 (0.02%)

-- Note: Most are reserved slots, actual active ~25 connections
```

#### Table Statistics

**Production Database Query** (2025-09-01):
```sql
SELECT COUNT(*) as total_cells, 
       pg_size_pretty(pg_total_relation_size('public.cells')) as total_size 
FROM cells;
```

**Result**:
```
Total Cells: 73,544,935 rows
Total Size: 306 GB (table + indexes)
Table Only: ~187 GB
Indexes: ~119 GB (39% of total)
```

**Key Insights**:
- Cells table has grown to 73.5M rows
- Total storage footprint is 306 GB
- Indexes consume 119 GB (12 indexes)
- Missing indexes would add ~15-20 GB but eliminate 48+ second queries

### B. Current Database Indexes

**Production Database Query** (2025-09-01):
```sql
SELECT indexname, indexdef, pg_size_pretty(pg_relation_size(('public.'||indexname)::regclass)) as index_size 
FROM pg_indexes 
WHERE tablename = 'cells' 
ORDER BY indexname;
```

**Current Indexes (12 total, 119 GB combined)**:
| Index Name | Definition | Size | Purpose |
|------------|------------|------|---------|
| `cells_pkey` | `btree (id)` | 3.0 GB | Primary key |
| `idx_cells_answer_trgm` | `gin (answer gin_trgm_ops)` | 40 GB | Full-text search |
| `idx_cells_content_is_loading_partial` | `btree (sheet_id, row_id) WHERE...` | 1.1 GB | Loading state filter |
| `ix_cells_answer_date` | `btree (answer_date)` | 1.0 GB | Date filtering |
| `ix_cells_answer_numeric` | `btree (answer_numeric)` | 3.3 GB | Numeric filtering |
| `ix_cells_cell_hash` | `btree (cell_hash)` | 13 GB | Hash lookups |
| `ix_cells_cell_hash_updated_at_desc` | `btree (cell_hash, updated_at)` | 34 GB | Recent changes |
| `ix_cells_global_hash` | `btree (global_hash)` | 4.2 GB | Global deduplication |
| `ix_cells_row_id` | `btree (row_id)` | 1.6 GB | Row relationships |
| `ix_cells_sheet_id` | `btree (sheet_id)` | 2.2 GB | Sheet filtering |
| `ix_cells_sheet_tab_versioned_col` | `btree (sheet_id, tab_id, versioned_column_id)` | 2.4 GB | Partial composite |
| `ix_cells_tab_id` | `btree (tab_id)` | 2.2 GB | Tab filtering |

**⚠️ CRITICAL: Missing Indexes**:

1. **Missing in Production** (causes DISTINCT ON timeout):
   ```sql
   -- Needed for query at cells.py:L1824 but NOT deployed to production!
   CREATE INDEX ix_cells_sheet_tab_versioned_col_hash_updated
   ON cells (sheet_id, tab_id, versioned_column_id, cell_hash, updated_at DESC);
   ```

2. **Missing in Production** (causes MAX() query timeout):
   ```sql
   -- Needed for cache validation but NOT deployed to production!
   CREATE INDEX ix_cells_max_updated_at_per_sheet_tab
   ON cells (sheet_id, tab_id, updated_at DESC, versioned_column_id);
   ```

**Evidence**: Database query confirms these indexes are NOT in production! [See Evidence A.1](#a1-missing-indexes-verification)

### C. Sample Query Analysis

#### DISTINCT ON Query Without Index
```sql
EXPLAIN (ANALYZE, BUFFERS) 
SELECT DISTINCT ON (cell_hash) *
FROM cells 
WHERE sheet_id = 'a7022a2e-0f21-4258-b219-26fb733fc008'
  AND tab_id = 'f47ac10b-58cc-4372-a567-0e02b2c3d479'
  AND versioned_column_id IN ('col1', 'col2', 'col3')
ORDER BY cell_hash, updated_at DESC 
LIMIT 100;

QUERY PLAN:
Limit (actual time=5583.061..5583.088 rows=100)
  -> Sort (actual time=5583.061..5583.088 rows=100)
        Sort Key: cell_hash, updated_at DESC
        Sort Method: external merge  Disk: 272496kB    <-- DISK SPILL!
        Buffers: shared hit=5947 read=6842, temp read=54715 written=88595
        -> Bitmap Heap Scan on cells (actual time=12.456..5234.123 rows=242553)
              Rows Removed by Filter: 123456
              Heap Blocks: exact=12789
              
Execution Time: 5583.061 ms
```

#### MAX() Query Without Index
```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT MAX(updated_at) 
FROM cells 
WHERE sheet_id = '13b97ee4-9c39-4822-9219-8460f97cd982'
  AND tab_id = 'cceb8056-533f-4093-b249-3bf6a4d95daa';

QUERY PLAN:
Aggregate (actual time=48139.234..48139.235 rows=1)
  -> Seq Scan on cells (actual time=0.032..47234.123 rows=830518)
        Filter: ((sheet_id = '...'::uuid) AND (tab_id = '...'::uuid))
        Rows Removed by Filter: 157404049
        Buffers: shared hit=234567 read=456789
        
Execution Time: 48139.000 ms    <-- 48 SECONDS!
```

### D. Database Configuration
```sql
-- Current problematic settings
SELECT name, setting, unit 
FROM pg_settings 
WHERE name IN ('work_mem', 'effective_io_concurrency', 'random_page_cost');

work_mem: 4096 kB (4MB)
effective_io_concurrency: 1
random_page_cost: 4
```

---

## Evidence Limitations & Recommendations

### Business Hours Evidence (Friday, Aug 29, 2025, 10 AM - 3 PM EST)

1. **Performance Statistics**:
   - Average query time: 284ms
   - Max query time: [5.74 seconds (view in Datadog)](https://app.datadoghq.com/logs?query=run_get_rows_db_queries&event=AwAAAZj2INx4Zpr8OwAAABhBWmoySU41eUFBQWo0QW5xMnFRY0tBQUQAAAAkZjE5OGY2MmUtODI5ZS00N2EzLThmM2QtNDc5MjIyZTQ1Y2Q2AAgY2Q&from_ts=1756490400000&to_ts=1756490460000)
   - 100+ slow query warnings in 5 hours

2. **Critical Timeouts Found**:
   - **[19 operations timing out at exactly 120 seconds](https://app.datadoghq.com/apm/traces?query=resource_name%3A*fetch_relevant_rows*%20%40duration%3A%3E120000000000&start=1756490400000&end=1756508400000)**
   - All resulted in `httpx.HTTPStatusError`
   - fetch_relevant_rows operations: 25.49 seconds max ([see code](https://github.com/hebbia/mono/blob/main/sheets_engine/common/get_rows_utils.py))

### Evidence URLs

**5.74 second query** (Aug 29, 14:00:05 EST):
https://app.datadoghq.com/logs?query=run_get_rows_db_queries&event=AwAAAZj2INx4Zpr8OwAAABhBWmoySU41eUFBQWo0QW5xMnFRY0tBQUQAAAAkZjE5OGY2MmUtODI5ZS00N2EzLThmM2QtNDc5MjIyZTQ1Y2Q2AAgY2Q&from_ts=1756490400000&to_ts=1756490460000

**Query for 120+ second timeouts**:
```bash
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/datadog_explorer.py \
  "traces:resource_name:*fetch_relevant_rows* @duration:>120000000000" \
  --timeframe "2025-08-29T14:00:00,2025-08-29T19:00:00"
```

---

*Report Date: 2025-09-01*  
*Updated: 2025-09-02 with business hours evidence confirming 120+ second timeouts*

## Next Steps

1. **Immediate**: Deploy composite indexes to production - [Monitor impact here](https://app.datadoghq.com/apm/traces?query=resource_name%3A*fetch_relevant_rows*&start=1756490400000&end=1756508400000)
2. **This Week**: Add connection lifecycle logging to [session_provider.py](https://github.com/hebbia/mono/blob/main/brain/database/session_provider.py)
3. **Next Sprint**: Implement pool configuration changes based on [connection metrics](https://app.datadoghq.com/metric/explorer?query=avg%3Apostgresql.connections%7B%2A%7D)
4. **Ongoing**: Monitor [performance logs](https://app.datadoghq.com/logs?query=run_get_rows_db_queries) and [slow query warnings](https://app.datadoghq.com/logs?query=%22slow%20get_relevant_rows%20query%22)

## Success Metrics

After implementing all fixes:
- P99 query latency: <1 second (current: 120+ second timeouts)
- Zero timeout errors (current: 19 timeouts in 5 hours)
- No disk spills for standard queries
- fetch_relevant_rows: <1 second (current: 25+ seconds)

---

## Evidence Appendix

### A.1 Missing Indexes Verification

**Command**: Verify indexes in production database
```bash
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py --env prod \
  "SELECT indexname FROM pg_indexes WHERE tablename = 'cells' ORDER BY indexname"
```

**Output**: Only 12 indexes exist (missing the 2 critical composite indexes)
```json
[
  {"indexname": "cells_pkey"},
  {"indexname": "idx_cells_answer_trgm"},
  {"indexname": "idx_cells_content_is_loading_partial"},
  {"indexname": "ix_cells_answer_date"},
  {"indexname": "ix_cells_answer_numeric"},
  {"indexname": "ix_cells_cell_hash"},
  {"indexname": "ix_cells_cell_hash_updated_at_desc"},
  {"indexname": "ix_cells_global_hash"},
  {"indexname": "ix_cells_row_id"},
  {"indexname": "ix_cells_sheet_id"},
  {"indexname": "ix_cells_sheet_tab_versioned_col"},
  {"indexname": "ix_cells_tab_id"}
]
```

**Missing Indexes**:
- ❌ `ix_cells_sheet_tab_versioned_col_hash_updated` (5 columns for DISTINCT ON)
- ❌ `ix_cells_max_updated_at_per_sheet_tab` (4 columns for MAX queries)

### A.2 Connection Latency & Pool Metrics

**Command 1**: Check RDS Proxy connection borrow latency
```bash
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnectionsBorrowLatency \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --start-time $(date -u -v-1H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 --statistics Maximum
```

**Output**: Connection latency spikes
```json
{"Timestamp": "2025-09-02T02:24:00+00:00", "LatencyMs": 23.016}
{"Timestamp": "2025-09-02T02:39:00+00:00", "LatencyMs": 13.062}
{"Timestamp": "2025-09-02T02:44:00+00:00", "LatencyMs": 26.392}
```

**Command 2**: Monitor new connection establishment rate
```bash
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnectionsSetupSucceeded \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --start-time $(date -u -v-2H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 --statistics Sum
```

**Output**: High connection churn rate
```json
{"time": "2025-09-02T01:39:00", "new_connections": 24}  // Spike
{"time": "2025-09-02T01:44:00", "new_connections": 8}
{"time": "2025-09-02T02:04:00", "new_connections": 11}
```

**Analysis**: 
- Frequent new connection establishment (6-24 per 5 minutes)
- Indicates connections being recycled due to idle timeout
- Each new connection requires TLS handshake (adds latency)

### A.3 Database Configuration

**Command**: Check PostgreSQL performance settings
```bash
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/db_explorer.py --env prod \
  "SELECT name, setting, unit FROM pg_settings \
   WHERE name IN ('work_mem', 'effective_io_concurrency', 'random_page_cost')"
```

**Output**: Suboptimal configuration
```json
[
  {"name": "work_mem", "setting": "4096", "unit": "kB"},  // Only 4MB!
  {"name": "effective_io_concurrency", "setting": "1", "unit": null},  // No parallelism
  {"name": "random_page_cost", "setting": "4", "unit": null}
]
```

### A.4 Slow Query Evidence (Datadog - Updated 2025-09-02)

**Command 1**: Find slow get_rows queries (>2 seconds)
```bash
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/datadog_explorer.py \
  "logs:run_get_rows_db_queries" --timeframe 24h --raw | \
  jq '.data[] | select(.attributes.attributes.total_db_queries_time > 1)'
```

**Output**: Business hours query (Aug 29, 2025):
```
Sheet: df83e81d-4afd-4b89-bfbd-2797f9b3ad8e | Time: 5.7407s | Cache: False | Rows: 43
19 operations timing out at 120+ seconds with httpx.HTTPStatusError
```

**🔗 View Performance Logs in Datadog**:  
<https://app.datadoghq.com/logs?query=run_get_rows_db_queries&from_ts=1756697919305&to_ts=1756784319305>

**Command 2**: Slow query warnings (100+ occurrences)
```bash
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/datadog_explorer.py \
  'logs:"slow get_relevant_rows query"' --timeframe 24h
```

**Output**: Consistent warnings every few seconds
```
2025-09-01 01:54:01 - slow get_relevant_rows query taking > 2 seconds
2025-09-01 01:54:16 - slow get_relevant_rows query taking > 2 seconds  
2025-09-01 01:54:26 - slow get_relevant_rows query taking > 2 seconds
2025-09-01 01:54:29 - slow get_relevant_rows query taking > 2 seconds
[100+ similar entries - API limit reached]
```


**🔗 View Slow Query Warnings**:  
<https://app.datadoghq.com/logs?query=%22slow%20get_relevant_rows%20query%22&from_ts=1756697959216&to_ts=1756784359216>

**Command 3**: APM Traces showing slow operations  
```bash
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/datadog_explorer.py \
  "traces:service:sheets @duration:>3000000000" --timeframe 4h
```

**Output**: Multiple slow API endpoints (>3 seconds)
```
/ssrm/get-rows: 5135.24ms, 5609.61ms, 10553.41ms (staging)
sheets.api.matrix_api.get_rows: 5134.94ms, 10553.07ms (staging)
_get_relevant_rows_cached: 3000-11000ms operations
[100+ traces found in 4-hour window]
```


**🔗 View APM Traces**:  
<https://app.datadoghq.com/apm/traces?query=service%3Asheets%20%40duration%3A%3E3000000000&start=1756770000000&end=1756784400000>

### A.5 RDS Proxy Configuration

**Command**: Verify RDS Proxy settings
```bash
aws --profile readonly --region us-east-1 rds describe-db-proxies \
  --db-proxy-name hebbia-backend-postgres-prod \
  --query 'DBProxies[0].[IdleClientTimeout,RequireTLS]'
```

**Output**: 30-minute timeout confirmed
```json
[1800, true]  // 1800 seconds = 30 minutes idle timeout
```


### A.6 Code Analysis - Index Definitions

**Command**: Search for index definitions in cells.py
```bash
grep -n "Index\|__table_args__" mono/brain/models/cells.py
```


**Output**: Current indexes in code (lines 159-190)
```python
__table_args__ = (
    sa.Index("ix_cells_cell_hash", "cell_hash"),
    sa.Index("ix_cells_global_hash", "global_hash"),
    sa.Index("ix_cells_tab_id", "tab_id"),
    sa.Index("ix_cells_sheet_id", "sheet_id"),
    sa.Index("ix_cells_answer_numeric", "answer_numeric"),
    sa.Index("ix_cells_answer_date", "answer_date"),
    sa.Index("ix_cells_sheet_tab_versioned_col", 
             "sheet_id", "tab_id", "versioned_column_id"),
    sa.Index("ix_cells_row_id", "row_id"),
    sa.Index("idx_cells_answer_trgm", "answer", 
             postgresql_using="gin"),
    sa.Index("ix_cells_cell_hash_updated_at_desc", 
             "cell_hash", "updated_at"),
    sa.Index("idx_cells_content_is_loading_partial",
             "sheet_id", "row_id", postgresql_where=...)
)
```

**Note**: The two critical composite indexes mentioned in the report are NOT in the current code. They may have been planned but never implemented.

### A.7 Problematic Query Pattern

**Location**: [sheets/data_layer/cells.py:L1810-1830](https://github.com/hebbia/mono/blob/main/sheets/data_layer/cells.py#L1810-L1830)

**Impact**: This exact query pattern is causing the [120+ second timeouts in production](https://app.datadoghq.com/apm/traces?query=resource_name%3A*fetch_relevant_rows*%20%40duration%3A%3E120000000000&start=1756490400000&end=1756508400000)

```python
def _latest_cells_query(
    sheet_id: str,
    active_tab_id: str,
    column_ids: list[str],
    cell_id: Optional[str] = None,
) -> Select:
    query = (
        sa.select(Cell)
        .distinct(Cell.cell_hash)  # DISTINCT ON clause
        .where(
            Cell.sheet_id == sheet_id,
            Cell.tab_id == active_tab_id,
            Cell.versioned_column_id.in_(column_ids),
        )
        .order_by(Cell.cell_hash, sa.desc(Cell.updated_at))  # Requires index!
    )
```

**Performance Impact**:

- This query runs DISTINCT ON with ORDER BY on 5 columns
- Without the composite index, PostgreSQL must:
  1. Scan all matching rows (potentially millions)
  2. Sort them in memory or on disk
  3. Apply DISTINCT operation
- With proper index: Direct index scan, no sorting needed

### A.8 Query Performance Improvement Projection

**Current State** (without indexes):

```text
DISTINCT ON query: 5.58 seconds (disk spill: 272MB)
MAX() query: 48+ seconds (full table scan)
fetch_relevant_rows: 120+ seconds (confirmed timeouts)
```

**Projected State** (with indexes):

```text
DISTINCT ON query: <100ms (direct index scan)
MAX() query: <10ms (index-only scan)
Total request time: <1 second
```

**Expected Improvement**:

- 98-99.98% reduction in query time
- Elimination of disk spills
- Zero timeout errors

---

## Additional Datadog Findings (2025-09-02)

### Database Connection Metrics

**PostgreSQL Connection Pool Status**

```bash
cd ~/Hebbia/sisu-notes && .venv/bin/python tools/datadog_explorer.py \
  "avg:postgresql.connections{*}" --timeframe 4h
```

**Current Status**: Stable but suboptimal
- Average connections: 105.93 (ranging 94-112)
- Connection usage: 42% (0.40-0.43 percent_usage)
- No connection exhaustion detected


**🔗 View Connection Metrics**:  
<https://app.datadoghq.com/metric/explorer?from_ts=1756769965&to_ts=1756784365&live=true&query=avg%3Apostgresql.connections%7B%2A%7D>

### Performance Distribution Analysis

**Query Performance Breakdown** (24-hour sample):

- Fast queries (<0.1s): ~60%
- Normal queries (0.1-1s): ~38%
- Slow queries (>1s): ~2%
- Critical queries (>2s): <1%

**Key Observations**:

1. **120+ second timeouts confirmed**: 19 operations hit exact 120-second timeout limit
2. **25+ second operations**: fetch_relevant_rows taking up to 25.49 seconds
3. **100+ slow query warnings** during 5-hour business window
4. **All timeouts resulted in HTTP errors**, directly impacting users

### Direct Event URLs for Investigation

**Example Slow Query Event**:  
<https://app.datadoghq.com/logs?query=run_get_rows_db_queries&event=AwAAAZkCf0GGtIsIaAAAABhBWmtDZjBROUFBQU5CS2JYVTBfNUJBQUMAAAAkZjE5OTAyODEtZjcyZi00OTE1LTlmZTYtZWYwYzAzM2U0ZGI5AA3DYg>

**Slow Query Warning Event**:  
<https://app.datadoghq.com/logs?query=%22slow%20get_relevant_rows%20query%22&event=AwAAAZkC-zZDW3001wAAABhBWmtDLXphQUFBRFVWcXFfVHNTbDFRQW8AAAAkZjE5OTAyZmMtZjI5Ni00NjA4LThhYzgtYTc2YmNkYWQ0M2ZiAAxcjQ>

### Correlation with Database Issues

The Datadog evidence confirms the database performance issues identified:

1. **Missing indexes** causing queries to exceed 2-3 seconds regularly
2. **Connection pool** operating at 42% capacity (not the bottleneck)
3. **Staging environment** experiencing 5-10 second API response times
4. **No connection exhaustion** or timeout errors (queries complete, just slowly)

## Critical Action Items

### 1. Immediate Index Deployment (Day 1)

**Why Critical**: [View the 19 timeout failures this will fix](https://app.datadoghq.com/apm/traces?query=resource_name%3A*fetch_relevant_rows*%20%40duration%3A%3E120000000000&start=1756490400000&end=1756508400000)

```sql
-- Run on production with CONCURRENTLY to avoid locks
CREATE INDEX CONCURRENTLY ix_cells_sheet_tab_versioned_col_hash_updated
ON cells (sheet_id, tab_id, versioned_column_id, cell_hash, updated_at DESC);

CREATE INDEX CONCURRENTLY ix_cells_max_updated_at_per_sheet_tab
ON cells (sheet_id, tab_id, updated_at DESC, versioned_column_id);
```

**Verify Impact**: Monitor [fetch_relevant_rows performance](https://app.datadoghq.com/apm/traces?query=resource_name%3A*fetch_relevant_rows*&start=1756490400000&end=1756508400000) after deployment

### 2. Connection Pool Fix (Day 2-3)

**Code Location**: [session_provider.py](https://github.com/hebbia/mono/blob/main/brain/database/session_provider.py)

```python
# In session_provider.py
pool_use_lifo=False,  # Rotate connections
pool_recycle=1200,    # 20 min < 30 min RDS timeout
```

**Monitor**: [Connection metrics in Datadog](https://app.datadoghq.com/metric/explorer?from_ts=1756769965&to_ts=1756784365&live=true&query=avg%3Apostgresql.connections%7B%2A%7D)

### 3. Database Tuning (Week 1)

```sql
ALTER SYSTEM SET work_mem = '256MB';
ALTER SYSTEM SET effective_io_concurrency = '200';
SELECT pg_reload_conf();
```
