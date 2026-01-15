#!/usr/bin/env python3
"""
Database migration: Add Prey Project-style hardware fields to Device model
Run this script once to update the database schema
"""

import sqlite3
import os
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / 'database' / 'antitheft.db'

def migrate():
    """Add hardware fields to devices table"""
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Check which columns already exist
        cursor.execute("PRAGMA table_info(devices)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # Define new columns
        new_columns = [
            ('serial_number', 'TEXT'),
            ('bios_vendor', 'TEXT'),
            ('bios_version', 'TEXT'),
            ('motherboard_vendor', 'TEXT'),
            ('motherboard_model', 'TEXT'),
            ('motherboard_serial', 'TEXT'),
            ('cpu_model', 'TEXT'),
            ('cpu_cores', 'INTEGER'),
            ('cpu_threads', 'INTEGER'),
            ('cpu_speed_mhz', 'INTEGER'),
            ('ram_mb', 'INTEGER'),
            ('ram_gb', 'REAL'),
            ('network_interfaces', 'TEXT'),
            ('mac_addresses', 'TEXT')
        ]
        
        # Add columns that don't exist
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE devices ADD COLUMN {column_name} {column_type}")
                    print(f"[OK] Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"[WARN] Error adding {column_name}: {e}")
            else:
                print(f"[SKIP] Column already exists: {column_name}")
        
        conn.commit()
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Hardware Fields Migration")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print()
    
    migrate()
    
    print()
    print("=" * 60)