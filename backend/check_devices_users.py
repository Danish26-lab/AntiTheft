#!/usr/bin/env python3
"""
Check Devices and Users
Lists all devices and users to help with manual linking
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app
from models import db, Device, User

with app.app_context():
    print("=" * 60)
    print("DEVICES")
    print("=" * 60)
    devices = Device.query.all()
    if not devices:
        print("No devices found in database.")
    else:
        for device in devices:
            user_email = None
            if device.user_id:
                user = User.query.get(device.user_id)
                user_email = user.email if user else "Unknown"
            print(f"\nDevice ID: {device.device_id}")
            print(f"  Name: {device.name}")
            print(f"  Type: {device.device_type}")
            print(f"  User ID: {device.user_id}")
            print(f"  User Email: {user_email or 'UNOWNED (not linked)'}")
            print(f"  Fingerprint Hash: {device.fingerprint_hash[:20] + '...' if device.fingerprint_hash else 'None'}")
    
    print("\n" + "=" * 60)
    print("USERS")
    print("=" * 60)
    users = User.query.all()
    if not users:
        print("No users found in database.")
    else:
        for user in users:
            device_count = Device.query.filter_by(user_id=user.id).count()
            print(f"\nEmail: {user.email}")
            print(f"  Name: {user.name}")
            print(f"  ID: {user.id}")
            print(f"  Linked Devices: {device_count}")
