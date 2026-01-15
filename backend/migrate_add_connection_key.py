#!/usr/bin/env python3
"""
Migration script to add connection_key column to devices table
"""

import sqlite3
import sys
import io
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def migrate_database():
    """Add connection_key column to devices table"""
    
    # Get database path
    backend_dir = Path(__file__).parent
    project_dir = backend_dir.parent
    database_dir = project_dir / 'database'
    db_path = database_dir / 'antitheft.db'
    
    if not db_path.exists():
        print("Database file not found. It will be created automatically when you restart the backend.")
        return
    
    print(f"Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(devices)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add connection_key column if it doesn't exist
        if 'connection_key' not in columns:
            print("Adding connection_key column...")
            cursor.execute("ALTER TABLE devices ADD COLUMN connection_key VARCHAR(64)")
            # Create index for faster lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_devices_connection_key ON devices(connection_key)")
            print("✓ Added connection_key column and index")
        else:
            print("✓ connection_key column already exists")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == '__main__':
    migrate_database()

