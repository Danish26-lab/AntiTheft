#!/usr/bin/env python3
"""
Register iOS device with the Anti-Theft System
"""

import json
import requests
import platform
import sys
import io
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / 'ios_config.json'
API_BASE_URL = 'http://localhost:5000/api'

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def get_device_info():
    """Get iOS device information"""
    hostname = platform.node() if hasattr(platform, 'node') else "iPhone"
    system = platform.system()
    
    # Try to get iOS version
    ios_version = "Unknown"
    try:
        import subprocess
        result = subprocess.run(
            ['sw_vers', '-productVersion'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            ios_version = result.stdout.strip()
    except:
        pass
    
    # Get device model if available
    device_model = "iPhone"
    try:
        import objc_util  # Pythonista
        device_info = objc_util.ObjCClass('UIDevice').currentDevice()
        device_model = str(device_info.model())
        ios_version = str(device_info.systemVersion())
    except:
        pass
    
    # Create device ID
    device_id = f"{hostname}-ios"
    
    # Get device name
    device_name = f"{hostname} (iOS {ios_version})"
    
    return {
        'device_id': device_id,
        'name': device_name,
        'device_type': 'iphone',
        'hostname': hostname,
        'platform': 'iOS',
        'version': ios_version,
        'model': device_model
    }

def register_device(device_info, user_email='admin@antitheft.com', password='admin123', connection_key=None):
    """Register device with backend"""
    print(f"\n📱 Registering iOS Device...")
    print(f"   Device ID: {device_info['device_id']}")
    print(f"   Name: {device_info['name']}")
    print(f"   iOS Version: {device_info['version']}")
    print()
    
    # First, login to get token
    print("🔐 Logging in...")
    login_response = requests.post(
        f"{API_BASE_URL}/login",
        json={
            'email': user_email,
            'password': password
        },
        timeout=10
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    try:
        login_data = login_response.json()
        token = login_data.get('access_token')
        if not token:
            print("❌ No access token received")
            return False
    except:
        print("❌ Invalid login response")
        return False
    
    print("✅ Login successful")
    print()
    
    # Register device or connect to existing device
    if connection_key:
        print("📝 Connecting to existing device with connection key...")
    else:
        print("📝 Registering device...")
    
    register_data = {
        'device_id': device_info['device_id'],
        'name': device_info['name'],
        'device_type': device_info['device_type']
    }
    
    if connection_key:
        register_data['connection_key'] = connection_key
    
    register_response = requests.post(
        f"{API_BASE_URL}/register_device",
        json=register_data,
        headers={'Authorization': f'Bearer {token}'},
        timeout=10
    )
    
    if register_response.status_code == 200 or register_response.status_code == 201:
        if connection_key:
            print("✅ Device connected successfully!")
        else:
            print("✅ Device registered successfully!")
        print()
        
        # Save config
        config = {
            'device_id': device_info['device_id'],
            'user_email': user_email
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"💾 Configuration saved to: {CONFIG_FILE}")
        print()
        print("🚀 You can now run: python ios_agent.py")
        return True
    else:
        print(f"❌ Registration failed: {register_response.status_code}")
        try:
            error_data = register_response.json()
            print(f"   Error: {error_data.get('error', 'Unknown error')}")
        except:
            print(f"   Response: {register_response.text}")
        return False

def main():
    print("=" * 50)
    print("📱 iOS Device Registration")
    print("=" * 50)
    print()
    
    # Get device info
    device_info = get_device_info()
    
    # Get credentials and connection key (non-interactive mode if running from command line)
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Register iOS device with Anti-Theft System')
    parser.add_argument('--connect-key', type=str, help='Connection key to connect to existing device')
    parser.add_argument('--scan-qr', action='store_true', help='Scan QR code from camera')
    args = parser.parse_args()
    
    # Handle QR code scanning for iOS
    connection_key = args.connect_key
    if args.scan_qr:
        try:
            from ios_qr_scanner import scan_qr_with_camera
            print("📷 Scanning QR code with camera...")
            connection_key = scan_qr_with_camera()
            if not connection_key:
                print("❌ Could not scan QR code. Exiting.")
                return
        except ImportError as e:
            print("⚠️ iOS QR scanner not available: {e}")
            print("   Make sure you're running in Pythonista")
            print("   Or use --connect-key manually")
            return
    
    try:
        print("Enter your credentials (or press Enter for defaults):")
        user_email = input(f"Email [admin@antitheft.com]: ").strip() or 'admin@antitheft.com'
        password = input(f"Password [admin123]: ").strip() or 'admin123'
    except (EOFError, KeyboardInterrupt):
        # Non-interactive mode - use defaults
        user_email = 'admin@antitheft.com'
        password = 'admin123'
        print("\nUsing default credentials (non-interactive mode)")
    print()
    
    # Register
    if register_device(device_info, user_email, password, connection_key=connection_key):
        print("=" * 50)
        print("✅ Registration Complete!")
        print("=" * 50)
        print()
        print("Next steps:")
        print("1. Run: python ios_agent.py")
        print("2. Your device will appear in the web dashboard")
        print()
    else:
        print("=" * 50)
        print("❌ Registration Failed")
        print("=" * 50)
        print()
        print("Please check:")
        print("- Backend server is running (http://localhost:5000)")
        print("- Credentials are correct")
        print("- Network connection is active")
        print()

if __name__ == '__main__':
    main()

