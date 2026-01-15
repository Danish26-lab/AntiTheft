#!/usr/bin/env python3
"""
Manually register device with hardware information
Run this to update the existing device with hardware info
"""

import json
import requests
from pathlib import Path
from hardware_detection import detect_hardware

CONFIG_FILE = Path(__file__).parent / 'config.json'
API_BASE_URL = 'http://localhost:5000/api'

def main():
    # Load config
    if not CONFIG_FILE.exists():
        print("[ERROR] config.json not found!")
        return
    
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    device_id = config.get('device_id')
    user_email = config.get('user_email', 'admin@antitheft.com')
    
    if not device_id:
        print("[ERROR] device_id not found in config.json!")
        return
    
    print(f"[INFO] Detecting hardware for device: {device_id}...")
    
    # Detect hardware
    try:
        hardware_info = detect_hardware()
        print(f"[OK] Hardware detected!")
        print(f"   Vendor: {hardware_info.get('system_info', {}).get('vendor', 'Unknown')}")
        print(f"   Model: {hardware_info.get('system_info', {}).get('model', 'Unknown')}")
        print(f"   CPU: {hardware_info.get('cpu_info', {}).get('model', 'Unknown')}")
        print()
    except Exception as e:
        print(f"[ERROR] Hardware detection failed: {e}")
        return
    
    # Build payload
    payload = {
        "device_id": device_id,  # Use device_id from config, not from hardware detection
        "user_email": user_email,
        "os_info": hardware_info.get("os_info", {}),
        "system_info": hardware_info.get("system_info", {}),
        "bios_info": hardware_info.get("bios_info", {}),
        "motherboard_info": hardware_info.get("motherboard_info", {}),
        "cpu_info": hardware_info.get("cpu_info", {}),
        "ram_info": hardware_info.get("ram_info", {}),
        "network_info": hardware_info.get("network_info", {})
    }
    
    print(f"[INFO] Registering device with hardware info...")
    print(f"   Endpoint: {API_BASE_URL}/devices/agent/register")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/devices/agent/register",
            json=payload,
            timeout=15
        )
        
        if response.status_code in (200, 201):
            print(f"[SUCCESS] Device registered successfully!")
            print(f"   Message: {response.json().get('message', 'OK')}")
            print()
            print("[INFO] Refresh the dashboard to see hardware information!")
        else:
            print(f"[ERROR] Registration failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        print("   Make sure the backend server is running!")

if __name__ == "__main__":
    main()