#!/usr/bin/env python3
"""
Test script to verify lock command works
This simulates what happens when the backend sends a lock command
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent import DeviceAgent
import time

def test_lock():
    """Test the lock command directly"""
    print("=" * 60)
    print("Testing Lock Command")
    print("=" * 60)
    
    # Create agent instance
    agent = DeviceAgent()
    
    if not agent.device_id:
        print("❌ ERROR: Device not registered!")
        print("   Please run: python register_device.py")
        return False
    
    print(f"✅ Device ID: {agent.device_id}")
    print(f"✅ User: {agent.user_email}")
    print()
    
    # Test lock command directly
    print("🔒 Testing lock command...")
    print("   Password: test123")
    print("   Message: This is a test lock")
    print()
    
    try:
        agent.execute_lock(password='test123', message='This is a test lock')
        print()
        print("✅ Lock command executed!")
        print("   The lock screen should appear on your screen.")
        print("   Enter password 'test123' to unlock.")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_lock()
    sys.exit(0 if success else 1)

