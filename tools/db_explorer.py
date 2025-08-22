#!/usr/bin/env python3
"""
Hebbia Database Explorer - Flexible SQL Query Tool
Usage: python db_explorer.py "<sql_query>"
"""

import os
import sys
import json

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

try:
    from .config import DB_PASSWORD
except ImportError:
    try:
        from config import DB_PASSWORD
    except ImportError:
        print("❌ Configuration not found. Please ensure tools/config.py exists with DB_PASSWORD.")
        sys.exit(1)

class HebbiaDatabaseExplorer:
    def __init__(self):
        self.connection_params = {
            'host': 'read-write-endpoint-staging.endpoint.proxy-cqyf4jsjudre.us-east-1.rds.amazonaws.com',
            'port': 5432,
            'database': 'hebbia',
            'user': 'postgres',
            'password': DB_PASSWORD
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
        """Execute query and return results as list of dictionaries"""
        try:
            self.cursor.execute(query)
            columns = [desc[0] for desc in self.cursor.description]
            rows = self.cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []

def main():
    if len(sys.argv) != 2:
        print("""
Hebbia Database Explorer - Flexible SQL Query Tool

Usage:
  python db_explorer.py "<sql_query>"

Examples:
  python db_explorer.py "SELECT * FROM users WHERE name = 'Sisu Xi'"
  python db_explorer.py "SELECT COUNT(*) FROM users"
  python db_explorer.py "SELECT id, name, email FROM users WHERE email LIKE '%@hebbia.ai%' LIMIT 10"

For complete database knowledge and examples, see:
  .claude/command/database.md
        """)
        return
    
    query = sys.argv[1]
    
    db = HebbiaDatabaseExplorer()
    
    if not db.connect():
        return
    
    try:
        print("✅ Connected to Hebbia database")
        results = db.execute_query(query)
        
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