#!/usr/bin/env python3
"""
Migration script to add WiFi geofence columns to existing database
This preserves all existing device data
"""

import sqlite3
import os
import sys
import io
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def migrate_database():
    """Add WiFi geofence columns to devices table"""
    
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
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(devices)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add geofence_type column if it doesn't exist
        if 'geofence_type' not in columns:
            print("Adding geofence_type column...")
            cursor.execute("ALTER TABLE devices ADD COLUMN geofence_type VARCHAR(20) DEFAULT 'gps'")
            print("✓ Added geofence_type column")
        else:
            print("✓ geofence_type column already exists")
        
        # Add geofence_wifi_ssid column if it doesn't exist
        if 'geofence_wifi_ssid' not in columns:
            print("Adding geofence_wifi_ssid column...")
            cursor.execute("ALTER TABLE devices ADD COLUMN geofence_wifi_ssid VARCHAR(100)")
            print("✓ Added geofence_wifi_ssid column")
        else:
            print("✓ geofence_wifi_ssid column already exists")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Database migration completed successfully!")
        print("Your existing devices are preserved and ready to use.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == '__main__':
    migrate_database()

