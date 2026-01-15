#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Migration: Add Remote Data Wipe Tables
Adds ApprovedFolder and WipeOperation tables to the database.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from flask import Flask
from models import db, ApprovedFolder, WipeOperation

# Create minimal Flask app for migration
app = Flask(__name__)

# Configuration
db_url = os.getenv('DATABASE_URL')
if not db_url:
    backend_dir = Path(__file__).parent.resolve()
    project_dir = backend_dir.parent.resolve()
    database_dir = project_dir / 'database'
    database_dir.mkdir(exist_ok=True, parents=True)
    db_path = database_dir / 'antitheft.db'
    db_path_str = str(db_path.resolve())
    if os.name == 'nt':
        db_path_normalized = db_path_str.replace('\\', '/')
        db_url = f'sqlite:///{db_path_normalized}'
    else:
        db_url = f'sqlite:///{db_path_str}'

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def migrate():
    """Run migration to add wipe-related tables"""
    with app.app_context():
        try:
            # Create tables
            db.create_all()
            print("Migration completed: Wipe tables created successfully")
            print("   - approved_folders table")
            print("   - wipe_operations table")
            return True
        except Exception as e:
            print(f"Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
