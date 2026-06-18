# -*- coding: utf-8 -*-
"""
AegisOps Demo Vulnerability Target
==================================
This application intentionally contains security anti-patterns (CWE-89 SQL Injection) 
to serve as an automated remediation playground for the AegisOps engine.
"""

import sqlite3
from typing import Dict, Any

class VulnerableApp:
    """Target application with intentional SQL injection flaws."""

    def __init__(self, db_path: str = "demo.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, secret_key TEXT)")
        cursor.execute("INSERT OR IGNORE INTO users (id, username, secret_key) VALUES (1, 'admin', 'sk_aegis_9982347')")
        conn.commit()
        conn.close()

    def get_user_secret_vulnerable(self, username: str) -> str:
        """
        Vulnerable method executing direct raw string formatting SQL query (CWE-89).
        Allows input values like: admin' OR '1'='1
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # VULNERABLE: Direct string formatting into SQL statement
        query = f"SELECT secret_key FROM users WHERE username = '{username}'"
        cursor.execute(query)
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "No user found."

    def get_user_secret_secure(self, username: str) -> str:
        """
        Remediated secure version utilizing parameterized query.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # SECURE: Using placeholding parameters
        query = "SELECT secret_key FROM users WHERE username = ?"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "No user found."

if __name__ == "__main__":
    app = VulnerableApp()
    # Simple validation check of the vulnerability
    secret = app.get_user_secret_vulnerable("admin' OR '1'='1")
    print(f"Retrieved Secret: {secret}")
