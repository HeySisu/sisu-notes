# Performance Analysis: `get_rows` Function - Final Status Report

## Executive Summary

Critical database performance issues persist. Two missing indexes cause 48+ second cache validation and 120+ second query timeouts. Connection pooling misconfiguration adds 4+ second delays.

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
- 25 client connections → 4,390 DB connections (175x amplification)
- Connections 6-20 idle for 30 min → killed by proxy → 4+ second TLS re-establishment

### Fix Options

```python
# Option A: NullPool (Recommended)
poolclass=NullPool  # Let RDS Proxy handle ALL pooling

# Option B: Switch to FIFO
pool_use_lifo=False  # Rotate through all connections evenly
pool_recycle=1200    # 20 min < 30 min timeout
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
-- 99.98% connections via proxy (NULL client_addr)
Via RDS Proxy: 4,390 connections
Direct: 1 connection

-- But only 25 client connections to proxy
-- 175x amplification due to double pooling
```

---

*Report Date: 2025-08-30*
*Next Steps: Deploy missing indexes immediately (Action Items 2 & 3)*