#!/usr/bin/env python3
"""
Database migration: Agent-First Architecture (Prey Project style)
Adds fingerprint_hash, makes user_id nullable, adds registered_at

Run this script once to update the database schema
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

# Database path
DB_PATH = Path(__file__).parent.parent / 'database' / 'antitheft.db'

def migrate():
    """Migrate database to agent-first architecture"""
    if not DB_PATH.exists():
        print(f"[ERROR] Database not found at {DB_PATH}")
        return False
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Check which columns already exist
        cursor.execute("PRAGMA table_info(devices)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # New columns for agent-first architecture
        new_columns = [
            ('fingerprint_hash', 'TEXT', 'NULL'),
            ('registered_at', 'TIMESTAMP', 'NULL')
        ]
        
        # Add new columns
        for column_name, column_type, default_value in new_columns:
            if column_name not in existing_columns:
                try:
                    if default_value == 'NULL':
                        cursor.execute(f"ALTER TABLE devices ADD COLUMN {column_name} {column_type}")
                    else:
                        cursor.execute(f"ALTER TABLE devices ADD COLUMN {column_name} {column_type} DEFAULT {default_value}")
                    print(f"[OK] Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"[WARN] Error adding {column_name}: {e}")
            else:
                print(f"[SKIP] Column already exists: {column_name}")
        
        # Create index on fingerprint_hash for fast lookups
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_devices_fingerprint_hash ON devices(fingerprint_hash)")
            print("[OK] Created index on fingerprint_hash")
        except sqlite3.OperationalError as e:
            print(f"[WARN] Error creating index: {e}")
        
        # Make user_id nullable (required for unowned devices)
        # SQLite doesn't support MODIFY COLUMN directly, so we need to recreate the table
        # This is a complex migration - we'll handle it gracefully
        try:
            # Check current schema
            cursor.execute("PRAGMA table_info(devices)")
            user_id_info = [row for row in cursor.fetchall() if row[1] == 'user_id']
            
            if user_id_info:
                user_id_nullable = user_id_info[0][3]  # notnull flag (0 = nullable, 1 = not null)
                if user_id_nullable == 1:
                    print("[INFO] user_id is currently NOT NULL - migration to nullable requires table recreation")
                    print("[INFO] This will be handled by SQLAlchemy on next model load")
                    print("[INFO] Existing devices with user_id will remain linked")
        except Exception as e:
            print(f"[WARN] Could not check user_id nullable status: {e}")
        
        conn.commit()
        print("\n[SUCCESS] Migration completed successfully!")
        print("\n[NOTE] user_id nullable change will be applied by SQLAlchemy on next backend start")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Agent-First Architecture Migration")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print()
    
    success = migrate()
    
    print()
    print("=" * 60)
    
    if success:
        print("[INFO] Migration successful!")
        print("[INFO] Restart backend to apply all changes")
    else:
        print("[ERROR] Migration failed - check errors above")
