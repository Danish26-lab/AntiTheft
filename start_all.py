#!/usr/bin/env python3
"""
Smart Anti-Theft System - Start All Services
One script to run backend, frontend, and device agents
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

# Windows doesn't support ANSI colors by default
if sys.platform == 'win32':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

def print_color(text, color):
    """Print colored text"""
    if sys.platform == 'win32':
        print(text)
    else:
        print(f"{color}{text}{Colors.RESET}")

def check_port(port):
    """Check if port is in use"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

def start_backend():
    """Start Flask backend server"""
    backend_dir = Path(__file__).parent / 'backend'
    print_color("📦 Starting Backend Server...", Colors.CYAN)
    
    if sys.platform == 'win32':
        # Capture output so we can see errors
        return subprocess.Popen(
            ['python', 'app.py'],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
    else:
        return subprocess.Popen(
            ['python3', 'app.py'],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

def start_frontend():
    """Start React frontend server"""
    frontend_dir = Path(__file__).parent / 'frontend'
    print_color("🌐 Starting Frontend Server...", Colors.CYAN)
    
    if sys.platform == 'win32':
        return subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd=frontend_dir,
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        return subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

def start_device_agent():
    """Start device agent"""
    agent_dir = Path(__file__).parent / 'device_agent'
    print_color("🤖 Starting Device Agent...", Colors.CYAN)
    
    if sys.platform == 'win32':
        return subprocess.Popen(
            ['python', 'agent.py'],
            cwd=agent_dir,
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        return subprocess.Popen(
            ['python3', 'agent.py'],
            cwd=agent_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

def main():
    print_color("🚀 Starting Smart Anti-Theft System...", Colors.GREEN)
    print("=" * 50)
    print()
    
    # Check ports
    print_color("Checking ports...", Colors.CYAN)
    if check_port(5000):
        print_color("⚠️  Port 5000 (Backend) is already in use", Colors.YELLOW)
    if check_port(3000):
        print_color("⚠️  Port 3000 (Frontend) is already in use", Colors.YELLOW)
    print()
    
    processes = []
    
    try:
        # Start Backend
        backend_proc = start_backend()
        processes.append(('Backend', backend_proc))
        time.sleep(2)
        
        if check_port(5000):
            print_color("✅ Backend running on http://localhost:5000", Colors.GREEN)
        else:
            print_color("⏳ Backend starting...", Colors.YELLOW)
        
        # Start Frontend
        frontend_proc = start_frontend()
        processes.append(('Frontend', frontend_proc))
        time.sleep(3)
        
        if check_port(3000):
            print_color("✅ Frontend running on http://localhost:3000", Colors.GREEN)
        else:
            print_color("⏳ Frontend starting...", Colors.YELLOW)
        
        # Start Device Agent
        agent_proc = start_device_agent()
        processes.append(('Device Agent', agent_proc))
        time.sleep(2)
        
        print_color("✅ Device Agent started (monitoring for commands)", Colors.GREEN)
        
        print()
        print("=" * 50)
        print_color("🎉 All Services Started!", Colors.GREEN)
        print()
        print_color("📱 Access Points:", Colors.CYAN)
        print("  • Dashboard:  http://localhost:3000")
        print("  • QR Scanner:  http://192.168.0.19:3000/qr-scanner")
        print("  • Backend API: http://localhost:5000/api/health")
        print()
        print_color("🔐 Default Login:", Colors.CYAN)
        print("  • Email: admin@antitheft.com")
        print("  • Password: admin123")
        print()
        print_color("⚠️  IMPORTANT: Keep Device Agent window open!", Colors.YELLOW)
        print("  The agent must be running to receive lock commands.")
        print()
        print_color("⚠️  Press Ctrl+C to stop all services", Colors.YELLOW)
        print()
        
        # Keep running and monitor processes
        while True:
            time.sleep(1)
            
            # Check if processes are still alive
            for name, proc in processes:
                if proc.poll() is not None:
                    print_color(f"❌ {name} process ended!", Colors.RED)
                    
                    # Try to read error output
                    try:
                        if proc.stdout:
                            output = proc.stdout.read()
                            if output:
                                print_color(f"Error output from {name}:", Colors.RED)
                                print(output)
                    except Exception as e:
                        print_color(f"Could not read {name} error output: {e}", Colors.YELLOW)
                    
                    # Exit on backend crash
                    if name == 'Backend':
                        print_color("Backend crashed. Exiting...", Colors.RED)
                        raise KeyboardInterrupt
                    
    except KeyboardInterrupt:
        print()
        print_color("🛑 Stopping all services...", Colors.YELLOW)
        
        for name, proc in processes:
            try:
                if sys.platform == 'win32':
                    proc.terminate()
                else:
                    proc.send_signal(signal.SIGTERM)
                proc.wait(timeout=5)
                print_color(f"✅ {name} stopped", Colors.GREEN)
            except:
                proc.kill()
                print_color(f"⚠️  {name} force stopped", Colors.YELLOW)
        
        print_color("✅ All services stopped.", Colors.GREEN)
    except Exception as e:
        print_color(f"❌ Error: {e}", Colors.RED)
        sys.exit(1)

if __name__ == '__main__':
    main()

