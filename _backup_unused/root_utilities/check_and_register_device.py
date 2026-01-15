#!/usr/bin/env python3
"""
Check if device is registered and help register it if missing
"""

import sqlite3
import json
import requests
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Paths
database_dir = Path(__file__).parent / 'database'
db_path = database_dir / 'antitheft.db'
config_file = Path(__file__).parent / 'device_agent' / 'config.json'
API_BASE_URL = 'http://localhost:5000/api'

def check_device_in_db():
    """Check if device exists in database"""
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get device_id from config
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                device_id = config.get('device_id')
                
                if device_id:
                    cursor.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,))
                    device = cursor.fetchone()
                    
                    if device:
                        # Get column names
                        cursor.execute("PRAGMA table_info(devices);")
                        columns_info = cursor.fetchall()
                        columns = [col[1] for col in columns_info]
                        
                        device_dict = dict(zip(columns, device))
                        print(f"✅ Device found in database: {device_id}")
                        print(f"   Name: {device_dict.get('name', 'N/A')}")
                        print(f"   Status: {device_dict.get('status', 'N/A')}")
                        print(f"   User ID: {device_dict.get('user_id', 'N/A')}")
                        conn.close()
                        return device_dict
                    else:
                        print(f"❌ Device '{device_id}' NOT found in database")
                        conn.close()
                        return None
        else:
            print("❌ Config file not found. Please register device first.")
            conn.close()
            return None
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return None

def register_device_now():
    """Register the device with backend"""
    if not config_file.exists():
        print("❌ Config file not found. Cannot register device.")
        return False
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    device_id = config.get('device_id')
    user_email = config.get('user_email', 'admin@antitheft.com')
    
    if not device_id:
        print("❌ Device ID not found in config")
        return False
    
    print(f"\n📝 Registering device: {device_id}")
    print(f"   User: {user_email}")
    
    # Login first
    try:
        login_response = requests.post(
            f'{API_BASE_URL}/login',
            json={
                'email': user_email,
                'password': 'admin123'
            },
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
        
        token = login_response.json().get('access_token')
        if not token:
            print("❌ No access token received")
            return False
        
        print("✅ Login successful")
        
        # Register device
        import platform
        import socket
        hostname = socket.gethostname()
        system = platform.system()
        release = platform.release()
        
        device_name = f"{hostname} ({system} {release})"
        device_type = 'laptop' if 'Laptop' in platform.platform() else 'desktop'
        
        register_response = requests.post(
            f'{API_BASE_URL}/register_device',
            json={
                'device_id': device_id,
                'name': device_name,
                'device_type': device_type
            },
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        
        if register_response.status_code in [200, 201]:
            print(f"✅ Device registered successfully!")
            print(f"   Device ID: {device_id}")
            print(f"   Name: {device_name}")
            return True
        elif register_response.status_code == 400:
            error_msg = register_response.json().get('error', '')
            if 'already registered' in error_msg.lower():
                print(f"⚠️ Device already registered: {device_id}")
                print("   Device should appear in dashboard now")
                return True
            else:
                print(f"❌ Registration failed: {error_msg}")
                return False
        else:
            print(f"❌ Registration failed: {register_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server.")
        print("   Make sure backend is running: python backend/app.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Device Registration Checker")
    print("=" * 60)
    print()
    
    # Check if device exists in database
    device = check_device_in_db()
    
    if device:
        print("\n✅ Your device is registered!")
        print("\nIf it's not showing in the dashboard:")
        print("1. Make sure backend is running: python backend/app.py")
        print("2. Make sure frontend is running: cd frontend && npm run dev")
        print("3. Refresh the devices page")
        print("4. Check if you're logged in with the correct account")
    else:
        print("\n❌ Device is NOT registered in database")
        print("\nWould you like to register it now?")
        response = input("Register device? (y/n): ").strip().lower()
        
        if response == 'y':
            if register_device_now():
                print("\n✅ Registration complete!")
                print("   Your device should now appear in the dashboard")
                print("   Start the agent: python device_agent/agent.py")
            else:
                print("\n❌ Registration failed. Please check the errors above.")
        else:
            print("\nTo register manually:")
            print("1. Go to http://localhost:3000/devices")
            print("2. Click '+ NEW DEVICE'")
            print("3. Or run: python device_agent/register_device.py")

if __name__ == '__main__':
    main()

