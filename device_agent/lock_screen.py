#!/usr/bin/env python3
"""
Custom Lock Screen Overlay
Shows a fullscreen lock screen with password unlock
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import json
import platform
import socket
from pathlib import Path

# Lock state file
LOCK_STATE_FILE = Path(__file__).parent / 'lock_state.json'
LOCK_PORT = 12345  # Port for lock screen instance check

class LockScreen:
    def __init__(self, password='antitheft2024', message=''):
        self.password = password
        self.message = message
        self.unlocked = False
        
        # Create fullscreen window
        self.root = tk.Tk()
        self.setup_window()
        self.create_ui()
        
        # Make window stay on top and block input
        self.root.attributes('-topmost', True)
        self.root.attributes('-fullscreen', True)
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Grab all input focus
        try:
            self.root.grab_set_global()  # Global grab - blocks all other windows (if available)
        except:
            self.root.grab_set()  # Fallback to regular grab
        self.root.focus_force()
        
        # Disable Alt+Tab, Alt+F4, etc.
        self.root.bind('<Alt-Tab>', lambda e: 'break')
        self.root.bind('<Alt-F4>', lambda e: 'break')
        self.root.bind('<Control-Alt-Delete>', lambda e: 'break')
        self.root.bind('<Escape>', lambda e: 'break')
        self.root.bind('<Control-c>', lambda e: 'break')
        self.root.bind('<Control-q>', lambda e: 'break')
        
        # Prevent window from being closed
        self.root.protocol('WM_DELETE_WINDOW', lambda: None)
        
        # Start a simple server to detect if lock screen is running
        self.start_lock_server()
        
        # Focus on password entry
        self.root.after(100, self.password_entry.focus)
    
    def start_lock_server(self):
        """Start a simple server to detect if lock screen is running"""
        try:
            import threading
            def server():
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.bind(('localhost', LOCK_PORT))
                    sock.listen(1)
                    while not self.unlocked:
                        try:
                            conn, addr = sock.accept()
                            conn.close()
                        except:
                            break
                    sock.close()
                except:
                    pass
            thread = threading.Thread(target=server, daemon=True)
            thread.start()
        except:
            pass
        
    def setup_window(self):
        """Configure window to be fullscreen and always on top"""
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window to fullscreen
        self.root.geometry(f'{screen_width}x{screen_height}+0+0')
        self.root.configure(bg='#1a1a1a')  # Dark background
        
        # Center window
        self.root.update_idletasks()
        
    def create_ui(self):
        """Create the lock screen UI"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(expand=True, fill='both')
        
        # Lock icon (using Unicode lock symbol)
        icon_frame = tk.Frame(main_frame, bg='#1a1a1a')
        icon_frame.pack(pady=(100, 50))
        
        # Create a white circle with lock icon
        icon_canvas = tk.Canvas(icon_frame, width=120, height=120, bg='#1a1a1a', highlightthickness=0)
        icon_canvas.pack()
        
        # Draw white circle
        icon_canvas.create_oval(10, 10, 110, 110, fill='white', outline='white')
        
        # Draw lock icon (simplified)
        icon_canvas.create_rectangle(40, 50, 80, 85, fill='#1a1a1a', outline='#1a1a1a', width=0)
        icon_canvas.create_arc(35, 45, 85, 75, start=0, extent=180, fill='#1a1a1a', outline='#1a1a1a', width=3)
        
        # Instruction text
        instruction_label = tk.Label(
            main_frame,
            text="Please type the password to unlock:",
            font=('Segoe UI', 16),
            fg='white',
            bg='#1a1a1a'
        )
        instruction_label.pack(pady=(0, 30))
        
        # Password entry frame
        entry_frame = tk.Frame(main_frame, bg='#1a1a1a')
        entry_frame.pack(pady=10)
        
        # Password entry
        self.password_entry = tk.Entry(
            entry_frame,
            font=('Segoe UI', 18),
            width=30,
            show='●',  # Show dots instead of characters
            bg='white',
            fg='#1a1a1a',
            relief='flat',
            bd=0,
            insertbackground='#1a1a1a'
        )
        self.password_entry.pack(padx=20, pady=10)
        self.password_entry.bind('<Return>', self.check_password)
        self.password_entry.bind('<KeyPress>', self.on_key_press)
        
        # Error message label (initially hidden)
        self.error_label = tk.Label(
            main_frame,
            text="",
            font=('Segoe UI', 12),
            fg='#ff4444',
            bg='#1a1a1a'
        )
        self.error_label.pack(pady=10)
        
        # Optional message display
        if self.message:
            message_frame = tk.Frame(main_frame, bg='#1a1a1a')
            message_frame.pack(pady=(50, 0))
            
            message_label = tk.Label(
                message_frame,
                text=self.message,
                font=('Segoe UI', 14),
                fg='#ffaa00',
                bg='#1a1a1a',
                wraplength=600,
                justify='center'
            )
            message_label.pack()
        
        # Unlock button (optional, password entry is primary method)
        button_frame = tk.Frame(main_frame, bg='#1a1a1a')
        button_frame.pack(pady=30)
        
        unlock_button = tk.Button(
            button_frame,
            text="Unlock",
            font=('Segoe UI', 14),
            bg='#0078d4',
            fg='white',
            activebackground='#005a9e',
            activeforeground='white',
            relief='flat',
            padx=40,
            pady=10,
            cursor='hand2',
            command=self.check_password
        )
        unlock_button.pack()
        
    def on_key_press(self, event):
        """Clear error message when user starts typing"""
        if self.error_label.cget('text'):
            self.error_label.config(text='')
    
    def check_password(self, event=None):
        """Check if entered password is correct"""
        # Get entered password exactly as typed (case-sensitive)
        entered_password = self.password_entry.get().strip()
        
        # Debug: Print password comparison
        print(f"DEBUG: Entered password: '{entered_password}' (length: {len(entered_password)})")
        print(f"DEBUG: Expected password: '{self.password}' (length: {len(self.password)})")
        print(f"DEBUG: Entered bytes: {entered_password.encode('utf-8')}")
        print(f"DEBUG: Expected bytes: {self.password.encode('utf-8')}")
        print(f"DEBUG: Case-sensitive match: {entered_password == self.password}")
        
        # Case-sensitive exact match (preserve user's exact input)
        if entered_password == self.password:
            self.unlocked = True
            # Release grab before destroying
            try:
                self.root.grab_release()
            except:
                pass
            # Clear lock state file
            if LOCK_STATE_FILE.exists():
                try:
                    LOCK_STATE_FILE.unlink()
                except:
                    pass
            self.root.quit()
            self.root.destroy()
        else:
            # Show error
            self.error_label.config(text="Incorrect password. Please try again.")
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()
            # Shake animation (simple)
            self.shake_window()
    
    def shake_window(self):
        """Simple shake animation for wrong password"""
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        for i in range(5):
            offset = 10 if i % 2 == 0 else -10
            self.root.geometry(f'+{x + offset}+{y}')
            self.root.update()
            self.root.after(50)
        self.root.geometry(f'+{x}+{y}')
    
    def run(self):
        """Run the lock screen"""
        try:
            self.root.mainloop()
        except:
            pass

def save_lock_state(password, message=''):
    """Save lock state to file"""
    state = {
        'locked': True,
        'password': password,
        'message': message
    }
    with open(LOCK_STATE_FILE, 'w') as f:
        json.dump(state, f)

def is_locked():
    """Check if device is currently locked"""
    return LOCK_STATE_FILE.exists()

def get_lock_state():
    """Get current lock state"""
    if LOCK_STATE_FILE.exists():
        try:
            with open(LOCK_STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def is_lock_screen_running():
    """Check if lock screen is already running"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex(('localhost', LOCK_PORT))
        sock.close()
        return result == 0
    except:
        return False

def show_lock_screen(password='antitheft2024', message=''):
    """Show the lock screen"""
    # Check if already running
    if is_lock_screen_running():
        return  # Lock screen already active
    
    # Save lock state
    save_lock_state(password, message)
    
    # Create and run lock screen
    lock_screen = LockScreen(password=password, message=message)
    lock_screen.run()

if __name__ == '__main__':
    # Get password and message from command line or lock state file
    password = 'antitheft2024'
    message = ''
    
    # Get from command line arguments
    if len(sys.argv) > 1:
        password = sys.argv[1]
    if len(sys.argv) > 2:
        # Join all remaining args as message (in case message has spaces)
        message = ' '.join(sys.argv[2:])
    
    # Or get from lock state file if no args provided
    if len(sys.argv) == 1:
        state = get_lock_state()
        if state:
            password = state.get('password', password)
            message = state.get('message', message)
    
    show_lock_screen(password=password, message=message)

