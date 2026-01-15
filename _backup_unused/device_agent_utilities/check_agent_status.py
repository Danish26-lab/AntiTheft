#!/usr/bin/env python3
"""
Check if agent is running and can detect lock commands
"""

import requests
import json
from pathlib import Path

API_BASE_URL = 'http://localhost:5000/api'
CONFIG_FILE = Path(__file__).parent / 'config.json'

def check_agent_status():
    """Check agent status and test lock command detection"""
    print("=" * 60)
    print("Agent Status Checker")
    print("=" * 60)
    
    # Load device ID from config
    if not CONFIG_FILE.exists():
        print("❌ ERROR: config.json not found!")
        print("   Please run: python register_device.py")
        return
    
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        device_id = config.get('device_id')
    
    if not device_id:
        print("❌ ERROR: device_id not found in config!")
        return
    
    print(f"✅ Device ID: {device_id}")
    print()
    
    # Check backend connection
    print("1. Checking backend connection...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/get_device_status/{device_id}",
            timeout=5
        )
        if response.status_code == 200:
            device_data = response.json()
            status = device_data.get('status', 'unknown')
            print(f"   ✅ Backend connected")
            print(f"   📊 Current device status: {status}")
        else:
            print(f"   ❌ Backend returned status: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("   ❌ ERROR: Cannot connect to backend!")
        print("   Make sure backend is running: python backend/app.py")
        return
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return
    
    print()
    
    # Check activity logs
    print("2. Checking recent activity logs...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/get_activity_logs/{device_id}",
            timeout=5
        )
        if response.status_code == 200:
            logs = response.json().get('logs', [])
            lock_logs = [log for log in logs if log.get('action') == 'lock']
            if lock_logs:
                print(f"   ✅ Found {len(lock_logs)} lock command(s) in logs")
                latest = lock_logs[0]
                print(f"   📋 Latest lock command: {latest.get('description', 'N/A')}")
            else:
                print("   ⚠️  No lock commands found in logs")
        else:
            print(f"   ⚠️  Could not get activity logs: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Error getting logs: {e}")
    
    print()
    
    # Instructions
    print("=" * 60)
    print("Instructions:")
    print("=" * 60)
    print("1. Make sure the agent is running:")
    print("   cd device_agent")
    print("   python agent.py")
    print()
    print("2. The agent checks for commands every 10 seconds")
    print()
    print("3. When you click 'Confirm' in the dashboard:")
    print("   - Backend sets device status to 'locked'")
    print("   - Agent should detect this within 10 seconds")
    print("   - Agent launches lock screen")
    print()
    print("4. Check agent console/logs for:")
    print("   - 'Status check: Current=active, Server=locked'")
    print("   - 'COMMAND DETECTED: LOCK'")
    print("   - 'Executing LOCK command'")
    print("   - 'Lock screen process started'")

if __name__ == '__main__':
    check_agent_status()

