#!/usr/bin/env python3
"""
Test script to update device location manually
"""

import requests
import json

API_BASE_URL = 'http://localhost:5000/api'
DEVICE_ID = 'Danish-windows'

def update_device_location():
    """Manually update device location for testing"""
    
    # CORRECT device location (user confirmed)
    location = {
        "lat": 2.1624511,  # Actual device location
        "lng": 102.4231699
    }
    
    payload = {
        "device_id": DEVICE_ID,
        "user": "admin@antitheft.com",
        "location": location,
        "status": "active"
    }
    
    try:
        print(f"Updating location for device: {DEVICE_ID}")
        print(f"Location: {location['lat']}, {location['lng']}")
        
        response = requests.post(
            f"{API_BASE_URL}/update_location",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("[SUCCESS] Location updated successfully!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"[ERROR] Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to backend. Make sure backend is running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == '__main__':
    update_device_location()

