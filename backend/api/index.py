"""
Vercel Serverless Function Entry Point for Flask App
This file is required by Vercel to run the Flask application as a serverless function.
"""

import sys
import os
from pathlib import Path

# Set Vercel environment flag
os.environ['VERCEL'] = '1'

# Add backend directory to Python path
# Handle both absolute and relative paths
backend_dir = Path(__file__).parent.parent
backend_path = str(backend_dir.resolve())

# Add to Python path
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Change working directory to backend for relative imports
os.chdir(backend_path)

try:
    # Import the Flask app instance
    from app import app
    
    # Vercel automatically wraps Flask WSGI apps
    # Just export the app instance - Vercel will handle the rest
    # Vercel looks for 'app' or 'application' variable
    application = app
    
    # Export both names for compatibility
    __all__ = ['app', 'application']
    
    # Debug output (won't show in production but helpful for logs)
    print(f"[VERCEL] Flask app loaded successfully from {backend_path}")
    print(f"[VERCEL] App routes: {[str(rule) for rule in app.url_map.iter_rules()][:5]}...")
    
except Exception as e:
    import traceback
    error_details = traceback.format_exc()
    print(f"[VERCEL ERROR] Failed to import Flask app: {e}")
    print(f"[VERCEL ERROR] Traceback: {error_details}")
    
    # If import fails, create a minimal error app
    from flask import Flask
    error_app = Flask(__name__)
    
    @error_app.route('/', defaults={'path': ''})
    @error_app.route('/<path:path>')
    def error_handler(path):
        return {
            'error': 'Failed to initialize Flask app',
            'message': str(e),
            'type': type(e).__name__,
            'path': path,
            'sys_path': sys.path[:3]  # First 3 entries
        }, 500
    
    app = error_app
    application = error_app
    __all__ = ['app', 'application']
