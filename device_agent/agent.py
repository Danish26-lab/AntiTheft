#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Anti-Theft Device Agent
Runs in background and reports device status to the backend server
"""

import json
import time
import requests
import platform
import socket
import logging
import os
import sys
import io
import threading
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from register_device import register_with_token, read_token

# Import hardware detection and fingerprinting
try:
    from hardware_detection import detect_hardware
    HARDWARE_DETECTION_AVAILABLE = True
except ImportError:
    HARDWARE_DETECTION_AVAILABLE = False
    logging.warning("Hardware detection module not available")

try:
    from fingerprint import generate_fingerprint, get_fingerprint_info
    FINGERPRINT_AVAILABLE = True
except ImportError:
    FINGERPRINT_AVAILABLE = False
    logging.warning("Fingerprint module not available")

# Fix Windows console encoding for Unicode support
if sys.platform == 'win32':
    try:
        # Try to set UTF-8 encoding for console
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass  # If it fails, continue anyway

# Import WiFi monitor
try:
    from wifi_monitor import get_wifi_ssid, is_wifi_connected, get_wifi_signal_strength
except ImportError:
    # Fallback if wifi_monitor not available
    def get_wifi_ssid():
        return None
    def is_wifi_connected(required_ssid=None):
        return False, None
    def get_wifi_signal_strength():
        return None, None

# Configuration
CONFIG_FILE = Path(__file__).parent / 'config.json'
LOG_FILE = Path(__file__).parent / 'agent.log'
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000/api')

# Custom logging handler that handles Unicode encoding errors gracefully
class SafeStreamHandler(logging.StreamHandler):
    """Stream handler that safely handles Unicode encoding errors"""
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Replace problematic Unicode characters if encoding fails
            try:
                stream.write(msg + self.terminator)
            except UnicodeEncodeError:
                # Fallback: remove or replace problematic characters
                safe_msg = msg.encode('ascii', errors='replace').decode('ascii')
                stream.write(safe_msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

# Setup logging with safe handlers
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
console_handler = SafeStreamHandler(sys.stdout)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[file_handler, console_handler]
)

class DeviceAgent:
    def __init__(self):
        self.device_id = None
        self.user_email = None
        self.status = 'active'
        self.last_known_location = None  # Store last known accurate location
        self.last_gps_attempt_time = None  # Track when we last tried GPS
        self.gps_failed_count = 0  # Count consecutive GPS failures
        self.lock_executed = False  # Track if lock command was already executed
        self.last_lock_status = None  # Track last lock status to prevent duplicate execution
        self.alarm_running = False  # Track if alarm loop is currently running
        self.alarm_thread = None   # Background alarm thread
        self.local_server = None  # Local HTTP server for browser discovery
        self.local_server_thread = None
        
        # Prey Project-style Agent-First automatic registration on startup
        # Device registers itself BEFORE any user account exists
        self._attempt_auto_registration()
        
        self.load_config()
        
        # Start local HTTP server for browser discovery (device linking)
        self._start_local_server()
        
        # CRITICAL: Clear any cached wrong location on startup
        # This ensures we always try GPS first, not cached wrong IP geolocation
        self._clear_wrong_cached_location()
        
        # Also clear any cached location that's clearly wrong (Seremban area: 2.67, 101.99)
        # This helps if device moved to Merlimau but cached location is still Seremban
        if self.last_known_location:
            seremban_lat = 2.67
            seremban_lng = 101.99
            distance_from_seremban = self._calculate_distance(
                seremban_lat, seremban_lng,
                self.last_known_location['lat'],
                self.last_known_location['lng']
            )
            # If cached location is in Seremban area (within 5km), clear it to force fresh GPS
            if distance_from_seremban < 5000:
                logging.warning(f"🗑️ Clearing cached Seremban location: {self.last_known_location}")
                logging.warning(f"   Will force fresh GPS location on next check.")
                self.last_known_location = None
                self.gps_failed_count = 0
        
        # Check Windows Location Services on startup
        if platform.system().lower() == 'windows':
            self._check_location_services()
        
    def load_config(self):
        """Load configuration from config.json"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.device_id = config.get('device_id')
                    self.user_email = config.get('user_email')
                    self.google_maps_api_key = config.get('google_maps_api_key')
                    logging.info(f"Loaded config: device_id={self.device_id}, user={self.user_email}")
                    if self.google_maps_api_key:
                        logging.info("✅ Google Maps API key loaded - will use Google Geolocation API as fallback")
                    
                    # Ensure device_id is always set (generate if missing)
                    if not self.device_id:
                        hostname = socket.gethostname()
                        self.device_id = f"{hostname}-{platform.system().lower()}"
                        config['device_id'] = self.device_id
                        with open(CONFIG_FILE, 'w') as f:
                            json.dump(config, f, indent=2)
                        logging.info(f"Generated device_id: {self.device_id}")
            else:
                logging.warning("config.json not found. Creating default config...")
                self.create_default_config()
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """Create default configuration file"""
        hostname = socket.gethostname()
        self.device_id = f"{hostname}-{platform.system().lower()}"
        
        config = {
            "device_id": self.device_id,
            "user_email": "admin@antitheft.com",
            "report_interval": 60,  # 1 minute for real-time tracking
            "check_commands_interval": 60,  # 1 minute
            "google_maps_api_key": None
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        logging.info(f"Created default config: {self.device_id}")
    
    def _attempt_auto_registration(self):
        """
        Prey Project-style Agent-First Registration
        
        Agent registers itself on startup using hardware fingerprint.
        Device is created as UNOWNED and will be linked to user account later.
        This happens BEFORE any user account exists - pure agent-first architecture.
        """
        try:
            # Check if device is already registered (has device_id in config)
            device_registered = False
            if CONFIG_FILE.exists():
                try:
                    with open(CONFIG_FILE, 'r') as f:
                        config = json.load(f)
                    if config.get('device_id'):
                        device_registered = True
                        self.device_id = config['device_id']
                        logging.info(f"[AUTO-REG] Device already registered: {self.device_id}")
                except:
                    pass
            
            if device_registered:
                # Device already registered, just verify it exists on server
                return True
            
            # Device not registered - perform agent-first registration
            if not FINGERPRINT_AVAILABLE:
                logging.error("[AUTO-REG] Fingerprint module not available! Cannot register device.")
                return False
            
            if not HARDWARE_DETECTION_AVAILABLE:
                logging.error("[AUTO-REG] Hardware detection module not available! Cannot register device.")
                return False
            
            logging.info("[AUTO-REG] Starting agent-first registration (Prey Project style)...")
            
            # Generate hardware fingerprint
            fingerprint_hash = generate_fingerprint()
            fingerprint_info = get_fingerprint_info()
            logging.info(f"[AUTO-REG] Fingerprint generated: {fingerprint_hash[:16]}...")
            logging.info(f"[AUTO-REG] Fingerprint quality: UUID={fingerprint_info['has_machine_uuid']}, Serial={fingerprint_info['has_serial']}, MACs={fingerprint_info['mac_count']}")
            
            # Detect full hardware information
            logging.info("[AUTO-REG] Detecting hardware information...")
            hardware_info = detect_hardware()
            os_info = hardware_info.get("os_info", {})
            system_info = hardware_info.get("system_info", {})
            logging.info(f"[AUTO-REG] Hardware detected: {system_info.get('vendor', 'Unknown')} {system_info.get('model', 'Unknown')}")
            
            # Build registration payload
            payload = {
                "fingerprint_hash": fingerprint_hash,
                "agent_version": "1.0.0",
                "os_info": os_info,
                "hardware_info": {
                    "system_info": system_info,
                    "bios_info": hardware_info.get("bios_info", {}),
                    "motherboard_info": hardware_info.get("motherboard_info", {}),
                    "cpu_info": hardware_info.get("cpu_info", {}),
                    "ram_info": hardware_info.get("ram_info", {}),
                    "network_info": hardware_info.get("network_info", {})
                }
            }
            
            # Register with backend (no user account required)
            logging.info("[AUTO-REG] Sending registration request to backend...")
            response = requests.post(
                f"{API_BASE_URL}/agent/register",
                json=payload,
                timeout=15
            )
            
            if response.status_code in (200, 201):
                result = response.json()
                device_id = result.get('device_id')
                user_linked = result.get('user_linked', False)
                
                if device_id:
                    # Save device_id to config
                    try:
                        config = {}
                        if CONFIG_FILE.exists():
                            with open(CONFIG_FILE, 'r') as f:
                                config = json.load(f)
                        config['device_id'] = device_id
                        config['fingerprint_hash'] = fingerprint_hash
                        with open(CONFIG_FILE, 'w') as f:
                            json.dump(config, f, indent=2)
                        logging.info(f"[AUTO-REG] Device registered: {device_id}")
                        logging.info(f"[AUTO-REG] Device status: {'LINKED to user' if user_linked else 'UNOWNED (awaiting user link)'}")
                        self.device_id = device_id
                        return True
                    except Exception as e:
                        logging.error(f"[AUTO-REG] Could not save device_id to config: {e}")
                        return False
                else:
                    logging.error("[AUTO-REG] No device_id in response!")
                    return False
            else:
                error_msg = response.json().get('error', 'Unknown error') if response.content else 'No response'
                logging.error(f"[AUTO-REG] Registration failed: {response.status_code} - {error_msg}")
                return False
                
        except Exception as e:
            logging.error(f"[AUTO-REG] Registration error: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
    
    def _start_local_server(self):
        """Start local HTTP server on localhost for browser to discover device_id"""
        try:
            # Create handler class that has access to agent instance
            agent_instance = self
            
            class LocalDeviceHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    """Handle GET requests from browser"""
                    if self.path == '/device-info' or self.path == '/device-info/':
                        # Return device_id for browser discovery
                        device_id = agent_instance.device_id or 'not-registered'
                        fingerprint_hash = None
                        try:
                            if CONFIG_FILE.exists():
                                with open(CONFIG_FILE, 'r') as f:
                                    config = json.load(f)
                                fingerprint_hash = config.get('fingerprint_hash')
                        except:
                            pass
                        
                        response_data = {
                            'device_id': device_id,
                            'fingerprint_hash': fingerprint_hash,
                            'status': 'registered' if device_id and device_id != 'not-registered' else 'pending'
                        }
                        
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')  # Allow browser access
                        self.end_headers()
                        self.wfile.write(json.dumps(response_data).encode('utf-8'))
                    else:
                        self.send_response(404)
                        self.end_headers()
                
                def log_message(self, format, *args):
                    # Suppress default logging for local server
                    pass
            
            # Try port 9123 (Prey uses 12767, but we'll use a different port)
            LOCAL_PORT = 9123
            try:
                self.local_server = HTTPServer(('127.0.0.1', LOCAL_PORT), LocalDeviceHandler)
                self.local_server_thread = threading.Thread(
                    target=self.local_server.serve_forever,
                    daemon=True,
                    name="LocalDeviceServer"
                )
                self.local_server_thread.start()
                logging.info(f"[LOCAL-SERVER] Started local discovery server on http://127.0.0.1:{LOCAL_PORT}/device-info")
            except OSError as e:
                # Port might be in use
                logging.warning(f"[LOCAL-SERVER] Could not start local server on port {LOCAL_PORT}: {e}")
        except Exception as e:
            logging.warning(f"[LOCAL-SERVER] Error starting local server: {e}")
    
    def register_with_server(self):
        """
        Prey Project-style registration with comprehensive hardware detection.
        Uses native OS commands to detect real hardware information.
        """
        try:
            if not self.user_email:
                logging.warning("No user_email in config.json – skipping device auto-registration")
                return

            # Detect hardware information using native OS commands
            hardware_info = None
            if HARDWARE_DETECTION_AVAILABLE:
                try:
                    logging.info("🔍 Detecting hardware information (Prey Project style)...")
                    hardware_info = detect_hardware()
                    logging.info(f"✅ Hardware detected: {hardware_info.get('system_info', {}).get('vendor', 'Unknown')} {hardware_info.get('system_info', {}).get('model', 'Unknown')}")
                    
                    # Keep existing device_id from config to avoid creating duplicate devices
                    # The hardware detection may return a UUID, but we want to update the existing device
                    # So we use the device_id from config.json and just update the hardware info
                    logging.info(f"📝 Using existing device_id: {self.device_id} (hardware info will update existing device)")
                except Exception as e:
                    logging.error(f"⚠️ Hardware detection failed: {e}")
                    logging.warning("   Continuing with basic registration...")
                    hardware_info = None
            
            # Build registration payload
            if hardware_info:
                # Use Prey Project-style endpoint with full hardware info
                payload = {
                    "device_id": self.device_id,
                    "user_email": self.user_email,
                    "os_info": hardware_info.get("os_info", {}),
                    "system_info": hardware_info.get("system_info", {}),
                    "bios_info": hardware_info.get("bios_info", {}),
                    "motherboard_info": hardware_info.get("motherboard_info", {}),
                    "cpu_info": hardware_info.get("cpu_info", {}),
                    "ram_info": hardware_info.get("ram_info", {}),
                    "network_info": hardware_info.get("network_info", {})
                }
                endpoint = f"{API_BASE_URL}/devices/agent/register"
                logging.info(f"🚀 Registering device with full hardware info via native agent endpoint...")
            else:
                # Fallback to basic registration
                payload = {
                    "device_id": self.device_id,
                    "user_email": self.user_email,
                    "device_type": platform.system().lower(),
                    "name": f"{socket.gethostname()} ({platform.system()})"
                }
                endpoint = f"{API_BASE_URL}/agent_register_device"
                logging.info(f"📝 Registering device with basic info (hardware detection unavailable)...")

            response = requests.post(
                endpoint,
                json=payload,
                timeout=15
            )

            if response.status_code in (200, 201):
                logging.info(f"Device registration successful: {response.json().get('message')}")
            elif response.status_code == 404:
                error_msg = response.json().get('error', 'Unknown error')
                logging.warning(f"⚠️ Device registration failed: User '{self.user_email}' not found!")
                logging.info(f"   🔍 This might mean the email in config.json doesn't match your registered email")
                logging.info(f"   🔄 Checking for automatic config updates...")
                
                # Check for config updates when registration fails
                if self.check_for_config_update():
                    logging.info(f"   ✅ Config was auto-updated! Retrying registration...")
                    # Reload config and try again
                    self.load_config()
                    # Retry registration with hardware info if available
                    if hardware_info:
                        retry_payload = {
                            "device_id": self.device_id,
                            "user_email": self.user_email,
                            "os_info": hardware_info.get("os_info", {}),
                            "system_info": hardware_info.get("system_info", {}),
                            "bios_info": hardware_info.get("bios_info", {}),
                            "motherboard_info": hardware_info.get("motherboard_info", {}),
                            "cpu_info": hardware_info.get("cpu_info", {}),
                            "ram_info": hardware_info.get("ram_info", {}),
                            "network_info": hardware_info.get("network_info", {})
                        }
                        retry_endpoint = f"{API_BASE_URL}/devices/agent/register"
                    else:
                        retry_payload = {
                            "device_id": self.device_id,
                            "user_email": self.user_email,
                            "device_type": platform.system().lower(),
                            "name": f"{socket.gethostname()} ({platform.system()})"
                        }
                        retry_endpoint = f"{API_BASE_URL}/agent_register_device"
                    
                    retry_response = requests.post(
                        retry_endpoint,
                        json=retry_payload,
                        timeout=15
                    )
                    if retry_response.status_code in (200, 201):
                        logging.info(f"✅ Device registration successful after auto-update!")
                    else:
                        logging.error(f"   Still failed after auto-update. Manual setup may be needed.")
                        logging.error(f"   Solution: Update config.json with your registered email:")
                        logging.error(f"   - Run: python update_config_email.py your-email@example.com")
                else:
                    logging.error(f"   No automatic config update found. Manual setup required:")
                    logging.error(f"   - Run: python update_config_email.py your-email@example.com")
                    logging.error(f"   - Or manually edit config.json and set 'user_email' to your registered email")
            else:
                logging.error(f"Device registration failed: {response.status_code} - {response.text}")
        except Exception as e:
            logging.error(f"Error registering device with server: {e}")
    
    def get_location(self):
        """
        Get device location with REAL-TIME GPS priority:
        1. ALWAYS try Windows Location API first (GPS/WiFi triangulation) - multiple attempts with long timeouts
        2. Only if GPS completely fails, try IP geolocation as last resort
        3. NEVER use IP geolocation if it's in KL area (wrong ISP location)
        4. NEVER cache IP geolocation - only cache real GPS locations
        5. Return None if we can't get real location (don't report wrong location)
        """
        # ============================================
        # METHOD 1: Windows Location API (GPS/WiFi) - ALWAYS TRY THIS FIRST
        # ============================================
        if platform.system().lower() == 'windows':
            import subprocess
            import time as time_module
            
            # Always try GPS with extended timeouts to maximize chance of success
            current_time = time_module.time()
            if self.last_gps_attempt_time and (current_time - self.last_gps_attempt_time) < 300:
                # GPS failed recently, use longer timeouts
                timeout_strategies = [
                    (30, "quick"),
                    (60, "medium"),
                    (90, "long")
                ]
            else:
                # Normal operation - use faster timeouts for real-time tracking
                # Start with quick attempts, then escalate if needed
                timeout_strategies = [
                    (15, "quick"),   # Fast first attempt for real-time
                    (30, "medium"),
                    (60, "long"),
                    (90, "extended")
                ]
            
            self.last_gps_attempt_time = current_time
            
            for max_wait, strategy in timeout_strategies:
                try:
                    # Try Windows Runtime Geolocation API first (more modern, better support)
                    ps_script = f"""
                    try {{
                        # Method 1: Try Windows Runtime Geolocation API (Windows 10+)
                        Add-Type -AssemblyName System.Runtime.WindowsRuntime
                        $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? {{ $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation\\`1' }})[0]
                        Function Await($WinRtTask, $ResultType) {{
                            $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
                            $netTask = $asTask.Invoke($null, @($WinRtTask))
                            $netTask.Wait(-1) | Out-Null
                            $netTask.Result
                        }}
                        
                        [Windows.Devices.Geolocation.Geolocator,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
                        $geolocator = New-Object Windows.Devices.Geolocation.Geolocator
                        $geolocator.DesiredAccuracy = [Windows.Devices.Geolocation.PositionAccuracy]::High
                        $geolocator.DesiredAccuracyInMeters = 10
                        
                        $task = $geolocator.GetGeopositionAsync()
                        $geoposition = Await $task ([Windows.Devices.Geolocation.Geoposition])
                        
                        if ($geoposition -and $geoposition.Coordinate) {{
                            $lat = $geoposition.Coordinate.Point.Position.Latitude
                            $lng = $geoposition.Coordinate.Point.Position.Longitude
                            $acc = $geoposition.Coordinate.Accuracy
                            
                            if ($lat -ne 0 -and $lng -ne 0) {{
                                Write-Output "$lat,$lng,$acc"
                                exit 0
                            }}
                        }}
                    }} catch {{
                        Write-Host "Windows Runtime API failed: $_" -ForegroundColor Yellow
                    }}
                    
                    # Method 2: Fallback to old GeoCoordinateWatcher API
                    try {{
                        Add-Type -AssemblyName System.Device -ErrorAction SilentlyContinue
                        if ([System.Device.Location.GeoCoordinateWatcher]::IsSupported) {{
                            $loc = New-Object System.Device.Location.GeoCoordinateWatcher([System.Device.Location.GeoPositionAccuracy]::High)
                            $loc.Start()
                            $maxWait = {max_wait}
                            $waited = 0
                            while ($loc.Status -ne 'Ready' -and $loc.Status -ne 'NoData' -and $waited -lt $maxWait) {{
                                Start-Sleep -Seconds 1
                                $waited++
                                if ($waited % 10 -eq 0) {{
                                    Write-Host "GPS Status: $($loc.Status) (waited $waited seconds)" -ForegroundColor Yellow
                                }}
                            }}
                            $status = $loc.Status
                            if ($status -eq 'Ready' -and -not $loc.Position.Location.IsUnknown) {{
                                $lat = $loc.Position.Location.Latitude
                                $lng = $loc.Position.Location.Longitude
                                $acc = $loc.Position.Location.HorizontalAccuracy
                                # Accept accuracy up to 10000m (10km) - still better than IP geolocation
                                if ($acc -gt 0 -and $acc -lt 10000) {{
                                    Write-Output "$lat,$lng,$acc"
                                    $loc.Stop()
                                    exit 0
                                }}
                            }}
                            $loc.Stop()
                        }}
                    }} catch {{
                        Write-Host "GeoCoordinateWatcher failed: $_" -ForegroundColor Yellow
                    }}
                    
                    Write-Output "UNKNOWN"
                    """
                    result = subprocess.run(
                        ['powershell', '-Command', ps_script],
                        capture_output=True,
                        text=True,
                        timeout=max_wait + 5  # Add 5 seconds buffer
                    )
                    
                    # Log PowerShell output for debugging
                    if result.stdout and result.stdout.strip():
                        logging.debug(f"PowerShell GPS output: {result.stdout.strip()}")
                    if result.stderr and result.stderr.strip():
                        logging.debug(f"PowerShell GPS errors: {result.stderr.strip()}")
                    
                    if result.returncode == 0:
                        output = result.stdout.strip()
                        # Check for error messages in stderr that might indicate permission issues
                        if result.stderr and ("denied" in result.stderr.lower() or "permission" in result.stderr.lower()):
                            logging.warning(f"⚠️ Location permission issue detected: {result.stderr.strip()}")
                            logging.warning("   Windows may need to prompt for location permission")
                            logging.warning("   Try running the agent once and allow location access when prompted")
                        
                        if output and output != "UNKNOWN" and output != "NOT_SUPPORTED":
                            parts = output.split(',')
                            if len(parts) >= 2:
                                location = {
                                    "lat": float(parts[0]),
                                    "lng": float(parts[1])
                                }
                                if len(parts) > 2:
                                    accuracy = float(parts[2])
                                    # Accept GPS locations with accuracy up to 5000m
                                    # WiFi triangulation can be 100-1000m, still much better than IP geolocation
                                    # Accept GPS locations with accuracy up to 10000m (10km)
                                    # This is still much better than IP geolocation which can be 50-100km off
                                    if accuracy > 0 and accuracy < 10000:
                                        if accuracy < 20:  # Less than 20m - excellent GPS
                                            logging.info(f"✅ EXCELLENT GPS location: {location} (accuracy: {accuracy:.1f}m)")
                                        elif accuracy < 50:  # Less than 50m - very good GPS
                                            logging.info(f"✅ HIGH ACCURACY GPS: {location} (accuracy: {accuracy:.1f}m)")
                                        elif accuracy < 100:  # Less than 100m - good GPS
                                            logging.info(f"✅ Good GPS location: {location} (accuracy: {accuracy:.1f}m)")
                                        elif accuracy < 500:  # Less than 500m - acceptable GPS/WiFi
                                            logging.info(f"✅ WiFi triangulation location: {location} (accuracy: {accuracy:.1f}m)")
                                        elif accuracy < 2000:  # Less than 2km - low accuracy but still better than IP
                                            logging.info(f"⚠️ Low accuracy location (better than IP): {location} (accuracy: {accuracy:.1f}m)")
                                        elif accuracy < 5000:  # Less than 5km - very low but acceptable
                                            logging.info(f"⚠️ Very low accuracy location: {location} (accuracy: {accuracy:.1f}m)")
                                        else:  # 5-10km - still better than IP geolocation
                                            logging.info(f"⚠️ Very low accuracy but accepting: {location} (accuracy: {accuracy:.1f}m)")
                                        # Store as last known good location
                                        self.last_known_location = location
                                        self.gps_failed_count = 0  # Reset failure count on success
                                        return location
                                    else:
                                        if strategy != "long":  # Only log warning on last attempt
                                            logging.debug(f"GPS accuracy too poor ({accuracy:.1f}m), trying longer wait...")
                                        continue
                                else:
                                    logging.info(f"Got location from Windows Location API: {location}")
                                    self.last_known_location = location
                                    return location
                        elif output == "NOT_SUPPORTED":
                            logging.warning("❌ Windows Location API not supported")
                            logging.warning("   Even though Location Services is enabled, the API isn't accessible")
                            logging.warning("   This might mean:")
                            logging.warning("   1. PowerShell needs location permission (check Settings > Location > Desktop apps)")
                            logging.warning("   2. The device doesn't have location hardware")
                            logging.warning("   3. Windows needs to be restarted after enabling Location Services")
                            self.gps_failed_count += 1
                            break  # Don't retry if not supported
                except subprocess.TimeoutExpired:
                    self.gps_failed_count += 1
                    if strategy == "extended" or (strategy == "long" and len(timeout_strategies) == 3):
                        logging.warning(f"❌ GPS timed out after {max_wait}s")
                        logging.warning("   Location Services is enabled, but GPS/WiFi location isn't being returned")
                        logging.warning("   Possible reasons:")
                        logging.warning("   1. No GPS signal (try near a window)")
                        logging.warning("   2. WiFi location services need time to triangulate")
                        logging.warning("   3. Windows needs to build location database")
                        logging.warning("   4. Location permission not granted to PowerShell/Python")
                        logging.warning("   💡 Try: Settings > Privacy & Security > Location > Allow desktop apps to access location")
                        logging.warning("   The agent will use Google Geolocation API (WiFi-based) as fallback")
                    elif strategy != "extended":
                        logging.debug(f"GPS attempt ({strategy}) timed out, trying longer wait...")
                    continue
                except Exception as win_error:
                    self.gps_failed_count += 1
                    logging.debug(f"Windows Location API error ({strategy}): {win_error}")
                    if "NOT_SUPPORTED" in str(win_error) or strategy == "extended" or (strategy == "long" and len(timeout_strategies) == 3):
                        break  # Don't retry if not supported or last attempt
                    continue
            
            # GPS failed after all attempts
            if self.gps_failed_count > 0:
                logging.warning(f"❌ GPS failed after {len(timeout_strategies)} attempts")
                logging.warning("⚠️ Will try Google Geolocation API, then IP geolocation as last resort")
        
        # ============================================
        # METHOD 2: Google Geolocation API (WiFi-based, more accurate than IP)
        # ============================================
        # Try Google Geolocation API if we have API key and GPS failed
        if self.google_maps_api_key and platform.system().lower() == 'windows':
            google_location = self._get_google_geolocation()
            if google_location:
                # Get accuracy from the API response (stored in the location dict if available)
                # We need to check accuracy before accepting the location
                # For now, we'll validate it's not in KL area and has reasonable accuracy
                kl_area_lat = 3.14
                kl_area_lng = 101.69
                distance_from_kl = self._calculate_distance(
                    kl_area_lat, kl_area_lng,
                    google_location['lat'], google_location['lng']
                )
                if distance_from_kl >= 20000:  # Not in KL area - good location
                    # Check if we have a last known accurate location to compare
                    if self.last_known_location:
                        # Calculate distance from last known location
                        distance_from_last = self._calculate_distance(
                            self.last_known_location['lat'], self.last_known_location['lng'],
                            google_location['lat'], google_location['lng']
                        )
                        # If Google location is very far from last known (>100km), it's likely wrong
                    # But allow reasonable jumps (device might have moved to Merlimau, etc.)
                        if distance_from_last > 100000:  # Only reject if >100km difference (very unlikely to be real movement)
                            logging.warning(f"⚠️ Google Geolocation API location is {distance_from_last/1000:.1f}km from last known location - likely inaccurate, rejecting")
                            logging.warning(f"   Last known: {self.last_known_location}, Google API: {google_location}")
                            # Don't use this inaccurate location, try to get better one
                            return None
                        elif distance_from_last > 10000:  # 10-100km difference - log but accept (device might have moved)
                            logging.info(f"📍 Device moved {distance_from_last/1000:.1f}km from last known location - accepting new location")
                    
                    logging.info(f"✅✅ Got location from Google Geolocation API: {google_location}")
                    self.last_known_location = google_location
                    return google_location
                else:
                    logging.warning(f"⚠️ Google Geolocation also shows KL area, rejecting...")
        
        # ============================================
        # METHOD 3: IP Geolocation - ONLY AS LAST RESORT
        # ============================================
        # Only try IP geolocation if GPS completely failed
        # But we will REJECT it if it's in KL area (wrong ISP location)
        
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
            # Try each IP service in order
            ip_location = None
            for service in location_services:
                try:
                    response = requests.get(service['url'], timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        location = service['parser'](data)
                        if location and location.get('lat') and location.get('lng'):
                            ip_location = location
                            logging.info(f"Got location from IP service {service['url']}: {ip_location}")
                            break
                except Exception as service_error:
                    logging.debug(f"Service {service['url']} failed: {service_error}")
                    continue
            
            # Process IP location if we got one
            if ip_location:
                # Check if IP location is in KL area (common ISP location issue)
                kl_area_lat = 3.14
                kl_area_lng = 101.69
                distance_from_kl = self._calculate_distance(
                    kl_area_lat, kl_area_lng,
                    ip_location['lat'], ip_location['lng']
                )
                
                # If we have a last known GPS location, prefer it over IP
                if self.last_known_location:
                    # Check if last known is also in KL
                    last_known_dist_kl = self._calculate_distance(
                        kl_area_lat, kl_area_lng,
                        self.last_known_location['lat'],
                        self.last_known_location['lng']
                    )
                    # If last known GPS is NOT in KL, use it (it's more accurate)
                    if last_known_dist_kl >= 20000:
                        distance = self._calculate_distance(
                            self.last_known_location['lat'], self.last_known_location['lng'],
                            ip_location['lat'], ip_location['lng']
                        )
                        if distance > 10000:  # IP location differs by >10km
                            logging.warning(f"⚠️ IP location differs by {distance/1000:.1f}km from GPS. Using cached GPS.")
                            return self.last_known_location
                        else:
                            logging.info(f"⚠️ IP location close to GPS. Using cached GPS (more accurate).")
                            return self.last_known_location
                    # else: last known is also in KL, might be wrong - use fresh IP location
                
                # No cached GPS location, or cached location is also in KL
                # Use IP geolocation as fallback (better than nothing)
                if distance_from_kl < 20000:
                    logging.warning(f"⚠️⚠️ Using IP geolocation (GPS unavailable): {ip_location}")
                    logging.warning(f"   ⚠️ WARNING: This shows ISP location (KL area), may not be your actual device location!")
                    logging.warning(f"   Accuracy: Off by 10-100km (shows ISP location, not device location)")
                    logging.warning(f"   💡 For accurate tracking, enable Windows Location Services:")
                    logging.warning(f"      Settings > Privacy & Security > Location > Turn ON")
                else:
                    logging.warning(f"⚠️ Using IP geolocation (GPS unavailable): {ip_location}")
                    logging.warning(f"   Accuracy may be off by 10-100km")
                    logging.warning(f"   💡 Enable Windows Location Services for accurate tracking")
                
                # Use IP location as fallback - don't cache it (only cache GPS)
                return ip_location
            
            # No IP location available either
            # Use last known GPS location if available
            if self.last_known_location:
                kl_area_lat = 3.14
                kl_area_lng = 101.69
                distance_from_kl = self._calculate_distance(
                    kl_area_lat, kl_area_lng,
                    self.last_known_location['lat'],
                    self.last_known_location['lng']
                )
                if distance_from_kl < 20000:  # Cached location is in KL area
                    logging.warning(f"⚠️ Cached location is in KL area (may be IP geolocation): {self.last_known_location}")
                    logging.warning(f"   Will try to get fresh location, but will use this if GPS fails")
                    # Try GPS one more time, but don't reject cached location completely
                    if platform.system().lower() == 'windows':
                        gps_location = self._force_gps_location()
                        if gps_location:
                            logging.info(f"✅✅ Got GPS after clearing wrong cache: {gps_location}")
                            self.last_known_location = gps_location
                            return gps_location
                    # GPS failed - use cached location anyway (better than nothing)
                    logging.warning(f"⚠️ GPS failed. Using cached location: {self.last_known_location}")
                    return self.last_known_location
                else:
                    logging.info(f"✅ Using last known GPS location: {self.last_known_location}")
                    return self.last_known_location
            
            # No location available at all - this shouldn't happen if IP geolocation worked
            logging.error(f"❌ All location methods failed. Cannot get device location.")
            return None
            
        except Exception as e:
            logging.error(f"Error getting location: {e}")
            # Return last known GPS location if available
            if self.last_known_location:
                logging.info(f"Using last known GPS location after error: {self.last_known_location}")
                return self.last_known_location
            return None
    
    def _force_gps_location(self):
        """Force a GPS location refresh with longer timeout - uses Windows Runtime API"""
        if platform.system().lower() != 'windows':
            return None
        
        import subprocess
        # Try with progressive timeouts: longer timeouts for better GPS success
        timeout_strategies = [(90, "medium"), (150, "long"), (180, "extended")]
        
        for max_wait, strategy in timeout_strategies:
            try:
                logging.info(f"🔄 Forcing GPS location refresh ({strategy} attempt, up to {max_wait}s)...")
                ps_script = f"""
                try {{
                    # Try Windows Runtime Geolocation API (Windows 10+)
                    Add-Type -AssemblyName System.Runtime.WindowsRuntime
                    $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? {{ $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation\\`1' }})[0]
                    Function Await($WinRtTask, $ResultType) {{
                        $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
                        $netTask = $asTask.Invoke($null, @($WinRtTask))
                        $netTask.Wait(-1) | Out-Null
                        $netTask.Result
                    }}
                    
                    [Windows.Devices.Geolocation.Geolocator,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
                    $geolocator = New-Object Windows.Devices.Geolocation.Geolocator
                    $geolocator.DesiredAccuracy = [Windows.Devices.Geolocation.PositionAccuracy]::High
                    $geolocator.DesiredAccuracyInMeters = 10
                    
                    $task = $geolocator.GetGeopositionAsync()
                    $geoposition = Await $task ([Windows.Devices.Geolocation.Geoposition])
                    
                    if ($geoposition -and $geoposition.Coordinate) {{
                        $lat = $geoposition.Coordinate.Point.Position.Latitude
                        $lng = $geoposition.Coordinate.Point.Position.Longitude
                        $acc = $geoposition.Coordinate.Accuracy
                        
                        if ($lat -ne 0 -and $lng -ne 0) {{
                            Write-Output "$lat,$lng,$acc"
                            exit 0
                        }}
                    }}
                }} catch {{
                    Write-Host "Windows Runtime API failed: $_" -ForegroundColor Yellow
                }}
                
                # Fallback to old API
                try {{
                    Add-Type -AssemblyName System.Device -ErrorAction SilentlyContinue
                    if ([System.Device.Location.GeoCoordinateWatcher]::IsSupported) {{
                        $loc = New-Object System.Device.Location.GeoCoordinateWatcher([System.Device.Location.GeoPositionAccuracy]::High)
                        $loc.Stop()
                        Start-Sleep -Seconds 1
                        $loc.Start()
                        $maxWait = {max_wait}
                        $waited = 0
                        while ($loc.Status -ne 'Ready' -and $loc.Status -ne 'NoData' -and $waited -lt $maxWait) {{
                            Start-Sleep -Seconds 1
                            $waited++
                        }}
                        if ($loc.Status -eq 'Ready' -and -not $loc.Position.Location.IsUnknown) {{
                            $lat = $loc.Position.Location.Latitude
                            $lng = $loc.Position.Location.Longitude
                            $acc = $loc.Position.Location.HorizontalAccuracy
                            # Accept accuracy up to 10000m (10km) - still better than IP geolocation
                            if ($acc -gt 0 -and $acc -lt 10000) {{
                                Write-Output "$lat,$lng,$acc"
                                $loc.Stop()
                                exit 0
                            }}
                        }}
                        $loc.Stop()
                    }}
                }} catch {{
                    Write-Host "GeoCoordinateWatcher failed: $_" -ForegroundColor Yellow
                }}
                
                Write-Output "UNKNOWN"
                """
                result = subprocess.run(
                    ['powershell', '-Command', ps_script],
                    capture_output=True,
                    text=True,
                    timeout=max_wait + 5
                )
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if output and output != "UNKNOWN" and output != "NOT_SUPPORTED":
                        parts = output.split(',')
                        if len(parts) >= 2:
                            location = {
                                "lat": float(parts[0]),
                                "lng": float(parts[1])
                            }
                            if len(parts) > 2:
                                accuracy = float(parts[2])
                                logging.info(f"✅ GPS location refresh successful: {location} (accuracy: {accuracy:.1f}m)")
                            else:
                                logging.info(f"✅ GPS location refresh successful: {location}")
                            return location
                        elif output == "NOT_SUPPORTED":
                            logging.warning("Windows Location API not supported")
                            return None
            except subprocess.TimeoutExpired:
                if strategy != "extended":
                    logging.debug(f"GPS refresh ({strategy}) timed out, trying longer...")
                    continue
                else:
                    logging.warning("GPS refresh timed out after all attempts")
            except Exception as e:
                if strategy == "extended":
                    logging.warning(f"GPS refresh failed: {e}")
                else:
                    logging.debug(f"GPS refresh ({strategy}) error: {e}, trying longer...")
                    continue
        
        return None
    
    def _clear_wrong_cached_location(self):
        """Clear any cached location that's in KL area (wrong ISP location)"""
        if self.last_known_location:
            kl_area_lat = 3.14
            kl_area_lng = 101.69
            distance_from_kl = self._calculate_distance(
                kl_area_lat, kl_area_lng,
                self.last_known_location['lat'],
                self.last_known_location['lng']
            )
            if distance_from_kl < 20000:  # Within 20km of KL
                logging.warning(f"🗑️ Clearing cached KL location: {self.last_known_location}")
                logging.warning(f"   This was likely wrong IP geolocation. Will force GPS on next attempt.")
                self.last_known_location = None
                self.gps_failed_count = 0  # Reset GPS failure count
    
    def _check_location_services(self):
        """Check if Windows Location Services is enabled and provide detailed diagnostics"""
        if platform.system().lower() != 'windows':
            return
        
        try:
            import subprocess
            ps_script = """
            # Check registry for location services
            $locationEnabled = (Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location" -Name "Value" -ErrorAction SilentlyContinue)
            $locationValue = if ($locationEnabled) { $locationEnabled.Value } else { "NotSet" }
            
            # Check if Windows Runtime Geolocation is available
            $runtimeAvailable = $false
            try {
                Add-Type -AssemblyName System.Runtime.WindowsRuntime -ErrorAction Stop
                [Windows.Devices.Geolocation.Geolocator,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
                $runtimeAvailable = $true
            } catch {
                $runtimeAvailable = $false
            }
            
            # Check if old API is available
            $oldApiAvailable = $false
            try {
                Add-Type -AssemblyName System.Device -ErrorAction Stop
                $oldApiAvailable = [System.Device.Location.GeoCoordinateWatcher]::IsSupported
            } catch {
                $oldApiAvailable = $false
            }
            
            Write-Output "LocationServices=$locationValue"
            Write-Output "RuntimeAPI=$runtimeAvailable"
            Write-Output "OldAPI=$oldApiAvailable"
            """
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                location_enabled = False
                runtime_available = False
                old_api_available = False
                
                for line in result.stdout.strip().split('\n'):
                    if 'LocationServices=' in line:
                        value = line.split('=')[1].strip()
                        location_enabled = (value == "Allow")
                    elif 'RuntimeAPI=' in line:
                        runtime_available = (line.split('=')[1].strip() == "True")
                    elif 'OldAPI=' in line:
                        old_api_available = (line.split('=')[1].strip() == "True")
                
                if not location_enabled:
                    logging.error("=" * 70)
                    logging.error("❌❌ CRITICAL: Windows Location Services is DISABLED!")
                    logging.error("   This is why GPS is not working!")
                    logging.error("")
                    logging.error("   📍 TO ENABLE LOCATION SERVICES:")
                    logging.error("   1. Press Win+I to open Windows Settings")
                    logging.error("   2. Go to: Privacy & Security > Location")
                    logging.error("   3. Turn ON 'Location services' (toggle at top)")
                    logging.error("   4. Turn ON 'Allow apps to access your location'")
                    logging.error("   5. Turn ON 'Allow desktop apps to access your location'")
                    logging.error("   6. Restart this device agent")
                    logging.error("")
                    logging.error("   Without Location Services, GPS will NEVER work!")
                    logging.error("=" * 70)
                else:
                    logging.info("✅ Windows Location Services is enabled")
                    if runtime_available:
                        logging.info("✅ Windows Runtime Geolocation API is available")
                    if old_api_available:
                        logging.info("✅ Legacy GeoCoordinateWatcher API is available")
                    if not runtime_available and not old_api_available:
                        logging.warning("⚠️ Neither GPS API is available - GPS may not work")
            else:
                logging.warning("Could not check Location Services status")
        except Exception as e:
            logging.warning(f"Could not check Location Services: {e}")
    
    def _get_wifi_access_points(self):
        """Get WiFi access points for Google Geolocation API"""
        if platform.system().lower() != 'windows':
            return []
        
        try:
            import subprocess
            import re
            # Get WiFi networks using netsh
            ps_script = """
            netsh wlan show networks mode=bssid | Out-String
            """
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return []
            
            access_points = []
            output = result.stdout
            current_ssid = None
            current_bssid = None
            current_signal = None
            
            for line in output.split('\n'):
                line = line.strip()
                # SSID line
                if line.startswith('SSID'):
                    match = re.search(r'SSID\s+\d+\s*:\s*(.+)', line)
                    if match:
                        current_ssid = match.group(1).strip()
                # BSSID line
                elif 'BSSID' in line and current_ssid:
                    match = re.search(r'BSSID\s+\d+\s*:\s*([0-9a-fA-F:]+)', line)
                    if match:
                        # Keep colons in MAC address format (Google API requires format: AA:BB:CC:DD:EE:FF)
                        current_bssid = match.group(1).strip().upper()
                # Signal line
                elif 'Signal' in line and '%' in line:
                    match = re.search(r'Signal\s*:\s*(\d+)%', line)
                    if match:
                        current_signal = int(match.group(1))
                        # Convert signal % to RSSI (approximate: 100% = -30, 0% = -100)
                        rssi = -30 - (100 - current_signal) * 0.7
                        
                        # Check if MAC address is valid (17 chars with colons: AA:BB:CC:DD:EE:FF)
                        if current_ssid and current_bssid and len(current_bssid) == 17:
                            access_points.append({
                                'macAddress': current_bssid,
                                'signalStrength': int(rssi),
                                'signalToNoiseRatio': 0  # Not available from netsh
                            })
                            # Reset for next AP
                            current_bssid = None
                            current_signal = None
            
            # Sort by signal strength (strongest first) and limit to 20 APs (Google API limit)
            access_points_sorted = sorted(access_points, key=lambda x: x['signalStrength'], reverse=True)
            result = access_points_sorted[:20]
            
            if result:
                logging.debug(f"Collected {len(result)} WiFi access points for Google Geolocation API")
            else:
                logging.debug("No WiFi access points found for Google Geolocation API")
            
            return result
        except Exception as e:
            logging.debug(f"Error getting WiFi access points: {e}")
            return []
    
    def _get_google_geolocation(self):
        """Get location using Google Geolocation API with WiFi access points"""
        if not self.google_maps_api_key:
            return None
        
        try:
            # Get WiFi access points
            wifi_aps = self._get_wifi_access_points()
            
            if not wifi_aps:
                logging.debug("No WiFi access points found for Google Geolocation API")
                return None
            
            # Prepare request payload
            payload = {
                'wifiAccessPoints': wifi_aps
            }
            
            # Call Google Geolocation API
            url = f'https://www.googleapis.com/geolocation/v1/geolocate?key={self.google_maps_api_key}'
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'location' in data:
                    # Google Geolocation API returns: {"location": {"lat": X, "lng": Y}}
                    # Ensure we're using the correct order (lat, lng)
                    api_lat = data['location'].get('lat')
                    api_lng = data['location'].get('lng')
                    
                    # Validate coordinates are in correct ranges
                    if api_lat is None or api_lng is None:
                        logging.warning("Google Geolocation API returned invalid coordinates")
                        return None
                    
                    # Ensure lat is between -90 and 90, lng is between -180 and 180
                    if not (-90 <= api_lat <= 90) or not (-180 <= api_lng <= 180):
                        logging.warning(f"Google Geolocation API returned out-of-range coordinates: lat={api_lat}, lng={api_lng}")
                        return None
                    
                    location = {
                        'lat': float(api_lat),
                        'lng': float(api_lng)
                    }
                    accuracy = data.get('accuracy', 0)  # in meters
                    
                    # Log number of WiFi APs used for better debugging
                    num_aps = len(wifi_aps) if wifi_aps else 0
                    
                    if accuracy < 100:
                        logging.info(f"✅✅ EXCELLENT Google Geolocation API: {location} (accuracy: {accuracy:.0f}m, {num_aps} WiFi APs)")
                    elif accuracy < 1000:
                        logging.info(f"✅ Good Google Geolocation API: {location} (accuracy: {accuracy:.0f}m, {num_aps} WiFi APs)")
                    elif accuracy < 5000:
                        logging.warning(f"⚠️ Low accuracy Google Geolocation API: {location} (accuracy: {accuracy:.0f}m, {num_aps} WiFi APs)")
                        logging.warning(f"   For better accuracy, enable Windows Location Services (GPS)")
                    else:
                        # REJECT locations with poor accuracy (>5000m) - they're too inaccurate
                        logging.warning(f"❌ REJECTING Google Geolocation API result: {location} (accuracy: {accuracy:.0f}m, {num_aps} WiFi APs)")
                        logging.warning(f"   ⚠️ Accuracy too poor ({accuracy/1000:.1f}km) - location is unreliable!")
                        logging.warning(f"   💡 Enable Windows Location Services (GPS) for accurate tracking:")
                        logging.warning(f"      Settings > Privacy & Security > Location > Turn ON")
                        logging.warning(f"      Then allow PowerShell/Python to access location")
                        return None  # Reject poor accuracy results - don't use this location
                    
                    return location
                else:
                    logging.warning("Google Geolocation API returned no location")
            elif response.status_code == 403:
                logging.warning("⚠️ Google Geolocation API access denied - check API key permissions")
            else:
                logging.warning(f"Google Geolocation API error: {response.status_code} - {response.text}")
        except Exception as e:
            logging.debug(f"Error calling Google Geolocation API: {e}")
        
        return None
    
    def _calculate_distance(self, lat1, lng1, lat2, lng2):
        """
        Calculate distance between two coordinates in meters using Haversine formula
        """
        from math import radians, sin, cos, sqrt, atan2
        R = 6371000  # Earth radius in meters
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lng = radians(lng2 - lng1)
        
        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
    
    def get_battery_percentage(self):
        """Get battery percentage for the device"""
        if platform.system().lower() == 'windows':
            try:
                import subprocess
                # PowerShell command to get battery percentage
                ps_script = """
                $battery = Get-WmiObject -Class Win32_Battery
                if ($battery) {
                    $percentage = $battery.EstimatedChargeRemaining
                    Write-Output $percentage
                } else {
                    Write-Output "N/A"
                }
                """
                result = subprocess.run(
                    ['powershell', '-Command', ps_script],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if output and output != "N/A" and output.isdigit():
                        return int(output)
            except Exception as e:
                logging.debug(f"Error getting battery percentage: {e}")
        # For non-Windows or if battery not available, return None
        return None
    
    def get_device_info(self):
        """Get device system information"""
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }
    
    def report_status(self):
        """
        Report device status to backend with REAL-TIME location.
        Only reports if we have a valid GPS location - never reports wrong IP geolocation.
        """
        try:
            # CRITICAL: If we have a cached location in Seremban area (2.67, 101.99), clear it
            # This ensures we get fresh GPS location if device moved to Merlimau
            if self.last_known_location:
                seremban_lat = 2.67
                seremban_lng = 101.99
                distance_from_seremban = self._calculate_distance(
                    seremban_lat, seremban_lng,
                    self.last_known_location['lat'],
                    self.last_known_location['lng']
                )
                # If cached location is in Seremban area (within 5km), clear it to force fresh GPS
                if distance_from_seremban < 5000:
                    logging.warning(f"🗑️ Clearing cached Seremban location before getting fresh GPS: {self.last_known_location}")
                    logging.warning(f"   Device is in Merlimau, but cached location is Seremban. Forcing fresh GPS check.")
                    self.last_known_location = None
                    self.gps_failed_count = 0
            
            # Get location - this method now handles all validation and GPS priority
            location = self.get_location()
            
            # If get_location() returns None, try one final GPS attempt
            if not location:
                logging.warning("⚠️ Cannot get location from any method. Trying final GPS attempt...")
                # Try one final GPS attempt with maximum timeout
                if platform.system().lower() == 'windows':
                    logging.info("🔄 Attempting one final GPS location attempt with maximum timeout...")
                    gps_location = self._force_gps_location()
                    if gps_location:
                        logging.info(f"✅✅ SUCCESS! Got GPS location on final attempt: {gps_location}")
                        location = gps_location
                        self.last_known_location = gps_location
                        self.gps_failed_count = 0
                    else:
                        # GPS failed - get_location() should have tried IP geolocation already
                        # If it still returned None, all methods failed
                        logging.warning("⚠️ GPS failed. IP geolocation should have been used as fallback.")
                        if not location:
                            logging.error("❌ All location methods failed. Skipping location report.")
                            return False
                else:
                    if not location:
                        return False
            
            # If location is in KL area, warn but still use it (better than no location)
            kl_area_lat = 3.14
            kl_area_lng = 101.69
            distance_from_kl = self._calculate_distance(kl_area_lat, kl_area_lng, location['lat'], location['lng'])
            
            if distance_from_kl < 20000:  # Within 20km of KL
                # Check if we have a last known GPS location that's NOT in KL
                if self.last_known_location:
                    last_known_dist_kl = self._calculate_distance(
                        kl_area_lat, kl_area_lng,
                        self.last_known_location['lat'],
                        self.last_known_location['lng']
                    )
                    if last_known_dist_kl > 20000:  # Last known GPS is NOT in KL
                        # Last GPS was elsewhere - prefer it over KL IP geolocation
                        logging.warning(f"⚠️ Current location shows KL area, but last GPS was elsewhere.")
                        logging.warning(f"   Using last known GPS location: {self.last_known_location}")
                        location = self.last_known_location
                    # else: both are in KL, might be correct or both wrong - use current location
                # else: No cached GPS - use IP geolocation (already warned in get_location)
            
            # At this point, we have a valid location (either GPS or validated IP)
            # Check if device has moved significantly (100m threshold)
            # BUT: If cached location is in Seremban area, always use fresh GPS location
            if self.last_known_location:
                # Check if cached location is in Seremban area
                seremban_lat = 2.67
                seremban_lng = 101.99
                cached_in_seremban = self._calculate_distance(
                    seremban_lat, seremban_lng,
                    self.last_known_location['lat'],
                    self.last_known_location['lng']
                ) < 5000
                
                distance = self._calculate_distance(
                    self.last_known_location['lat'], self.last_known_location['lng'],
                    location['lat'], location['lng']
                )
                
                # If cached location is in Seremban, always use fresh GPS location (device moved to Merlimau)
                if cached_in_seremban:
                    logging.info(f"📍 Cached location is in Seremban, but device is now at: {location}")
                    logging.info(f"   Using fresh GPS location (device moved {distance/1000:.1f}km)")
                    payload = {
                        "device_id": self.device_id,
                        "user": self.user_email,
                        "location": location,  # Always use fresh location when cached is Seremban
                        "status": self.status
                    }
                # For real-time tracking, report location even if device hasn't moved much
                # But use shorter interval for "unchanged" locations
                elif distance < 50:  # Device hasn't moved significantly (reduced from 100m for real-time)
                    logging.debug(f"Device hasn't moved ({distance:.1f}m), using cached location")
                    # Still report but mark location as unchanged
                    payload = {
                        "device_id": self.device_id,
                        "user": self.user_email,
                        "location": self.last_known_location,  # Use cached GPS location
                        "status": self.status,
                        "location_unchanged": True
                    }
                else:
                    # Device moved - report new location
                    logging.info(f"Device moved {distance:.1f}m, updating location")
                    payload = {
                        "device_id": self.device_id,
                        "user": self.user_email,
                        "location": location,
                        "status": self.status
                    }
            else:
                # First time getting location - always report it
                payload = {
                    "device_id": self.device_id,
                    "user": self.user_email,
                    "location": location,
                    "status": self.status
                }
            
            # Add current WiFi SSID to all payloads
            current_wifi_ssid = get_wifi_ssid()
            if current_wifi_ssid:
                payload["current_wifi_ssid"] = current_wifi_ssid
            
            # Add battery percentage if available
            battery_percentage = self.get_battery_percentage()
            if battery_percentage is not None:
                payload["battery_percentage"] = battery_percentage
            
            response = requests.post(
                f"{API_BASE_URL}/update_location",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                # Only cache GPS locations - never cache IP geolocation
                # GPS locations are already cached in get_location(), but update here if needed
                if 'location_unchanged' not in payload:
                    # Only cache if location is NOT in KL area (GPS location)
                    kl_area_lat = 3.14
                    kl_area_lng = 101.69
                    distance_from_kl = self._calculate_distance(kl_area_lat, kl_area_lng, location['lat'], location['lng'])
                    if distance_from_kl >= 20000:  # Not in KL area - this is GPS
                        self.last_known_location = location
                    # else: IP geolocation in KL area - don't cache it
                logging.info(f"✅ Status reported successfully: {location}")
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
    
    def check_for_config_update(self):
        """Check for pending configuration updates and apply them automatically"""
        try:
            # Make sure device_id is set
            if not self.device_id:
                logging.warning("Cannot check for config update: device_id not set")
                return False
                
            response = requests.get(
                f"{API_BASE_URL}/check_config_update/{self.device_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('has_update') and data.get('user_email'):
                    new_email = data.get('user_email')
                    # Only update if email is different
                    if new_email != self.user_email:
                        is_suggested = data.get('suggested', False)
                        if is_suggested:
                            logging.info(f"🔄 Auto-setup detected: Found recently registered user {new_email}")
                            logging.info(f"   Current config email: {self.user_email}")
                            logging.info(f"   Attempting automatic configuration update...")
                        else:
                            logging.info(f"🔄 Auto-updating config: {self.user_email} -> {new_email}")
                        
                        if self.update_config_email(new_email):
                            # Reload config to get new email
                            self.load_config()
                            logging.info(f"✅ Config auto-updated successfully!")
                            # If this was a suggested update, try registering immediately
                            if is_suggested:
                                logging.info(f"   Attempting automatic device registration...")
                                # Give it a moment for config to be saved
                                time.sleep(0.5)
                                self.register_with_server()
                            return True
                elif data.get('has_update') == False:
                    logging.debug(f"No config updates available for device {self.device_id}")
            else:
                logging.debug(f"Config update check returned status {response.status_code}")
            return False
        except requests.exceptions.RequestException as e:
            logging.debug(f"Network error checking for config update: {e}")
            return False
        except Exception as e:
            logging.error(f"Error checking for config update: {e}")
            return False
    
    def update_config_email(self, new_email):
        """Update user_email in config.json"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
            else:
                # Create default config if it doesn't exist
                hostname = socket.gethostname()
                self.device_id = f"{hostname}-{platform.system().lower()}"
                config = {
                    "device_id": self.device_id,
                    "user_email": new_email,
                    "report_interval": 300,
                    "check_commands_interval": 0.2
                }
            
            # Update email
            old_email = config.get('user_email', 'not set')
            config['user_email'] = new_email
            
            # Save config
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            
            logging.info(f"Config updated: {old_email} -> {new_email}")
            return True
        except Exception as e:
            logging.error(f"Error updating config: {e}")
            return False

    def check_for_commands(self):
        """Check for remote commands from server and WiFi geofence"""
        try:
            # Check by getting device status
            response = requests.get(
                f"{API_BASE_URL}/get_device_status/{self.device_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                device_data = response.json()
                status = device_data.get('status', 'active')
                
                # Log status check for debugging
                if status != self.status:
                    logging.info(f"📡 Status check: Current={self.status}, Server={status}")
                
                # Check WiFi geofence if enabled
                geofence_enabled = device_data.get('geofence_enabled', False)
                geofence_type = device_data.get('geofence_type', 'gps')
                geofence_wifi_ssid = device_data.get('geofence_wifi_ssid')
                
                if geofence_enabled and geofence_type == 'wifi' and geofence_wifi_ssid:
                    # Check WiFi connection status and signal strength
                    current_ssid = get_wifi_ssid()
                    is_connected, _ = is_wifi_connected(geofence_wifi_ssid)
                    signal_strength, signal_ssid = get_wifi_signal_strength()
                    
                    # Get signal threshold from geofence_radius_m (repurposed to store signal %)
                    signal_threshold = device_data.get('geofence_radius_m', 30)  # Default 30%
                    
                    # Check for breach conditions:
                    # 1. Disconnected from required network
                    # 2. Connected to different network
                    # 3. Signal strength below threshold (if connected to required network)
                    breach_detected = False
                    breach_reason = ""
                    
                    if not is_connected or (current_ssid and current_ssid != geofence_wifi_ssid):
                        breach_detected = True
                        breach_reason = f"Disconnected from required network '{geofence_wifi_ssid}'. Current: {current_ssid or 'DISCONNECTED'}"
                    elif signal_strength is not None and signal_ssid == geofence_wifi_ssid:
                        # Check signal strength threshold
                        if signal_strength < signal_threshold:
                            breach_detected = True
                            breach_reason = f"WiFi signal strength ({signal_strength}%) below threshold ({signal_threshold}%)"
                    
                    if breach_detected:
                        logging.warning(f"⚠️ WiFi GEOFENCE BREACH: {breach_reason}")
                        
                        # Trigger alarm by updating device status
                        if self.status != 'alarm':
                            logging.error(f"🚨 ALARM TRIGGERED: {breach_reason}!")
                            self.status = 'alarm'
                            
                            # Update location immediately with alarm status to notify backend
                            try:
                                location = self.get_location()
                                if location:
                                    # Use correct endpoint format
                                    payload = {
                                        "device_id": self.device_id,
                                        "user": self.user_email,
                                        "location": location,
                                        "status": "alarm",
                                        "wifi_geofence_breach": True,
                                        "breach_details": {
                                            "required_ssid": geofence_wifi_ssid,
                                            "current_ssid": current_ssid or "DISCONNECTED",
                                            "signal_strength": signal_strength,
                                            "signal_threshold": signal_threshold,
                                            "reason": breach_reason
                                        }
                                    }
                                    response = requests.post(
                                        f"{API_BASE_URL}/update_location",
                                        json=payload,
                                        timeout=10
                                    )
                                    if response.status_code == 200:
                                        logging.info("✅ Alarm status sent to backend successfully")
                                    else:
                                        logging.error(f"Failed to send alarm status: {response.status_code}")
                            except Exception as e:
                                logging.error(f"Error sending alarm notification: {e}")
                
                # Check if status changed (indicating command)
                # Handle both 'lock' and 'locked' status
                command = None
                if status != self.status:
                    if status == 'locked' or status == 'lock':
                        command = 'lock'
                    elif status == 'alarm':
                        command = 'alarm'
                    elif status == 'wiped' or status == 'wipe':
                        command = 'wipe'
                
                if command:
                    # Prevent duplicate execution - only execute if lock screen is actually still running
                    # Check if lock screen process is actually running before preventing re-lock
                    if command == 'lock':
                        lock_screen_running = False
                        try:
                            # Check if lock screen is still running via socket
                            import socket
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(0.1)
                            result = sock.connect_ex(('localhost', 12345))  # LOCK_PORT from prey_lock_screen.py
                            sock.close()
                            if result == 0:
                                lock_screen_running = True
                        except Exception:
                            pass  # Ignore socket errors
                        
                        # Also check if lock_state.json exists (indicates lock screen is active)
                        lock_state_file = Path(__file__).parent / 'lock_state.json'
                        if lock_state_file.exists():
                            lock_screen_running = True
                        
                        # Only skip if lock screen is actually running
                        if lock_screen_running:
                            logging.info(f"🔒 Lock screen is already running, skipping duplicate lock command")
                            self.status = status  # Update status but don't execute again
                            if self.last_lock_status != 'locked':
                                self.last_lock_status = 'locked'
                            # Skip command execution - lock screen is already running
                            # Don't execute command below
                        else:
                            # Lock screen is not running - proceed with command execution
                            # This allows re-locking after unlock
                            logging.warning(f"🔔 COMMAND DETECTED: {command.upper()} (status changed from '{self.status}' to '{status}')")
                        # Get additional command details from activity logs
                        lock_password = None
                        lock_message = None
                        
                        # Try to get the latest lock command details
                        try:
                            logs_response = requests.get(
                                f"{API_BASE_URL}/get_activity_logs/{self.device_id}",
                                timeout=10
                            )
                            if logs_response.status_code == 200:
                                logs = logs_response.json().get('logs', [])
                                # Sort logs by ID (most recent first) to ensure we get the latest
                                # Find the most recent lock command by checking all logs
                                latest_lock_log = None
                                latest_log_id = -1
                                
                                for log in logs:
                                    if log.get('action') == 'lock' and 'password' in log.get('description', ''):
                                        log_id = log.get('id', 0)
                                        if log_id > latest_log_id:
                                            latest_log_id = log_id
                                            latest_lock_log = log
                                
                                if latest_lock_log:
                                    desc = latest_lock_log.get('description', '')
                                    logging.info(f"📋 Found LATEST lock log (ID: {latest_log_id}): {desc}")
                                    
                                    # Extract password from description
                                    if 'password:' in desc:
                                        parts = desc.split('password:')
                                        if len(parts) > 1:
                                            # Extract password - handle both formats:
                                            # "password: danish26" or "password: danish26, Message: ..."
                                            password_part = parts[1].strip()
                                            logging.info(f"🔍 Raw password part: '{password_part}'")
                                            
                                            # Split by comma first (if message exists), then by space
                                            if ',' in password_part:
                                                # Format: "password: danish26, Message: ..."
                                                lock_password = password_part.split(',')[0].strip()
                                            else:
                                                # Format: "password: danish26"
                                                # Take everything up to the first space or end of string
                                                lock_password = password_part.split()[0] if password_part else None
                                            
                                            # Remove any trailing punctuation and whitespace
                                            if lock_password:
                                                lock_password = lock_password.rstrip(',. ;:')
                                                lock_password = lock_password.strip()
                                            
                                            logging.info(f"🔑 Extracted password: '{lock_password}' (length: {len(lock_password) if lock_password else 0})")
                                            logging.info(f"🔑 Password bytes: {lock_password.encode('utf-8') if lock_password else None}")
                                    if 'Message:' in desc:
                                        parts = desc.split('Message:')
                                        if len(parts) > 1:
                                            lock_message = parts[1].strip()
                                            logging.info(f"💬 Extracted message: {lock_message}")
                                else:
                                    logging.warning("⚠️ No lock command found in activity logs")
                        except Exception as e:
                            logging.warning(f"Could not get activity logs: {e}")
                            import traceback
                            logging.error(traceback.format_exc())
                        
                        # Use default password if not found
                        if command == 'lock' and not lock_password:
                            lock_password = 'antitheft2024'
                            logging.info(f"🔑 Using default password: {lock_password}")
                        
                        # Save password to lock state file immediately for reliable access
                        if command == 'lock' and lock_password:
                            try:
                                lock_state_file = Path(__file__).parent / 'lock_state.json'
                                import json
                                
                                # Delete old lock state file first to ensure clean state
                                if lock_state_file.exists():
                                    try:
                                        lock_state_file.unlink()
                                        logging.info("🗑️ Deleted old lock_state.json")
                                    except Exception as e:
                                        logging.warning(f"Could not delete old lock state: {e}")
                                
                                # Ensure password is a string and properly formatted
                                clean_password = str(lock_password).strip()
                                lock_state = {
                                    'locked': True,
                                    'password': clean_password,
                                    'message': (lock_message or '').strip()
                                }
                                
                                # Write new lock state
                                with open(lock_state_file, 'w', encoding='utf-8') as f:
                                    json.dump(lock_state, f, ensure_ascii=False)
                                
                                logging.info(f"💾 Saved NEW password to lock_state.json: '{clean_password}' (length: {len(clean_password)})")
                                logging.info(f"💾 Password bytes saved: {clean_password.encode('utf-8')}")
                                
                                # Verify it was saved correctly
                                try:
                                    with open(lock_state_file, 'r', encoding='utf-8') as f:
                                        verify_state = json.load(f)
                                        verify_password = verify_state.get('password', '')
                                        logging.info(f"✅ Verified saved password: '{verify_password}' (matches: {verify_password == clean_password})")
                                except Exception as e:
                                    logging.warning(f"Could not verify saved password: {e}")
                                    
                            except Exception as e:
                                logging.warning(f"Could not save lock state: {e}")
                                import traceback
                                logging.error(traceback.format_exc())
                            
                            self.execute_command(command, lock_password=lock_password, lock_message=lock_message)
                            self.status = status
                            if command == 'lock':
                                self.last_lock_status = 'locked'
                                logging.info(f"🔒 Lock executed - status set to 'locked', last_lock_status set to 'locked'")
                            else:
                                self.last_lock_status = None
                    
                    # Handle non-lock commands (alarm, wipe, etc.)
                    elif command != 'lock':
                        logging.warning(f"🔔 COMMAND DETECTED: {command.upper()} (status changed from '{self.status}' to '{status}')")
                        self.execute_command(command)
                        self.status = status
                        self.last_lock_status = None
                else:
                    # CRITICAL: Detect if device was unlocked locally FIRST (before checking status changes)
                    # This ensures we catch unlock immediately and update status before any other checks
                    if self.status == 'locked' and self.last_lock_status == 'locked':
                        lock_state_file = Path(__file__).parent / 'lock_state.json'
                        is_lock_running = False
                        
                        # Check if lock screen is still running
                        try:
                            # Method 1: Check if lock_state.json exists (deleted on unlock)
                            if lock_state_file.exists():
                                is_lock_running = True
                            else:
                                # Method 2: Check if lock screen process is running via socket
                                import socket
                                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                sock.settimeout(0.1)
                                result = sock.connect_ex(('localhost', 12345))  # LOCK_PORT from prey_lock_screen.py
                                sock.close()
                                if result == 0:
                                    is_lock_running = True
                        except Exception as e:
                            logging.debug(f"Error checking lock screen status: {e}")
                        
                        # If lock screen is NOT running, device was unlocked
                        if not is_lock_running:
                            logging.info("🔓 Lock screen was unlocked! Detected unlock - updating status to 'active'")
                            self.status = 'active'
                            self.last_lock_status = None
                            
                            # Immediately report status change to backend
                            try:
                                location = self.get_location()
                                payload = {
                                    "device_id": self.device_id,
                                    "user": self.user_email,
                                    "status": "active"  # CRITICAL: Explicitly set status to 'active' for unlock
                                }
                                
                                if location:
                                    payload["location"] = location
                                else:
                                    # Even without location, send status update
                                    logging.info("⚠️ No location available, but sending status update anyway")
                                
                                # Add battery percentage if available
                                battery_percentage = self.get_battery_percentage()
                                if battery_percentage is not None:
                                    payload["battery_percentage"] = battery_percentage
                                
                                logging.info(f"📤 Sending unlock status update to backend: {payload}")
                                response = requests.post(
                                    f"{API_BASE_URL}/update_location",
                                    json=payload,
                                    timeout=10
                                )
                                if response.status_code == 200:
                                    response_data = response.json()
                                    logging.info(f"✅ Status updated to 'active' after unlock. Backend response: {response_data.get('device', {}).get('status', 'unknown')}")
                                else:
                                    logging.warning(f"⚠️ Failed to update status after unlock: {response.status_code} - {response.text[:200]}")
                            except Exception as e:
                                logging.error(f"❌ Error updating status after unlock: {e}")
                                import traceback
                                logging.error(traceback.format_exc())
                    
                    # No new command, but status may have changed (e.g., alarm cleared)
                    if status != self.status:
                        logging.info(f"Status updated without command: {self.status} -> {status}")
                        self.status = status
                    
                    # If alarm was running and status is no longer 'alarm', stop the alarm loop
                    if self.alarm_running and self.status != 'alarm':
                        logging.info("Alarm status cleared on server, stopping local alarm")
                        self.alarm_running = False
                    
                    # If status changed back to active (unlocked), reset lock tracking
                    if status == 'active' and self.last_lock_status == 'locked':
                        self.last_lock_status = None
                        self.status = 'active'  # Ensure local status matches
                
                # Check for pending wipe operations (separate from status-based commands)
                try:
                    wipe_response = requests.get(
                        f"{API_BASE_URL}/v1/wipe/pending/{self.device_id}",
                        timeout=5
                    )
                    if wipe_response.status_code == 200:
                        wipe_data = wipe_response.json()
                        if wipe_data.get('has_pending'):
                            operation_id = wipe_data.get('operation_id')
                            # Support both 'paths' and 'folders' keys for compatibility
                            paths = wipe_data.get('paths', wipe_data.get('folders', []))
                            wipe_status = wipe_data.get('status', 'pending')
                            
                            if wipe_status == 'pending':
                                logging.warning(f"🗑️ Pending wipe operation detected: {len(paths)} item(s)")
                                # Execute wipe in background thread to avoid blocking
                                wipe_thread = threading.Thread(
                                    target=self.execute_wipe,
                                    args=(paths, operation_id),
                                    daemon=True
                                )
                                wipe_thread.start()
                except Exception as e:
                    logging.debug(f"Error checking for pending wipe: {e}")
                
                # Check for pending file browse requests
                try:
                    browse_response = requests.get(
                        f"{API_BASE_URL}/v1/wipe/browse_request/{self.device_id}",
                        timeout=5
                    )
                    if browse_response.status_code == 200:
                        browse_data = browse_response.json()
                        if browse_data.get('has_request'):
                            browse_path = browse_data.get('path')
                            request_id = browse_data.get('request_id')
                            
                            # List files in background thread
                            browse_thread = threading.Thread(
                                target=self._handle_browse_request,
                                args=(browse_path, request_id),
                                daemon=True
                            )
                            browse_thread.start()
                except Exception as e:
                    logging.debug(f"Error checking for browse requests: {e}")
                    
        except Exception as e:
            logging.error(f"Error checking for commands: {e}")
    
    def execute_command(self, command, **kwargs):
        """Execute remote command locally"""
        logging.warning(f"⚠️ REMOTE COMMAND RECEIVED: {command.upper()}")
        
        if command == 'lock':
            password = kwargs.get('lock_password', 'antitheft2024')
            message = kwargs.get('lock_message', '')
            self.execute_lock(password=password, message=message)
        elif command == 'alarm':
            self.execute_alarm()
        elif command == 'wipe':
            # Wipe command from status change - check for pending operation
            self.execute_wipe()
        else:
            logging.warning(f"Unknown command: {command}")
    
    def execute_lock(self, password='antitheft2024', message=''):
        """Lock device screen/input with password and optional message"""
        # Ensure password is a string and strip whitespace
        password = str(password).strip() if password else 'antitheft2024'
        message = str(message).strip() if message else ''
        
        # Validate password - must not be empty
        if not password:
            logging.error("❌ Invalid password: password cannot be empty")
            password = 'antitheft2024'
            logging.warning(f"⚠️ Using default password: {password}")
        
        logging.info("🔒 Executing LOCK command")
        logging.info(f"Unlock password: '{password}' (length: {len(password)})")
        logging.info(f"Password bytes: {password.encode('utf-8')}")
        if message:
            logging.info(f"Lock message: {message}")
        
        # Save password to a debug file for troubleshooting
        try:
            debug_file = Path(__file__).parent / 'lock_password_debug.txt'
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"Password: {password}\n")
                f.write(f"Length: {len(password)}\n")
                f.write(f"Bytes: {password.encode('utf-8')}\n")
                f.write(f"Message: {message}\n")
        except Exception as e:
            logging.warning(f"Could not write debug file: {e}")
        
        system = platform.system().lower()
        try:
            # Check if lock screen is already running
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                result = sock.connect_ex(('localhost', 12345))  # LOCK_PORT from prey_lock_screen.py
                sock.close()
                if result == 0:
                    logging.warning("⚠️ Lock screen is already running, skipping duplicate lock")
                    return  # Lock screen already active, don't start another one
            except Exception:
                pass  # Ignore socket errors, continue with lock attempt
            
            # Use Prey-style lock screen for all platforms
            import subprocess
            # Try Prey-style lock screen first, fallback to regular lock screen
            lock_script = Path(__file__).parent / 'prey_lock_screen.py'
            if not lock_script.exists():
                lock_script = Path(__file__).parent / 'lock_screen.py'
            
            if lock_script.exists():
                # Launch lock screen as separate process
                # Build command with password and message
                # Password and message are passed as separate arguments (subprocess handles escaping)
                cmd = [sys.executable, str(lock_script), password]
                if message:
                    cmd.append(message)  # Message as separate argument (will be joined in lock_screen.py)
                
                # Create temporary files to capture stderr for debugging
                import tempfile
                stderr_file = None
                try:
                    stderr_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt', prefix='lock_stderr_')
                    stderr_path = stderr_file.name
                    stderr_file.close()
                except Exception as e:
                    logging.debug(f"Could not create stderr file: {e}")
                    stderr_path = None
                
                try:
                    if system == 'windows':
                        # Windows: Use regular python.exe (not pythonw.exe) so tkinter window is visible
                        # Don't hide the console - we need the lock screen to be visible
                        # Use CREATE_NEW_CONSOLE to ensure the window appears
                        if stderr_path:
                            stderr_handle = open(stderr_path, 'w', encoding='utf-8')
                        else:
                            stderr_handle = subprocess.DEVNULL
                        
                        process = subprocess.Popen(
                            cmd,
                            creationflags=subprocess.CREATE_NEW_CONSOLE,
                            stderr=stderr_handle,
                            stdout=subprocess.DEVNULL
                        )
                        if stderr_path:
                            stderr_handle.close()
                        logging.info(f"✅ Lock screen process started (PID: {process.pid})")
                        logging.info(f"   Command: {' '.join(cmd)}")
                    else:
                        # macOS/Linux: Run in background
                        stderr_handle = open(stderr_path, 'w') if stderr_path else subprocess.DEVNULL
                        process = subprocess.Popen(
                            cmd, 
                            stdout=subprocess.DEVNULL, 
                            stderr=stderr_handle
                        )
                        if stderr_path:
                            stderr_handle.close()
                        logging.info(f"✅ Lock screen process started (PID: {process.pid})")
                except Exception as e:
                    logging.error(f"❌ Failed to start lock screen process: {e}")
                    raise
                
                # Wait a moment to check if process started successfully
                time.sleep(0.5)
                if process.poll() is not None:
                    # Process already exited - there was an error
                    logging.error(f"❌ Lock screen process exited immediately with code: {process.returncode}")
                    logging.error(f"   Command was: {' '.join(cmd)}")
                    
                    # Try to read stderr for error details
                    if stderr_path and Path(stderr_path).exists():
                        try:
                            with open(stderr_path, 'r', encoding='utf-8', errors='replace') as f:
                                stderr_content = f.read()
                                if stderr_content:
                                    logging.error(f"   Error output: {stderr_content[:500]}")  # First 500 chars
                        except Exception as e:
                            logging.debug(f"Could not read stderr file: {e}")
                        finally:
                            try:
                                Path(stderr_path).unlink()
                            except:
                                pass
                    
                    # Common error troubleshooting
                    logging.error("   Troubleshooting:")
                    logging.error("   1. Check if tkinter is installed: python -c 'import tkinter'")
                    logging.error("   2. Check if Python can access display (Windows should work)")
                    logging.error("   3. Check lock_screen.log for detailed error messages")
                    logging.error("   4. Verify lock screen script exists and is readable")
                    
                    # Retry custom lock screen instead of falling back to Windows lock
                    logging.warning("⚠️ Custom lock screen failed, retrying...")
                    try:
                        # Retry with a longer wait time
                        time.sleep(1)
                        retry_process = subprocess.Popen(
                            cmd,
                            creationflags=subprocess.CREATE_NEW_CONSOLE if system == 'windows' else 0,
                            stderr=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL
                        )
                        time.sleep(0.5)
                        if retry_process.poll() is None:
                            logging.info("✅ Custom lock screen started on retry")
                            logging.info(f"✅ Lock command executed. Unlock password: {password}")
                        else:
                            logging.error("❌ Custom lock screen failed on retry. Will NOT use Windows lock (to preserve custom password).")
                            logging.error("   Please check lock_screen.log for details and fix the custom lock screen.")
                    except Exception as retry_error:
                        logging.error(f"❌ Retry also failed: {retry_error}")
                        logging.error("   Will NOT use Windows lock (to preserve custom password).")
                        logging.error("   Please check lock_screen.log for details and fix the custom lock screen.")
                else:
                    logging.info("✅ Custom lock screen launched successfully")
                    logging.info(f"✅ Lock command executed. Unlock password: {password}")
                    logging.info("💡 The password is saved in the activity log for reference")
                    
                    # Clean up stderr file if process is running
                    if stderr_path and Path(stderr_path).exists():
                        try:
                            Path(stderr_path).unlink()
                        except:
                            pass
            else:
                # Custom lock screen not available - do NOT use Windows lock (would use Windows PIN)
                logging.error("❌ Custom lock screen not found!")
                logging.error("   Will NOT use Windows lock (to preserve custom password).")
                logging.error("   Please ensure prey_lock_screen.py or lock_screen.py exists in device_agent folder.")
                logging.error("   The device will NOT be locked until the custom lock screen is available.")
            
        except Exception as e:
            logging.error(f"❌ Error executing lock: {e}")
            import traceback
            logging.error(traceback.format_exc())
            
            # Do NOT use Windows lock fallback - it would use Windows PIN instead of custom password
            logging.error("❌ Custom lock screen failed. Will NOT use Windows lock (to preserve custom password).")
            logging.error("   Please check the error above and ensure the custom lock screen can start.")
            logging.error("   The device will NOT be locked until the custom lock screen works properly.")
    
    def execute_alarm(self):
        """Start a continuous alarm sound until alarm status is cleared"""
        logging.info("🚨 Executing ALARM command (continuous until cleared)")
        
        # If alarm is already running, don't start another thread
        if self.alarm_running:
            logging.info("Alarm already running, skipping new alarm start")
            return
        
        self.alarm_running = True
        
        def alarm_loop():
            try:
                system = platform.system().lower()
                logging.info("Alarm loop started")
                
                if system == 'windows':
                    import winsound
                    # Louder-feeling alarm: higher frequency, longer duration, no fixed repeat count
                    while self.alarm_running and self.status == 'alarm':
                        winsound.Beep(2000, 800)  # 2000 Hz, 0.8s
                        time.sleep(0.1)           # Short pause between beeps
                else:
                    # Unix-like: continuous terminal bell
                    while self.alarm_running and self.status == 'alarm':
                        print('\a', end='', flush=True)
                        time.sleep(0.3)
                
                logging.info("Alarm loop exiting (alarm_running=%s, status=%s)", self.alarm_running, self.status)
            except Exception as e:
                logging.error(f"Error in alarm loop: {e}")
            finally:
                self.alarm_running = False
                logging.info("Alarm loop stopped")
        
        # Start alarm in background thread so agent can keep polling server
        self.alarm_thread = threading.Thread(target=alarm_loop, daemon=True)
        self.alarm_thread.start()
    
    def _is_path_valid(self, path):
        """Validate that path is within D:\\ and not a system directory"""
        path_normalized = path.replace('/', '\\').upper()
        
        # Must start with D:\
        if not path_normalized.startswith('D:\\'):
            return False
        
        # Block system directories
        blocked_paths = [
            'D:\\WINDOWS',
            'D:\\PROGRAM FILES',
            'D:\\PROGRAM FILES (X86)',
            'D:\\SYSTEM VOLUME INFORMATION',
            'D:\\$RECYCLE.BIN',
            'D:\\RECYCLER'
        ]
        
        for blocked in blocked_paths:
            if path_normalized.startswith(blocked):
                return False
        
        return True
    
    def list_files(self, path='D:\\'):
        """
        List files and folders from a given path (rooted at D:\\).
        Returns list of items with metadata.
        """
        try:
            path_normalized = path.replace('/', '\\')
            
            # Validate path
            if not self._is_path_valid(path_normalized):
                return {'error': 'Invalid path. Must be within D:\\ and not a system directory.'}
            
            folder = Path(path_normalized)
            
            if not folder.exists():
                return {'error': 'Path does not exist'}
            
            if not folder.is_dir():
                return {'error': 'Path is not a directory'}
            
            items = []
            
            # Add parent directory link if not at root
            if path_normalized.upper() != 'D:\\':
                parent_path = str(folder.parent)
                if self._is_path_valid(parent_path):
                    items.append({
                        'name': '..',
                        'path': parent_path,
                        'type': 'folder',
                        'size': None
                    })
            
            # List files and folders
            try:
                for item in folder.iterdir():
                    try:
                        item_path = str(item)
                        if not self._is_path_valid(item_path):
                            continue  # Skip blocked items
                        
                        item_info = {
                            'name': item.name,
                            'path': item_path,
                            'type': 'folder' if item.is_dir() else 'file'
                        }
                        
                        # Get size for files
                        if item.is_file():
                            try:
                                item_info['size'] = item.stat().st_size
                            except:
                                item_info['size'] = None
                        else:
                            item_info['size'] = None
                        
                        items.append(item_info)
                    except PermissionError:
                        continue  # Skip items we can't access
                    except Exception as e:
                        logging.debug(f"Error reading item {item}: {e}")
                        continue
                
                # Sort: folders first, then files, both alphabetically
                items.sort(key=lambda x: (x['type'] != 'folder', x['name'].lower()))
                
                return {
                    'path': path_normalized,
                    'items': items,
                    'count': len(items)
                }
            except PermissionError:
                return {'error': 'Permission denied'}
            except Exception as e:
                return {'error': f'Error listing directory: {e}'}
                
        except Exception as e:
            logging.error(f"Error listing files: {e}")
            return {'error': str(e)}
    
    def execute_wipe(self, paths_to_wipe=None, operation_id=None):
        """
        Execute remote data wipe on specified files/folders.
        Paths must be within D:\\ and not system directories.
        """
        logging.warning("🗑️ Executing REMOTE DATA WIPE command")
        
        # If paths_to_wipe not provided, get from server
        if not paths_to_wipe or not operation_id:
            try:
                response = requests.get(
                    f"{API_BASE_URL}/v1/wipe/pending/{self.device_id}",
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get('has_pending'):
                        # Support both 'paths' and 'folders' keys
                        paths_to_wipe = data.get('paths', data.get('folders', []))
                        operation_id = data.get('operation_id')
                    else:
                        logging.info("No pending wipe operation")
                        return
                else:
                    logging.error(f"Failed to get pending wipe: {response.status_code}")
                    return
            except Exception as e:
                logging.error(f"Error checking for pending wipe: {e}")
                return
        
        # Validate all paths
        invalid_paths = []
        for path in paths_to_wipe:
            if not self._is_path_valid(path):
                invalid_paths.append(path)
        
        if invalid_paths:
            error_msg = f"Some paths are invalid or blocked: {invalid_paths}"
            logging.error(f"❌ {error_msg}")
            self._report_wipe_status(operation_id, 'failed', 0, 0, 0, error_msg)
            return
        
        # Report wipe started
        self._report_wipe_status(operation_id, 'in_progress', 0, 0, 0)
        
        # Count total items first
        total_items = 0
        items_deleted = 0
        errors = []
        
        try:
            import shutil
            
            # First pass: count all items
            for path_str in paths_to_wipe:
                path_obj = Path(path_str)
                
                if not path_obj.exists():
                    logging.warning(f"⚠️ Path does not exist: {path_str}")
                    continue
                
                if path_obj.is_file():
                    total_items += 1
                elif path_obj.is_dir():
                    try:
                        for root, dirs, files in os.walk(path_obj):
                            total_items += len(files) + len(dirs)
                    except Exception as e:
                        logging.warning(f"Error counting items in {path_str}: {e}")
            
            # Second pass: delete items
            for path_str in paths_to_wipe:
                path_obj = Path(path_str)
                
                if not path_obj.exists():
                    continue
                
                if path_obj.is_file():
                    # Delete single file
                    try:
                        logging.info(f"🗑️ Deleting file: {path_str}")
                        path_obj.unlink()
                        items_deleted += 1
                        
                        # Update progress
                        if total_items > 0:
                            progress = int((items_deleted / total_items) * 100)
                            self._report_wipe_status(
                                operation_id, 'in_progress',
                                progress, items_deleted, total_items
                            )
                    except Exception as e:
                        error_msg = f"Error deleting file {path_str}: {e}"
                        errors.append(error_msg)
                        logging.error(f"❌ {error_msg}")
                
                elif path_obj.is_dir():
                    # Recursively delete folder
                    try:
                        logging.info(f"🗑️ Deleting folder: {path_str}")
                        
                        # Delete all files and subdirectories
                        for root, dirs, files in os.walk(path_obj, topdown=False):
                            # Delete files
                            for file in files:
                                file_path = Path(root) / file
                                try:
                                    file_path.unlink()
                                    items_deleted += 1
                                    
                                    # Update progress every 10 items
                                    if items_deleted % 10 == 0 and total_items > 0:
                                        progress = int((items_deleted / total_items) * 100)
                                        self._report_wipe_status(
                                            operation_id, 'in_progress',
                                            progress, items_deleted, total_items
                                        )
                                except Exception as e:
                                    errors.append(f"Error deleting {file_path}: {e}")
                                    logging.warning(f"Error deleting {file_path}: {e}")
                            
                            # Delete directories
                            for dir_name in dirs:
                                dir_path = Path(root) / dir_name
                                try:
                                    dir_path.rmdir()
                                    items_deleted += 1
                                except Exception:
                                    pass  # Ignore if not empty or can't be removed
                        
                        # Try to remove root directory
                        try:
                            if path_obj.exists() and not any(path_obj.iterdir()):
                                path_obj.rmdir()
                                items_deleted += 1
                        except Exception:
                            pass  # Ignore if not empty or can't be removed
                        
                        logging.info(f"✅ Deleted folder: {path_str}")
                        
                    except Exception as e:
                        error_msg = f"Error deleting folder {path_str}: {e}"
                        errors.append(error_msg)
                        logging.error(f"❌ {error_msg}")
            
            # Report completion
            if errors:
                error_message = f"Completed with {len(errors)} errors: {'; '.join(errors[:3])}"
                self._report_wipe_status(
                    operation_id, 'completed',
                    100, items_deleted, total_items, error_message
                )
            else:
                self._report_wipe_status(
                    operation_id, 'completed',
                    100, items_deleted, total_items
                )
            
            logging.info(f"✅ Wipe operation completed: {items_deleted}/{total_items} items deleted")
            
        except Exception as e:
            error_msg = f"Fatal error during wipe: {e}"
            logging.error(f"❌ {error_msg}")
            self._report_wipe_status(operation_id, 'failed', 0, items_deleted, total_items, error_msg)
    
    def _handle_browse_request(self, path, request_id):
        """Handle file browse request from backend"""
        try:
            logging.info(f"📁 Processing browse request: {path}")
            result = self.list_files(path)
            
            # Send result back to backend
            payload = {
                'device_id': self.device_id,
                'path': path,
                'request_id': request_id,
                'items': result.get('items', []) if 'error' not in result else [],
                'error': result.get('error')
            }
            
            response = requests.post(
                f"{API_BASE_URL}/v1/wipe/browse_result",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logging.debug(f"Browse result sent for path: {path}")
            else:
                logging.warning(f"Failed to send browse result: {response.status_code}")
                
        except Exception as e:
            logging.error(f"Error handling browse request: {e}")
            # Try to send error back
            try:
                payload = {
                    'device_id': self.device_id,
                    'path': path,
                    'request_id': request_id,
                    'items': [],
                    'error': str(e)
                }
                requests.post(
                    f"{API_BASE_URL}/v1/wipe/browse_result",
                    json=payload,
                    timeout=5
                )
            except:
                pass
    
    def _report_wipe_status(self, operation_id, status, progress=0, files_deleted=0, total_files=0, error_message=None):
        """Report wipe operation status to server"""
        if not operation_id:
            return
        
        try:
            payload = {
                'device_id': self.device_id,
                'operation_id': operation_id,
                'status': status,
                'progress_percentage': progress,
                'files_deleted': files_deleted,
                'total_files': total_files
            }
            if error_message:
                payload['error_message'] = error_message
            
            response = requests.post(
                f"{API_BASE_URL}/v1/wipe/update_status",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logging.debug(f"Wipe status reported: {status} ({progress}%)")
            else:
                logging.warning(f"Failed to report wipe status: {response.status_code}")
        except Exception as e:
            logging.error(f"Error reporting wipe status: {e}")
    
    def capture_screenshot(self):
        """Capture screenshot (if device is missing)"""
        try:
            logging.info("📸 Attempting to capture screenshot")
            # In production, use libraries like PIL/Pillow or pyautogui
            # For demo, just log the action
            screenshot_path = f"screenshots/{self.device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            logging.info(f"Screenshot would be saved to: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logging.error(f"Error capturing screenshot: {e}")
            return None
    
    def run(self):
        """Main agent loop"""
        logging.info("🤖 Device Agent Starting...")
        logging.info(f"Device ID: {self.device_id}")
        logging.info(f"User: {self.user_email}")
        logging.info(f"API URL: {API_BASE_URL}")
        
        # First, check for automatic config updates (before registration)
        # This allows auto-setup when user registers a new account
        logging.info("🔍 Checking for automatic configuration updates...")
        config_updated = self.check_for_config_update()
        if config_updated:
            logging.info("✅ Configuration was auto-updated, proceeding with registration...")
        else:
            logging.info("ℹ️ No automatic config updates found (this is normal if you already have the correct email)")
        
        # Then, make sure this physical device is registered for this user
        # If registration fails due to wrong email, check for updates again
        try:
            self.register_with_server()
        except Exception as e:
            logging.warning(f"Registration failed, checking for config updates again: {e}")
            # If registration failed, check for updates one more time
            self.check_for_config_update()
            # Try registering again
            self.register_with_server()
        
        # CRITICAL: Force GPS location update on startup to clear any wrong cached location
        logging.info("🔄 Forcing GPS location update on startup to ensure accurate location...")
        if platform.system().lower() == 'windows':
            startup_gps = self._force_gps_location()
            if startup_gps:
                logging.info(f"✅✅ Got GPS location on startup: {startup_gps}")
                self.last_known_location = startup_gps
                # Immediately report this GPS location to clear any wrong location in database
                try:
                    payload = {
                        "device_id": self.device_id,
                        "user": self.user_email,
                        "location": startup_gps,
                        "status": self.status,
                        "force_update": True
                    }
                    response = requests.post(
                        f"{API_BASE_URL}/update_location",
                        json=payload,
                        timeout=10
                    )
                    if response.status_code == 200:
                        logging.info(f"✅ Startup GPS location reported successfully: {startup_gps}")
                    else:
                        logging.warning(f"⚠️ Failed to report startup GPS location: {response.status_code}")
                except Exception as e:
                    logging.warning(f"⚠️ Error reporting startup GPS location: {e}")
            else:
                logging.warning("⚠️ Could not get GPS location on startup. Will keep trying...")
        
        # Load report interval from config
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                report_interval = config.get('report_interval', 15)  # Default 15 seconds for real-time tracking
                # Make command checks very fast so lock feels instant
                # Allow override from config, but default to 0.2s (5 times per second)
                check_interval = config.get('check_commands_interval', 0.2)
        except:
            report_interval = 15  # 15 seconds for real-time tracking
            # Default to 0.2s for snappy command detection if config not found
            check_interval = 0.2
        
        last_report = 0
        last_command_check = 0
        last_config_check = 0
        config_check_interval = 10  # Check for config updates every 10 seconds (more aggressive)
        startup_time = time.time()
        
        try:
            while True:
                current_time = time.time()
                time_since_startup = current_time - startup_time
                
                # Report status periodically
                if current_time - last_report >= report_interval:
                    self.report_status()
                    last_report = current_time
                    # Also check for commands immediately after reporting status
                    # This ensures we catch commands right after they're sent
                    self.check_for_commands()
                    last_command_check = current_time
                
                # Check for config updates more frequently (every 10 seconds)
                # This helps catch new user registrations quickly
                # Check even more frequently in the first 5 minutes after startup
                if time_since_startup < 300:  # First 5 minutes
                    aggressive_interval = 5  # Every 5 seconds for first 5 minutes
                else:
                    aggressive_interval = config_check_interval
                
                if current_time - last_config_check >= aggressive_interval:
                    self.check_for_config_update()
                    last_config_check = current_time
                
                # Check for commands frequently for immediate response
                if current_time - last_command_check >= check_interval:
                    self.check_for_commands()
                    last_command_check = current_time
                
                # Small sleep to avoid 100% CPU, but keep it fast for near-instant commands
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logging.info("🛑 Agent stopped by user")
        except Exception as e:
            logging.error(f"Fatal error in agent loop: {e}")
            raise

def main():
    agent = DeviceAgent()
    agent.run()

if __name__ == '__main__':
    main()

