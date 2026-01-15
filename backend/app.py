from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import sys
from datetime import timedelta
from pathlib import Path
from models import db, init_db
from routes.device_routes import device_bp
from routes.user_routes import user_bp
from routes.breach_routes import breach_bp
from routes.automation_routes import automation_bp
from routes.wipe_routes import wipe_bp
from utils.scheduler import init_scheduler

# Create Flask app instance
app = Flask(__name__)

# Set FLASK_APP environment variable if not set (for flask CLI)
if not os.environ.get('FLASK_APP'):
    os.environ['FLASK_APP'] = 'app.py'

# Disable Flask's instance folder to avoid path conflicts
app.instance_path = None

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Fix database path - use absolute path
db_url = os.getenv('DATABASE_URL')

# Check if we're in a serverless environment (Vercel, AWS Lambda, etc.)
is_serverless = os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME') or os.getenv('FUNCTION_NAME')

if not db_url:
    if is_serverless:
        # On serverless, we MUST use DATABASE_URL environment variable
        # SQLite won't work - use PostgreSQL or another cloud database
        print("[ERROR] DATABASE_URL environment variable is required for serverless deployment")
        print("[ERROR] SQLite is not supported on Vercel. Please set DATABASE_URL to a PostgreSQL connection string.")
        # Use a placeholder that will fail gracefully
        db_url = 'sqlite:///:memory:'
    else:
        # Local development - use SQLite
        backend_dir = Path(__file__).parent.resolve()
        project_dir = backend_dir.parent.resolve()
        database_dir = project_dir / 'database'
        
        # Create directory with proper permissions
        try:
            database_dir.mkdir(exist_ok=True, parents=True)
        except PermissionError as e:
            print(f"Warning: Could not create database directory: {e}")
        
        # Use Windows-compatible path format
        db_path = database_dir / 'antitheft.db'
        
        # Convert to absolute path string
        db_path_str = str(db_path.resolve())
        
        # SQLite URI format: sqlite:///absolute/path/to/database.db
        if os.name == 'nt':  # Windows
            db_path_normalized = db_path_str.replace('\\', '/')
            db_url = f'sqlite:///{db_path_normalized}'
        else:
            db_url = f'sqlite:///{db_path_str}'
        
        print(f"Database path: {db_path_str}")
        print(f"Database URL: {db_url}")
        print(f"Database directory exists: {database_dir.exists()}")
        print(f"Database directory writable: {os.access(str(database_dir), os.W_OK)}")
else:
    print(f"Using DATABASE_URL from environment: {db_url[:20]}...")

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
CORS(app)
jwt = JWTManager(app)
db.init_app(app)

# Initialize database (with error handling for serverless)
try:
    with app.app_context():
        init_db()
        # Enable WAL mode for better concurrency (only for SQLite, skip on serverless)
        if db_url and db_url.startswith('sqlite'):
            try:
                engine = db.get_engine()
                with engine.connect() as conn:
                    conn.execute(db.text("PRAGMA journal_mode=WAL"))
                    conn.commit()
                print("[OK] SQLite WAL mode enabled for better concurrency")
            except Exception as e:
                print(f"[WARN] Could not enable WAL mode: {e}")
except Exception as e:
    print(f"[WARN] Database initialization error (may be expected on serverless): {e}")

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(device_bp, url_prefix='/api')
app.register_blueprint(breach_bp, url_prefix='/api')
app.register_blueprint(automation_bp, url_prefix='/api')
app.register_blueprint(wipe_bp, url_prefix='/api')

# Initialize scheduler (skip on serverless/Vercel - schedulers don't work in serverless)
# Check if we're in a serverless environment
is_serverless = os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME') or os.getenv('FUNCTION_NAME')
if not is_serverless:
    try:
        init_scheduler(app)
    except Exception as e:
        print(f"[WARN] Scheduler initialization failed (may be expected): {e}")
else:
    print("[INFO] Skipping scheduler initialization (serverless environment)")

@app.route('/api/health')
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        db_status = 'unknown'
        try:
            with app.app_context():
                db.session.execute(db.text('SELECT 1'))
                db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)[:50]}'
        
        return {
            'status': 'ok',
            'message': 'Anti-Theft System API is running',
            'database': db_status,
            'environment': 'serverless' if os.getenv('VERCEL') else 'local'
        }, 200
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }, 500

if __name__ == '__main__':
    # Disable reloader on Windows to avoid database path issues
    use_reloader = sys.platform != 'win32'
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=use_reloader)

