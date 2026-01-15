#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick script to approve a folder for remote wipe without GUI
Usage: python quick_approve_folder.py "C:\path\to\folder"
"""

import json
import os
import sys
from pathlib import Path
import requests

CONFIG_FILE = Path(__file__).parent / 'config.json'
APPROVED_FOLDERS_FILE = Path(__file__).parent / 'approved_folders.json'
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000/api')

# System-critical paths that must never be approved
BLOCKED_PATHS = [
    'C:\\Windows',
    'C:\\Program Files',
    'C:\\ProgramData',
    'C:\\Program Files (x86)',
    '/System',
    '/Library',
    '/usr',
    '/bin',
    '/sbin',
    '/etc'
]

def is_path_blocked(folder_path):
    """Check if a folder path is in the blocked list"""
    folder_path_normalized = folder_path.replace('/', '\\').upper()
    for blocked in BLOCKED_PATHS:
        blocked_normalized = blocked.replace('/', '\\').upper()
        if folder_path_normalized.startswith(blocked_normalized):
            return True
    return False

def main():
    # Get folder from command line or use a default test folder
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        # Default: use Documents folder as test
        folder_path = os.path.join(os.path.expanduser('~'), 'Documents', 'TestWipe')
        print(f"No folder specified. Using default test folder: {folder_path}")
        print("You can specify a folder: python quick_approve_folder.py \"C:\\path\\to\\folder\"")
    
    # Normalize path
    folder_path = os.path.normpath(folder_path)
    
    # Validate folder
    if not os.path.exists(folder_path):
        print(f"ERROR: Folder does not exist: {folder_path}")
        print("Creating test folder...")
        try:
            os.makedirs(folder_path, exist_ok=True)
            print(f"Created test folder: {folder_path}")
        except Exception as e:
            print(f"ERROR: Could not create folder: {e}")
            return False
    
    if not os.path.isdir(folder_path):
        print(f"ERROR: Path is not a directory: {folder_path}")
        return False
    
    # Check if blocked
    if is_path_blocked(folder_path):
        print(f"ERROR: This folder is a system-critical path and cannot be approved: {folder_path}")
        return False
    
    # Load existing approved folders
    approved_folders = []
    if APPROVED_FOLDERS_FILE.exists():
        try:
            with open(APPROVED_FOLDERS_FILE, 'r') as f:
                data = json.load(f)
                approved_folders = data.get('folders', [])
        except:
            pass
    
    # Add folder if not already approved
    if folder_path not in approved_folders:
        approved_folders.append(folder_path)
        print(f"Added folder to approved list: {folder_path}")
    else:
        print(f"Folder already approved: {folder_path}")
    
    # Save to file
    try:
        with open(APPROVED_FOLDERS_FILE, 'w') as f:
            json.dump({'folders': approved_folders}, f, indent=2)
        print(f"Saved {len(approved_folders)} approved folder(s) to {APPROVED_FOLDERS_FILE}")
    except Exception as e:
        print(f"ERROR: Could not save approved folders: {e}")
        return False
    
    # Sync to server
    if not CONFIG_FILE.exists():
        print("WARNING: config.json not found. Cannot sync to server.")
        return True
    
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        device_id = config.get('device_id')
    
    print(f"Syncing to server (device_id: {device_id})...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/v1/approved_folders/{device_id}",
            json={'folders': approved_folders},
            timeout=10
        )
        if response.status_code == 200:
            print("SUCCESS: Folders synced to server!")
            print(f"You can now use Custom Wipe from the dashboard.")
            return True
        else:
            print(f"WARNING: Server returned error {response.status_code}")
            print(f"Response: {response.text}")
            print("Folders saved locally but not synced to server.")
            print("Make sure backend is running and try again.")
            return True  # Still return True since local save worked
    except requests.exceptions.ConnectionError:
        print("WARNING: Cannot connect to server (backend may not be running)")
        print("Folders saved locally. Sync will happen when backend is available.")
        return True
    except Exception as e:
        print(f"WARNING: Error syncing to server: {e}")
        print("Folders saved locally. Sync will happen when backend is available.")
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

