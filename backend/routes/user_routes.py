from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, Device, ActivityLog, DeviceLinkToken
from datetime import datetime, timezone, timedelta
import uuid
import os
import requests
import hashlib

user_bp = Blueprint('user', __name__)

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '913466167374-2t1no6si29f0phe28pef83oaolv836pm.apps.googleusercontent.com')

@user_bp.route('/register_user', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'User already exists'}), 400
        
        # Create new user
        user = User(
            email=data['email'],
            name=data.get('name', data['email'].split('@')[0]),
            is_admin=data.get('is_admin', False)
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()  # Flush to get user.id
        
        # Prey Project-style Device Linking
        # Link existing agent device if device_id or fingerprint_hash is provided
        device_id = data.get('device_id')
        fingerprint_hash = data.get('fingerprint_hash')
        linked_device = None
        
        if device_id:
            # Link by device_id
            device = Device.query.filter_by(device_id=device_id).first()
            if device:
                if device.user_id is not None:
                    return jsonify({'error': f'Device {device_id} is already linked to another user'}), 409
                device.user_id = user.id
                linked_device = device
                logging.info(f"Linked device {device_id} to user {user.email}")
        elif fingerprint_hash:
            # Link by fingerprint_hash
            device = Device.query.filter_by(fingerprint_hash=fingerprint_hash).first()
            if device:
                if device.user_id is not None:
                    return jsonify({'error': 'Device is already linked to another user'}), 409
                device.user_id = user.id
                linked_device = device
                logging.info(f"Linked device {device.device_id} (fingerprint) to user {user.email}")
        
        # Legacy: Automatically register an OS-level device if provided (browser detection - deprecated)
        os_device = data.get('os_device') or data.get('browser_device')
        if os_device and not linked_device:
            try:
                device_id = os_device.get('device_id')
                if device_id:
                    # Use provided device_name or build from OS + device_class + browser
                    device_name = os_device.get('device_name') or 'Unknown Device'

                    # Derive last_ip from payload or from request
                    raw_ip = os_device.get('last_ip')
                    if not raw_ip:
                        # Prefer X-Forwarded-For when behind proxies
                        forwarded_for = request.headers.get('X-Forwarded-For', '')
                        if forwarded_for:
                            raw_ip = forwarded_for.split(',')[0].strip()
                        else:
                            raw_ip = request.remote_addr

                    # Check if this OS device already exists globally
                    existing_device = Device.query.filter_by(device_id=device_id).first()
                    if existing_device and existing_device.user_id != user.id:
                        # Device ID is already bound to a different user; skip creating to avoid conflict
                        print(f"Skipping OS device registration: device_id {device_id} belongs to another user")
                    elif not existing_device:
                        now_utc = datetime.now(timezone.utc)

                        device = Device(
                            device_id=device_id,
                            name=device_name,
                            device_type='os_device',
                            user_id=user.id,
                            status='active',
                            # OS-level fields
                            os_name=os_device.get('os_name'),
                            os_version=os_device.get('os_version'),
                            architecture=os_device.get('architecture'),
                            device_class=os_device.get('device_class'),
                            gpu=os_device.get('gpu'),
                            # Browser fields
                            browser=os_device.get('browser'),
                            browser_name=os_device.get('browser_name'),
                            browser_version=os_device.get('browser_version'),
                            # Environment fields
                            platform=os_device.get('platform'),
                            user_agent=os_device.get('user_agent'),
                            screen_resolution=os_device.get('screen_resolution'),
                            timezone=os_device.get('timezone'),
                            last_ip=raw_ip,
                            is_primary=True,
                            last_seen=now_utc,
                            # Legacy field for backward compatibility
                            os=os_device.get('os') or os_device.get('os_version')
                        )
                        db.session.add(device)
                        db.session.flush()  # Get device.id for activity log
                        
                        # Log device creation
                        log = ActivityLog(
                            device_id=device.id,
                            action='device_registered',
                            description=f'OS device "{device_name}" automatically registered during signup'
                        )
                        db.session.add(log)
                    elif existing_device and existing_device.user_id == user.id:
                        # Update metadata and continue without creating a new row
                        existing_device.device_type = existing_device.device_type or 'os_device'
                        existing_device.os_name = os_device.get('os_name') or existing_device.os_name
                        existing_device.os_version = os_device.get('os_version') or existing_device.os_version
                        existing_device.architecture = os_device.get('architecture') or existing_device.architecture
                        existing_device.device_class = os_device.get('device_class') or existing_device.device_class
                        existing_device.gpu = os_device.get('gpu') or existing_device.gpu
                        existing_device.browser = os_device.get('browser') or existing_device.browser
                        existing_device.browser_name = os_device.get('browser_name') or existing_device.browser_name
                        existing_device.browser_version = os_device.get('browser_version') or existing_device.browser_version
                        existing_device.platform = os_device.get('platform') or existing_device.platform
                        existing_device.user_agent = os_device.get('user_agent') or existing_device.user_agent
                        existing_device.screen_resolution = os_device.get('screen_resolution') or existing_device.screen_resolution
                        existing_device.timezone = os_device.get('timezone') or existing_device.timezone
                        existing_device.last_ip = raw_ip or existing_device.last_ip
                        existing_device.last_seen = datetime.now(timezone.utc)
                        existing_device.os = os_device.get('os') or os_device.get('os_version') or existing_device.os
            except Exception as device_err:
                # Don't fail registration if device creation fails
                print(f"Warning: Could not auto-register OS device: {device_err}")
        
        # Log device linking if device was linked
        if linked_device:
            log = ActivityLog(
                device_id=linked_device.id,
                action='device_linked',
                description=f'Device "{linked_device.name}" linked to user {user.email}'
            )
            db.session.add(log)
        
        db.session.commit()
        
        response_data = {
            'message': 'User registered successfully',
            'user': user.to_dict()
        }
        
        if linked_device:
            response_data['device_linked'] = True
            response_data['device'] = linked_device.to_dict()
            response_data['message'] = 'User registered and device linked successfully'
        else:
            response_data['device_linked'] = False
            response_data['message'] = 'User registered successfully. Start the agent to link your device.'
        
        return jsonify(response_data), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create access token (identity must be string)
        access_token = create_access_token(identity=str(user.id))

        # Prey Project-style Device Linking on Login
        # Link existing agent device if device_id or fingerprint_hash is provided
        device_id = data.get('device_id')
        fingerprint_hash = data.get('fingerprint_hash')
        linked_device = None
        
        if device_id:
            device = Device.query.filter_by(device_id=device_id).first()
            if device:
                if device.user_id is None:
                    # Link unowned device to this user
                    device.user_id = user.id
                    linked_device = device
                    logging.info(f"Linked device {device_id} to user {user.email} on login")
                elif device.user_id == user.id:
                    # Already linked to this user
                    linked_device = device
                else:
                    # Device belongs to another user - skip
                    logging.warning(f"Device {device_id} belongs to another user, skipping link")
        elif fingerprint_hash:
            device = Device.query.filter_by(fingerprint_hash=fingerprint_hash).first()
            if device:
                if device.user_id is None:
                    device.user_id = user.id
                    linked_device = device
                    logging.info(f"Linked device {device.device_id} (fingerprint) to user {user.email} on login")
                elif device.user_id == user.id:
                    linked_device = device
                else:
                    logging.warning(f"Device {device.device_id} belongs to another user, skipping link")
        
        # Log device linking
        if linked_device and linked_device.user_id == user.id:
            try:
                log = ActivityLog(
                    device_id=linked_device.id,
                    action='device_linked',
                    description=f'Device "{linked_device.name}" linked to user {user.email} on login'
                )
                db.session.add(log)
                db.session.commit()
            except:
                pass
        
        # Legacy: Optionally update or auto-register an OS device on login (browser detection - deprecated)
        os_device = data.get('os_device') or data.get('browser_device')
        if os_device and not linked_device:
            try:
                device_id = os_device.get('device_id')
                if device_id:
                    # Determine IP address for this login
                    raw_ip = os_device.get('last_ip')
                    if not raw_ip:
                        forwarded_for = request.headers.get('X-Forwarded-For', '')
                        if forwarded_for:
                            raw_ip = forwarded_for.split(',')[0].strip()
                        else:
                            raw_ip = request.remote_addr

                    device_name = os_device.get('device_name') or 'Unknown Device'
                    now_utc = datetime.now(timezone.utc)

                    # First, check if device_id exists globally and belongs to another user
                    device_global = Device.query.filter_by(device_id=device_id).first()
                    if device_global and device_global.user_id != user.id:
                        # Do not re-use a device_id owned by another user; skip creation
                        print(f"Skipping OS device update/registration: device_id {device_id} belongs to another user")
                        db.session.commit()
                        return jsonify({
                            'access_token': access_token,
                            'user': user.to_dict()
                        }), 200

                    # Try to find an existing OS device for this user/device_id
                    device = Device.query.filter_by(device_id=device_id, user_id=user.id).first()
                    if device:
                        # Update metadata and last seen
                        device.device_type = device.device_type or 'os_device'
                        # Update OS-level fields
                        device.os_name = os_device.get('os_name') or device.os_name
                        device.os_version = os_device.get('os_version') or device.os_version
                        device.architecture = os_device.get('architecture') or device.architecture
                        device.device_class = os_device.get('device_class') or device.device_class
                        device.gpu = os_device.get('gpu') or device.gpu
                        # Update browser fields
                        device.browser = os_device.get('browser') or device.browser
                        device.browser_name = os_device.get('browser_name') or device.browser_name
                        device.browser_version = os_device.get('browser_version') or device.browser_version
                        # Update environment fields
                        device.platform = os_device.get('platform') or device.platform
                        device.user_agent = os_device.get('user_agent') or device.user_agent
                        device.screen_resolution = os_device.get('screen_resolution') or device.screen_resolution
                        device.timezone = os_device.get('timezone') or device.timezone
                        device.last_ip = raw_ip or device.last_ip
                        device.last_seen = now_utc
                        # Legacy field
                        device.os = os_device.get('os') or os_device.get('os_version') or device.os
                    else:
                        # No existing device – auto-register a new OS device
                        # Mark as primary only if user has no other devices yet
                        has_any_device = Device.query.filter_by(user_id=user.id).count() > 0
                        device = Device(
                            device_id=device_id,
                            name=device_name,
                            device_type='os_device',
                            user_id=user.id,
                            status='active',
                            # OS-level fields
                            os_name=os_device.get('os_name'),
                            os_version=os_device.get('os_version'),
                            architecture=os_device.get('architecture'),
                            device_class=os_device.get('device_class'),
                            gpu=os_device.get('gpu'),
                            # Browser fields
                            browser=os_device.get('browser'),
                            browser_name=os_device.get('browser_name'),
                            browser_version=os_device.get('browser_version'),
                            # Environment fields
                            platform=os_device.get('platform'),
                            user_agent=os_device.get('user_agent'),
                            screen_resolution=os_device.get('screen_resolution'),
                            timezone=os_device.get('timezone'),
                            last_ip=raw_ip,
                            is_primary=not has_any_device,
                            last_seen=now_utc,
                            # Legacy field
                            os=os_device.get('os') or os_device.get('os_version')
                        )
                        db.session.add(device)
                        db.session.flush()

                        log = ActivityLog(
                            device_id=device.id,
                            action='device_registered',
                            description=f'OS device "{device_name}" automatically registered during login'
                        )
                        db.session.add(log)

                    db.session.commit()
            except Exception as device_err:
                # Do not block login if device update/registration fails
                print(f"Warning: Could not update/register OS device on login: {device_err}")
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/google_login', methods=['POST'])
def google_login():
    """
    Handle Google OAuth login
    Verifies the Google ID token and creates/updates user account
    """
    try:
        data = request.get_json()
        id_token = data.get('id_token')
        
        if not id_token:
            return jsonify({'error': 'ID token is required'}), 400
        
        # Verify the Google ID token
        try:
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token as google_id_token
            
            # Verify the token
            idinfo = google_id_token.verify_oauth2_token(
                id_token, 
                google_requests.Request(), 
                GOOGLE_CLIENT_ID
            )
            
            # Get user info from Google
            google_email = idinfo.get('email')
            google_name = idinfo.get('name', google_email.split('@')[0])
            google_picture = idinfo.get('picture')
            
            if not google_email:
                return jsonify({'error': 'Email not provided by Google'}), 400
            
            # Check if user exists
            user = User.query.filter_by(email=google_email).first()
            
            if not user:
                # Create new user
                user = User(
                    email=google_email,
                    name=google_name,
                    is_admin=False
                )
                # Set a random password (won't be used for Google login)
                user.set_password(os.urandom(32).hex())
                db.session.add(user)
                db.session.flush()  # Flush to get user.id
                
                # Note: Browser device registration for Google login would need to be done
                # from the frontend after login, as we don't have browser info here
                
                db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=str(user.id))
            
            return jsonify({
                'access_token': access_token,
                'user': user.to_dict()
            }), 200
            
        except ValueError as e:
            # Invalid token
            return jsonify({'error': 'Invalid Google token'}), 401
        except Exception as e:
            return jsonify({'error': f'Google authentication failed: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/admin/register_missing_devices', methods=['POST'])
@jwt_required()
def register_missing_devices():
    """
    Admin endpoint to register browser devices for users without any devices
    This can be called while the server is running
    """
    try:
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        # Check if user is admin
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        registered_devices = []
        skipped_users = []
        
        # Get all users
        users = User.query.all()
        
        for u in users:
            # Check if user has any devices
            device_count = Device.query.filter_by(user_id=u.id).count()
            
            if device_count == 0:
                # Generate browser device ID
                hash_obj = hashlib.md5(f"browser_{u.email}".encode())
                device_id = f"browser-{hash_obj.hexdigest()[:12]}"
                
                # Check if device ID already exists
                existing = Device.query.filter_by(device_id=device_id).first()
                if existing:
                    skipped_users.append({
                        'email': u.email,
                        'reason': 'Device ID already exists'
                    })
                    continue
                
                # Create device name
                device_name = f"{u.name or u.email.split('@')[0]}'s Browser"
                
                # Create browser device
                device = Device(
                    device_id=device_id,
                    name=device_name,
                    device_type='desktop',
                    user_id=u.id,
                    status='active',
                    last_seen=datetime.now(timezone.utc)
                )
                
                db.session.add(device)
                db.session.flush()  # Flush to get device.id
                
                # Log registration
                log = ActivityLog(
                    device_id=device.id,
                    action='device_registered',
                    description=f'Browser device auto-registered for user {u.email}'
                )
                db.session.add(log)
                
                registered_devices.append({
                    'user_email': u.email,
                    'device_id': device_id,
                    'device_name': device_name
                })
        
        db.session.commit()
        
        return jsonify({
            'message': f'Registered {len(registered_devices)} browser device(s)',
            'registered_devices': registered_devices,
            'skipped_users': skipped_users,
            'total_registered': len(registered_devices)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@user_bp.route('/client_info', methods=['GET'])
def client_info():
    """
    Lightweight endpoint to return basic client networking info.
    Currently used by the frontend to:
      - Capture the public IP address for browser-based devices
    """
    try:
        forwarded_for = request.headers.get('X-Forwarded-For', '')
        if forwarded_for:
            ip = forwarded_for.split(',')[0].strip()
        else:
            ip = request.remote_addr

        return jsonify({
            'ip': ip
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

