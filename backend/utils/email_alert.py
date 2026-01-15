import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')

def send_alert_email(recipient, subject, body, html_body=None):
    """
    Send alert email using SMTP
    
    Args:
        recipient: Email address of recipient
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body
    """
    try:
        if not SMTP_USER or not SMTP_PASSWORD:
            print(f"[EMAIL] Would send email to {recipient}: {subject}")
            print(f"[EMAIL] Body: {body}")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_USER
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Add plain text part
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)
        
        # Add HTML part if provided
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"[EMAIL] Alert sent to {recipient}: {subject}")
        return True
        
    except Exception as e:
        print(f"[EMAIL] Error sending email: {e}")
        return False

def send_device_alert(recipient, device_name, action, location=None):
    """Send device alert email"""
    subject = f"⚠️ Alert: Action Triggered on Your Device - {device_name}"
    
    body = f"""Your device "{device_name}" has had the following action triggered:
    
Action: {action.upper()}
Time: {datetime.now().strftime('%d-%b-%Y %H:%M')}
"""
    
    if location:
        body += f"Location: {location.get('lat')}, {location.get('lng')}\n"
    
    body += "\nIf this was not you, please secure your account immediately."
    
    return send_alert_email(recipient, subject, body)

def send_geofence_alert(recipient, device_name, location):
    """Send geofence breach alert"""
    breach_type = location.get('breach_type', 'Geofence')
    
    if breach_type == 'WiFi Geofence':
        signal_strength = location.get('signal_strength')
        signal_threshold = location.get('signal_threshold', 30)
        reason = location.get('reason', 'WiFi geofence breach detected')
        
        subject = f"🚨 URGENT: Device {device_name} Stolen or Moved Out of WiFi Range!"
        body = f"""🚨 ALARM TRIGGERED: Your device "{device_name}" has triggered the WiFi geofence alarm!

Reason: {reason}

This could indicate:
- Device has been stolen
- Device has been moved out of WiFi range
- WiFi signal has weakened significantly
- Unauthorized access

Required WiFi Network: {location.get('required_ssid', 'Unknown')}
Current WiFi Status: {location.get('current_ssid', 'DISCONNECTED')}"""
        
        if signal_strength is not None:
            body += f"""
WiFi Signal Strength: {signal_strength}% (Threshold: {signal_threshold}%)"""
        
        body += f"""
Current Location: {location.get('lat')}, {location.get('lng')}
Time: {datetime.now().strftime('%d-%b-%Y %H:%M:%S')}

⚠️ ACTION REQUIRED:
1. Check if you moved the device yourself
2. If not, your device may have been stolen
3. Open your Smart Anti-Theft dashboard to track and secure the device:
   {FRONTEND_BASE_URL}
4. From the dashboard, select the device and use the Screen lock action to immediately lock the screen
5. Optionally trigger the remote alarm or wipe actions if necessary

If this was not you, please secure your account immediately!
"""
    else:
        subject = f"🚨 Geofence Alert: Device {device_name} Left Safe Zone"
        body = f"""Your device "{device_name}" has left the designated safe zone.

Current Location: {location.get('lat')}, {location.get('lng')}
Time: {datetime.now().strftime('%d-%b-%Y %H:%M')}

Please verify this is expected activity.
"""
    
    return send_alert_email(recipient, subject, body)

def send_missing_device_alert(recipient, device_name):
    """Send missing device alert"""
    subject = f"🔴 Missing Device Alert: {device_name}"
    
    body = f"""Your device "{device_name}" has been marked as missing.

Time: {datetime.now().strftime('%d-%b-%Y %H:%M')}

The device will attempt to capture screenshots and report its location.
Please take immediate action if this device was stolen.
"""
    
    return send_alert_email(recipient, subject, body)

def send_breach_alert(recipient, breach_count, breaches):
    """Send breach detection alert"""
    subject = f"⚠️ Security Alert: {breach_count} Breach(es) Detected"
    
    body = f"""Security Breach Detection Report

We detected {breach_count} breach(es) associated with your account:

"""
    
    for breach in breaches[:5]:  # Show first 5
        body += f"- {breach.get('breach_name')} ({breach.get('severity')} severity)\n"
    
    if len(breaches) > 5:
        body += f"\n... and {len(breaches) - 5} more breach(es)\n"
    
    body += f"\nDate: {datetime.now().strftime('%d-%b-%Y %H:%M')}\n"
    body += "\nPlease change your passwords and enable two-factor authentication."
    
    return send_alert_email(recipient, subject, body)

def send_weekly_summary(recipient, stats):
    """Send weekly security summary"""
    subject = "📊 Weekly Security Summary - Anti-Theft System"
    
    body = f"""Weekly Security Summary

Date: {datetime.now().strftime('%d-%b-%Y')}

Statistics:
- Total Devices: {stats.get('total_devices', 0)}
- Missing Devices: {stats.get('missing_devices', 0)}
- Active Devices: {stats.get('active_devices', 0)}
- Breach Alerts: {stats.get('breach_alerts', 0)}
- Actions Triggered: {stats.get('actions_triggered', 0)}

Please review your device security status.
"""
    
    return send_alert_email(recipient, subject, body)

