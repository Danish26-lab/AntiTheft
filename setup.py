#!/usr/bin/env python3
"""
Setup script for Smart Anti-Theft System
"""

import os
import subprocess
import sys

def create_env_file():
    """Create .env file from .env.example if it doesn't exist"""
    if not os.path.exists('.env') and os.path.exists('.env.example'):
        import shutil
        shutil.copy('.env.example', '.env')
        print("✅ Created .env file from .env.example")
        print("⚠️  Please edit .env file with your configuration")
    elif os.path.exists('.env'):
        print("✅ .env file already exists")
    else:
        print("⚠️  .env.example not found")

def setup_backend():
    """Setup backend dependencies"""
    print("\n📦 Setting up backend...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Backend dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing backend dependencies: {e}")
        return False
    return True

def setup_frontend():
    """Setup frontend dependencies"""
    print("\n📦 Setting up frontend...")
    os.chdir('frontend')
    try:
        subprocess.check_call(['npm', 'install'])
        print("✅ Frontend dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing frontend dependencies: {e}")
        return False
    finally:
        os.chdir('..')
    return True

def setup_device_agent():
    """Setup device agent dependencies"""
    print("\n📦 Setting up device agent...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'device_agent/requirements.txt'])
        print("✅ Device agent dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing device agent dependencies: {e}")
        return False
    return True

def main():
    print("🛡️  Smart Anti-Theft System Setup")
    print("=" * 50)
    
    # Create .env file
    create_env_file()
    
    # Setup backend
    if not setup_backend():
        print("\n❌ Backend setup failed")
        sys.exit(1)
    
    # Setup frontend
    if not setup_frontend():
        print("\n❌ Frontend setup failed")
        sys.exit(1)
    
    # Setup device agent
    if not setup_device_agent():
        print("\n❌ Device agent setup failed")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n📝 Next steps:")
    print("1. Edit .env file with your configuration")
    print("2. Start backend: cd backend && python app.py")
    print("3. Start frontend: cd frontend && npm run dev")
    print("4. Run device agent: cd device_agent && python agent.py")
    print("\n🔐 Default login: admin@antitheft.com / admin123")

if __name__ == '__main__':
    main()

