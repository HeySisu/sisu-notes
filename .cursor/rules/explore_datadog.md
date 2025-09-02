# Hebbia Datadog Explorer

**Tool:** `cd ~/Hebbia/sisu-notes && .venv/bin/python tools/datadog_explorer.py`

Query metrics, logs, and APM traces from Datadog. API keys in `tools/config.py`.

## Essential Commands

### 🔍 Performance Investigation
```bash
# Get_rows performance logs (from final_report.md investigation)
.venv/bin/python tools/datadog_explorer.py "logs:run_get_rows_db_queries" --timeframe 2h

# Find slow queries (>1 second)
.venv/bin/python tools/datadog_explorer.py "logs:run_get_rows_db_queries" --raw | \
  jq '.data[] | select(.attributes.attributes.total_db_queries_time > 1)'

# Performance distribution analysis
.venv/bin/python tools/datadog_explorer.py "logs:run_get_rows_db_queries" --raw | \
  jq -r '.data[].attributes.attributes.total_db_queries_time' | \
  awk '{if($1<0.1) fast++; else if($1<1) normal++; else slow++} 
       END {printf "Fast: %d, Normal: %d, Slow: %d\n", fast, normal, slow}'
```

### 📝 Log Queries
```bash
# Basic log search
.venv/bin/python tools/datadog_explorer.py "logs:keyword"

# Service errors
.venv/bin/python tools/datadog_explorer.py "logs:service:sheets status:error"

# Complex filters
.venv/bin/python tools/datadog_explorer.py "logs:service:sheets run_get_rows_db_queries"

# Raw JSON for analysis
.venv/bin/python tools/datadog_explorer.py "logs:query" --raw
```

### 📊 Metrics
```bash
# Database performance
.venv/bin/python tools/datadog_explorer.py "avg:postgresql.connections{*}"
.venv/bin/python tools/datadog_explorer.py "avg:postgresql.query.time{*}"
.venv/bin/python tools/datadog_explorer.py "avg:postgresql.max_connections{*}"
.venv/bin/python tools/datadog_explorer.py "avg:postgresql.percent_usage_connections{*}"

# Database trace metrics (APM)
.venv/bin/python tools/datadog_explorer.py "avg:trace.postgres.connect{*}"
.venv/bin/python tools/datadog_explorer.py "avg:trace.postgres.query.time{*}"
.venv/bin/python tools/datadog_explorer.py "percentile:trace.postgres.query.time{*}:95"
.venv/bin/python tools/datadog_explorer.py "avg:trace.postgres.query.rows{*}"

# API latency
.venv/bin/python tools/datadog_explorer.py "avg:trace.request.duration{service:hebbia-api}"
.venv/bin/python tools/datadog_explorer.py "percentile:trace.request.duration{service:sheets}:95"

# System resources
.venv/bin/python tools/datadog_explorer.py "avg:system.cpu.idle{*}"
.venv/bin/python tools/datadog_explorer.py "avg:system.mem.used{*}"
```

### 🔎 Discovery
```bash
# List all metrics
.venv/bin/python tools/datadog_explorer.py "list-metrics"

# Search specific metrics
.venv/bin/python tools/datadog_explorer.py "list-metrics" --search "postgres"
.venv/bin/python tools/datadog_explorer.py "list-metrics" --search "trace"

# Get metric details
.venv/bin/python tools/datadog_explorer.py "info:postgresql.connections"
```

## Query Syntax

### Log Query Syntax
- **Prefix**: All log queries start with `logs:`
- **Service**: `logs:service:sheets`
- **Status**: `logs:status:error` or `logs:status:warn`
- **Host**: `logs:host:ip-10-1-1-188`
- **Tags**: `logs:@tagname:value`
- **Text**: `logs:"exact phrase"` or `logs:keyword`
- **Multiple**: `logs:service:sheets status:error`

### Metric Aggregations
- `avg:` - Average
- `sum:` - Total
- `min:` / `max:` - Min/Max
- `count:` - Count
- `percentile:metric{*}:95` - 95th percentile

### Modifiers
- `.as_rate()` - Convert to rate/sec
- `.as_count()` - Convert to count
- `.rollup(avg, 60)` - 60s buckets
- `by {tag}` - Group by tag

### Timeframes
- Minutes: `5m`, `15m`, `30m`
- Hours: `1h` (default), `2h`, `4h`, `8h`, `12h`
- Days: `1d`, `2d`, `7d`, `14d`, `30d`

## Database Connection Analysis

### PostgreSQL Metrics
```bash
# Connection pool usage
.venv/bin/python tools/datadog_explorer.py "avg:postgresql.connections{*}" --timeframe 2h
.venv/bin/python tools/datadog_explorer.py "max:postgresql.connections{*}" --timeframe 2h
.venv/bin/python tools/datadog_explorer.py "avg:postgresql.percent_usage_connections{*}" --timeframe 2h

# Connection performance (from APM traces)
.venv/bin/python tools/datadog_explorer.py "avg:trace.postgres.connect{*}" --timeframe 2h
.venv/bin/python tools/datadog_explorer.py "max:trace.postgres.connect{*}" --timeframe 2h
.venv/bin/python tools/datadog_explorer.py "percentile:trace.postgres.connect{*}:95" --timeframe 2h

# Query performance
.venv/bin/python tools/datadog_explorer.py "avg:trace.postgres.query.time{*}" --timeframe 2h
.venv/bin/python tools/datadog_explorer.py "percentile:trace.postgres.query.time{*}:95" --timeframe 2h
.venv/bin/python tools/datadog_explorer.py "percentile:trace.postgres.query.time{*}:99" --timeframe 2h

# Connection analysis with filters
.venv/bin/python tools/datadog_explorer.py "avg:postgresql.connections{env:prod}" --timeframe 1h
.venv/bin/python tools/datadog_explorer.py "avg:trace.postgres.connect{env:prod,service:sheets}" --timeframe 1h
```

## Analysis Patterns

### Finding Performance Issues
```bash
# Query time distribution
.venv/bin/python tools/datadog_explorer.py "logs:run_get_rows_db_queries" --timeframe 6h --raw | \
  jq -r '.data[].attributes.attributes.total_db_queries_time' | \
  awk '{total+=$1; n++} END {printf "Avg: %.3fs (n=%d)\n", total/n, n}'

# Cache hit rate
.venv/bin/python tools/datadog_explorer.py "logs:run_get_rows_db_queries" --raw | \
  jq -r '.data[].attributes.attributes.cache_hit' | \
  grep -c true

# Slow sheet identification
.venv/bin/python tools/datadog_explorer.py "logs:run_get_rows_db_queries" --raw | \
  jq -r 'select(.attributes.attributes.total_db_queries_time > 5) | 
         "\(.attributes.attributes.sheet): \(.attributes.attributes.total_db_queries_time)s"'
```

### Error Analysis
```bash
# Error rate by service
.venv/bin/python tools/datadog_explorer.py "logs:status:error" --raw | \
  jq -r '.data[].attributes.service' | sort | uniq -c | sort -rn

# Transaction rollbacks
.venv/bin/python tools/datadog_explorer.py "logs:\"rolling back transaction\"" --timeframe 1h

# Parse failures
.venv/bin/python tools/datadog_explorer.py "logs:\"Failed to parse\"" --timeframe 1h
```

## Key Findings from Investigation

From analyzing `get_rows` performance logs:
- **10% of queries are critical** (>1 second execution time)
- **Average DB query time: 0.704s** even with cache hits
- **Missing indexes** cause 48+ second queries (see final_report.md)
- **Common errors**: Transaction rollbacks, parse failures

## Quick Reference

```bash
# Most useful commands for debugging
alias ddlogs='cd ~/Hebbia/sisu-notes && .venv/bin/python tools/datadog_explorer.py'

# Recent performance logs
ddlogs "logs:run_get_rows_db_queries" --timeframe 1h

# Current errors
ddlogs "logs:service:sheets status:error" --timeframe 15m

# Database load
ddlogs "avg:postgresql.connections{*}" --timeframe 1h
ddlogs "avg:postgresql.percent_usage_connections{*}" --timeframe 1h

# Database performance (APM traces)
ddlogs "avg:trace.postgres.connect{*}" --timeframe 1h
ddlogs "percentile:trace.postgres.query.time{*}:95" --timeframe 1h

# API latency
ddlogs "percentile:trace.request.duration{service:sheets}:95" --timeframe 1h
```

## Troubleshooting

- **SSL Warning**: Ignore LibreSSL warnings - non-critical
- **No data**: Expand timeframe or check service name
- **Rate limit**: 1000 requests/hour for metrics
- **Authentication**: Verify keys in tools/config.py