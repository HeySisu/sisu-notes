#!/usr/bin/env python3
"""
Hebbia Datadog Explorer - Query metrics, logs, and APM data
Usage: python datadog_explorer.py "<query>" [--timeframe 1h] [--raw]

Quick Examples:
  # Metrics
  python datadog_explorer.py "avg:system.cpu.idle{*}"
  
  # Logs (prefix with 'logs:')
  python datadog_explorer.py "logs:run_get_rows_db_queries"
  python datadog_explorer.py "logs:service:sheets status:error"
  
  # Discovery
  python datadog_explorer.py "list-metrics" --search "postgres"
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime, timedelta
import re
import urllib.parse

def ensure_venv():
    """Ensure we're running in the virtual environment"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    venv_python = os.path.join(repo_root, '.venv', 'bin', 'python')

    if not os.path.exists(venv_python):
        print("❌ Virtual environment not found. Please run:")
        print(f"  cd {repo_root}")
        print("  python3 -m venv .venv")
        print("  .venv/bin/pip install requests")
        sys.exit(1)

    if sys.executable != venv_python:
        print("🔄 Switching to virtual environment...")
        os.execv(venv_python, [venv_python] + sys.argv)

ensure_venv()

try:
    from config import PROD_DATADOG_API_KEY, PROD_DATADOG_APP_KEY
except ImportError:
    print("❌ Configuration not found. Please ensure tools/config.py exists with Datadog keys:")
    print("  PROD_DATADOG_API_KEY = 'your_api_key'")
    print("  PROD_DATADOG_APP_KEY = 'your_app_key'")
    sys.exit(1)

class DatadogExplorer:
    def __init__(self):
        self.api_key = PROD_DATADOG_API_KEY
        self.app_key = PROD_DATADOG_APP_KEY
        self.base_url = "https://api.datadoghq.com/api/v1"
        self.base_url_v2 = "https://api.datadoghq.com/api/v2"
        self.logs_url = f"{self.base_url_v2}/logs/events/search"
        self.traces_url = f"{self.base_url_v2}/spans/events/search"
        self.headers = {
            "DD-API-KEY": self.api_key,
            "DD-APPLICATION-KEY": self.app_key
        }

    def parse_timeframe(self, timeframe: str) -> tuple:
        """Convert timeframe string to (from_time, to_time) tuple
        
        Supported formats:
        - Relative: '1h', '2d', '30m' (time ago from now)
        - Absolute: '2025-01-03' (single day)
        - Range: '2025-01-03,2025-01-05' (from,to)
        - ISO: '2025-01-03T10:00:00,2025-01-03T18:00:00'
        - Unix: '1754539200,1754711999' (timestamps)
        """
        # Check for comma-separated range
        if ',' in timeframe:
            parts = timeframe.split(',')
            if len(parts) == 2:
                from_str, to_str = parts
                
                # Try to parse as Unix timestamps
                try:
                    from_ts = int(from_str)
                    to_ts = int(to_str)
                    # If values are in milliseconds (>10 digits), convert to seconds
                    if from_ts > 9999999999:
                        from_ts = from_ts // 1000
                    if to_ts > 9999999999:
                        to_ts = to_ts // 1000
                    return (from_ts, to_ts)
                except ValueError:
                    pass
                
                # Try to parse as date strings
                try:
                    from_dt = self._parse_datetime(from_str)
                    to_dt = self._parse_datetime(to_str)
                    return (int(from_dt.timestamp()), int(to_dt.timestamp()))
                except:
                    print(f"⚠️ Invalid range format '{timeframe}', using default 1h")
                    now = int(datetime.now().timestamp())
                    return (now - 3600, now)
        
        # Check for single date (whole day)
        if '-' in timeframe and not timeframe.startswith('-'):
            try:
                dt = self._parse_datetime(timeframe)
                # Set to start of day
                start_dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                # Set to end of day
                end_dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                return (int(start_dt.timestamp()), int(end_dt.timestamp()))
            except:
                pass
        
        # Original relative time parsing
        match = re.match(r'^(\d+)([mhd])$', timeframe)
        if match:
            value, unit = match.groups()
            value = int(value)
            
            if unit == 'm':
                seconds_ago = value * 60
            elif unit == 'h':
                seconds_ago = value * 3600
            elif unit == 'd':
                seconds_ago = value * 86400
            else:
                seconds_ago = 3600
            
            now = int(datetime.now().timestamp())
            return (now - seconds_ago, now)
        
        # Default to 1 hour
        print(f"⚠️ Invalid timeframe '{timeframe}', using default 1h")
        now = int(datetime.now().timestamp())
        return (now - 3600, now)
    
    def _parse_datetime(self, dt_str: str) -> datetime:
        """Parse various datetime formats"""
        dt_str = dt_str.strip()
        
        # Try ISO format with timezone
        if 'T' in dt_str:
            try:
                # Handle with timezone
                if '+' in dt_str or dt_str.endswith('Z'):
                    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                else:
                    # Assume local timezone
                    return datetime.fromisoformat(dt_str)
            except:
                pass
        
        # Try common date formats
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m-%d-%Y', '%m/%d/%Y']:
            try:
                return datetime.strptime(dt_str, fmt)
            except:
                continue
        
        raise ValueError(f"Could not parse datetime: {dt_str}")

    def query_metrics(self, query: str, timeframe: str = "1h"):
        """Query Datadog metrics"""
        from_time, to_time = self.parse_timeframe(timeframe)

        params = {
            "from": from_time,
            "to": to_time,
            "query": query
        }

        try:
            response = requests.get(
                f"{self.base_url}/query",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Query failed: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None

    def list_metrics(self, search: str = None, timeframe: str = "1h"):
        """List available metrics"""
        from_time, to_time = self.parse_timeframe(timeframe)

        params = {"from": from_time}
        
        try:
            response = requests.get(
                f"{self.base_url}/metrics",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            metrics = data.get('metrics', [])
            if search:
                metrics = [m for m in metrics if search.lower() in m.lower()]
            
            return {"metrics": metrics, "count": len(metrics)}
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to list metrics: {e}")
            return None

    def get_metric_metadata(self, metric_name: str):
        """Get metadata for a specific metric"""
        try:
            response = requests.get(
                f"{self.base_url}/metrics/{metric_name}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to get metric metadata: {e}")
            return None

    def query_logs(self, query: str, timeframe: str = "1h", limit: int = 100):
        """Query Datadog logs"""
        from_ts, to_ts = self.parse_timeframe(timeframe)
        from_time = datetime.fromtimestamp(from_ts)
        to_time = datetime.fromtimestamp(to_ts)
        
        # Format times in RFC3339 format required by logs API
        from_str = from_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        to_str = to_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        payload = {
            "filter": {
                "from": from_str,
                "to": to_str,
                "query": query
            },
            "page": {
                "limit": limit
            },
            "sort": "timestamp"
        }
        
        try:
            response = requests.post(
                self.logs_url,
                json=payload,
                headers={**self.headers, "Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Log query failed: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None

    def query_traces(self, query: str, timeframe: str = "1h", limit: int = 100):
        """Query Datadog APM traces/spans"""
        from_ts, to_ts = self.parse_timeframe(timeframe)
        from_time = datetime.fromtimestamp(from_ts)
        to_time = datetime.fromtimestamp(to_ts)
        
        # Format times in RFC3339 format required by spans API
        from_str = from_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        to_str = to_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        payload = {
            "data": {
                "type": "search_request",
                "attributes": {
                    "filter": {
                        "from": from_str,
                        "to": to_str,
                        "query": query
                    },
                    "page": {
                        "limit": limit
                    },
                    "sort": "timestamp"
                }
            }
        }
        
        try:
            response = requests.post(
                self.traces_url,
                json=payload,
                headers={**self.headers, "Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Trace query failed: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None

    def generate_log_url(self, query: str, timeframe: str = "1h", event_id: str = None) -> str:
        """Generate Datadog Log Explorer URL, optionally for a specific event"""
        from_ts_sec, to_ts_sec = self.parse_timeframe(timeframe)
        
        # Convert to milliseconds timestamp
        from_ts = int(from_ts_sec * 1000)
        to_ts = int(to_ts_sec * 1000)
        
        # URL encode the query
        encoded_query = urllib.parse.quote(query)
        
        # Build the base URL
        url = f"https://app.datadoghq.com/logs?query={encoded_query}"
        
        # Add event ID if provided
        if event_id:
            url += f"&event={event_id}"
        
        # Add standard parameters
        url += f"&from_ts={from_ts}&to_ts={to_ts}"
        url += "&agg_m=count&agg_m_source=base&agg_t=count"
        url += "&cols=host%2Cservice&fromUser=true&messageDisplay=inline"
        url += "&refresh_mode=sliding&storage=hot&stream_sort=desc&viz=stream&live=true"
        
        return url
    
    def generate_trace_url(self, query: str, timeframe: str = "1h") -> str:
        """Generate Datadog APM Trace URL"""
        from_ts_sec, to_ts_sec = self.parse_timeframe(timeframe)
        
        # Convert to milliseconds timestamp
        start_ms = int(from_ts_sec * 1000)
        end_ms = int(to_ts_sec * 1000)
        
        # URL encode the query
        encoded_query = urllib.parse.quote(query)
        
        # Build the URL
        url = f"https://app.datadoghq.com/apm/traces?query={encoded_query}&start={start_ms}&end={end_ms}&paused=true"
        return url
    
    def generate_metric_url(self, query: str, timeframe: str = "1h") -> str:
        """Generate Datadog Metrics Explorer URL"""
        from_ts, to_ts = self.parse_timeframe(timeframe)
        
        # Already in seconds timestamp format
        
        # URL encode the query
        encoded_query = urllib.parse.quote(query)
        
        # Build the URL
        url = f"https://app.datadoghq.com/metric/explorer?from_ts={from_ts}&to_ts={to_ts}&live=true&query={encoded_query}"
        return url

    def validate_connection(self):
        """Validate API keys"""
        try:
            response = requests.get(
                f"{self.base_url}/validate",
                headers={"DD-API-KEY": self.api_key}
            )
            if response.status_code == 200:
                return True
            else:
                print(f"⚠️ API key validation returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection validation failed: {e}")
            return False

    def format_results(self, data: dict, query_type: str = "metrics", url: str = None, show_event_urls: bool = False, query: str = None, timeframe: str = "1h"):
        """Format results for display"""
        if not data:
            return None

        if query_type == "list":
            metrics = data.get('metrics', [])
            print(f"→ {data.get('count', 0)} metrics found")
            for metric in metrics[:50]:  # Show first 50
                print(f"  • {metric}")
            if len(metrics) > 50:
                print(f"  ... and {len(metrics) - 50} more")
            return data
        
        elif query_type == "traces":
            traces = data.get('data', [])
            print(f"→ {len(traces)} trace spans found")
            
            for idx, trace in enumerate(traces[:20]):  # Show first 20 traces
                attrs = trace.get('attributes', {})
                custom = attrs.get('custom', {})
                
                # Extract main attributes
                timestamp = attrs.get('start_timestamp', attrs.get('end_timestamp', 'unknown'))
                resource_name = attrs.get('resource_name', attrs.get('operation_name', 'unknown'))
                service = attrs.get('service', custom.get('base_service', 'unknown'))
                duration = custom.get('duration', 0)
                env = attrs.get('env', custom.get('env', 'unknown'))
                error = attrs.get('error')
                
                # Extract database info if present
                db_info = custom.get('db', {})
                db_statement = db_info.get('statement', '')
                
                # Try to parse timestamp
                try:
                    ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    ts_str = timestamp
                
                # Convert duration from nanoseconds to milliseconds
                duration_ms = duration / 1_000_000 if duration else 0
                
                print(f"\n  [{idx + 1}] {ts_str} | {service} | {resource_name} | {duration_ms:.2f}ms")
                
                # Show additional attributes if present (indented)
                if db_statement:
                    print(f"      DB: {db_statement[:80]}...")  # Truncate long statements
                if error:
                    print(f"      ERROR: {error}")
            
            if len(traces) > 20:
                print(f"\n  ... and {len(traces) - 20} more trace spans")
            
            return data
        
        elif query_type == "logs":
            logs = data.get('data', [])
            print(f"→ {len(logs)} log entries found")
            
            for idx, log_entry in enumerate(logs[:20]):  # Show first 20 logs
                attrs = log_entry.get('attributes', {})
                
                # Extract log ID for direct link
                log_id = log_entry.get('id', None)
                
                # Extract main attributes
                timestamp = attrs.get('timestamp', 'unknown')
                message = attrs.get('message', 'no message')
                service = attrs.get('service', 'unknown')
                host = attrs.get('host', attrs.get('attributes', {}).get('host', 'unknown'))
                status = attrs.get('status', 'info')
                
                # Extract nested attributes for performance logs
                nested_attrs = attrs.get('attributes', {})
                
                # Try to parse timestamp
                try:
                    ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    ts_str = timestamp
                
                # Truncate message if too long
                msg_display = message[:100] + "..." if len(message) > 100 else message
                status_icon = "❌" if status == "error" else "⚠️" if status == "warn" else ""
                print(f"\n  [{idx + 1}] {ts_str} | {service} | {status_icon}{status}")
                print(f"      {msg_display}")
                
                # If it's a performance log, show the metrics inline
                if 'run_get_rows_db_queries' in str(message) and nested_attrs:
                    perf_parts = []
                    if 'total_db_queries_time' in nested_attrs:
                        perf_parts.append(f"DB: {nested_attrs.get('total_db_queries_time')}s")
                    if 'cache_hit' in nested_attrs:
                        perf_parts.append(f"Cache: {nested_attrs.get('cache_hit')}")
                    if 'total_row_count' in nested_attrs:
                        perf_parts.append(f"Rows: {nested_attrs.get('total_row_count')}")
                    if perf_parts:
                        print(f"      {' | '.join(perf_parts)}")
                
                # Show event-specific URL if requested and ID is available
                if show_event_urls and log_id and query:
                    event_url = self.generate_log_url(query, timeframe, log_id)
                    print(f"      🔗 {event_url}")
            
            if len(logs) > 20:
                print(f"\n  ... and {len(logs) - 20} more log entries")
            
            return data

        elif query_type == "metrics":
            if 'series' in data:
                series = data.get('series', [])
                print(f"→ {len(series)} series returned")
                
                for idx, s in enumerate(series[:5]):  # Show first 5 series
                    metric = s.get('metric', 'unknown')
                    points = s.get('pointlist', [])
                    scope = s.get('scope', '')
                    
                    if points:
                        values = [p[1] for p in points if p[1] is not None]
                        if values:
                            stats = f"min={min(values):.2f}, max={max(values):.2f}, avg={sum(values)/len(values):.2f}"
                            print(f"\n  [{idx + 1}] {metric} ({len(points)} points)")
                            print(f"      {scope}")
                            print(f"      {stats}")
                        else:
                            print(f"\n  [{idx + 1}] {metric} - no data")
                    else:
                        print(f"\n  [{idx + 1}] {metric} - no points")
                
                if len(series) > 5:
                    print(f"\n  ... and {len(series) - 5} more series")
            else:
                print("→ No series data returned")
            
            # Display URL if provided
            if url:
                print(f"\n🔗 {url}")
            
            return data

        # Display URL if provided
        if url:
            print(f"\n🔗 {url}")
        
        return data

def main():
    parser = argparse.ArgumentParser(
        description='Hebbia Datadog Explorer - Query metrics, logs, and APM data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📊 METRICS:
  avg:system.cpu.idle{*}                                     # CPU usage
  avg:postgresql.connections{*}                              # DB connections
  avg:postgresql.percent_usage_connections{*}                # Connection pool usage %
  avg:trace.postgres.connect{*}                              # DB connection time (APM)
  percentile:trace.postgres.query.time{*}:95                 # P95 query time
  avg:trace.request.duration{service:hebbia-api}             # API latency
  percentile:trace.request.duration{service:sheets}:95       # P95 latency

🐘 POSTGRESQL METRICS:
  avg:postgresql.connections{*}                              # Active connections
  avg:postgresql.max_connections{*}                          # Max connections allowed
  avg:postgresql.percent_usage_connections{*}                # Connection pool usage %
  avg:trace.postgres.connect{*}                              # Connection time (APM)
  avg:trace.postgres.query.time{*}                           # Query execution time
  avg:trace.postgres.query.rows{*}                           # Rows returned

📝 LOGS (prefix with 'logs:'):
  logs:run_get_rows_db_queries                               # Performance logs
  logs:service:sheets status:error                           # Service errors
  logs:@performance.total_db_queries_time:>1                 # Slow queries

🔍 APM TRACES (prefix with 'traces:' or 'spans:'):
  traces:env:prod resource_name:postgres.connect             # DB connections
  traces:env:prod resource_name:postgres.connect @duration:>1000000000  # Slow DB connections (>1s)
  traces:service:sheets @duration:>5000000000                # Slow traces (>5s)
  traces:env:prod service:postgres                           # All postgres traces

🔍 DISCOVERY:
  list-metrics                                                # List all metrics
  list-metrics --search postgres                             # Find specific metrics
  info:postgresql.connections                                # Metric metadata

📊 RAW OUTPUT (for analysis):
  --raw                                                       # JSON output for jq/awk
  --raw | jq '.data[].attributes.attributes'                 # Extract log attributes

⏰ TIMEFRAMES: 5m, 15m, 1h (default), 24h, 7d
        """
    )

    parser.add_argument(
        'query',
        help='Datadog metric query or command (list-metrics, info:metric_name)'
    )

    parser.add_argument(
        '--timeframe',
        default='1h',
        help='''Time range for the query (default: 1h). 
Formats:
  - Relative: 5m, 15m, 1h, 24h, 7d
  - Single day: 2025-01-03
  - Date range: 2025-01-03,2025-01-05
  - ISO range: 2025-01-03T10:00:00,2025-01-03T18:00:00
  - Unix timestamps: 1754539200,1754711999
  - Unix milliseconds: 1754539200000,1754711999999'''
    )

    parser.add_argument(
        '--search',
        help='Search filter for list-metrics command'
    )

    parser.add_argument(
        '--raw',
        action='store_true',
        help='Output raw JSON response'
    )
    
    parser.add_argument(
        '--no-url',
        action='store_true',
        help='Hide Datadog web UI URL (URLs are shown by default)'
    )
    
    parser.add_argument(
        '--event-urls',
        action='store_true',
        help='Show direct links to individual log events (for logs only)'
    )

    args = parser.parse_args()

    dd = DatadogExplorer()

    # Validate connection silently unless there's an error
    if not dd.validate_connection():
        print("❌ Failed to validate API key. Please check your configuration.")
        sys.exit(1)

    # Handle special commands
    if args.query == "list-metrics":
        if not args.raw:
            print(f"🔍 list-metrics [{args.timeframe}]")
        results = dd.list_metrics(search=args.search or args.query.split(':')[1] if ':' in args.query else None, 
                                 timeframe=args.timeframe)
        if args.raw and results:
            print(json.dumps(results, indent=2))
        else:
            dd.format_results(results, query_type="list")
    
    elif args.query.startswith("info:"):
        metric_name = args.query[5:]
        if not args.raw:
            print(f"ℹ️ {args.query}")
        results = dd.get_metric_metadata(metric_name)
        if results:
            print(json.dumps(results, indent=2))
        else:
            print("No metadata found")
    
    elif args.query.startswith("traces:") or args.query.startswith("spans:"):
        # APM trace/span query
        prefix_len = 7 if args.query.startswith("traces:") else 6
        trace_query = args.query[prefix_len:].strip()
        if not args.raw:
            print(f"🔍 {args.query} [{args.timeframe}]")
        
        # Generate URL (shown by default unless --no-url)
        url = None if args.no_url else dd.generate_trace_url(trace_query, args.timeframe)
        
        results = dd.query_traces(trace_query, args.timeframe)
        
        if args.raw and results:
            print(json.dumps(results, indent=2, default=str))
        else:
            dd.format_results(results, query_type="traces", url=url)
    
    elif args.query.startswith("logs:"):
        # Log query
        log_query = args.query[5:].strip()
        if not args.raw:
            print(f"📝 {args.query} [{args.timeframe}]")
        
        # Generate URL (shown by default unless --no-url)
        url = None if args.no_url else dd.generate_log_url(log_query, args.timeframe)
        
        results = dd.query_logs(log_query, args.timeframe)
        
        if args.raw and results:
            print(json.dumps(results, indent=2, default=str))
        else:
            dd.format_results(results, query_type="logs", url=url, 
                            show_event_urls=args.event_urls, query=log_query, 
                            timeframe=args.timeframe)
    
    else:
        # Regular metric query
        if not args.raw:
            print(f"📊 {args.query} [{args.timeframe}]")
        
        # Generate URL (shown by default unless --no-url)
        url = None if args.no_url else dd.generate_metric_url(args.query, args.timeframe)
        
        results = dd.query_metrics(args.query, args.timeframe)
        
        if args.raw and results:
            print(json.dumps(results, indent=2, default=str))
        else:
            dd.format_results(results, query_type="metrics", url=url)

if __name__ == "__main__":
    main()