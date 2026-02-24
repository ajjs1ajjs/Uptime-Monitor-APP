#!/usr/bin/env python3
"""CLI tool for password management"""
import sys
import os
import argparse
import sqlite3
import bcrypt

def get_db_path():
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check common locations
    paths = [
        os.path.join(app_dir, "sites.db"),
        "/var/lib/uptime-monitor/sites.db",
        os.path.expanduser("~/UptimeMonitor/data/sites.db"),
    ]
    
    for p in paths:
        if os.path.exists(p):
            return p
    
    return paths[0]

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def init_auth(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin BOOLEAN DEFAULT 0,
        must_change_password BOOLEAN DEFAULT 1,
        created_at TEXT,
        last_login TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        user_id INTEGER,
        created_at TEXT,
        expires_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    c.execute("SELECT id FROM users WHERE username = 'admin'")
    if not c.fetchone():
        password_hash = hash_password('admin')
        c.execute("INSERT INTO users (username, password_hash, is_admin, must_change_password, created_at) VALUES (?, ?, 1, 1, datetime('now'))",
                 ('admin', password_hash))
        print("✓ Created default user: admin / admin")
    else:
        print("✓ User 'admin' already exists")
    
    conn.commit()
    conn.close()
    print(f"✓ Database initialized at {db_path}")

def reset_password(db_path, username, password):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    password_hash = hash_password(password)
    c.execute("UPDATE users SET password_hash = ?, must_change_password = 1 WHERE username = ?",
             (password_hash, username))
    
    if c.rowcount == 0:
        print(f"✗ User '{username}' not found")
        conn.close()
        sys.exit(1)
    
    conn.commit()
    conn.close()
    print(f"✓ Password reset for user '{username}' to '{password}'")

def list_users(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("SELECT id, username, is_admin, must_change_password, last_login FROM users")
    rows = c.fetchall()
    
    if not rows:
        print("No users found")
    else:
        print("\nUsers:")
        print(f"{'ID':<5} {'Username':<15} {'Admin':<8} {'Must Change':<12} {'Last Login'}")
        print("-" * 60)
        for row in rows:
            print(f"{row[0]:<5} {row[1]:<15} {'Yes' if row[2] else 'No':<8} {'Yes' if row[3] else 'No':<12} {row[4] or 'Never'}")
    
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Uptime Monitor CLI")
    parser.add_argument("--db", default=None, help="Path to database")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    subparsers.add_parser("init", help="Initialize database and create default user")
    
    reset_parser = subparsers.add_parser("reset-password", help="Reset user password")
    reset_parser.add_argument("--user", default="admin", help="Username")
    reset_parser.add_argument("--password", default="admin", help="New password")
    
    subparsers.add_parser("list-users", help="List all users")
    
    args = parser.parse_args()
    
    db_path = args.db or get_db_path()
    
    if args.command == "init":
        init_auth(db_path)
    elif args.command == "reset-password":
        reset_password(db_path, args.user, args.password)
    elif args.command == "list-users":
        list_users(db_path)
    else:
        parser.print_help()
