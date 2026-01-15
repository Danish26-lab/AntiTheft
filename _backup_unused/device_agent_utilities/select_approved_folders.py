#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Folder Selection UI for Remote Data Wipe
Allows users to select folders that can be remotely wiped.
Only approved folders are eligible for remote wipe operations.
"""

import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import requests
import platform

# Configuration
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

def load_config():
    """Load device configuration"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
    return {}

def load_approved_folders():
    """Load previously approved folders"""
    try:
        if APPROVED_FOLDERS_FILE.exists():
            with open(APPROVED_FOLDERS_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {'folders': []}

def save_approved_folders(folders):
    """Save approved folders locally"""
    try:
        with open(APPROVED_FOLDERS_FILE, 'w') as f:
            json.dump({'folders': folders}, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving folders: {e}")
        return False

def sync_to_server(device_id, folders):
    """Sync approved folders to backend server"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/v1/approved_folders/{device_id}",
            json={'folders': folders},
            timeout=10
        )
        if response.status_code == 200:
            return True, "Folders synced to server successfully"
        else:
            return False, f"Server error: {response.json().get('error', 'Unknown error')}"
    except requests.exceptions.RequestException as e:
        return False, f"Network error: {str(e)}"

class FolderSelectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Remote Data Wipe - Folder Selection")
        self.root.geometry("700x600")
        
        self.config = load_config()
        self.device_id = self.config.get('device_id')
        if not self.device_id:
            messagebox.showerror("Error", "Device ID not found in config.json")
            sys.exit(1)
        
        self.approved_folders = load_approved_folders().get('folders', [])
        
        self.setup_ui()
        self.refresh_folder_list()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Header
        header = tk.Label(
            self.root,
            text="Select Folders for Remote Data Wipe",
            font=('Arial', 16, 'bold'),
            pady=10
        )
        header.pack()
        
        # Info text
        info_text = tk.Label(
            self.root,
            text="Only selected folders can be remotely wiped. System folders are protected.",
            font=('Arial', 10),
            fg='gray',
            pady=5
        )
        info_text.pack()
        
        # Folder list frame
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox
        self.folder_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('Courier', 10)
        )
        self.folder_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.folder_listbox.yview)
        
        # Buttons frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        # Add folder button
        add_btn = tk.Button(
            button_frame,
            text="➕ Add Folder",
            command=self.add_folder,
            width=15,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # Remove folder button
        remove_btn = tk.Button(
            button_frame,
            text="➖ Remove Selected",
            command=self.remove_folder,
            width=15,
            bg='#f44336',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        remove_btn.pack(side=tk.LEFT, padx=5)
        
        # Save button
        save_btn = tk.Button(
            button_frame,
            text="💾 Save & Sync",
            command=self.save_and_sync,
            width=15,
            bg='#2196F3',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = tk.Label(
            self.root,
            text="",
            font=('Arial', 9),
            fg='green'
        )
        self.status_label.pack(pady=5)
    
    def add_folder(self):
        """Add a folder to the approved list"""
        folder = filedialog.askdirectory(title="Select Folder to Approve for Remote Wipe")
        if not folder:
            return
        
        folder = os.path.normpath(folder)
        
        # Check if blocked
        if is_path_blocked(folder):
            messagebox.showerror(
                "Blocked Path",
                f"This folder is a system-critical path and cannot be approved:\n{folder}\n\nSystem folders are protected for your safety."
            )
            return
        
        # Check if already added
        if folder in self.approved_folders:
            messagebox.showinfo("Already Added", "This folder is already in the approved list.")
            return
        
        # Confirm addition
        if messagebox.askyesno(
            "Confirm Folder Addition",
            f"Add this folder to the approved list?\n\n{folder}\n\nThis folder can be remotely wiped if your device is stolen."
        ):
            self.approved_folders.append(folder)
            self.refresh_folder_list()
            self.status_label.config(text=f"Added: {folder}", fg='green')
    
    def remove_folder(self):
        """Remove selected folder from approved list"""
        selection = self.folder_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a folder to remove.")
            return
        
        index = selection[0]
        folder = self.approved_folders[index]
        
        if messagebox.askyesno("Confirm Removal", f"Remove this folder from the approved list?\n\n{folder}"):
            self.approved_folders.pop(index)
            self.refresh_folder_list()
            self.status_label.config(text=f"Removed: {folder}", fg='orange')
    
    def refresh_folder_list(self):
        """Refresh the folder list display"""
        self.folder_listbox.delete(0, tk.END)
        for folder in self.approved_folders:
            self.folder_listbox.insert(tk.END, folder)
        
        if not self.approved_folders:
            self.status_label.config(text="No approved folders. Click 'Add Folder' to get started.", fg='gray')
        else:
            self.status_label.config(text=f"{len(self.approved_folders)} folder(s) approved", fg='blue')
    
    def save_and_sync(self):
        """Save folders locally and sync to server"""
        if not self.approved_folders:
            if not messagebox.askyesno(
                "No Folders",
                "No folders are approved. This means remote wipe will not be available.\n\nContinue anyway?"
            ):
                return
        
        # Save locally
        if save_approved_folders(self.approved_folders):
            self.status_label.config(text="Saving locally...", fg='blue')
            self.root.update()
            
            # Sync to server
            success, message = sync_to_server(self.device_id, self.approved_folders)
            
            if success:
                self.status_label.config(text="✅ Saved and synced successfully!", fg='green')
                messagebox.showinfo("Success", f"Approved folders saved and synced to server.\n\n{len(self.approved_folders)} folder(s) approved.")
            else:
                self.status_label.config(text=f"⚠️ Local save OK, but server sync failed: {message}", fg='orange')
                messagebox.showwarning(
                    "Partial Success",
                    f"Folders saved locally, but server sync failed:\n\n{message}\n\nYou can try syncing again later."
                )
        else:
            self.status_label.config(text="❌ Failed to save locally", fg='red')
            messagebox.showerror("Error", "Failed to save folders locally.")

def main():
    """Main entry point"""
    root = tk.Tk()
    app = FolderSelectionApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()

