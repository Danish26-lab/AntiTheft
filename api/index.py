"""
Vercel Root API Entry Point
This is a simpler entry point at the root api/ directory
"""

import sys
import os
from pathlib import Path

# Set Vercel environment flag
os.environ['VERCEL'] = '1'

# Add backend directory to Python path
project_root = Path(__file__).parent.parent
backend_dir = project_root / 'backend'
backend_path = str(backend_dir.resolve())

# Add to Python path
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Change working directory to backend for relative imports
try:
    os.chdir(backend_path)
except Exception:
    pass  # Ignore if can't change directory

try:
    # Import the Flask app instance
    from app import app
    
    # Vercel automatically wraps Flask WSGI apps
    # Export both 'app' and 'application' for compatibility
    application = app
    
    __all__ = ['app', 'application']
    
    print(f"[VERCEL] Flask app loaded successfully from {backend_path}")
    
except Exception as e:
    import traceback
    error_msg = str(e)
    error_trace = traceback.format_exc()
    
    print(f"[VERCEL ERROR] Failed to load Flask app: {error_msg}")
    print(f"[VERCEL ERROR] Traceback: {error_trace}")
    
    # Create error handler Flask app
    from flask import Flask
    error_app = Flask(__name__)
    
    @error_app.route('/', defaults={'path': ''})
    @error_app.route('/<path:path>')
    def error_handler(path):
        return {
            'error': 'Flask initialization failed',
            'message': error_msg,
            'type': type(e).__name__,
            'path_attempted': backend_path,
            'sys_path': sys.path[:3]
        }, 500
    
    app = error_app
    application = error_app
    __all__ = ['app', 'application']
