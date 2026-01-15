#!/usr/bin/env python3
"""
Test if device API returns the device
"""

import requests
import json
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API_BASE_URL = 'http://localhost:5000/api'

print("Testing Device API...")
print("=" * 60)

# Try to login
try:
    print("\n1. Testing login...")
    login_response = requests.post(
        f'{API_BASE_URL}/login',
        json={
            'email': 'admin@antitheft.com',
            'password': 'admin123'
        },
        timeout=5
    )
    
    if login_response.status_code == 200:
        token = login_response.json().get('access_token')
        print("[OK] Login successful")
        
        # Get devices
        print("\n2. Fetching devices...")
        devices_response = requests.get(
            f'{API_BASE_URL}/get_devices',
            headers={'Authorization': f'Bearer {token}'},
            timeout=5
        )
        
        if devices_response.status_code == 200:
            devices = devices_response.json().get('devices', [])
            print(f"[OK] Found {len(devices)} device(s):")
            for device in devices:
                print(f"   - {device.get('name')} ({device.get('device_id')})")
        else:
            print(f"[ERROR] Failed to get devices: {devices_response.status_code}")
            print(f"   Response: {devices_response.text}")
    else:
        print(f"[ERROR] Login failed: {login_response.status_code}")
        print(f"   Response: {login_response.text}")
        
except requests.exceptions.ConnectionError:
    print("[ERROR] Cannot connect to backend server!")
    print("   Make sure backend is running: python backend/app.py")
except Exception as e:
    print(f"[ERROR] {e}")

