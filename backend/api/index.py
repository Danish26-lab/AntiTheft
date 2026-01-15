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
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Also add current directory for imports
current_dir = str(Path(__file__).parent.resolve())
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Import the Flask app instance
    from app import app
    
    # Vercel automatically wraps Flask WSGI apps
    # Just export the app instance - Vercel will handle the rest
    # Vercel looks for 'app' or 'application' variable
    application = app
    
    # Export both names for compatibility
    __all__ = ['app', 'application']
    
except Exception as e:
    # If import fails, create a minimal error app
    from flask import Flask
    error_app = Flask(__name__)
    
    @error_app.route('/<path:path>')
    def error_handler(path):
        return {
            'error': 'Failed to initialize Flask app',
            'message': str(e),
            'type': type(e).__name__
        }, 500
    
    app = error_app
    application = error_app
    __all__ = ['app', 'application']
