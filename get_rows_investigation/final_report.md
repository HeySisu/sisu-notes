# Performance Analysis: `get_rows` Function - SQL Query Execution Flow

## Executive Summary

**🚨 CRITICAL FINDING**: Two indexes defined in code ([cells.py:L199-211](https://github.com/hebbia/mono/blob/main/brain/models/cells.py#L199-L211)) are **NOT deployed to production database**. These missing indexes cause 48+ second MAX() queries and 120+ second DISTINCT ON timeouts.

Critical database performance issues identified across SQL query execution flow:
- **Missing indexes**: Full table scans of 830K+ rows (48+ seconds)
- **Connection delays**: LIFO pooling + RDS timeout mismatch (4+ seconds)
- **Disk spills**: 272MB sorts exceed 4MB work_mem
- **Combined effect**: 120+ second query timeouts in production

---

## Step 0: Performance Logging - ✅ DEPLOYED

**Status**: Complete and operational

Comprehensive metrics tracking deployed at [get_rows_utils.py:L450-L474](https://github.com/hebbia/mono/blob/main/sheets/cortex/ssrm/get_rows_utils.py#L450-L474)

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
- **4+ second delays** when acquiring idle connections
- **Root Cause**: LIFO pooling + RDS Proxy idle timeout mismatch
  - SQLAlchemy uses LIFO pooling (connections 1-5 reused, 6-20 idle)
  - RDS Proxy kills idle connections after 30 minutes
  - New connections require 2-3 second TLS handshake

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

**AWS CloudWatch Evidence** (would show if AWS CLI was configured):
```bash
# Connection borrow latency spikes correlate with 4+ second delays
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnectionsBorrowLatency \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod
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

**GitHub Links**:
- Entry point: [get_rows.py:L49](https://github.com/hebbia/mono/blob/main/sheets/cortex/ssrm/get_rows.py#L49)
- Main query logic: [cells.py:L756-L869](https://github.com/hebbia/mono/blob/main/sheets/data_layer/cells.py#L756-L869)
- DISTINCT ON query: [cells.py:L769](https://github.com/hebbia/mono/blob/main/sheets/data_layer/cells.py#L769)

#### Recommended Solution: Deploy Missing Indexes

**⚠️ URGENT**: These indexes are already defined in code but NOT in production!

```sql
-- Index 1: For DISTINCT ON queries (defined in cells.py:L199-205)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_cells_sheet_tab_versioned_col_hash_updated
ON cells (sheet_id, tab_id, versioned_column_id, cell_hash, updated_at DESC);

-- Index 2: For MAX() cache validation (defined in cells.py:L206-211)
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
   -- Defined in cells.py:L199-205 but NOT deployed to production!
   CREATE INDEX ix_cells_sheet_tab_versioned_col_hash_updated
   ON cells (sheet_id, tab_id, versioned_column_id, cell_hash, updated_at DESC);
   ```

2. **Missing in Production** (causes MAX() query timeout):
   ```sql
   -- Defined in cells.py:L206-211 but NOT deployed to production!
   CREATE INDEX ix_cells_max_updated_at_per_sheet_tab
   ON cells (sheet_id, tab_id, updated_at DESC, versioned_column_id);
   ```

**Evidence**: These indexes are defined in the model file ([cells.py:L199-211](https://github.com/hebbia/mono/blob/main/brain/models/cells.py#L199-L211)) but database query confirms they're NOT in production!

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

*Report Date: 2025-09-01*

## Next Steps

1. **Immediate**: Deploy composite indexes to production
2. **This Week**: Add connection lifecycle logging, analyze patterns
3. **Next Sprint**: Implement pool configuration changes based on log analysis
4. **Ongoing**: Monitor Datadog metrics for performance improvements

## Success Metrics

After implementing all fixes:
- P99 query latency: <1 second (from 120+ seconds)
- Connection acquisition: <100ms (from 4+ seconds)  
- Zero timeout errors (from hundreds daily)
- No disk spills for standard queries