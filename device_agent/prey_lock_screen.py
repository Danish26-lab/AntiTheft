#!/usr/bin/env python3
"""
Prey Project-style Lock Screen
Uses Windows API for secure, system-level screen locking
Based on: https://github.com/programmerjake/preyproject-lock-screen
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
import json
import platform
import socket
import threading
import time
import logging
from pathlib import Path

# Setup logging for lock screen debugging
log_file = Path(__file__).parent / 'lock_screen.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

# Windows API imports
if platform.system().lower() == 'windows':
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        # Windows constants
        WS_EX_TOPMOST = 0x00000008
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_APPWINDOW = 0x00040000
        WS_POPUP = 0x80000000
        WS_VISIBLE = 0x10000000
        SW_SHOW = 5
        HWND_TOPMOST = -1
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_SHOWWINDOW = 0x0040
        GWL_EXSTYLE = -20
        GWL_STYLE = -16
        
        # Input blocking
        WH_KEYBOARD_LL = 13
        WH_MOUSE_LL = 14
        WM_KEYDOWN = 0x0100
        WM_SYSKEYDOWN = 0x0104
        HC_ACTION = 0
        
        WINDOWS_API_AVAILABLE = True
    except:
        WINDOWS_API_AVAILABLE = False
else:
    WINDOWS_API_AVAILABLE = False

# Lock state file
LOCK_STATE_FILE = Path(__file__).parent / 'lock_state.json'
LOCK_PORT = 12345  # Port for lock screen instance check

class PreyLockScreen:
    def __init__(self, password='antitheft2024', message=''):
        # Ensure password is a string and strip whitespace (but preserve case)
        self.password = str(password).strip() if password else 'antitheft2024'
        self.message = str(message).strip() if message else ''
        self.unlocked = False
        
        # Validate password
        if not self.password:
            logging.error("❌ Invalid password: password cannot be empty")
            self.password = 'antitheft2024'
            logging.warning(f"⚠️ Using default password: {self.password}")
        
        # Log the exact password being used
        logging.info(f"🔐 PreyLockScreen initialized with password: '{self.password}' (length: {len(self.password)})")
        logging.info(f"🔐 Password bytes: {self.password.encode('utf-8')}")
        self.hook_handle = None
        self.mouse_hook_handle = None
        self.password_entry = None  # Will be set in create_ui
        
        try:
            # Create fullscreen window
            logging.info("Creating tkinter root window...")
            self.root = tk.Tk()
            logging.info("Root window created, setting up...")
            
            try:
                self.setup_window()
                logging.info("Window setup complete, creating UI...")
            except Exception as setup_error:
                logging.error(f"❌ Error setting up window: {setup_error}")
                import traceback
                logging.error(traceback.format_exc())
                raise
            
            try:
                self.create_ui()
                logging.info("UI created, password_entry available: %s", self.password_entry is not None)
                
                if self.password_entry is None:
                    raise Exception("Password entry field was not created - UI creation failed")
            except Exception as ui_error:
                logging.error(f"❌ Error creating UI: {ui_error}")
                import traceback
                logging.error(traceback.format_exc())
                raise
        except Exception as init_error:
            logging.error(f"❌ CRITICAL ERROR in PreyLockScreen initialization: {init_error}")
            import traceback
            logging.error(traceback.format_exc())
            # Try to clean up if root was created
            try:
                if hasattr(self, 'root'):
                    self.root.destroy()
            except:
                pass
            raise
        
        # Apply Windows API enhancements if available
        if WINDOWS_API_AVAILABLE and platform.system().lower() == 'windows':
            logging.info("Applying Windows API enhancements...")
            self.apply_windows_enhancements()
            logging.info("Windows API enhancements applied")
        
        # Make window stay on top and block input
        self.root.attributes('-topmost', True)
        self.root.attributes('-fullscreen', True)
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Force window to front and make it visible
        self.root.lift()
        self.root.focus_force()
        self.root.update()
        
        # Grab all input focus - but allow input to our window
        try:
            # Use regular grab_set instead of global - allows input to our window
            self.root.grab_set()
        except:
            pass
        
        # Ensure window is on top after a short delay
        self.root.after(100, lambda: self.root.lift())
        self.root.after(200, lambda: self.root.focus_force())
        self.root.after(300, lambda: self.password_entry.focus_set())
        
        # Install keyboard/mouse hooks on Windows for better blocking
        if WINDOWS_API_AVAILABLE and platform.system().lower() == 'windows':
            self.install_hooks()
        
        # Disable Alt+Tab, Alt+F4, etc.
        # Some Tk versions / platforms don't support certain keysyms (like <Super>),
        # so wrap all binds in try/except to avoid hard crashes.
        try:
            self.root.bind('<Alt-Tab>', lambda e: 'break')
        except Exception:
            pass
        try:
            self.root.bind('<Alt-F4>', lambda e: 'break')
        except Exception:
            pass
        try:
            self.root.bind('<Control-Alt-Delete>', lambda e: 'break')
        except Exception:
            pass
        try:
            self.root.bind('<Escape>', lambda e: 'break')
        except Exception:
            pass
        try:
            self.root.bind('<Control-c>', lambda e: 'break')
        except Exception:
            pass
        try:
            self.root.bind('<Control-q>', lambda e: 'break')
        except Exception:
            pass
        # These can raise "bad event type or keysym" on some Windows/Tk builds,
        # so protect them as well. If they fail, normal Windows key behavior remains.
        try:
            self.root.bind('<Super>', lambda e: 'break')  # Windows key
            self.root.bind('<Super-l>', lambda e: 'break')  # Windows+L
        except Exception:
            pass
        
        # Prevent window from being closed
        self.root.protocol('WM_DELETE_WINDOW', lambda: None)
        
        # Start a simple server to detect if lock screen is running
        self.start_lock_server()
        
        # Keep window on top periodically
        self.keep_on_top()
        
        # Focus on password entry - multiple attempts to ensure it works
        # Use longer delays to ensure window is fully rendered
        def focus_password():
            try:
                if self.password_entry:
                    self.password_entry.focus_set()
                    self.password_entry.icursor(0)
                    self.root.update()
            except:
                pass
        
        self.root.after(100, focus_password)
        self.root.after(300, focus_password)
        self.root.after(500, focus_password)
        self.root.after(1000, focus_password)  # Final attempt after 1 second
    
    def apply_windows_enhancements(self):
        """Apply Windows API enhancements for better security"""
        try:
            # Get window handle
            hwnd = self.root.winfo_id()
            
            # Make window truly topmost using Windows API
            user32.SetWindowPos(
                hwnd,
                HWND_TOPMOST,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
            )
            
            # Remove from taskbar
            ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ex_style |= WS_EX_TOOLWINDOW
            ex_style &= ~WS_EX_APPWINDOW
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)
            
        except Exception as e:
            print(f"Warning: Could not apply Windows enhancements: {e}")
    
    def install_hooks(self):
        """Install low-level keyboard and mouse hooks to block input"""
        try:
            our_hwnd = self.root.winfo_id()
            
            # Define hook procedure
            HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
            
            def low_level_keyboard_proc(nCode, wParam, lParam):
                """Block system keys but allow normal input to our window"""
                if nCode >= HC_ACTION:
                    # Get foreground window
                    fg_hwnd = user32.GetForegroundWindow()
                    # Only block system keys (ESC, Windows keys) if not our window
                    if fg_hwnd != our_hwnd:
                        # Block system keys that could escape
                        if wParam in (0x1B, 0x5B, 0x5C):  # ESC, Windows keys
                            return 1
                    # Always allow input to our window - don't block normal keys
                return user32.CallNextHookExW(self.hook_handle, nCode, wParam, lParam)
            
            # Install keyboard hook only (mouse hook can be too restrictive)
            keyboard_proc = HOOKPROC(low_level_keyboard_proc)
            self.hook_handle = user32.SetWindowsHookExW(
                WH_KEYBOARD_LL,
                keyboard_proc,
                kernel32.GetModuleHandleW(None),
                0
            )
            
        except Exception as e:
            # Hooks are optional - continue without them
            pass
            self.hook_handle = None
            self.mouse_hook_handle = None
    
    def uninstall_hooks(self):
        """Uninstall keyboard and mouse hooks"""
        try:
            if self.hook_handle:
                user32.UnhookWindowsHookExW(self.hook_handle)
                self.hook_handle = None
            if self.mouse_hook_handle:
                user32.UnhookWindowsHookExW(self.mouse_hook_handle)
                self.mouse_hook_handle = None
        except:
            pass
    
    def keep_on_top(self):
        """Periodically ensure window stays on top"""
        if not self.unlocked:
            try:
                if WINDOWS_API_AVAILABLE and platform.system().lower() == 'windows':
                    hwnd = self.root.winfo_id()
                    user32.SetWindowPos(
                        hwnd,
                        HWND_TOPMOST,
                        0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
                    )
                else:
                    self.root.attributes('-topmost', True)
            except:
                pass
            self.root.after(100, self.keep_on_top)  # Check every 100ms
    
    def start_lock_server(self):
        """Start a simple server to detect if lock screen is running"""
        try:
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
        
        # Force window to be visible
        self.root.deiconify()  # Ensure window is not iconified
        self.root.lift()  # Bring to front
        self.root.focus_force()  # Force focus
        
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
        
        # Password entry - make sure it's focusable and accepts input
        self.password_entry = tk.Entry(
            entry_frame,
            font=('Segoe UI', 18),
            width=30,
            show='●',  # Show dots instead of characters
            bg='white',
            fg='#1a1a1a',
            relief='flat',
            bd=2,
            highlightthickness=2,
            highlightbackground='#0078d4',
            highlightcolor='#0078d4',
            insertbackground='#1a1a1a',
            takefocus=True  # Ensure it can receive focus
        )
        # CRITICAL: Ensure field starts completely empty - no auto-fill
        self.password_entry.delete(0, tk.END)
        self.password_entry.pack(padx=20, pady=10)
        self.password_entry.bind('<Return>', self.check_password)
        self.password_entry.bind('<KeyPress>', self.on_key_press)
        self.password_entry.bind('<FocusIn>', lambda e: self.password_entry.config(highlightbackground='#0078d4'))
        self.password_entry.bind('<FocusOut>', lambda e: self.password_entry.config(highlightbackground='#666666'))
        
        # Make entry field clickable to focus
        self.password_entry.bind('<Button-1>', lambda e: self.password_entry.focus_set())
        
        # Prevent any auto-fill, paste, or clipboard operations
        self.password_entry.bind('<Control-v>', lambda e: 'break')  # Block paste
        self.password_entry.bind('<Shift-Insert>', lambda e: 'break')  # Block paste
        self.password_entry.bind('<Button-2>', lambda e: 'break')  # Block middle-click paste
        self.password_entry.bind('<Button-3>', lambda e: 'break')  # Block right-click paste
        
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
        if not self.password_entry:
            return
        
        entered_password = self.password_entry.get().strip()
        
        # Don't allow empty password
        if not entered_password:
            self.error_label.config(text="Please enter a password.")
            self.password_entry.focus()
            return
        
        # Debug logging - show exact comparison
        logging.info("=" * 60)
        logging.info("PASSWORD COMPARISON:")
        logging.info(f"  Entered: '{entered_password}' (length: {len(entered_password)})")
        logging.info(f"  Expected: '{self.password}' (length: {len(self.password)})")
        logging.info(f"  Entered bytes: {entered_password.encode('utf-8')}")
        logging.info(f"  Expected bytes: {self.password.encode('utf-8')}")
        logging.info(f"  Are equal? {entered_password == self.password}")
        logging.info(f"  Are equal (case-insensitive)? {entered_password.lower() == self.password.lower()}")
        logging.info("=" * 60)
        
        # Case-sensitive exact match (preserve user's exact input)
        if entered_password == self.password:
            logging.info("✅✅ PASSWORD CORRECT - UNLOCKING INSTANTLY")
            self.unlocked = True
            
            # Delete lock state file FIRST (before closing window) so agent detects unlock immediately
            try:
                if LOCK_STATE_FILE.exists():
                    LOCK_STATE_FILE.unlink()
                    logging.info("🗑️ Lock state file deleted (unlock detected)")
            except Exception as e:
                logging.warning(f"Could not delete lock state file: {e}")
            
            # INSTANT UNLOCK - Close window immediately, do cleanup in background
            # Uninstall hooks first (must be done before window closes)
            if WINDOWS_API_AVAILABLE and platform.system().lower() == 'windows':
                self.uninstall_hooks()
            
            # Release grab immediately
            try:
                self.root.grab_release()
            except:
                pass
            
            # Close window INSTANTLY - don't wait for anything
            self.root.quit()
            self.root.destroy()
            
            # Do cleanup operations in background (non-blocking)
            def cleanup_background():
                try:
                    # Lock state file already deleted above, but double-check
                    if LOCK_STATE_FILE.exists():
                        try:
                            LOCK_STATE_FILE.unlink()
                        except:
                            pass
                    
                    # Update backend status to active (unlocked) - non-blocking
                    try:
                        import requests
                        from pathlib import Path
                        import json
                        config_file = Path(__file__).parent / 'config.json'
                        if config_file.exists():
                            with open(config_file, 'r') as f:
                                config = json.load(f)
                                device_id = config.get('device_id')
                                user_email = config.get('user_email', '')
                                if device_id:
                                    # Notify backend that device is unlocked
                                    # Include user email if available for proper authentication
                                    payload = {
                                            'device_id': device_id,
                                            'status': 'active'
                                    }
                                    if user_email:
                                        payload['user'] = user_email
                                    
                                    try:
                                        response = requests.post(
                                            'http://localhost:5000/api/update_location',
                                            json=payload,
                                            timeout=5  # Increased timeout for reliability
                                        )
                                        if response.status_code == 200:
                                            logging.info("✅ Backend status updated to 'active' after unlock")
                                        else:
                                            logging.warning(f"⚠️ Backend status update returned {response.status_code}: {response.text[:200]}")
                                    except requests.exceptions.RequestException as req_error:
                                        logging.warning(f"⚠️ Failed to update backend status after unlock: {req_error}")
                                        # Don't fail - agent will detect unlock on next check
                    except Exception as update_error:
                        logging.warning(f"⚠️ Error updating backend status after unlock: {update_error}")
                        # Don't fail - agent will detect unlock on next check
                    
                    logging.info("✅ Unlock cleanup completed")
                except:
                    pass
            
            # Run cleanup in background thread so it doesn't block
            cleanup_thread = threading.Thread(target=cleanup_background, daemon=True)
            cleanup_thread.start()
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
        """Run the lock screen - stays open until password is entered"""
        logging.info("=" * 60)
        logging.info("LOCK SCREEN STARTING")
        logging.info("=" * 60)
        
        try:
            # Ensure password field is empty and ready
            if self.password_entry:
                self.password_entry.delete(0, tk.END)
                logging.info("Password field cleared")
            else:
                logging.error("CRITICAL: Password entry field is None!")
                raise Exception("Password entry field not initialized")
            
            # Force window to be visible and on top
            logging.info("Making window visible...")
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.root.update_idletasks()
            self.root.update()
            
            # Ensure window stays on top
            self.root.attributes('-topmost', True)
            
            # Focus password field
            logging.info("Focusing password field...")
            self.password_entry.focus_set()
            self.password_entry.icursor(0)
            self.root.update()
            
            logging.info("Window is ready. Entering mainloop - window will stay open until password is entered.")
            logging.info("User can now type password manually in the field.")
            
            # Run mainloop - this blocks until window is closed
            # The window will only close when check_password() calls root.quit()
            self.root.mainloop()
            
            logging.info("Mainloop exited - window was closed (password entered correctly)")
        except Exception as e:
            logging.error(f"CRITICAL ERROR in lock screen mainloop: {e}")
            import traceback
            logging.error(traceback.format_exc())
            # Try to keep window open even if there's an error
            try:
                logging.info("Attempting to keep window open despite error...")
                self.root.mainloop()
            except:
                logging.error("Failed to keep window open")
        finally:
            logging.info("Cleaning up lock screen...")
            # Cleanup hooks
            if WINDOWS_API_AVAILABLE and platform.system().lower() == 'windows':
                self.uninstall_hooks()
            logging.info("Lock screen cleanup complete")

def save_lock_state(password, message=''):
    """Save lock state to file"""
    # Ensure password is a string and properly formatted
    clean_password = str(password).strip() if password else 'antitheft2024'
    state = {
        'locked': True,
        'password': clean_password,
        'message': str(message).strip() if message else ''
    }
    with open(LOCK_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False)
    logging.info(f"💾 Lock state saved with password: '{clean_password}' (length: {len(clean_password)})")

def is_locked():
    """Check if device is currently locked"""
    return LOCK_STATE_FILE.exists()

def get_lock_state():
    """Get current lock state"""
    if LOCK_STATE_FILE.exists():
        try:
            with open(LOCK_STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
                # Ensure password is properly extracted and cleaned
                if 'password' in state:
                    state['password'] = str(state['password']).strip()
                    logging.info(f"📖 Read password from lock_state.json: '{state['password']}' (length: {len(state['password'])})")
                    logging.info(f"📖 Password bytes: {state['password'].encode('utf-8')}")
                    logging.info(f"📖 Full lock state: {state}")
                return state
        except Exception as e:
            logging.error(f"Error reading lock state file: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return None
    else:
        logging.warning("⚠️ lock_state.json does not exist")
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
    """Show the Prey-style lock screen"""
    import logging
    logging.info(f"🔒 show_lock_screen called with password length: {len(password)}")
    
    # Check if already running
    if is_lock_screen_running():
        logging.warning("Lock screen already running, skipping")
        return  # Lock screen already active
    
    # Save lock state
    save_lock_state(password, message)
    logging.info("Lock state saved")
    
    try:
        # Create and run lock screen
        logging.info("Creating PreyLockScreen instance...")
        lock_screen = PreyLockScreen(password=password, message=message)
        logging.info("PreyLockScreen created, starting mainloop...")
        
        # This will block until password is entered correctly
        lock_screen.run()
        logging.info("Lock screen closed (unlocked)")
    except Exception as e:
        logging.error(f"Error showing lock screen: {e}")
        import traceback
        logging.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    try:
        # Get password and message from command line or lock state file
        password = 'antitheft2024'
        message = ''
        
        # Priority 1: Check lock state file first (most reliable - saved by agent)
        state = get_lock_state()
        if state:
            password = state.get('password', password)
            message = state.get('message', message)
            logging.info(f"📥 Password from lock state file: '{password}' (length: {len(password)})")
            logging.info(f"📥 Password bytes: {password.encode('utf-8')}")
        else:
            # Priority 2: Get from command line arguments
            if len(sys.argv) > 1:
                password = sys.argv[1].strip()  # Strip whitespace from command line arg
                logging.info(f"📥 Password from command line: '{password}' (length: {len(password)})")
                logging.info(f"📥 Password bytes: {password.encode('utf-8')}")
            if len(sys.argv) > 2:
                # Join all remaining args as message (in case message has spaces)
                message = ' '.join(sys.argv[2:])
        
        # Final cleanup - ensure no extra whitespace and it's a string
        password = str(password).strip() if password else 'antitheft2024'
        logging.info(f"🔐 Final password to use: '{password}' (length: {len(password)})")
        logging.info(f"🔐 Final password bytes: {password.encode('utf-8')}")
        
        # Validate tkinter is available before proceeding
        try:
            import tkinter as tk
            test_root = tk.Tk()
            test_root.withdraw()  # Hide test window
            test_root.destroy()
            logging.info("✅ Tkinter is available and working")
        except ImportError:
            logging.error("❌ Tkinter is not installed. Please install it:")
            logging.error("   Windows: Usually included with Python")
            logging.error("   Linux: sudo apt-get install python3-tk")
            logging.error("   macOS: Usually included with Python")
            sys.exit(1)
        except Exception as tk_error:
            logging.error(f"❌ Tkinter test failed: {tk_error}")
            logging.error("   This might indicate a display issue or missing dependencies")
            sys.exit(1)
        
        show_lock_screen(password=password, message=message)
    except KeyboardInterrupt:
        logging.info("Lock screen interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"❌ CRITICAL ERROR in lock screen main: {e}")
        import traceback
        logging.error(traceback.format_exc())
        sys.exit(1)

