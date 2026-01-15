#!/usr/bin/env python3
"""
Simple test to verify lock screen stays open and accepts input
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Testing Lock Screen - Simple Test")
print("=" * 60)
print()
print("This will launch the lock screen.")
print("The window should stay open until you enter the password.")
print("Password: test123")
print()
print("Press Ctrl+C to cancel, or wait for lock screen...")
print()

try:
    from prey_lock_screen import show_lock_screen
    
    print("Launching lock screen...")
    show_lock_screen(password='test123', message='Test lock screen - enter password manually')
    
    print()
    print("=" * 60)
    print("Lock screen closed!")
    print("=" * 60)
    
except KeyboardInterrupt:
    print("\nTest cancelled")
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

