# AWS RDS Proxy & Connection Analysis

Quick reference for monitoring RDS Proxy health and database performance metrics.

## Prerequisites

```bash
# Login to AWS SSO
aws sso login --profile readonly

# Verify authentication
aws --profile readonly sts get-caller-identity
# Expected: "Arn": "arn:aws:sts::660342524566:assumed-role/AWSReservedSSO_ReadOnlyAccess_..."
```

## 1. Quick Health Check

### Most Important Metrics (Run These First)
```bash
# Database Connections: Proxy → DB (should be ~100-150)
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --start-time $(date -u -v-1H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 --statistics Average \
  --output json | jq '.Datapoints | sort_by(.Timestamp) | last'
# Current: ~100 connections

# Client Connections: Apps → Proxy (should be <50 for healthy)
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name ClientConnections \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --start-time $(date -u -v-1H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 --statistics Average \
  --output json | jq '.Datapoints | sort_by(.Timestamp) | last'
# Current: ~26 connections (healthy)

# Borrow Latency: Time to get connection (should be <10ms)
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnectionsBorrowLatency \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --start-time $(date -u -v-1H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 --statistics Maximum \
  --output json | jq '.Datapoints | sort_by(.Timestamp) | last | .Maximum as $us | {Timestamp, "Microseconds": $us, "Milliseconds": ($us/1000)}'
# Current: ~8-26ms (moderate)

```

## 2. Automated Health Check Script

Save as `/tmp/check_connection_health.sh` and run with `bash /tmp/check_connection_health.sh`:

```bash
#!/bin/bash
PROXY_NAME="hebbia-backend-postgres-prod"
PROFILE="readonly"
REGION="us-east-1"

echo "=== RDS Proxy Health Check ==="
echo "Time: $(date)"

# Fetch metrics
DB_CONN=$(aws --profile $PROFILE --region $REGION cloudwatch get-metric-statistics \
  --namespace AWS/RDS --metric-name DatabaseConnections \
  --dimensions Name=ProxyName,Value=$PROXY_NAME \
  --start-time $(date -u -v-1H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 --statistics Average --output json | \
  jq -r '.Datapoints | sort_by(.Timestamp) | last | .Average')

CLIENT_CONN=$(aws --profile $PROFILE --region $REGION cloudwatch get-metric-statistics \
  --namespace AWS/RDS --metric-name ClientConnections \
  --dimensions Name=ProxyName,Value=$PROXY_NAME \
  --start-time $(date -u -v-1H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 --statistics Average --output json | \
  jq -r '.Datapoints | sort_by(.Timestamp) | last | .Average')

BORROW_LATENCY=$(aws --profile $PROFILE --region $REGION cloudwatch get-metric-statistics \
  --namespace AWS/RDS --metric-name DatabaseConnectionsBorrowLatency \
  --dimensions Name=ProxyName,Value=$PROXY_NAME \
  --start-time $(date -u -v-1H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 --statistics Maximum --output json | \
  jq -r '.Datapoints | sort_by(.Timestamp) | last | .Maximum')

echo "📊 Metrics:"
echo "  Database Connections: ${DB_CONN}"
echo "  Client Connections: ${CLIENT_CONN}" 
echo "  Borrow Latency: $(echo "scale=1; $BORROW_LATENCY/1000" | bc)ms"

# Health Assessment
if (( $(echo "$BORROW_LATENCY > 50000" | bc -l) )); then
    echo "  ⚠️  HIGH latency - connection pressure"
elif (( $(echo "$BORROW_LATENCY > 10000" | bc -l) )); then
    echo "  ⚡ MODERATE latency - monitor"
else
    echo "  ✅ HEALTHY"
fi
```

## 3. Additional Metrics

### List All Available Metrics
```bash
# See all 24 available RDS Proxy metrics
aws --profile readonly --region us-east-1 cloudwatch list-metrics \
  --namespace AWS/RDS \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --output json | jq '.Metrics[].MetricName' | sort | uniq
```

### Failed Connections Check
```bash
# Should always be 0 in healthy system
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnectionsSetupFailed \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --start-time $(date -u -v-3H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 600 --statistics Sum \
  --output json | jq '.Datapoints | sort_by(.Timestamp) | last'
```

### Currently Borrowed Connections
```bash
# Active connections in use right now
aws --profile readonly --region us-east-1 cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnectionsCurrentlyBorrowed \
  --dimensions Name=ProxyName,Value=hebbia-backend-postgres-prod \
  --start-time $(date -u -v-1H '+%Y-%m-%dT%H:%M:%S') \
  --end-time $(date -u '+%Y-%m-%dT%H:%M:%S') \
  --period 300 --statistics Average \
  --output json | jq '.Datapoints | sort_by(.Timestamp) | last'
```

## 4. Performance Thresholds

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| **Borrow Latency** | <10ms | 10-50ms | >50ms |
| **Client Connections** | <50 | 50-100 | >100 |
| **Failed Setups** | 0 | 1-5 | >5 |
| **DB Connections** | 80-120 | 120-150 | >150 |

## 5. Connection Architecture

```
Apps (6,892) → Proxy Clients (~70) → DB Connections (135) → PostgreSQL (12,000 max)
                     ↑                      ↑
              Bottleneck here        Multiplexing works
```

## 6. Quick Debugging

```bash
# Check if proxy is accessible
aws --profile readonly --region us-east-1 rds describe-db-proxies \
  --db-proxy-name hebbia-backend-postgres-prod \
  --query 'DBProxies[0].Status' --output text
# Should return: available

# Get proxy endpoint
aws --profile readonly --region us-east-1 rds describe-db-proxies \
  --db-proxy-name hebbia-backend-postgres-prod \
  --query 'DBProxies[0].Endpoint' --output text
# Returns: hebbia-backend-postgres-prod.proxy-cqyf4jsjudre.us-east-1.rds.amazonaws.com
```

## 7. Staging Environment

Replace `hebbia-backend-postgres-prod` with `hebbia-backend-postgres-staging` in any command above to check staging metrics.