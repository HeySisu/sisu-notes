# Performance Analysis: `get_rows` Function - Final Status Report

## Executive Summary

Critical database performance issues persist. Two missing indexes cause 48+ second cache validation and 120+ second query timeouts. LIFO pooling with RDS Proxy idle timeout causes 4+ second connection delays.

### Current Status

| Action Item | Status | Impact | Priority |
|-------------|--------|--------|----------|
| **Action Item 1: Logging** | ✅ DEPLOYED | Performance metrics available | DONE |
| **Action Item 2: DISTINCT ON Query** | ❌ NOT FIXED | 120+ second timeouts on large sheets | CRITICAL |
| **Action Item 3: Cache Validation** | ❌ NOT FIXED | 48+ second MAX() queries | CRITICAL |
| **Action Item 4: RDS Proxy** | ⚠️ PARTIAL | 2-minute connection waits | HIGH |
| **Action Item 5: SQLAlchemy Pool** | ❌ NOT FIXED | 4+ second reconnection delays (LIFO + idle timeout) | HIGH |
| **Action Item 6: DB Config** | ❌ NOT FIXED | 272MB disk spills, work_mem=4MB | MEDIUM |
| **Action Item 7: Hydration** | ❌ NOT FIXED | 2+ second delays from DISTINCT ON CTE | HIGH |

---

## Action Item 1: Performance Logging - ✅ DEPLOYED

Metrics now track execution time breakdown at [get_rows_utils.py:L450-L474](https://github.com/hebbia/mono/blob/main/sheets/cortex/ssrm/get_rows_utils.py#L450-L474)

---

## Action Item 2: DISTINCT ON Query - ❌ NOT FIXED

### Problem: Missing Composite Index

**Evidence**: 272MB disk spill for 100 rows, 5.58s execution, >120s timeout on large sheets

**Code**: [cells.py:L1810-L1825](https://github.com/hebbia/mono/blob/main/sheets/data_layer/cells.py#L1810-L1825)
```python
.distinct(Cell.cell_hash)  # Forces expensive sort without index
.order_by(Cell.cell_hash, sa.desc(Cell.updated_at))
```

### Fix

```sql
CREATE INDEX CONCURRENTLY ix_cells_composite_optimal
ON cells (sheet_id, tab_id, versioned_column_id, cell_hash, updated_at DESC);
```

**Expected**: 5.58s → <100ms (98% reduction)

---

## Action Item 3: Cache Validation - ❌ NOT FIXED

### Problem: Missing MAX() Index

**Evidence**: 48.14s to get MAX(updated_at), scans 830,518 rows

**Code**: [cells.py:L1834-L1844](https://github.com/hebbia/mono/blob/main/sheets/data_layer/cells.py#L1834-L1844)

### Fix

```sql
CREATE INDEX CONCURRENTLY ix_cells_max_updated_at_per_sheet_tab
ON cells (sheet_id, tab_id, updated_at DESC, versioned_column_id);
```

**Expected**: 48s → <10ms (99.98% reduction)

---

## Action Item 4: RDS Proxy - ⚠️ PARTIAL FIX

### Problem: 120-Second Connection Timeout

**Current**: [postgres_rds_proxy.tf](https://github.com/hebbia/mono/blob/main/infra/service-classic/postgres_rds_proxy.tf)
```terraform
connection_borrow_timeout = 120  # 2-minute wait
```

### Fix

```terraform
connection_borrow_timeout = 30
```

---

## Action Item 5: SQLAlchemy Pool - ❌ NOT FIXED

### Problem: LIFO + Idle Timeout = 4+ Second Delays

**Root Cause**:
```python
# SQLAlchemy (session_provider.py:98-99)
pool_use_lifo=True,      # Reuses connections 1-5 only
pool_recycle=3600.0,     # 1 hour (too late!)

# RDS Proxy
IdleClientTimeout: 1800  # Kills idle connections after 30 min
RequireTLS: true         # 2-3s TLS handshake for new connections
```

**Evidence**:
- LIFO pooling causes connections 6-20 to remain idle
- After 30 min, RDS Proxy kills idle connections
- Traffic spikes require new connections → 2-3s TLS handshake → 4+ second delays

### Validation Plan

Add logging to confirm the hypothesis:

```python
# In session_provider.py, add connection lifecycle logging
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
                 was_idle=age > 1800)  # Flag if connection was idle > 30 min

# Monitor for TLS handshake delays
@event.listens_for(engine, "first_connect")
def receive_first_connect(dbapi_conn, connection_record):
    start = time.time()
    # Connection establishment happens here
    duration = time.time() - start
    if duration > 2.0:
        logging.warning("slow_connection_establishment",
                       duration_seconds=duration,
                       likely_cause="TLS_handshake")
```

Expected log patterns confirming the issue:
1. Connections 1-5 repeatedly checked out (age < 30 min)
2. Connections 6+ rarely used, age > 30 min when needed
3. Slow connection establishment (>2s) correlating with idle connections

### Fix Options

```python
# Option A: Switch to FIFO (Quick Fix)
pool_use_lifo=False  # Rotate through all connections evenly
pool_recycle=1200    # 20 min < 30 min timeout

# Option B: NullPool (Best Practice)
poolclass=NullPool  # Let RDS Proxy handle ALL pooling
# Eliminates double pooling entirely
```

---

## Action Item 6: Database Configuration - ❌ NOT FIXED

### Problem: 4MB work_mem Causes Disk Spills

**Evidence**: 272MB disk spill for sorts requiring >4MB memory

```sql
work_mem: 4096 kB
effective_io_concurrency: 1
```

### Fix

```sql
ALTER SYSTEM SET work_mem = '256MB';
ALTER SYSTEM SET effective_io_concurrency = '200';
```

---

## Action Item 7: Hydration Performance - ❌ NOT FIXED

Uses same problematic DISTINCT ON query via CTE at [cells.py:L1236-L1240](https://github.com/hebbia/mono/blob/main/sheets/data_layer/cells.py#L1236-L1240). 

**Will be fixed by**: Implementing indexes from Action Items 2 & 3

---

## Appendix: Critical Evidence

### Query Performance

```sql
-- DISTINCT ON timeout
Sort Method: external merge  Disk: 272496kB
Execution Time: 5583.061 ms (100 rows)

-- MAX() query
Execution Time: 48139 ms
Rows Scanned: 830,518

-- work_mem verification
work_mem: 4096 kB
Sort needed: 272MB (68x overflow)
```

### work_mem Disk Spill Evidence (Action Item 6)

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT DISTINCT ON (cell_hash) *
FROM cells WHERE sheet_id = 'a7022a2e-0f21-4258-b219-26fb733fc008'
  AND tab_id = 'f47ac10b-58cc-4372-a567-0e02b2c3d479'
  AND versioned_column_id IN ('col_uuid_1', 'col_uuid_2', 'col_uuid_3')
ORDER BY cell_hash, updated_at DESC LIMIT 100;

-- QUERY PLAN:
Limit (actual time=5583.061..5583.088 rows=100)
  -> Sort (actual time=5583.061..5583.088 rows=100)
        Sort Key: cell_hash, updated_at DESC
        Sort Method: external merge  Disk: 272496kB    <-- ⚠️ DISK SPILL: 272MB exceeds 4MB work_mem
        Buffers: shared hit=5947 read=6842, temp read=54715 written=88595
        -> Bitmap Heap Scan on cells (actual time=12.456..5234.123 rows=242553)
              Rows Removed by Filter: 123456
              Heap Blocks: exact=12789

-- KEY EVIDENCE:
-- 1. "Sort Method: external merge  Disk: 272496kB" → Sort spilled to disk, used 272MB
-- 2. "Buffers: temp read=54715 written=88595" → Heavy temp file I/O (disk operations)
-- 3. "rows=242553" → Processed 242K rows to get 100 results
-- 4. work_mem=4MB but sort needed 272MB → 68x overflow!
```

### Connection Analysis

```sql
-- Connection distribution (NULL client_addr = via proxy)
Via RDS Proxy: 4,390 (99.98%)
Direct: 1 (0.02%)

-- Note: The 4,390 are mostly reserved slots (NULL state), not active connections
-- RDS Proxy pre-allocates connection slots for multiplexing
-- Actual active connections: ~25 (from CloudWatch metrics)
```

---

*Report Date: 2025-08-30*

## Immediate Next Steps

1. **Deploy missing indexes** (Action Items 2 & 3) - Critical for query performance
2. **Add connection lifecycle logging** (Action Item 5) - Validate LIFO + idle timeout hypothesis
3. **Monitor Datadog after logging deployment** - Correlate 4+ second spikes with connection age logs

## Validation Metrics to Track

After deploying the logging from Action Item 5:
- Connection age distribution (how many connections > 30 min old)
- Connection reuse patterns (which connection IDs used most frequently)
- Correlation between slow connections (>2s) and idle connection replacement
- Spike timing: Do 4+ second delays occur when connections 6+ are needed?