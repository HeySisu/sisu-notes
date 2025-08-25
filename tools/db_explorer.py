#!/usr/bin/env python3
"""
Hebbia Database Explorer - READ-ONLY SQL Query Tool
Usage: python db_explorer.py "<sql_query>"

SAFETY FEATURES:
- Session-level read-only mode enforced by PostgreSQL
- Query validation to block write operations
- Automatic transaction rollback after each query
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
        """Establish database connection with read-only safety measures"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.cursor = self.conn.cursor()

            # Set session to read-only mode - PostgreSQL will enforce this
            self.cursor.execute("SET default_transaction_read_only = TRUE;")
            self.conn.commit()
            print("🔒 Database session set to read-only mode")

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

    def _validate_query(self, query: str) -> bool:
        """Validate that query appears to be read-only"""
        # Convert to lowercase and remove extra whitespace for analysis
        clean_query = ' '.join(query.lower().split())

        # List of potentially dangerous SQL keywords
        write_keywords = [
            'insert', 'update', 'delete', 'drop', 'create', 'alter',
            'truncate', 'replace', 'merge', 'grant', 'revoke',
            'set role', 'set session_authorization', 'copy', 'call', 'exec'
        ]

        for keyword in write_keywords:
            if keyword in clean_query:
                print(f"❌ Query blocked: Contains potentially unsafe keyword '{keyword}'")
                return False

        return True

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute query with multiple safety layers"""
        # Layer 1: Query validation
        if not self._validate_query(query):
            print("   Only SELECT statements and read-only operations are allowed")
            return []

        try:
            # Layer 2: Disable autocommit to control transactions
            self.conn.autocommit = False

            # Layer 3: Execute query (PostgreSQL session-level read-only will prevent writes)
            self.cursor.execute(query)
            columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []
            rows = self.cursor.fetchall() if self.cursor.description else []

            # Layer 4: Always rollback to ensure no changes persist (extra safety)
            self.conn.rollback()

            return [dict(zip(columns, row)) for row in rows] if columns else []

        except Exception as e:
            # Ensure rollback on any error
            try:
                self.conn.rollback()
            except:
                pass
            print(f"❌ Query failed: {e}")
            return []

def main():
    if len(sys.argv) != 2:
        print("""
Hebbia Database Explorer - READ-ONLY SQL Query Tool

🔒 SAFETY FEATURES (Multiple Layers):
  1. Query validation blocks write operations (INSERT, UPDATE, DELETE, etc.)
  2. PostgreSQL session-level read-only mode enforced
  3. Automatic transaction rollback after each query
  4. No changes can persist to the database

Usage:
  python db_explorer.py "<sql_query>"

✅ SAFE Examples:
  python db_explorer.py "SELECT * FROM users WHERE name = 'Sisu Xi'"
  python db_explorer.py "SELECT COUNT(*) FROM users"
  python db_explorer.py "SELECT id, name, email FROM users WHERE email LIKE '%@hebbia.ai%' LIMIT 10"
  python db_explorer.py "SELECT org.name, COUNT(u.id) FROM organizations org LEFT JOIN users u ON u.id = ANY(org.user_ids) GROUP BY org.name"

❌ BLOCKED Examples (will be rejected):
  python db_explorer.py "INSERT INTO users ..."  # ❌ Blocked by validation
  python db_explorer.py "UPDATE users SET ..."   # ❌ Blocked by validation
  python db_explorer.py "DELETE FROM users ..."  # ❌ Blocked by validation
  python db_explorer.py "DROP TABLE users"       # ❌ Blocked by validation

For complete database knowledge and examples, see:
  .claude/command/database.md
        """)
        return

    query = sys.argv[1]

    db = HebbiaDatabaseExplorer()

    if not db.connect():
        return

    try:
        print("✅ Connected to Hebbia database (read-only mode)")
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