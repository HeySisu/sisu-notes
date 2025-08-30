# AWS RDS Proxy & Connection Analysis Commands

This command file provides AWS CLI commands to investigate RDS Proxy connection bottlenecks and database performance issues.

## Prerequisites

```bash
# Authenticate with AWS SSO (AWS CLI v2)
aws sso login --profile readonly

# Verify authentication
aws --profile readonly sts get-caller-identity
```

## 1. RDS Proxy Connection Analysis

### List All Available RDS Proxy Metrics
```bash
# Discover available metrics for specific proxy
aws --profile readonly --region us-east-1 cloudwatch list-metrics \
  --namespace AWS/RDS \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --output json | jq '.Metrics[].MetricName' | sort | uniq
```

### Get Current Database Connections (Proxy → DB)
```bash
# Shows actual connections from RDS Proxy to PostgreSQL database
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --start-time $(date -u -v-1H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 \
  --statistics Average \
  --output json
```

### Get Client Connections (Apps → Proxy)
```bash
# Shows concurrent client connections to RDS Proxy
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name ClientConnections \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --start-time $(date -u -v-1H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 \
  --statistics Average \
  --output json
```

### Get Connection Borrow Latency (Proxy Delays)
```bash
# Shows time to get connection from proxy pool (microseconds)
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnectionsBorrowLatency \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --start-time $(date -u -v-3H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 600 \
  --statistics Maximum \
  --output json
```

### Get Connection Setup Metrics
```bash
# Successful connection setups (rate of new connections)
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnectionsSetupSucceeded \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --start-time $(date -u -v-3H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 600 \
  --statistics Sum \
  --output json

# Failed connection setups (should be 0 in healthy system)
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnectionsSetupFailed \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --start-time $(date -u -v-3H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 600 \
  --statistics Sum \
  --output json
```

### Get Current Borrowed Connections
```bash
# Shows how many connections are actively in use
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnectionsCurrentlyBorrowed \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --start-time $(date -u -v-1H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 \
  --statistics Average \
  --output json
```

## 2. Database Performance Analysis

### Query Response Latency
```bash
# Actual database query execution time
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name QueryDatabaseResponseLatency \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --start-time $(date -u -v-1H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 \
  --statistics Average,Maximum \
  --output json
```

### Database Instance Metrics
```bash
# Direct database connection count (bypassing proxy)
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=hebbia-backend-postgres-prod \
  --start-time $(date -u -v-1H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 \
  --statistics Average \
  --output json
```

## 3. Connection Bottleneck Analysis Script

### Complete Connection Health Check
```bash
#!/bin/bash
# save as check_connection_health.sh

PROXY_NAME="hebbia-backend-postgres-prod"
PROFILE="readonly"
REGION="us-east-1"
TIME_RANGE="-1H"

echo "=== RDS Proxy Connection Health Check ==="
echo "Proxy: $PROXY_NAME"
echo "Time: $(date)"
echo

# Get key metrics in parallel
echo "📊 Fetching metrics..."

# Database connections (proxy to DB)
DB_CONN=$(aws --profile $PROFILE --region $REGION cloudwatch get-metric-statistics \
  --namespace AWS/RDS --metric-name DatabaseConnections \
  --dimensions Name=ProxyName,Value=$PROXY_NAME \
  --start-time $(date -u -v$TIME_RANGE '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 --statistics Average --output json | \
  jq -r '.Datapoints | sort_by(.Timestamp) | last | .Average')

# Client connections (apps to proxy)  
CLIENT_CONN=$(aws --profile $PROFILE --region $REGION cloudwatch get-metric-statistics \
  --namespace AWS/RDS --metric-name ClientConnections \
  --dimensions Name=ProxyName,Value=$PROXY_NAME \
  --start-time $(date -u -v$TIME_RANGE '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 --statistics Average --output json | \
  jq -r '.Datapoints | sort_by(.Timestamp) | last | .Average')

# Borrow latency (microseconds)
BORROW_LATENCY=$(aws --profile $PROFILE --region $REGION cloudwatch get-metric-statistics \
  --namespace AWS/RDS --metric-name DatabaseConnectionsBorrowLatency \
  --dimensions Name=ProxyName,Value=$PROXY_NAME \
  --start-time $(date -u -v$TIME_RANGE '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 --statistics Maximum --output json | \
  jq -r '.Datapoints | sort_by(.Timestamp) | last | .Maximum')

echo "🔗 Connection Metrics:"
echo "  Database Connections (Proxy→DB): ${DB_CONN}"
echo "  Client Connections (Apps→Proxy): ${CLIENT_CONN}" 
echo "  Max Borrow Latency: ${BORROW_LATENCY}μs ($(echo "scale=1; $BORROW_LATENCY/1000" | bc)ms)"

# Calculate multiplexing ratio if we have both values
if [[ "$DB_CONN" != "null" && "$CLIENT_CONN" != "null" ]]; then
    RATIO=$(echo "scale=1; $CLIENT_CONN/$DB_CONN" | bc)
    echo "  Client:Database Ratio: ${RATIO}:1"
fi

echo
echo "🎯 Health Assessment:"
if (( $(echo "$BORROW_LATENCY > 50000" | bc -l) )); then
    echo "  ⚠️  HIGH borrow latency (>50ms) - connection pressure detected"
elif (( $(echo "$BORROW_LATENCY > 10000" | bc -l) )); then
    echo "  ⚡ MODERATE borrow latency (>10ms) - monitor closely"
else
    echo "  ✅ LOW borrow latency (<10ms) - healthy"
fi

if (( $(echo "$CLIENT_CONN > 100" | bc -l) )); then
    echo "  ⚠️  HIGH client connections (>100) - may indicate over-provisioning"
elif (( $(echo "$CLIENT_CONN > 50" | bc -l) )); then
    echo "  ⚡ MODERATE client connections (>50) - normal load"
else
    echo "  ✅ LOW client connections (<50) - light load"
fi
```

## 4. Troubleshooting Commands

### Check All DatabaseConnections Dimensions
```bash
# Find all connection metrics to understand proxy architecture
aws --profile readonly --region us-east-1 cloudwatch list-metrics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --output json | jq '.Metrics[] | select(.Dimensions[]?.Value | contains("hebbia-backend-postgres-prod"))'
```

### Get RDS Proxy Configuration
```bash
# View proxy settings (requires appropriate permissions)
aws --profile readonly --region us-east-1 rds describe-db-proxies \
  --db-proxy-name hebbia-backend-postgres-prod \
  --output table
```

### Check Proxy Target Groups
```bash
# View target group configuration 
aws --profile readonly --region us-east-1 rds describe-db-proxy-target-groups \
  --db-proxy-name hebbia-backend-postgres-prod \
  --output table
```

## 5. Useful Conversions & Analysis

### Convert Microseconds to Human Readable
```bash
# Convert CloudWatch microseconds to milliseconds/seconds
echo "Microseconds: 48687"
echo "Milliseconds: $(echo "scale=1; 48687/1000" | bc)"
echo "Seconds: $(echo "scale=3; 48687/1000000" | bc)"
```

### Calculate Connection Ratios
```bash
# Example calculation for multiplexing analysis
APP_CONNECTIONS=6892
PROXY_CLIENT_SLOTS=70
PROXY_DB_CONNECTIONS=135

echo "Application → Proxy ratio: $(echo "scale=1; $APP_CONNECTIONS/$PROXY_CLIENT_SLOTS" | bc):1"
echo "Proxy Client → DB ratio: $(echo "scale=1; $PROXY_CLIENT_SLOTS/$PROXY_DB_CONNECTIONS" | bc):1"
echo "Total multiplexing ratio: $(echo "scale=1; $APP_CONNECTIONS/$PROXY_DB_CONNECTIONS" | bc):1"
```

## 6. Key Insights from Investigation

### Connection Architecture Discovered
```
Applications (6,892) → RDS Proxy Client Slots (~70) → Database Connections (135) → PostgreSQL (12,000 limit)
                               ↑                           ↑
                    Bottleneck causing                Proxy multiplexing
                    4.10s delays                     working efficiently
```

### Critical Metrics to Monitor
1. **ClientConnections**: Should be <100 for healthy performance
2. **DatabaseConnectionsBorrowLatency**: Should be <10ms (10,000μs)
3. **DatabaseConnections**: Actual proxy-to-database connections
4. **DatabaseConnectionsSetupFailed**: Should always be 0

### Performance Thresholds
- **Healthy**: Borrow latency <10ms, Client connections <50
- **Warning**: Borrow latency 10-50ms, Client connections 50-100  
- **Critical**: Borrow latency >50ms, Client connections >100

---

**Usage**: These commands help diagnose RDS Proxy connection bottlenecks, identify multiplexing issues, and track performance improvements after scaling optimizations.