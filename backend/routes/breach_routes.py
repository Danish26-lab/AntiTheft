from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, BreachReport, User
from datetime import datetime
import requests
import hashlib

breach_bp = Blueprint('breach', __name__)

HAVEIBEENPWNED_API = 'https://api.pwnedpasswords.com/range/'

def check_breach_email(email):
    """Check if email has been breached using HaveIBeenPwned API"""
    try:
        # Use HaveIBeenPwned API v3 (requires API key for full access)
        # For demo purposes, we'll use a simplified version
        url = f'https://haveibeenpwned.com/api/v3/breachedaccount/{email}'
        headers = {'hibp-api-key': ''}  # API key would go here if available
        
        # For demo, return mock data
        # In production, make actual API call with proper authentication
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return []
        else:
            return []
    except Exception as e:
        print(f"Error checking breach: {e}")
        # Return mock data for demo
        return [
            {
                'Name': 'ExampleBreach',
                'Title': 'Example Data Breach',
                'Domain': 'example.com',
                'BreachDate': '2023-01-15',
                'Description': 'Example breach description'
            }
        ]

@breach_bp.route('/detect_breach', methods=['GET'])
@jwt_required()
def detect_breach():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        email = request.args.get('email', user.email)
        
        # Check for breaches
        breaches = check_breach_email(email)
        
        # Save or update breach reports
        for breach in breaches:
            existing = BreachReport.query.filter_by(
                user_id=user_id,
                breach_name=breach.get('Name', 'Unknown')
            ).first()
            
            if not existing:
                # Determine severity based on breach details
                severity = 'medium'
                if 'password' in breach.get('DataClasses', []):
                    severity = 'high'
                if 'credit-card' in breach.get('DataClasses', []):
                    severity = 'critical'
                
                report = BreachReport(
                    user_id=user_id,
                    email=email,
                    breach_name=breach.get('Name', 'Unknown'),
                    severity=severity,
                    description=breach.get('Description', 'No description available'),
                    date_detected=datetime.strptime(breach.get('BreachDate', '2023-01-01'), '%Y-%m-%d') if breach.get('BreachDate') else datetime.utcnow()
                )
                db.session.add(report)
        
        db.session.commit()
        
        # Get all breach reports for user
        reports = BreachReport.query.filter_by(user_id=user_id, is_resolved=False).all()
        
        return jsonify({
            'breaches_detected': len(breaches),
            'reports': [report.to_dict() for report in reports]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@breach_bp.route('/get_breach_reports', methods=['GET'])
@jwt_required()
def get_breach_reports():
    try:
        user_id = get_jwt_identity()
        resolved = request.args.get('resolved', 'false').lower() == 'true'
        
        reports = BreachReport.query.filter_by(
            user_id=user_id,
            is_resolved=resolved
        ).order_by(BreachReport.date_detected.desc()).all()
        
        return jsonify({
            'reports': [report.to_dict() for report in reports]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@breach_bp.route('/mark_breach_resolved', methods=['POST'])
@jwt_required()
def mark_breach_resolved():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        if not data or not data.get('report_id'):
            return jsonify({'error': 'report_id is required'}), 400
        
        report = BreachReport.query.filter_by(id=data['report_id'], user_id=user_id).first()
        if not report:
            return jsonify({'error': 'Breach report not found'}), 404
        
        report.is_resolved = True
        db.session.commit()
        
        return jsonify({
            'message': 'Breach marked as resolved',
            'report': report.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

