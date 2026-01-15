#!/usr/bin/env python3
"""
Test script for lock screen
Run this to test the lock screen functionality
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lock_screen import show_lock_screen

if __name__ == '__main__':
    print("Testing lock screen...")
    print("Password: test123")
    print("Message: This is a test lock screen")
    print("\nPress Ctrl+C to cancel, or enter the password to unlock")
    
    try:
        show_lock_screen(password='test123', message='This is a test lock screen')
        print("\n✅ Lock screen closed successfully!")
    except KeyboardInterrupt:
        print("\n❌ Test cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")

