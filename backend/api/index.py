"""
Vercel Serverless Function Entry Point for Flask App
This file is required by Vercel to run the Flask application as a serverless function.
"""

import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.resolve()))

# Import the Flask app instance
from app import app

# Vercel automatically wraps Flask WSGI apps
# Just export the app instance - Vercel will handle the rest
# Vercel looks for 'app' or 'application' variable
application = app

# Export both names for compatibility
__all__ = ['app', 'application']
