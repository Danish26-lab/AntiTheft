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

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Change working directory
os.chdir(backend_path)

try:
    from app import app
    application = app
    __all__ = ['app', 'application']
    print(f"[VERCEL] Flask app loaded from {backend_path}")
except Exception as e:
    import traceback
    print(f"[VERCEL ERROR] {e}")
    print(traceback.format_exc())
    
    from flask import Flask
    error_app = Flask(__name__)
    
    @error_app.route('/', defaults={'path': ''})
    @error_app.route('/<path:path>')
    def error_handler(path):
        return {
            'error': 'Flask initialization failed',
            'message': str(e),
            'type': type(e).__name__
        }, 500
    
    app = error_app
    application = error_app
    __all__ = ['app', 'application']
