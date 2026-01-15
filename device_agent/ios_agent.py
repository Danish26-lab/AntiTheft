#!/usr/bin/env python3
"""
iOS Device Agent for Anti-Theft System
Works with Pythonista app or can be run via Shortcuts automation
"""

import json
import time
import requests
import platform
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Configuration
CONFIG_FILE = Path(__file__).parent / 'ios_config.json'
LOG_FILE = Path(__file__).parent / 'ios_agent.log'
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000/api')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

class IOSDeviceAgent:
    def __init__(self):
        self.device_id = None
        self.user_email = None
        self.status = 'active'
        self.load_config()
    
    def load_config(self):
        """Load configuration from ios_config.json"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.device_id = config.get('device_id')
                    self.user_email = config.get('user_email')
                    logging.info(f"Loaded config: device_id={self.device_id}, user={self.user_email}")
            else:
                logging.warning("ios_config.json not found. Please register device first.")
                self.device_id = None
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            self.device_id = None
    
    def get_device_info(self):
        """Get iOS device information"""
        try:
            import platform as pl
            system = pl.system()
            
            # Get device model and iOS version if available
            device_model = "iPhone"
            ios_version = "Unknown"
            
            # Try to get more specific info
            try:
                # On iOS via Pythonista or similar
                import objc_util  # Pythonista specific
                device_info = objc_util.ObjCClass('UIDevice').currentDevice()
                device_model = str(device_info.model())
                ios_version = str(device_info.systemVersion())
            except:
                # Fallback for other Python environments
                try:
                    import subprocess
                    result = subprocess.run(
                        ['sw_vers', '-productVersion'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        ios_version = result.stdout.strip()
                except:
                    pass
            
            hostname = platform.node() if hasattr(platform, 'node') else "iPhone"
            
            return {
                'device_id': f"{hostname}-ios",
                'name': f"{hostname} (iOS {ios_version})",
                'device_type': 'iphone',
                'platform': 'iOS',
                'version': ios_version,
                'model': device_model
            }
        except Exception as e:
            logging.error(f"Error getting device info: {e}")
            return {
                'device_id': 'iphone-ios',
                'name': 'iPhone (iOS)',
                'device_type': 'iphone',
                'platform': 'iOS',
                'version': 'Unknown'
            }
    
    def get_location(self):
        """
        Get device location using multiple methods for iOS:
        1. Try CoreLocation via objc_util (Pythonista)
        2. Try IP geolocation services
        3. Fallback
        """
        # Method 1: Try CoreLocation (Pythonista on iOS)
        try:
            import objc_util
            from CoreLocation import CLLocationManager, kCLLocationAccuracyBest
            
            manager = CLLocationManager()
            
            # Request authorization
            if hasattr(manager, 'requestWhenInUseAuthorization'):
                manager.requestWhenInUseAuthorization()
            
            # Get location with high accuracy
            location = manager.location()
            if location:
                coord = location.coordinate()
                location_data = {
                    "lat": coord.latitude,
                    "lng": coord.longitude
                }
                logging.info(f"Got GPS location from CoreLocation: {location_data}")
                return location_data
        except ImportError:
            logging.debug("CoreLocation not available (not running on iOS/Pythonista)")
        except Exception as e:
            logging.debug(f"CoreLocation failed: {e}")
        
        # Method 2: Try IP geolocation services
        location_services = [
            {
                'url': 'http://ip-api.com/json/',
                'parser': lambda data: {
                    'lat': data.get('lat'),
                    'lng': data.get('lon')
                } if data.get('status') == 'success' else None
            },
            {
                'url': 'https://ipapi.co/json/',
                'parser': lambda data: {
                    'lat': data.get('latitude'),
                    'lng': data.get('longitude')
                } if data.get('latitude') and data.get('longitude') else None
            },
            {
                'url': 'https://get.geojs.io/v1/ip/geo.json',
                'parser': lambda data: {
                    'lat': float(data.get('latitude', 0)),
                    'lng': float(data.get('longitude', 0))
                } if data.get('latitude') and data.get('longitude') else None
            }
        ]
        
        try:
            for service in location_services:
                try:
                    response = requests.get(service['url'], timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        location = service['parser'](data)
                        if location and location.get('lat') and location.get('lng'):
                            logging.info(f"Got location from IP service: {location}")
                            return location
                except Exception as service_error:
                    logging.debug(f"Service {service['url']} failed: {service_error}")
                    continue
        except Exception as e:
            logging.error(f"Error getting location: {e}")
        
        return None
    
    def check_for_commands(self):
        """Check for remote commands from server"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/get_device_status/{self.device_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                device_data = response.json()
                status = device_data.get('status', 'active')
                
                # Check WiFi geofence if enabled
                geofence_enabled = device_data.get('geofence_enabled', False)
                geofence_type = device_data.get('geofence_type', 'gps')
                geofence_wifi_ssid = device_data.get('geofence_wifi_ssid')
                
                if geofence_enabled and geofence_type == 'wifi' and geofence_wifi_ssid:
                    # Check WiFi connection status
                    try:
                        current_ssid = self.get_wifi_ssid()
                        if not current_ssid or current_ssid != geofence_wifi_ssid:
                            logging.warning(f"⚠️ WiFi GEOFENCE BREACH: Disconnected from required network '{geofence_wifi_ssid}'")
                            self.status = 'alarm'
                            location = self.get_location()
                            if location:
                                requests.post(
                                    f"{API_BASE_URL}/update_location",
                                    json={
                                        'device_id': self.device_id,
                                        'location': {
                                            'lat': location['lat'],
                                            'lng': location['lng']
                                        },
                                        'status': 'alarm'
                                    },
                                    timeout=5
                                )
                    except Exception as e:
                        logging.debug(f"WiFi check failed: {e}")
                
                # Check if status changed (indicating command)
                command = None
                if status != self.status:
                    if status == 'locked' or status == 'lock':
                        command = 'lock'
                    elif status == 'alarm':
                        command = 'alarm'
                    elif status == 'wiped' or status == 'wipe':
                        command = 'wipe'
                
                if command:
                    self.execute_command(command, device_data)
                    self.status = status
                    
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error checking commands: {e}")
        except Exception as e:
            logging.error(f"Error checking commands: {e}")
    
    def get_wifi_ssid(self):
        """Get current WiFi SSID on iOS"""
        try:
            import objc_util
            from Network import nw_path_monitor, nw_path_monitor_set_queue
            
            # iOS WiFi detection via Network framework
            # This is simplified - full implementation would use proper Network framework APIs
            return None  # Placeholder - requires proper iOS API access
        except:
            return None
    
    def execute_command(self, command, device_data=None):
        """Execute remote command"""
        logging.info(f"Executing command: {command}")
        
        if command == 'lock':
            self.execute_lock()
        elif command == 'alarm':
            self.execute_alarm()
        elif command == 'wipe':
            self.execute_wipe()
    
    def execute_lock(self):
        """Lock iOS device screen"""
        logging.info("🔒 Executing LOCK command")
        try:
            # iOS doesn't have a direct way to lock via Python
            # But we can trigger the lock via shortcuts or display a message
            try:
                import objc_util
                from UIKit import UIApplication
                app = UIApplication.sharedApplication()
                # On iOS, we can't directly lock, but we can show an alert
                logging.warning("⚠️ iOS doesn't support programmatic lock. User action required.")
            except:
                logging.warning("⚠️ iOS lock not available in this environment")
        except Exception as e:
            logging.error(f"Error executing lock: {e}")
    
    def execute_alarm(self):
        """Trigger alarm on iOS device"""
        logging.info("🚨 Executing ALARM command")
        try:
            import objc_util
            from UIKit import UILocalNotification, UIApplication
            from datetime import datetime, timedelta
            
            app = UIApplication.sharedApplication()
            notification = UILocalNotification.alloc().init()
            notification.alertBody = "🚨 ALARM! Your device security has been triggered!"
            notification.soundName = "default"
            notification.fireDate = datetime.now()
            app.scheduleLocalNotification(notification)
            
            logging.info("✅ Alarm notification sent")
        except Exception as e:
            logging.warning(f"Alarm notification failed: {e}")
            # Fallback: just log it
            print("🚨🚨🚨 ALARM TRIGGERED! 🚨🚨🚨")
    
    def execute_wipe(self):
        """Wipe device data (iOS doesn't support this programmatically)"""
        logging.warning("⚠️ WIPE command received but iOS doesn't support programmatic data wipe")
        logging.warning("⚠️ This command should be executed manually via Find My iPhone or device settings")
    
    def report_status(self):
        """Report device status and location to server"""
        if not self.device_id:
            logging.error("Device not registered. Please run ios_register_device.py first")
            return False
        
        try:
            location = self.get_location()
            
            if not location:
                logging.warning("Could not get location")
                return False
            
            # Prepare update data
            update_data = {
                'device_id': self.device_id,
                'location': {
                    'lat': location['lat'],
                    'lng': location['lng']
                },
                'status': self.status
            }
            
            # Send location update - use the correct endpoint format
            response = requests.post(
                f"{API_BASE_URL}/update_location",
                json={
                    'device_id': self.device_id,
                    'location': {
                        'lat': location['lat'],
                        'lng': location['lng']
                    },
                    'status': self.status
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logging.info(f"✅ Status reported: Location {location['lat']:.4f}, {location['lng']:.4f}")
                return True
            else:
                logging.error(f"Failed to report status: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error reporting status: {e}")
            return False
        except Exception as e:
            logging.error(f"Error reporting status: {e}")
            return False
    
    def run(self, report_interval=300, check_commands_interval=60):
        """Main loop - continuously report status and check for commands"""
        if not self.device_id:
            logging.error("Device not registered. Please run ios_register_device.py first")
            return
        
        logging.info("🚀 iOS Device Agent started")
        logging.info(f"   Device ID: {self.device_id}")
        logging.info(f"   Report interval: {report_interval}s")
        logging.info(f"   Check commands interval: {check_commands_interval}s")
        
        last_report = 0
        last_check = 0
        
        try:
            while True:
                current_time = time.time()
                
                # Report location periodically
                if current_time - last_report >= report_interval:
                    self.report_status()
                    last_report = current_time
                
                # Check for commands periodically
                if current_time - last_check >= check_commands_interval:
                    self.check_for_commands()
                    last_check = current_time
                
                time.sleep(10)  # Sleep 10 seconds between checks
                
        except KeyboardInterrupt:
            logging.info("Agent stopped by user")
        except Exception as e:
            logging.error(f"Agent error: {e}")

if __name__ == '__main__':
    agent = IOSDeviceAgent()
    agent.run()

