#!/usr/bin/env python3
"""
Script to register missing browser devices via the API
This works while the server is running
"""

import requests
import sys

API_BASE = "http://localhost:5000/api"

def get_admin_token():
    """Login as admin to get access token"""
    login_data = {
        "email": "admin@antitheft.com",
        "password": "admin123"  # Default admin password
    }
    
    response = requests.post(f"{API_BASE}/login", json=login_data)
    
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print(f"❌ Failed to login as admin: {response.json().get('error', 'Unknown error')}")
        print("   Make sure the backend server is running and admin credentials are correct")
        return None

def register_missing_devices():
    """Register browser devices for users without devices"""
    print("🔐 Logging in as admin...")
    token = get_admin_token()
    
    if not token:
        sys.exit(1)
    
    print("✅ Admin login successful\n")
    print("🔍 Registering missing browser devices...\n")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_BASE}/admin/register_missing_devices", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}\n")
        
        if data.get('registered_devices'):
            print("📱 Registered Devices:")
            for device in data['registered_devices']:
                print(f"   • {device['user_email']}")
                print(f"     Device ID: {device['device_id']}")
                print(f"     Device Name: {device['device_name']}\n")
        
        if data.get('skipped_users'):
            print("⚠️  Skipped Users:")
            for skipped in data['skipped_users']:
                print(f"   • {skipped['email']}: {skipped['reason']}\n")
        
        print(f"\n📊 Total registered: {data['total_registered']}")
        print("\n✨ Done! You can now view the database to see the new devices.")
    else:
        error = response.json().get('error', 'Unknown error')
        print(f"❌ Failed to register devices: {error}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        register_missing_devices()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server.")
        print("   Make sure the backend server is running on http://localhost:5000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

