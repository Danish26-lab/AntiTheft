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

app = Flask(__name__)

# Disable Flask's instance folder to avoid path conflicts
app.instance_path = None

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Fix database path - use absolute path
db_url = os.getenv('DATABASE_URL')
if not db_url:
    # Get absolute path to database
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
    # On Windows, use forward slashes - SQLAlchemy handles this correctly
    if os.name == 'nt':  # Windows
        # Convert backslashes to forward slashes
        # SQLAlchemy will properly handle spaces in paths with forward slashes
        db_path_normalized = db_path_str.replace('\\', '/')
        # Ensure we have the correct format for absolute Windows paths
        # SQLAlchemy expects sqlite:///C:/path/to/db (3 slashes before the drive letter)
        db_url = f'sqlite:///{db_path_normalized}'
    else:
        # On Unix, use 3 slashes for absolute paths
        db_url = f'sqlite:///{db_path_str}'
    
    print(f"Database path: {db_path_str}")
    print(f"Database URL: {db_url}")
    print(f"Database directory exists: {database_dir.exists()}")
    print(f"Database directory writable: {os.access(str(database_dir), os.W_OK)}")

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
CORS(app)
jwt = JWTManager(app)
db.init_app(app)

# Initialize database
with app.app_context():
    init_db()
    # Enable WAL mode for better concurrency (allows multiple readers/writers)
    try:
        # Get the database engine and enable WAL mode
        engine = db.get_engine()
        with engine.connect() as conn:
            conn.execute(db.text("PRAGMA journal_mode=WAL"))
            conn.commit()
        print("✅ SQLite WAL mode enabled for better concurrency")
    except Exception as e:
        print(f"⚠️  Could not enable WAL mode: {e}")

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(device_bp, url_prefix='/api')
app.register_blueprint(breach_bp, url_prefix='/api')
app.register_blueprint(automation_bp, url_prefix='/api')
app.register_blueprint(wipe_bp, url_prefix='/api')

# Initialize scheduler
init_scheduler(app)

@app.route('/api/health')
def health():
    return {'status': 'ok', 'message': 'Anti-Theft System API is running'}, 200

if __name__ == '__main__':
    # Disable reloader on Windows to avoid database path issues
    use_reloader = sys.platform != 'win32'
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=use_reloader)

