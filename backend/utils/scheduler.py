from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from models import db, Device, BreachReport, User, AutomationRule
from routes.breach_routes import check_breach_email
from utils.email_alert import send_weekly_summary, send_breach_alert, send_geofence_alert
from utils.geofence import is_geofence_breach, check_geofence
import json

scheduler = BackgroundScheduler()

def init_scheduler(app):
    """Initialize background scheduler with tasks"""
    
    @scheduler.scheduled_job(trigger=CronTrigger(hour=0, minute=0), id='daily_status_update')
    def daily_status_update():
        """Check for inactive devices and mark as missing if inactive for > 24 hours"""
        with app.app_context():
            try:
                from datetime import timedelta
                threshold = datetime.utcnow() - timedelta(hours=24)
                
                inactive_devices = Device.query.filter(
                    Device.last_seen < threshold,
                    Device.status != 'missing'
                ).all()
                
                for device in inactive_devices:
                    device.status = 'inactive'
                    db.session.commit()
                    print(f"[SCHEDULER] Marked device {device.device_id} as inactive")
            except Exception as e:
                print(f"[SCHEDULER] Error in daily_status_update: {e}")
    
    @scheduler.scheduled_job(trigger=CronTrigger(day_of_week=6, hour=9, minute=0), id='weekly_breach_check')
    def weekly_breach_check():
        """Run weekly breach detection for all users"""
        with app.app_context():
            try:
                users = User.query.all()
                
                for user in users:
                    breaches = check_breach_email(user.email)
                    
                    if breaches:
                        # Create breach reports
                        for breach in breaches:
                            existing = BreachReport.query.filter_by(
                                user_id=user.id,
                                breach_name=breach.get('Name', 'Unknown')
                            ).first()
                            
                            if not existing:
                                severity = 'medium'
                                if 'password' in breach.get('DataClasses', []):
                                    severity = 'high'
                                if 'credit-card' in breach.get('DataClasses', []):
                                    severity = 'critical'
                                
                                from models import BreachReport
                                report = BreachReport(
                                    user_id=user.id,
                                    email=user.email,
                                    breach_name=breach.get('Name', 'Unknown'),
                                    severity=severity,
                                    description=breach.get('Description', '')
                                )
                                db.session.add(report)
                        
                        db.session.commit()
                        
                        # Send alert
                        reports = BreachReport.query.filter_by(
                            user_id=user.id,
                            is_resolved=False
                        ).all()
                        
                        send_breach_alert(
                            user.email,
                            len(reports),
                            [r.to_dict() for r in reports]
                        )
                        
                        print(f"[SCHEDULER] Breach check completed for {user.email}: {len(breaches)} breaches")
            except Exception as e:
                print(f"[SCHEDULER] Error in weekly_breach_check: {e}")
    
    @scheduler.scheduled_job(trigger=CronTrigger(day_of_week=0, hour=9, minute=0), id='weekly_summary')
    def weekly_summary():
        """Send weekly summary email to all users"""
        with app.app_context():
            try:
                users = User.query.all()
                
                for user in users:
                    devices = Device.query.filter_by(user_id=user.id).all()
                    missing_devices = [d for d in devices if d.is_missing]
                    active_devices = [d for d in devices if d.status == 'active']
                    breach_reports = BreachReport.query.filter_by(
                        user_id=user.id,
                        is_resolved=False
                    ).all()
                    
                    stats = {
                        'total_devices': len(devices),
                        'missing_devices': len(missing_devices),
                        'active_devices': len(active_devices),
                        'breach_alerts': len(breach_reports),
                        'actions_triggered': 0  # Could track this separately
                    }
                    
                    send_weekly_summary(user.email, stats)
                    print(f"[SCHEDULER] Weekly summary sent to {user.email}")
            except Exception as e:
                print(f"[SCHEDULER] Error in weekly_summary: {e}")
    
    @scheduler.scheduled_job(trigger=CronTrigger(minute='*/5'), id='geofence_check')
    def geofence_check():
        """Check geofence rules every 5 minutes"""
        with app.app_context():
            try:
                rules = AutomationRule.query.filter_by(
                    rule_type='geofence',
                    is_enabled=True
                ).all()
                
                for rule in rules:
                    if not rule.device_id:
                        continue
                    
                    device = Device.query.get(rule.device_id)
                    if not device or not device.last_lat or not device.last_lng:
                        continue
                    
                    config = json.loads(rule.config) if rule.config else {}
                    
                    # Check if device breached geofence
                    if is_geofence_breach(
                        device.last_lat,
                        device.last_lng,
                        config,
                        previous_inside=True  # Simplified - could track previous state
                    ):
                        # Send alert
                        send_geofence_alert(
                            device.owner.email,
                            device.name,
                            {'lat': device.last_lat, 'lng': device.last_lng}
                        )
                        print(f"[SCHEDULER] Geofence breach detected for device {device.device_id}")
            except Exception as e:
                print(f"[SCHEDULER] Error in geofence_check: {e}")
    
    scheduler.start()
    print("[SCHEDULER] Background scheduler started")
    return scheduler

