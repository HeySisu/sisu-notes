# Connection Monitoring Usage Guide

## Purpose
This guide explains how to use the new connection monitoring logs to diagnose and fix RDS Proxy 30-minute timeout issues causing long connection establishment times.

## The Problem We're Diagnosing
- RDS Proxy kills idle connections after 30 minutes
- SQLAlchemy doesn't know the connection is dead
- When SQLAlchemy tries to reuse a dead connection, it hangs for ~15 seconds before timeout
- This causes slow query performance sporadically

## Key Logs to Watch For

### 1. Stale Connection Reuse Detection
**Log Pattern:**
```
ERROR - stale_connection_reused: idle_seconds=1850.2, age=3700.5, checkouts=15, risk=May be killed by RDS Proxy
```

**What it means:**
- A connection sat idle for >30 minutes (1800 seconds)
- RDS Proxy has likely killed this connection
- The next query will likely timeout

**Action to take:**
- Immediately: This confirms RDS Proxy timeout is the issue
- Long-term: Adjust `pool_recycle` to less than 1800 seconds (e.g., 1500)

### 2. Slow Connection Acquisition
**Log Pattern:**
```
ERROR - slow_connection_acquisition: wait_seconds=15.3, cause=Pool exhaustion or timeout
```

**What it means:**
- Took >5 seconds to get a connection from the pool
- Likely because SQLAlchemy tried to use a dead connection first

**Action to take:**
- Check if preceded by `stale_connection_reused` log
- If yes, confirms the stale connection caused the delay

### 3. Old Connection Warning
**Log Pattern:**
```
WARNING - old_connection_active: age_seconds=7200.0, checkouts=50
```

**What it means:**
- Connection has been alive for >1 hour
- Not necessarily bad, but worth monitoring

**Action to take:**
- Monitor if these correlate with performance issues
- Consider setting `pool_recycle` more aggressively

### 4. Connection Recycled
**Log Pattern:**
```
INFO - connection_recycled: age_seconds=3600.0, total_checkouts=42, total_idle_time=2400.0
```

**What it means:**
- A connection was properly recycled by SQLAlchemy
- Shows the system is working correctly

**Action to take:**
- Good news - no action needed
- Validates that `pool_recycle` is working

### 5. Connection Invalidated
**Log Pattern:**
```
ERROR - connection_invalidated: age_seconds=1900.0, exception=OperationalError, checkouts=20
```

**What it means:**
- SQLAlchemy detected a bad connection and removed it
- The exception shows why it failed

**Action to take:**
- Check the exception type
- If timeout-related, likely confirms RDS Proxy issue

## Diagnosis Workflow

### Step 1: Confirm RDS Proxy Timeout is the Issue
1. Deploy the monitoring code
2. Wait for slow query reports
3. Check logs for pattern:
   ```
   ERROR - stale_connection_reused: idle_seconds=1850.2 ...
   ERROR - slow_connection_acquisition: wait_seconds=15.3 ...
   ```
4. If you see this pattern, RDS Proxy timeout is confirmed

### Step 2: Identify Scope of Problem
Query the logs to answer:
- How many connections idle >30 minutes daily?
- What's the correlation between idle time and acquisition delay?
- Which services/queries are most affected?

Example Datadog query:
```
service:brain 
"stale_connection_reused" 
| stats count by hour
```

### Step 3: Implement Fix
Based on findings, adjust configuration:

```python
# Current (problematic) configuration
engine = create_engine(
    config.url,
    pool_recycle=3600,  # 1 hour - too long!
    ...
)

# Fixed configuration
engine = create_engine(
    config.url,
    pool_recycle=1500,  # 25 minutes - beats RDS Proxy's 30-minute timeout
    pool_pre_ping=True,  # Also test connections before use
    ...
)
```

### Step 4: Validate Fix
After deploying the fix, monitor for:
1. Absence of `stale_connection_reused` errors
2. Reduction in `slow_connection_acquisition` errors
3. Overall query performance improvement

## Expected Outcomes

### Before Fix (with monitoring)
```
ERROR - stale_connection_reused: idle_seconds=2100.0, age=2100.0, checkouts=1, risk=May be killed by RDS Proxy
ERROR - slow_connection_acquisition: wait_seconds=15.2, cause=Pool exhaustion or timeout
[15 second delay in query execution]
```

### After Fix (pool_recycle=1500)
```
INFO - connection_recycled: age_seconds=1500.0, total_checkouts=25, total_idle_time=900.0
[Normal query execution, no delays]
```

## Long-term Monitoring

Set up alerts for:
- `stale_connection_reused` errors (critical - immediate action)
- `slow_connection_acquisition` > 10 per hour (warning - investigate)
- Average connection age trending upward (info - monitor)

## Summary

The monitoring helps us:
1. **Confirm** RDS Proxy timeout is causing issues (stale connection logs)
2. **Measure** the impact (slow acquisition frequency and duration)
3. **Fix** by adjusting pool_recycle to beat the 30-minute timeout
4. **Validate** the fix worked (absence of stale connection errors)

Without this monitoring, we only see symptoms (slow queries) but can't definitively identify the root cause or validate our fix.