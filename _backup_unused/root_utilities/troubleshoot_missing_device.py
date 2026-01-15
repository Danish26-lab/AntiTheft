#!/usr/bin/env python3
"""
Troubleshoot why device is not showing in dashboard
"""

import sqlite3
import json
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

database_dir = Path(__file__).parent / 'database'
db_path = database_dir / 'antitheft.db'
config_file = Path(__file__).parent / 'device_agent' / 'config.json'

print("=" * 60)
print("Device Troubleshooting")
print("=" * 60)
print()

# Check database
if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get device from config
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
            device_id = config.get('device_id')
            
            if device_id:
                cursor.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,))
                device = cursor.fetchone()
                
                if device:
                    cursor.execute("PRAGMA table_info(devices);")
                    columns_info = cursor.fetchall()
                    columns = [col[1] for col in columns_info]
                    device_dict = dict(zip(columns, device))
                    
                    print(f"[OK] Device found in database:")
                    print(f"   Device ID: {device_dict.get('device_id')}")
                    print(f"   Name: {device_dict.get('name')}")
                    print(f"   User ID: {device_dict.get('user_id')}")
                    print(f"   Status: {device_dict.get('status')}")
                    print()
                    
                    # Check user
                    cursor.execute("SELECT id, email FROM users WHERE id = ?", (device_dict.get('user_id'),))
                    user = cursor.fetchone()
                    if user:
                        print(f"[OK] User found:")
                        print(f"   User ID: {user[0]}")
                        print(f"   Email: {user[1]}")
                        print()
                        print("SOLUTION:")
                        print("1. Make sure you're logged in with email: " + user[1])
                        print("2. Refresh the devices page (F5 or Ctrl+R)")
                        print("3. Check if any filters are applied in the dashboard")
                        print("4. Make sure backend is running: python backend/app.py")
                        print("5. Make sure frontend is running: cd frontend && npm run dev")
                    else:
                        print("[ERROR] User not found for this device!")
                else:
                    print(f"[ERROR] Device '{device_id}' not found in database!")
                    print("   Run: python device_agent/register_device.py")
            else:
                print("[ERROR] Device ID not found in config file")
    else:
        print("[ERROR] Config file not found")
        print("   Run: python device_agent/register_device.py")
    
    conn.close()
else:
    print(f"[ERROR] Database not found at: {db_path}")

