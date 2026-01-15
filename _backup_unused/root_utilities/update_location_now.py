#!/usr/bin/env python3
"""
Quick script to update device location immediately
"""

import requests
import json

API_BASE_URL = 'http://localhost:5000/api'
DEVICE_ID = 'Danish-windows'

# Get location from IP
def get_location_from_ip():
    try:
        response = requests.get('http://ip-api.com/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'lat': data.get('lat'),
                    'lng': data.get('lon')
                }
    except:
        pass
    
    # No fallback - return None to avoid wrong location
    return None

def update_location():
    location = get_location_from_ip()
    
    payload = {
        "device_id": DEVICE_ID,
        "user": "admin@antitheft.com",
        "location": location,
        "status": "active"
    }
    
    try:
        print(f"[INFO] Updating location for {DEVICE_ID}...")
        print(f"   Location: {location['lat']:.6f}, {location['lng']:.6f}")
        
        response = requests.post(
            f"{API_BASE_URL}/update_location",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("[SUCCESS] Location updated successfully!")
            print("   Refresh your browser to see the location on the map.")
            return True
        else:
            print(f"[ERROR] {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == '__main__':
    update_location()

