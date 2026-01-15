#!/usr/bin/env python3
"""
Manual Device Linking Script
Links an existing device to a user account
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app
from models import db, Device, User

def link_device_to_user(device_id, user_email):
    """Link a device to a user account"""
    with app.app_context():
        device = Device.query.filter_by(device_id=device_id).first()
        if not device:
            print(f"[ERROR] Device '{device_id}' not found!")
            return False
        
        user = User.query.filter_by(email=user_email).first()
        if not user:
            print(f"[ERROR] User '{user_email}' not found!")
            return False
        
        if device.user_id is not None:
            if device.user_id == user.id:
                print(f"[INFO] Device '{device_id}' is already linked to user '{user_email}'")
                return True
            else:
                current_user = User.query.get(device.user_id)
                print(f"[ERROR] Device '{device_id}' is already linked to another user: '{current_user.email}'")
                return False
        
        # Link device to user
        device.user_id = user.id
        db.session.commit()
        
        print(f"[SUCCESS] Device '{device_id}' linked to user '{user_email}'")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python link_device_manual.py <device_id> <user_email>")
        print("\nExample:")
        print("  python link_device_manual.py Danish-windows admin@antitheft.com")
        sys.exit(1)
    
    device_id = sys.argv[1]
    user_email = sys.argv[2]
    
    print(f"Linking device '{device_id}' to user '{user_email}'...")
    success = link_device_to_user(device_id, user_email)
    
    if success:
        print("\n[SUCCESS] Device linked! Refresh your dashboard to see it.")
    else:
        print("\n[ERROR] Failed to link device. Check the errors above.")
        sys.exit(1)
