#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test script to verify wipe setup and approve a test folder
"""

import json
import os
import sys
import io
from pathlib import Path
import requests

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

CONFIG_FILE = Path(__file__).parent / 'config.json'
APPROVED_FOLDERS_FILE = Path(__file__).parent / 'approved_folders.json'
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000/api')

def main():
    print("=" * 60)
    print("Remote Data Wipe Setup Test")
    print("=" * 60)
    
    # Check config
    if not CONFIG_FILE.exists():
        print("[ERROR] config.json not found!")
        print("   Please ensure device_agent/config.json exists")
        return False
    
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        device_id = config.get('device_id')
        print(f"[OK] Device ID: {device_id}")
    
    # Check if folders already approved
    if APPROVED_FOLDERS_FILE.exists():
        with open(APPROVED_FOLDERS_FILE, 'r') as f:
            data = json.load(f)
            folders = data.get('folders', [])
            print(f"[OK] Found {len(folders)} approved folder(s)")
            for folder in folders:
                print(f"   - {folder}")
    else:
        print("[WARNING] No approved folders found")
        print("   Run: python select_approved_folders.py")
        print("   Or use this script to approve a test folder")
        
        # Ask if user wants to approve a test folder
        response = input("\nApprove a test folder now? (y/n): ").strip().lower()
        if response == 'y':
            test_folder = input("Enter folder path to approve (e.g., C:\\Users\\YourName\\Documents\\Test): ").strip()
            if test_folder and os.path.exists(test_folder) and os.path.isdir(test_folder):
                folders = [test_folder]
                with open(APPROVED_FOLDERS_FILE, 'w') as f:
                    json.dump({'folders': folders}, f, indent=2)
                print(f"[OK] Saved folder: {test_folder}")
            else:
                print("[ERROR] Invalid folder path")
                return False
    
    # Try to sync to server
    if APPROVED_FOLDERS_FILE.exists():
        with open(APPROVED_FOLDERS_FILE, 'r') as f:
            data = json.load(f)
            folders = data.get('folders', [])
        
        if folders:
            print(f"\n[SYNC] Syncing {len(folders)} folder(s) to server...")
            try:
                response = requests.post(
                    f"{API_BASE_URL}/v1/approved_folders/{device_id}",
                    json={'folders': folders},
                    timeout=10
                )
                if response.status_code == 200:
                    print("[OK] Successfully synced to server!")
                    return True
                else:
                    print(f"[ERROR] Server error: {response.status_code}")
                    print(f"   {response.text}")
                    return False
            except requests.exceptions.ConnectionError:
                print("[ERROR] Cannot connect to server")
                print("   Make sure backend is running on http://localhost:5000")
                return False
            except Exception as e:
                print(f"[ERROR] Error: {e}")
                return False
    
    return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n[OK] Setup complete! You can now use Custom Wipe from the dashboard.")
    else:
        print("\n[WARNING] Setup incomplete. Please check the errors above.")
    input("\nPress Enter to exit...")

