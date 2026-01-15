"""
Remote Data Wipe API Routes
Handles approved folder management and wipe operations.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Device, ApprovedFolder, WipeOperation, ActivityLog, User
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import threading
import time

# In-memory store for file browse requests/results (simple cache)
# In production, use Redis or database
_browse_requests = {}
_browse_lock = threading.Lock()

wipe_bp = Blueprint('wipe', __name__)

# System-critical paths that must never be wiped
BLOCKED_PATHS = [
    'C:\\Windows',
    'C:\\Program Files',
    'C:\\ProgramData',
    'C:\\Program Files (x86)',
    'D:\\Windows',
    'D:\\Program Files',
    'D:\\Program Files (x86)',
    'D:\\System Volume Information',
    '/System',
    '/Library',
    '/usr',
    '/bin',
    '/sbin',
    '/etc'
]

# Root path for file browser (only D:\ allowed)
FILE_BROWSER_ROOT = 'D:\\'

def is_path_blocked(folder_path):
    """Check if a folder path is in the blocked list"""
    folder_path_normalized = folder_path.replace('/', '\\').upper()
    for blocked in BLOCKED_PATHS:
        blocked_normalized = blocked.replace('/', '\\').upper()
        if folder_path_normalized.startswith(blocked_normalized):
            return True
    return False

def is_path_valid(path):
    """Validate that path is within allowed root (D:\\) and not blocked"""
    path_normalized = path.replace('/', '\\')
    # Must start with D:\
    if not path_normalized.upper().startswith('D:\\'):
        return False
    # Must not be blocked
    if is_path_blocked(path_normalized):
        return False
    return True

@wipe_bp.route('/v1/wipe/browse/<device_id>', methods=['GET'])
@jwt_required()
def browse_files(device_id):
    """
    Get file listing result (cached). Frontend polls this after requesting browse.
    """
    try:
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        # Verify device ownership
        device = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Get path parameter, default to D:\
        path = request.args.get('path', FILE_BROWSER_ROOT)
        path = path.replace('/', '\\')
        
        # Validate path
        if not is_path_valid(path):
            return jsonify({'error': 'Invalid path. Must be within D:\\ and not a system directory.'}), 400
        
        # Check cache for result
        cache_key = f"{device_id}:{path}"
        with _browse_lock:
            if cache_key in _browse_requests:
                result = _browse_requests[cache_key]
                # Check if result is recent (within 30 seconds)
                if result.get('type') == 'result' and time.time() - result.get('timestamp', 0) < 30:
                    return jsonify(result.get('data', {})), 200
        
        # No cached result, return pending
        return jsonify({
            'path': path,
            'items': [],
            'pending': True,
            'message': 'Requesting file list from device...'
        }), 200
        
    except Exception as e:
        logging.error(f"Error browsing files: {e}")
        return jsonify({'error': str(e)}), 500


@wipe_bp.route('/v1/wipe/browse_request/<device_id>', methods=['GET'])
def get_browse_request(device_id):
    """
    Device agent polls this to get pending file browse requests.
    """
    try:
        device = Device.query.filter_by(device_id=device_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Find pending browse requests for this device
        with _browse_lock:
            pending_requests = []
            current_time = time.time()
            for key, value in list(_browse_requests.items()):
                if key.startswith(f"{device_id}:"):
                    # Check if it's a request (not a result) or expired result
                    if value.get('type') == 'request' or (value.get('type') == 'result' and current_time - value.get('timestamp', 0) > 30):
                        if value.get('type') == 'result':
                            # Remove expired results
                            del _browse_requests[key]
                        else:
                            pending_requests.append({
                                'path': value.get('path'),
                                'request_id': key
                            })
            
            if pending_requests:
                # Return first pending request
                req = pending_requests[0]
                return jsonify({
                    'has_request': True,
                    'path': req['path'],
                    'request_id': req['request_id']
                }), 200
        
        return jsonify({'has_request': False}), 200
        
    except Exception as e:
        logging.error(f"Error getting browse request: {e}")
        return jsonify({'error': str(e)}), 500

@wipe_bp.route('/v1/wipe/browse_result', methods=['POST'])
def receive_browse_result():
    """
    Device agent calls this to submit file listing results.
    """
    try:
        data = request.get_json() or {}
        device_id = data.get('device_id')
        path = data.get('path', FILE_BROWSER_ROOT)
        items = data.get('items', [])
        error = data.get('error')
        request_id = data.get('request_id')
        
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        # Find device
        device = Device.query.filter_by(device_id=device_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Store result in cache
        cache_key = request_id or f"{device_id}:{path}"
        with _browse_lock:
            _browse_requests[cache_key] = {
                'type': 'result',
                'path': path,
                'items': items,
                'error': error,
                'timestamp': time.time(),
                'data': {
                    'path': path,
                    'items': items,
                    'count': len(items) if items else 0,
                    'error': error
                }
            }
            # Clean up old requests (older than 1 minute)
            current_time = time.time()
            for key in list(_browse_requests.keys()):
                if current_time - _browse_requests[key].get('timestamp', 0) > 60:
                    del _browse_requests[key]
        
        return jsonify({'message': 'Browse result received'}), 200
        
    except Exception as e:
        logging.error(f"Error receiving browse result: {e}")
        return jsonify({'error': str(e)}), 500

@wipe_bp.route('/v1/wipe/request_browse/<device_id>', methods=['POST'])
@jwt_required()
def request_browse(device_id):
    """
    Frontend requests file listing. Creates a browse request for device agent.
    """
    try:
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        # Verify device ownership
        device = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        data = request.get_json() or {}
        path = data.get('path', FILE_BROWSER_ROOT)
        path = path.replace('/', '\\')
        
        # Validate path
        if not is_path_valid(path):
            return jsonify({'error': 'Invalid path. Must be within D:\\ and not a system directory.'}), 400
        
        # Create browse request
        cache_key = f"{device_id}:{path}"
        with _browse_lock:
            _browse_requests[cache_key] = {
                'type': 'request',
                'path': path,
                'timestamp': time.time()
            }
        
        return jsonify({
            'message': 'Browse request created',
            'path': path,
            'request_id': cache_key
        }), 200
        
    except Exception as e:
        logging.error(f"Error requesting browse: {e}")
        return jsonify({'error': str(e)}), 500

@wipe_bp.route('/v1/approved_folders/<device_id>', methods=['GET'])
@jwt_required()
def get_approved_folders(device_id):
    """
    Get list of approved folders for a device.
    Only returns folders that were explicitly approved by the user on the device.
    """
    try:
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        # Verify device ownership
        device = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Get approved folders
        folders = ApprovedFolder.query.filter_by(device_id=device.id).all()
        
        return jsonify({
            'approved_folders': [folder.to_dict() for folder in folders]
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting approved folders: {e}")
        return jsonify({'error': str(e)}), 500

@wipe_bp.route('/v1/approved_folders/<device_id>', methods=['POST'])
def set_approved_folders(device_id):
    """
    Set approved folders for a device (called by device agent).
    This endpoint does NOT require JWT - device authenticates via device_id.
    """
    try:
        data = request.get_json() or {}
        folder_paths = data.get('folders', [])
        
        if not folder_paths:
            return jsonify({'error': 'folders array is required'}), 400
        
        # Find device
        device = Device.query.filter_by(device_id=device_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Validate and filter folders
        valid_folders = []
        for folder_path in folder_paths:
            if not folder_path or not isinstance(folder_path, str):
                continue
            
            # Block system-critical paths
            if is_path_blocked(folder_path):
                logging.warning(f"Blocked system-critical path: {folder_path}")
                continue
            
            # Normalize path
            folder_path = folder_path.strip()
            if folder_path:
                valid_folders.append(folder_path)
        
        # Remove existing approved folders for this device
        ApprovedFolder.query.filter_by(device_id=device.id).delete()
        
        # Add new approved folders
        for folder_path in valid_folders:
            folder = ApprovedFolder(
                device_id=device.id,
                folder_path=folder_path
            )
            db.session.add(folder)
        
        db.session.commit()
        
        logging.info(f"Approved folders updated for device {device_id}: {len(valid_folders)} folders")
        
        return jsonify({
            'message': 'Approved folders updated successfully',
            'count': len(valid_folders)
        }), 200
        
    except Exception as e:
        logging.error(f"Error setting approved folders: {e}")
        return jsonify({'error': str(e)}), 500

@wipe_bp.route('/v1/wipe/trigger', methods=['POST'])
@jwt_required()
def trigger_wipe():
    """
    Trigger a remote wipe operation on a device.
    Accepts direct file/folder paths (must be within D:\\).
    """
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        device_id = data.get('device_id')
        paths_to_wipe = data.get('paths', [])  # Array of file/folder paths
        
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        if not paths_to_wipe or not isinstance(paths_to_wipe, list) or len(paths_to_wipe) == 0:
            return jsonify({'error': 'paths array is required and must not be empty'}), 400
        
        # Verify device ownership
        device = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Validate all paths
        invalid_paths = []
        for path in paths_to_wipe:
            path_normalized = path.replace('/', '\\')
            if not is_path_valid(path_normalized):
                invalid_paths.append(path)
        
        if invalid_paths:
            return jsonify({
                'error': 'Some paths are invalid',
                'invalid_paths': invalid_paths,
                'message': 'All paths must start with D:\\ and not be system directories'
            }), 400
        
        # Normalize all paths
        wipe_paths = [p.replace('/', '\\') for p in paths_to_wipe]
        
        # Check for existing in-progress wipe
        existing_wipe = WipeOperation.query.filter_by(
            device_id=device.id,
            status='in_progress'
        ).first()
        
        if existing_wipe:
            return jsonify({
                'error': 'A wipe operation is already in progress',
                'operation_id': existing_wipe.id
            }), 400
        
        # Create wipe operation
        wipe_op = WipeOperation(
            device_id=device.id,
            user_id=user_id,
            folders_to_wipe=json.dumps(wipe_paths),
            status='pending'
        )
        db.session.add(wipe_op)
        
        # Update device status
        device.status = 'wiping'
        
        # Log wipe trigger with full audit trail
        paths_preview = ", ".join(wipe_paths[:3])
        if len(wipe_paths) > 3:
            paths_preview += f" ... (+{len(wipe_paths) - 3} more)"
        
        log = ActivityLog(
            device_id=device.id,
            action='wipe_triggered',
            description=f'Custom wipe triggered for {len(wipe_paths)} item(s): {paths_preview}'
        )
        db.session.add(log)
        
        db.session.commit()
        
        logging.info(f"Wipe operation triggered for device {device_id}: {len(wipe_paths)} paths")
        
        return jsonify({
            'message': 'Wipe operation triggered',
            'operation_id': wipe_op.id,
            'paths_count': len(wipe_paths),
            'paths': wipe_paths
        }), 200
        
    except Exception as e:
        logging.error(f"Error triggering wipe: {e}")
        return jsonify({'error': str(e)}), 500

@wipe_bp.route('/v1/wipe/status/<device_id>', methods=['GET'])
@jwt_required()
def get_wipe_status(device_id):
    """
    Get the status of the latest wipe operation for a device.
    """
    try:
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        # Verify device ownership
        device = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Get latest wipe operation
        wipe_op = WipeOperation.query.filter_by(device_id=device.id).order_by(
            WipeOperation.created_at.desc()
        ).first()
        
        if not wipe_op:
            return jsonify({
                'has_operation': False
            }), 200
        
        return jsonify({
            'has_operation': True,
            'operation': wipe_op.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting wipe status: {e}")
        return jsonify({'error': str(e)}), 500

@wipe_bp.route('/v1/wipe/update_status', methods=['POST'])
def update_wipe_status():
    """
    Update wipe operation status (called by device agent).
    This endpoint does NOT require JWT - device authenticates via device_id.
    """
    try:
        data = request.get_json() or {}
        device_id = data.get('device_id')
        operation_id = data.get('operation_id')
        status = data.get('status')  # pending, in_progress, completed, failed
        progress_percentage = data.get('progress_percentage', 0)
        files_deleted = data.get('files_deleted', 0)
        total_files = data.get('total_files', 0)
        error_message = data.get('error_message')
        
        if not device_id or not operation_id or not status:
            return jsonify({'error': 'device_id, operation_id, and status are required'}), 400
        
        # Find device
        device = Device.query.filter_by(device_id=device_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Find wipe operation
        wipe_op = WipeOperation.query.filter_by(id=operation_id, device_id=device.id).first()
        if not wipe_op:
            return jsonify({'error': 'Wipe operation not found'}), 404
        
        # Update status
        old_status = wipe_op.status
        wipe_op.status = status
        wipe_op.progress_percentage = max(0, min(100, progress_percentage))
        wipe_op.files_deleted = files_deleted
        wipe_op.total_files = total_files
        
        if error_message:
            wipe_op.error_message = error_message
        
        if status == 'in_progress' and not wipe_op.started_at:
            wipe_op.started_at = datetime.utcnow()
        
        if status in ('completed', 'failed'):
            wipe_op.completed_at = datetime.utcnow()
            # Update device status back to active
            if device.status == 'wiping':
                device.status = 'active'
        
        # Log status change
        if old_status != status:
            log = ActivityLog(
                device_id=device.id,
                action='wipe_status_update',
                description=f'Wipe operation {status}: {progress_percentage}% complete, {files_deleted}/{total_files} files deleted'
            )
            db.session.add(log)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Wipe status updated',
            'operation': wipe_op.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Error updating wipe status: {e}")
        return jsonify({'error': str(e)}), 500

@wipe_bp.route('/v1/wipe/pending/<device_id>', methods=['GET'])
def get_pending_wipe(device_id):
    """
    Get pending wipe operation for a device (called by device agent).
    This endpoint does NOT require JWT - device authenticates via device_id.
    """
    try:
        device = Device.query.filter_by(device_id=device_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Find pending or in_progress wipe operation
        wipe_op = WipeOperation.query.filter_by(
            device_id=device.id
        ).filter(
            WipeOperation.status.in_(['pending', 'in_progress'])
        ).order_by(WipeOperation.created_at.desc()).first()
        
        if not wipe_op:
            return jsonify({'has_pending': False}), 200
        
        paths = json.loads(wipe_op.folders_to_wipe) if wipe_op.folders_to_wipe else []
        # Support both 'folders' (legacy) and 'paths' keys for compatibility
        folders = paths  # Alias for backward compatibility
        
        return jsonify({
            'has_pending': True,
            'operation_id': wipe_op.id,
            'folders': folders,  # Device agent expects 'folders' key
            'paths': paths,  # Also include 'paths' for clarity
            'status': wipe_op.status
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting pending wipe: {e}")
        return jsonify({'error': str(e)}), 500

