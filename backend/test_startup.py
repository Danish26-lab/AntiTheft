#!/usr/bin/env python3
"""Test backend startup"""

import sys
import io

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 60)
print("Testing Backend Startup")
print("=" * 60)

try:
    print("\n[1/5] Importing Flask...")
    from flask import Flask
    print("✅ Flask imported")
    
    print("\n[2/5] Importing app module...")
    from app import app
    print("✅ App module imported")
    
    print("\n[3/5] Checking database configuration...")
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')
    print(f"✅ Database URI: {db_uri}")
    
    print("\n[4/5] Testing database connection...")
    from models import db
    with app.app_context():
        # Try a simple query
        from models import User
        count = User.query.count()
        print(f"✅ Database connected! Found {count} users")
    
    print("\n[5/5] Starting Flask server...")
    print("=" * 60)
    print("Backend should now be running on http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

