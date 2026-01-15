#!/usr/bin/env python3
"""
Helper script to update user_email in device agent config.json
Usage: python update_config_email.py your-email@example.com
"""

import json
import sys
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / 'config.json'

def update_email(new_email):
    """Update user_email in config.json"""
    try:
        # Read existing config
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
        else:
            # Create default config if it doesn't exist
            import socket
            import platform
            hostname = socket.gethostname()
            device_id = f"{hostname}-{platform.system().lower()}"
            config = {
                "device_id": device_id,
                "user_email": new_email,
                "report_interval": 300,
                "check_commands_interval": 0.2
            }
            print(f"⚠️  config.json not found. Creating new config with device_id: {device_id}")
        
        # Update email
        old_email = config.get('user_email', 'not set')
        config['user_email'] = new_email
        
        # Save config
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Successfully updated config.json")
        print(f"   Old email: {old_email}")
        print(f"   New email: {new_email}")
        print(f"   Device ID: {config.get('device_id', 'not set')}")
        print()
        print("📝 Next steps:")
        print("   1. Restart the device agent: python agent.py")
        print("   2. Your device will automatically register with your account")
        print("   3. Check the dashboard to see your device")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python update_config_email.py your-email@example.com")
        print()
        print("Example:")
        print("  python update_config_email.py user@example.com")
        sys.exit(1)
    
    new_email = sys.argv[1]
    
    # Basic email validation
    if '@' not in new_email or '.' not in new_email.split('@')[1]:
        print(f"⚠️  Warning: '{new_email}' doesn't look like a valid email address")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            sys.exit(1)
    
    print("📧 Updating device agent configuration...")
    print()
    
    if update_email(new_email):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()

