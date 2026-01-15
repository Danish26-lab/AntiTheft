#!/usr/bin/env python3
"""
Get real device location using IP geolocation
"""

import requests
import json

def get_location_from_ip():
    """Get location using IP geolocation service"""
    try:
        # Using ip-api.com (free, no API key required)
        response = requests.get('http://ip-api.com/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'lat': data.get('lat'),
                    'lng': data.get('lon'),
                    'city': data.get('city'),
                    'country': data.get('country'),
                    'ip': data.get('query')
                }
    except Exception as e:
        print(f"Error getting location from IP: {e}")
    
    return None

if __name__ == '__main__':
    location = get_location_from_ip()
    if location:
        print(json.dumps(location, indent=2))
    else:
        print("Failed to get location")

