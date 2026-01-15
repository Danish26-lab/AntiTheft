#!/usr/bin/env python3
"""
Test script to verify auto-setup is working
This simulates what the agent does when checking for config updates
"""

import requests
import json
import sys
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / 'config.json'
API_BASE_URL = 'http://localhost:5000/api'

def test_auto_setup():
    """Test the auto-setup endpoint"""
    print("🧪 Testing Auto-Setup Functionality")
    print("=" * 50)
    
    # Load current config
    if not CONFIG_FILE.exists():
        print("❌ config.json not found!")
        return False
    
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    device_id = config.get('device_id')
    current_email = config.get('user_email')
    
    print(f"📱 Device ID: {device_id}")
    print(f"📧 Current Email: {current_email}")
    print()
    
    # Test the check_config_update endpoint
    print("🔍 Checking for config updates...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/check_config_update/{device_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response received: {json.dumps(data, indent=2)}")
            
            if data.get('has_update'):
                new_email = data.get('user_email')
                is_suggested = data.get('suggested', False)
                
                print()
                print("🔄 CONFIG UPDATE AVAILABLE!")
                print(f"   Current email: {current_email}")
                print(f"   New email: {new_email}")
                print(f"   Suggested: {is_suggested}")
                print()
                
                if new_email != current_email:
                    print("💡 The agent would automatically update the config to:")
                    print(f"   {new_email}")
                    return True
                else:
                    print("ℹ️ Email matches, no update needed")
            else:
                print("ℹ️ No config updates available")
                print("   (This is normal if no recent user registrations)")
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server!")
        print("   Make sure the backend is running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = test_auto_setup()
    sys.exit(0 if success else 1)

