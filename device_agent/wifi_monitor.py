#!/usr/bin/env python3
"""
WiFi Connection Monitor
Detects WiFi SSID and connection status for geofencing based on WiFi range
"""

import platform
import subprocess
import re
import logging

def get_wifi_ssid():
    """
    Get the currently connected WiFi SSID
    Returns SSID string or None if not connected/disconnected
    """
    system = platform.system().lower()
    
    try:
        if system == 'windows':
            # Windows: Use netsh command
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout
                # Look for SSID line
                for line in output.split('\n'):
                    if 'SSID' in line and 'BSSID' not in line:
                        match = re.search(r'SSID\s*:\s*(.+)', line)
                        if match:
                            ssid = match.group(1).strip()
                            # Check if actually connected (not "Not connected")
                            if ssid and ssid.lower() != 'not connected':
                                return ssid
            return None
            
        elif system == 'darwin':  # macOS
            result = subprocess.run(
                ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if ' SSID:' in line:
                        ssid = line.split('SSID:')[1].strip()
                        return ssid if ssid else None
            return None
            
        elif system == 'linux':
            # Linux: Use nmcli or iwgetid
            try:
                result = subprocess.run(
                    ['iwgetid', '-r'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except FileNotFoundError:
                # Try nmcli as fallback
                result = subprocess.run(
                    ['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if ':yes:' in line or 'yes:' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                return parts[-1].strip()
            return None
            
    except Exception as e:
        logging.error(f"Error getting WiFi SSID: {e}")
        return None

def get_wifi_signal_strength():
    """
    Get WiFi signal strength in percentage (0-100)
    Returns (signal_strength: int, ssid: str or None)
    """
    system = platform.system().lower()
    
    try:
        if system == 'windows':
            # Windows: Use netsh command to get signal strength
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout
                ssid = None
                signal_percent = None
                
                for line in output.split('\n'):
                    # Get SSID
                    if 'SSID' in line and 'BSSID' not in line:
                        match = re.search(r'SSID\s*:\s*(.+)', line)
                        if match:
                            ssid = match.group(1).strip()
                            if ssid and ssid.lower() == 'not connected':
                                ssid = None
                    
                    # Get signal strength (percentage)
                    if 'Signal' in line and '%' in line:
                        match = re.search(r'Signal\s*:\s*(\d+)%', line)
                        if match:
                            signal_percent = int(match.group(1))
                
                if ssid and signal_percent is not None:
                    return signal_percent, ssid
                elif ssid:
                    # If connected but no signal info, assume good signal
                    return 100, ssid
                    
        elif system == 'darwin':  # macOS
            result = subprocess.run(
                ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                ssid = None
                rssi = None
                
                for line in result.stdout.split('\n'):
                    if ' SSID:' in line:
                        ssid = line.split('SSID:')[1].strip()
                    elif ' agrCtlRSSI:' in line:
                        try:
                            rssi = int(line.split('agrCtlRSSI:')[1].strip())
                        except:
                            pass
                
                if ssid and rssi is not None:
                    # Convert RSSI (dBm) to percentage (rough approximation)
                    # RSSI typically ranges from -100 (weak) to -30 (strong)
                    signal_percent = max(0, min(100, int((rssi + 100) * 100 / 70)))
                    return signal_percent, ssid
                elif ssid:
                    return 100, ssid
                    
        elif system == 'linux':
            # Linux: Use iwconfig or nmcli
            try:
                result = subprocess.run(
                    ['iwconfig'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'ESSID:' in line:
                            match = re.search(r'ESSID:"([^"]+)"', line)
                            if match:
                                ssid = match.group(1)
                        elif 'Signal level=' in line:
                            match = re.search(r'Signal level=(-?\d+)', line)
                            if match:
                                rssi = int(match.group(1))
                                # Convert to percentage
                                signal_percent = max(0, min(100, int((rssi + 100) * 100 / 70)))
                                if ssid:
                                    return signal_percent, ssid
            except:
                pass
                
    except Exception as e:
        logging.error(f"Error getting WiFi signal strength: {e}")
    
    return None, None

def is_wifi_connected(required_ssid=None):
    """
    Check if WiFi is connected
    If required_ssid is provided, check if connected to that specific network
    Returns (is_connected: bool, current_ssid: str or None)
    """
    current_ssid = get_wifi_ssid()
    
    if not current_ssid:
        return False, None
    
    if required_ssid:
        # Check if connected to the required network
        return current_ssid == required_ssid, current_ssid
    
    # Just check if any WiFi is connected
    return True, current_ssid

def get_available_wifi_networks():
    """
    Get list of available WiFi networks
    Returns list of SSID strings
    """
    system = platform.system().lower()
    networks = []
    
    try:
        if system == 'windows':
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'networks'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'SSID' in line and ':' in line:
                        match = re.search(r'SSID\s+\d+\s*:\s*(.+)', line)
                        if match:
                            networks.append(match.group(1).strip())
            return networks
            
        elif system == 'darwin':  # macOS
            result = subprocess.run(
                ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-s'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if parts:
                            networks.append(parts[0])
            return networks
            
        elif system == 'linux':
            try:
                result = subprocess.run(
                    ['nmcli', '-t', '-f', 'ssid', 'dev', 'wifi'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    networks = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                    return networks
            except:
                pass
            return []
            
    except Exception as e:
        logging.error(f"Error getting WiFi networks: {e}")
        return []

if __name__ == '__main__':
    # Test the functions
    print("Current WiFi SSID:", get_wifi_ssid())
    print("Is WiFi connected:", is_wifi_connected()[0])
    print("\nAvailable networks:")
    for network in get_available_wifi_networks()[:10]:  # Show first 10
        print(f"  - {network}")

