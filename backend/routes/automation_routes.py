from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, AutomationRule, Device
import json

automation_bp = Blueprint('automation', __name__)

@automation_bp.route('/automation_task', methods=['POST'])
@jwt_required()
def create_automation_task():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        if not data or not data.get('rule_type'):
            return jsonify({'error': 'rule_type is required'}), 400
        
        rule = AutomationRule(
            user_id=user_id,
            device_id=data.get('device_id'),
            rule_type=data['rule_type'],
            is_enabled=data.get('is_enabled', True),
            config=json.dumps(data.get('config', {}))
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({
            'message': 'Automation rule created',
            'rule': rule.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@automation_bp.route('/automation_task/<int:rule_id>', methods=['PUT'])
@jwt_required()
def update_automation_task(rule_id):
    try:
        user_id = get_jwt_identity()
        rule = AutomationRule.query.filter_by(id=rule_id, user_id=user_id).first()
        
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
        
        data = request.get_json()
        
        if 'is_enabled' in data:
            rule.is_enabled = data['is_enabled']
        if 'config' in data:
            rule.config = json.dumps(data['config'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Automation rule updated',
            'rule': rule.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@automation_bp.route('/automation_tasks', methods=['GET'])
@jwt_required()
def get_automation_tasks():
    try:
        user_id = get_jwt_identity()
        device_id = request.args.get('device_id')
        
        query = AutomationRule.query.filter_by(user_id=user_id)
        if device_id:
            query = query.filter_by(device_id=device_id)
        
        rules = query.all()
        
        return jsonify({
            'rules': [rule.to_dict() for rule in rules]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@automation_bp.route('/automation_task/<int:rule_id>', methods=['DELETE'])
@jwt_required()
def delete_automation_task(rule_id):
    try:
        user_id = get_jwt_identity()
        rule = AutomationRule.query.filter_by(id=rule_id, user_id=user_id).first()
        
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
        
        db.session.delete(rule)
        db.session.commit()
        
        return jsonify({'message': 'Automation rule deleted'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

