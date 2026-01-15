from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    devices = db.relationship('Device', backref='owner', lazy=True)
    breach_reports = db.relationship('BreachReport', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'is_admin': self.is_admin
        }

class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    fingerprint_hash = db.Column(db.String(64), unique=True, nullable=True, index=True)  # SHA-256 hash for device identification
    name = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(50))  # os_device, agent_device, laptop, phone, tablet, etc.
    # OS-level device metadata (for OS-based devices detected via browser/agent)
    os_name = db.Column(db.String(100))          # e.g. "Windows", "macOS", "Linux"
    os_version = db.Column(db.String(100))        # e.g. "Windows 11", "macOS Sonoma", "Ubuntu 22.04"
    architecture = db.Column(db.String(20))       # e.g. "x64", "arm64", "x86"
    device_class = db.Column(db.String(20))       # e.g. "laptop", "desktop", "mobile", "tablet"
    gpu = db.Column(db.String(200))               # GPU renderer from WebGL / agent
    brand = db.Column(db.String(100))             # e.g. "Acer"
    model_name = db.Column(db.String(150))        # e.g. "Aspire 5"
    cpu_info = db.Column(db.String(200))          # e.g. "Intel i7-1165G7"
    hostname = db.Column(db.String(150))          # OS hostname
    # Browser / environment metadata
    browser = db.Column(db.String(100))           # e.g. "Chrome 121.0"
    browser_name = db.Column(db.String(50))       # e.g. "Chrome"
    browser_version = db.Column(db.String(50))    # e.g. "121.0"
    platform = db.Column(db.String(100))         # navigator.platform
    user_agent = db.Column(db.Text)               # Full user agent string
    screen_resolution = db.Column(db.String(50))  # e.g. "1920x1080"
    timezone = db.Column(db.String(100))          # IANA timezone name
    last_ip = db.Column(db.String(45))           # IPv4 / IPv6 text
    # Legacy field for backward compatibility
    os = db.Column(db.String(100))               # Deprecated: use os_name + os_version
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for unowned devices (agent-first)
    status = db.Column(db.String(20), default='active')  # active, missing, locked, wiped
    last_lat = db.Column(db.Float)
    last_lng = db.Column(db.Float)
    last_location_update = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_primary = db.Column(db.Boolean, default=False)    # Primary device for the user (e.g. first browser)
    is_missing = db.Column(db.Boolean, default=False)
    missing_since = db.Column(db.DateTime)
    battery_percentage = db.Column(db.Integer)  # Battery percentage (0-100)
    # Geofence settings
    geofence_center_lat = db.Column(db.Float)
    geofence_center_lng = db.Column(db.Float)
    geofence_radius_m = db.Column(db.Float, default=200.0)  # Default 200 meters
    geofence_enabled = db.Column(db.Boolean, default=False)
    geofence_type = db.Column(db.String(20), default='gps')  # 'gps' or 'wifi'
    geofence_wifi_ssid = db.Column(db.String(100))  # WiFi SSID for WiFi-based geofencing
    was_inside_geofence = db.Column(db.Boolean, default=True)  # Track previous state
    current_wifi_ssid = db.Column(db.String(100))  # Current WiFi SSID (reported by device)
    connection_key = db.Column(db.String(64), unique=True, index=True)  # Key for device to connect (deprecated - agent-first)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    registered_at = db.Column(db.DateTime)  # When device was first registered (agent-first registration time)
    
    # Prey Project-style Hardware Information (from native agent)
    serial_number = db.Column(db.String(100))  # System serial number
    bios_vendor = db.Column(db.String(100))  # BIOS vendor (e.g., "AMI", "Phoenix", "Apple")
    bios_version = db.Column(db.String(100))  # BIOS version
    motherboard_vendor = db.Column(db.String(100))  # Motherboard manufacturer
    motherboard_model = db.Column(db.String(150))  # Motherboard model
    motherboard_serial = db.Column(db.String(100))  # Motherboard serial number
    cpu_model = db.Column(db.String(200))  # Full CPU model name
    cpu_cores = db.Column(db.Integer)  # Number of CPU cores
    cpu_threads = db.Column(db.Integer)  # Number of CPU threads/logical processors
    cpu_speed_mhz = db.Column(db.Integer)  # CPU speed in MHz
    ram_mb = db.Column(db.Integer)  # Total RAM in MB
    ram_gb = db.Column(db.Float)  # Total RAM in GB (calculated)
    network_interfaces = db.Column(db.Text)  # JSON array of network interfaces
    mac_addresses = db.Column(db.Text)  # JSON array of MAC addresses
    
    activity_logs = db.relationship('ActivityLog', backref='device', lazy=True)
    
    def to_dict(self):
        # Helper to format datetime with UTC timezone indicator
        def format_utc_datetime(dt):
            if dt is None:
                return None
            # Ensure UTC timezone is indicated with 'Z' suffix
            iso_str = dt.isoformat()
            if not iso_str.endswith('Z') and '+' not in iso_str and '-' not in iso_str[-6:]:
                # Add 'Z' to indicate UTC if timezone not present
                return iso_str + 'Z'
            return iso_str
        
        return {
            'id': self.id,
            'device_id': self.device_id,
            'name': self.name,
            'device_type': self.device_type,
            'os_name': self.os_name,
            'os_version': self.os_version,
            'architecture': self.architecture,
            'device_class': self.device_class,
            'gpu': self.gpu,
            'browser': self.browser,
            'browser_name': self.browser_name,
            'browser_version': self.browser_version,
            'platform': self.platform,
            'user_agent': self.user_agent,
            'screen_resolution': self.screen_resolution,
            'timezone': self.timezone,
            'last_ip': self.last_ip,
            'os': self.os,  # Legacy field for backward compatibility
            'user_id': self.user_id,
            'status': self.status,
            'last_lat': self.last_lat,
            'last_lng': self.last_lng,
            'last_location_update': format_utc_datetime(self.last_location_update),
            'last_seen': format_utc_datetime(self.last_seen),
            'is_missing': self.is_missing,
            'missing_since': format_utc_datetime(self.missing_since),
            'geofence_center_lat': self.geofence_center_lat,
            'geofence_center_lng': self.geofence_center_lng,
            'geofence_radius_m': self.geofence_radius_m,
            'geofence_enabled': self.geofence_enabled,
            'geofence_type': self.geofence_type,
            'geofence_wifi_ssid': self.geofence_wifi_ssid,
            'was_inside_geofence': self.was_inside_geofence,
            'current_wifi_ssid': self.current_wifi_ssid,  # Current WiFi SSID from device
            'connection_key': self.connection_key if self.connection_key else None,
            'battery_percentage': self.battery_percentage,  # Battery percentage (0-100)
            'created_at': format_utc_datetime(self.created_at),
            'registered_at': format_utc_datetime(self.registered_at),
            'is_primary': self.is_primary,
            'fingerprint_hash': self.fingerprint_hash,  # For device identification
            # Hardware information (Prey Project style)
            'serial_number': self.serial_number,
            'bios_vendor': self.bios_vendor,
            'bios_version': self.bios_version,
            'motherboard_vendor': self.motherboard_vendor,
            'motherboard_model': self.motherboard_model,
            'motherboard_serial': self.motherboard_serial,
            'cpu_model': self.cpu_model,
            'cpu_cores': self.cpu_cores,
            'cpu_threads': self.cpu_threads,
            'cpu_speed_mhz': self.cpu_speed_mhz,
            'ram_mb': self.ram_mb,
            'ram_gb': self.ram_gb,
            'network_interfaces': json.loads(self.network_interfaces) if self.network_interfaces else None,
            'mac_addresses': json.loads(self.mac_addresses) if self.mac_addresses else None
        }

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # location_update, lock, alarm, wipe, screenshot
    description = db.Column(db.Text)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    screenshot_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        # Format UTC datetime with 'Z' suffix
        def format_utc_datetime(dt):
            if dt is None:
                return None
            iso_str = dt.isoformat()
            if not iso_str.endswith('Z') and '+' not in iso_str and '-' not in iso_str[-6:]:
                return iso_str + 'Z'
            return iso_str
        
        return {
            'id': self.id,
            'device_id': self.device_id,
            'action': self.action,
            'description': self.description,
            'lat': self.lat,
            'lng': self.lng,
            'screenshot_path': self.screenshot_path,
            'created_at': format_utc_datetime(self.created_at)
        }

class BreachReport(db.Model):
    __tablename__ = 'breach_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    breach_name = db.Column(db.String(200), nullable=False)
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    date_detected = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    is_resolved = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        # Format UTC datetime with 'Z' suffix
        def format_utc_datetime(dt):
            if dt is None:
                return None
            iso_str = dt.isoformat()
            if not iso_str.endswith('Z') and '+' not in iso_str and '-' not in iso_str[-6:]:
                return iso_str + 'Z'
            return iso_str
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'breach_name': self.breach_name,
            'severity': self.severity,
            'date_detected': format_utc_datetime(self.date_detected),
            'description': self.description,
            'is_resolved': self.is_resolved
        }

class AutomationRule(db.Model):
    __tablename__ = 'automation_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'))
    rule_type = db.Column(db.String(50), nullable=False)  # geofence, inactivity, breach_check
    is_enabled = db.Column(db.Boolean, default=True)
    config = db.Column(db.Text)  # JSON string for rule configuration
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_id': self.device_id,
            'rule_type': self.rule_type,
            'is_enabled': self.is_enabled,
            'config': self.config,
            'created_at': self.created_at.isoformat()
        }

class ApprovedFolder(db.Model):
    """
    Stores user-approved folders that can be wiped remotely.
    Only folders explicitly approved by the user on the device are eligible.
    """
    __tablename__ = 'approved_folders'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    folder_path = db.Column(db.String(500), nullable=False)  # Full path to approved folder
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    device = db.relationship('Device', backref='approved_folders')
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'folder_path': self.folder_path,
            'created_at': self.created_at.isoformat()
        }

class WipeOperation(db.Model):
    """
    Tracks remote wipe operations with status and progress.
    """
    __tablename__ = 'wipe_operations'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    folders_to_wipe = db.Column(db.Text, nullable=False)  # JSON array of folder paths
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, failed
    progress_percentage = db.Column(db.Integer, default=0)  # 0-100
    files_deleted = db.Column(db.Integer, default=0)
    total_files = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)  # Error details if failed
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    device = db.relationship('Device', backref='wipe_operations')
    user = db.relationship('User', backref='wipe_operations')
    
    def to_dict(self):
        def format_utc_datetime(dt):
            if dt is None:
                return None
            iso_str = dt.isoformat()
            if not iso_str.endswith('Z') and '+' not in iso_str and '-' not in iso_str[-6:]:
                return iso_str + 'Z'
            return iso_str
        
        return {
            'id': self.id,
            'device_id': self.device_id,
            'user_id': self.user_id,
            'folders_to_wipe': self.folders_to_wipe,
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'files_deleted': self.files_deleted,
            'total_files': self.total_files,
            'error_message': self.error_message,
            'started_at': format_utc_datetime(self.started_at),
            'completed_at': format_utc_datetime(self.completed_at),
            'created_at': format_utc_datetime(self.created_at)
        }


class DeviceLinkToken(db.Model):
    """
    Short-lived token that allows a native agent to link a device to a user
    without needing credentials or config edits.
    """
    __tablename__ = 'device_link_tokens'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='device_link_tokens')

def init_db():
    """Initialize database tables"""
    try:
        db.create_all()
    except Exception as e:
        import traceback
        print(f"Error creating database tables: {e}")
        print(f"Database URI: {db.engine.url}")
        traceback.print_exc()
        raise
    
    # Create default admin user if not exists
    admin = User.query.filter_by(email='admin@antitheft.com').first()
    if not admin:
        admin = User(
            email='admin@antitheft.com',
            name='Admin User',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created: admin@antitheft.com / admin123")

