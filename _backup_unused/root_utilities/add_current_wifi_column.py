#!/usr/bin/env python3
"""
Add current_wifi_ssid column to devices table if it doesn't exist
"""

import sqlite3
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

database_dir = Path(__file__).parent / 'database'
db_path = database_dir / 'antitheft.db'

if not db_path.exists():
    print(f"Database not found at: {db_path}")
    sys.exit(1)

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute('PRAGMA table_info(devices)')
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'current_wifi_ssid' not in columns:
        print("Adding current_wifi_ssid column to devices table...")
        cursor.execute('ALTER TABLE devices ADD COLUMN current_wifi_ssid VARCHAR(100)')
        conn.commit()
        print("[SUCCESS] Column added successfully!")
    else:
        print("[SUCCESS] Column already exists")
    
    conn.close()
    print("Database migration complete!")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

