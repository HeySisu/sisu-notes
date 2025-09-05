#!/usr/bin/env python3
"""
Hebbia Database Explorer - READ-ONLY SQL Query Tool
Usage: python db_explorer.py [--env staging|prod] "<sql_query>"

NOTE: Uses readonly database users - write operations are blocked at the database level.
"""

import os
import sys
import json
import argparse
import subprocess
import socket

def ensure_venv():
    """Ensure we're running in the virtual environment"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    venv_python = os.path.join(repo_root, '.venv', 'bin', 'python')

    if not os.path.exists(venv_python):
        print("❌ Virtual environment not found. Please run:")
        print(f"  cd {repo_root}")
        print("  python3 -m venv .venv")
        print("  .venv/bin/pip install psycopg2-binary")
        sys.exit(1)

    if sys.executable != venv_python:
        print("🔄 Switching to virtual environment...")
        os.execv(venv_python, [venv_python] + sys.argv)

ensure_venv()

import psycopg2
from typing import List, Dict, Any

def check_tailscale_connection():
    """Check if Tailscale VPN is connected"""
    try:
        # Try the Tailscale CLI first (works on macOS with app installed)
        # On macOS, the CLI is at /Applications/Tailscale.app/Contents/MacOS/Tailscale
        tailscale_paths = [
            'tailscale',  # If installed via brew or in PATH
            '/Applications/Tailscale.app/Contents/MacOS/Tailscale'  # macOS app
        ]
        
        tailscale_cmd = None
        for path in tailscale_paths:
            try:
                result = subprocess.run([path, 'status'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    tailscale_cmd = path
                    break
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
        
        if not tailscale_cmd:
            return False, "Tailscale CLI not found. Please ensure Tailscale app is installed and running"
        
        # Get status
        result = subprocess.run([tailscale_cmd, 'status'], 
                               capture_output=True, text=True, timeout=5)
        
        # Check if we're connected (look for active status)
        status_output = result.stdout
        if 'Tailscale is stopped' in status_output:
            return False, "Tailscale is stopped. Please start the Tailscale app"
        
        # Additional check: try to resolve the database hosts
        staging_host = 'hebbia-backend-postgres-staging.cqyf4jsjudre.us-east-1.rds.amazonaws.com'
        
        try:
            socket.gethostbyname(staging_host)
            return True, "Tailscale connected and database hosts are reachable"
        except socket.gaierror:
            return False, "Tailscale appears connected but cannot resolve database hosts. Check VPN configuration."
            
    except subprocess.TimeoutExpired:
        return False, "Tailscale status check timed out"
    except Exception as e:
        return False, f"Error checking Tailscale status: {e}"

try:
    from config import STAGING_DB_PASSWORD, PROD_DB_PASSWORD
except ImportError:
    print("❌ Configuration not found. Please ensure tools/config.py exists with database passwords.")
    sys.exit(1)

class HebbiaDatabaseExplorer:
    def __init__(self, environment='staging'):
        self.environment = environment

        if environment == 'prod':
            self.connection_params = {
                'host': 'hebbia-backend-postgres-prod.cqyf4jsjudre.us-east-1.rds.amazonaws.com',
                'port': 5432,
                'database': 'hebbia',
                'user': 'readonly_user',
                'password': PROD_DB_PASSWORD
            }
        else:  # Default to staging
            self.connection_params = {
                'host': 'hebbia-backend-postgres-staging.cqyf4jsjudre.us-east-1.rds.amazonaws.com',
                'port': 5432,
                'database': 'hebbia',
                'user': 'readonly_user',
                'password': STAGING_DB_PASSWORD
            }

        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()



    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute query (readonly user prevents any write operations)"""
        try:
            # Set statement timeout to 1 minute (60000 milliseconds)
            self.cursor.execute("SET statement_timeout = 60000")
            self.cursor.execute(query)
            columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []
            rows = self.cursor.fetchall() if self.cursor.description else []
            return [dict(zip(columns, row)) for row in rows] if columns else []
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []

def main():
    # Check Tailscale VPN connection first
    vpn_connected, vpn_message = check_tailscale_connection()
    if not vpn_connected:
        print(f"❌ VPN Error: {vpn_message}")
        print("\n📡 To connect to Hebbia database, you need Tailscale VPN:")
        print("  1. Install Tailscale: https://tailscale.com/download")
        print("  2. Start Tailscale: tailscale up")
        print("  3. Authenticate if prompted")
        print("  4. Try this command again")
        sys.exit(1)
    
    print(f"✅ VPN Check: {vpn_message}")
    
    parser = argparse.ArgumentParser(
        description='Hebbia Database Explorer - READ-ONLY SQL Query Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🔒 READONLY ACCESS:
  Uses readonly database users - write operations are blocked at the database level.

✅ Examples:
  python db_explorer.py "SELECT * FROM users WHERE name = 'Sisu Xi'"
  python db_explorer.py --env prod "SELECT COUNT(*) FROM users"
  python db_explorer.py "SELECT id, name, email FROM users WHERE email LIKE '%@hebbia.ai%' LIMIT 10"
  python db_explorer.py --env staging "SELECT org.name, COUNT(u.id) FROM organizations org LEFT JOIN users u ON u.id = ANY(org.user_ids) GROUP BY org.name"

For complete database knowledge and examples, see:
  .claude/command/database.md
        """
    )

    parser.add_argument(
        '--env',
        choices=['staging', 'prod'],
        default='staging',
        help='Database environment to connect to (default: staging)'
    )

    parser.add_argument(
        'query',
        help='SQL query to execute'
    )

    args = parser.parse_args()

    db = HebbiaDatabaseExplorer(args.env)

    if not db.connect():
        return

    try:
        print(f"✅ Connected to Hebbia {args.env} database (readonly user)")
        results = db.execute_query(args.query)

        if results:
            print(f"📊 Query results ({len(results)} rows):")
            print(json.dumps(results, indent=2, default=str))
        else:
            print("📊 Query completed - no results returned")

    finally:
        db.disconnect()
        print("🔌 Disconnected from database")

if __name__ == "__main__":
    main()