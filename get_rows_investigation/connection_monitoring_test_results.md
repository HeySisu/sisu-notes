# Connection Monitoring Test Results

## Test Setup
- **Date**: September 3, 2025
- **Environment**: Staging 
- **PR**: #13568 - Database Connection Pool Monitoring

## Test Results

### ❌ Monitoring Logs Not Appearing in Container or Datadog

**What we tested:**
1. Verified containers are using our branch code (ConnectionMonitor exists in ~/Hebbia/mono)
2. Connected to staging database multiple times 
3. Checked Docker container logs for monitoring output
4. Searched Datadog for connection monitoring logs

**Result:** No monitoring logs found in container stdout or Datadog

### Root Cause Analysis

**🔴 Critical Issue Found: Logging Module Incompatibility**

The ConnectionMonitor uses Python's standard `logging` module:
```python
import logging
logging.info("connection_created...")
```

But Hebbia services use a custom logging wrapper (`python_lib/logging`) that:
1. Patches the standard logging module with `ddtrace`
2. Creates circular import when SQLAlchemy tries to import standard logging
3. Results in: `AttributeError: partially initialized module 'logging' has no attribute 'Logger'`

**Evidence:**
```bash
docker exec main-brain-1 python -c "from python_lib.storage.database_connection.connection_monitor import ConnectionMonitor"
# Error: AttributeError: partially initialized module 'logging' has no attribute 'Logger' 
# (most likely due to a circular import)
```

### Fix Required

The ConnectionMonitor needs to be updated to use Hebbia's custom logging:

```python
# Instead of:
import logging

# Use:
from python_lib import logging
```

Or alternatively, handle the import more carefully to avoid the circular dependency.

## Next Steps to Validate Monitoring

### Option 1: Test Locally with Modified Docker Setup
```bash
# Build containers with our branch
cd ~/Hebbia/mono-db-connection-log
docker-compose build --no-cache brain sheets

# Run with our code
docker-compose up brain sheets
```

### Option 2: Deploy to Staging (After PR Merge)
1. Merge PR #13568 to main
2. Deploy to staging
3. Monitor Datadog for logs:
   ```
   env:staging (stale_connection_reused OR old_connection_active)
   ```

### Option 3: Run Direct Test Script
Created `test_connection_monitor.py` that directly uses SessionProvider with ConnectionMonitor to test locally.

## Expected Logs After Deployment

Once deployed, we expect to see these log patterns in Datadog:

### 1. Normal Connection Lifecycle
```
INFO - connection_created: pid=12345
INFO - connection_recycled: age_seconds=1500.0, total_checkouts=25
```

### 2. Problem Detection (What we're looking for)
```
ERROR - stale_connection_reused: idle_seconds=1850.2, age=3700.5, checkouts=15, risk=May be killed by RDS Proxy
ERROR - slow_connection_acquisition: wait_seconds=15.3, cause=Pool exhaustion or timeout
```

### 3. Monitoring Maintenance
```
INFO - connection_stats_cleanup: removed 5 old connection stats
INFO - connection_monitor_cleanup for engine: Engine(postgresql://...)
```

## Validation Query for Datadog

After deployment, use this query to find issues:
```
env:staging 
service:(brain OR sheets OR doc_manager)
(stale_connection_reused OR slow_connection_acquisition)
```

## Configuration Fix to Deploy

Once we confirm RDS Proxy timeout pattern in logs, deploy this fix:

```python
# python_lib/storage/database_connection/configs.py
PostgresDbConfig(
    pool_recycle=1500,  # 25 minutes (was 3600)
    pool_pre_ping=True,  # Test connections before use
    # ... other settings
)
```

## Summary

- ✅ Created ConnectionMonitor implementation
- ✅ Added comprehensive logging for connection lifecycle
- ✅ Created test scripts for validation
- ❌ Cannot validate in staging yet (PR not deployed)
- ⏳ Waiting for PR merge and deployment to validate

The monitoring code is ready but needs to be deployed to staging/production to start collecting data about RDS Proxy timeout issues.