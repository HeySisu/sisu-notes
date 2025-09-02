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
        self.logs_url = "https://api.datadoghq.com/api/v2/logs/events/search"
        self.headers = {
            "DD-API-KEY": self.api_key,
            "DD-APPLICATION-KEY": self.app_key
        }

    def parse_timeframe(self, timeframe: str) -> int:
        """Convert timeframe string to seconds ago"""
        match = re.match(r'^(\d+)([mhd])$', timeframe)
        if not match:
            print(f"⚠️ Invalid timeframe '{timeframe}', using default 1h")
            return 3600
        
        value, unit = match.groups()
        value = int(value)
        
        if unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 3600
        elif unit == 'd':
            return value * 86400
        else:
            return 3600

    def query_metrics(self, query: str, timeframe: str = "1h"):
        """Query Datadog metrics"""
        seconds_ago = self.parse_timeframe(timeframe)
        to_time = int(datetime.now().timestamp())
        from_time = to_time - seconds_ago

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
        seconds_ago = self.parse_timeframe(timeframe)
        from_time = int(datetime.now().timestamp()) - seconds_ago

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
        seconds_ago = self.parse_timeframe(timeframe)
        to_time = datetime.now()
        from_time = to_time - timedelta(seconds=seconds_ago)
        
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

    def format_results(self, data: dict, query_type: str = "metrics"):
        """Format results for display"""
        if not data:
            return None

        if query_type == "list":
            metrics = data.get('metrics', [])
            print(f"\n📊 Found {data.get('count', 0)} metrics:")
            for metric in metrics[:50]:  # Show first 50
                print(f"  • {metric}")
            if len(metrics) > 50:
                print(f"  ... and {len(metrics) - 50} more")
            return data
        
        elif query_type == "logs":
            logs = data.get('data', [])
            print(f"\n📝 Found {len(logs)} log entries:")
            
            for idx, log_entry in enumerate(logs[:20]):  # Show first 20 logs
                attrs = log_entry.get('attributes', {})
                
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
                
                print(f"\n  Log {idx + 1}:")
                print(f"    Time: {ts_str}")
                print(f"    Service: {service}")
                print(f"    Host: {host}")
                print(f"    Status: {status}")
                print(f"    Message: {message}")
                
                # If it's a performance log, show the metrics
                if 'run_get_rows_db_queries' in str(message) and nested_attrs:
                    if 'total_db_queries_time' in nested_attrs:
                        print(f"    DB Query Time: {nested_attrs.get('total_db_queries_time', 'N/A')}s")
                    if 'hydration_time' in nested_attrs:
                        print(f"    Hydration Time: {nested_attrs.get('hydration_time', 'N/A')}s")
                    if 'cache_hit' in nested_attrs:
                        print(f"    Cache Hit: {nested_attrs.get('cache_hit', 'N/A')}")
                    if 'total_row_count' in nested_attrs:
                        print(f"    Total Rows: {nested_attrs.get('total_row_count', 'N/A')}")
                    if 'sheet' in nested_attrs:
                        print(f"    Sheet ID: {nested_attrs.get('sheet', 'N/A')}")
                    
                    # Show file info if available
                    file_info = nested_attrs.get('file_info', {})
                    if file_info:
                        print(f"    Source: {file_info.get('file', '')}:{file_info.get('line', '')}")
            
            if len(logs) > 20:
                print(f"\n  ... and {len(logs) - 20} more log entries")
            
            return data

        elif query_type == "metrics":
            if 'series' in data:
                series = data.get('series', [])
                print(f"\n📊 Query returned {len(series)} series:")
                
                for idx, s in enumerate(series[:5]):  # Show first 5 series
                    metric = s.get('metric', 'unknown')
                    points = s.get('pointlist', [])
                    scope = s.get('scope', '')
                    
                    print(f"\n  Series {idx + 1}:")
                    print(f"    Metric: {metric}")
                    print(f"    Scope: {scope}")
                    print(f"    Points: {len(points)}")
                    
                    if points:
                        # Show first and last few points
                        print(f"    First point: {datetime.fromtimestamp(points[0][0]/1000).strftime('%Y-%m-%d %H:%M:%S')} = {points[0][1]}")
                        if len(points) > 1:
                            print(f"    Last point:  {datetime.fromtimestamp(points[-1][0]/1000).strftime('%Y-%m-%d %H:%M:%S')} = {points[-1][1]}")
                        
                        # Calculate stats
                        values = [p[1] for p in points if p[1] is not None]
                        if values:
                            print(f"    Stats: min={min(values):.2f}, max={max(values):.2f}, avg={sum(values)/len(values):.2f}")
                
                if len(series) > 5:
                    print(f"\n  ... and {len(series) - 5} more series")
            else:
                print("📊 Query completed but no series data returned")
            
            return data

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
        help='Time range for the query (default: 1h). Examples: 5m, 15m, 1h, 24h, 7d'
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

    args = parser.parse_args()

    dd = DatadogExplorer()

    # Validate connection
    if not args.raw:
        print("🔐 Validating Datadog API connection...")
    if not dd.validate_connection():
        print("❌ Failed to validate API key. Please check your configuration.")
        sys.exit(1)
    
    if not args.raw:
        print("✅ Connected to Datadog API")

    # Handle special commands
    if args.query == "list-metrics":
        print(f"🔍 Listing metrics (timeframe: {args.timeframe})...")
        results = dd.list_metrics(search=args.search or args.query.split(':')[1] if ':' in args.query else None, 
                                 timeframe=args.timeframe)
        if args.raw and results:
            print(json.dumps(results, indent=2))
        else:
            dd.format_results(results, query_type="list")
    
    elif args.query.startswith("info:"):
        metric_name = args.query[5:]
        print(f"ℹ️ Getting metadata for metric: {metric_name}")
        results = dd.get_metric_metadata(metric_name)
        if results:
            print(json.dumps(results, indent=2))
        else:
            print("No metadata found")
    
    elif args.query.startswith("logs:"):
        # Log query
        log_query = args.query[5:].strip()
        if not args.raw:
            print(f"📝 Querying logs: {log_query}")
            print(f"⏰ Timeframe: {args.timeframe}")
        
        results = dd.query_logs(log_query, args.timeframe)
        
        if args.raw and results:
            print(json.dumps(results, indent=2, default=str))
        else:
            dd.format_results(results, query_type="logs")
    
    else:
        # Regular metric query
        print(f"📊 Querying: {args.query}")
        print(f"⏰ Timeframe: {args.timeframe}")
        
        results = dd.query_metrics(args.query, args.timeframe)
        
        if args.raw and results:
            print(json.dumps(results, indent=2, default=str))
        else:
            dd.format_results(results, query_type="metrics")

if __name__ == "__main__":
    main()