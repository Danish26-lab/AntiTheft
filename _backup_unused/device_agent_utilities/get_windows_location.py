#!/usr/bin/env python3
"""
Get accurate location on Windows using Windows Location API
"""

import subprocess
import json
import sys

def get_windows_location():
    """Try to get location from Windows Location API"""
    try:
        # PowerShell script to get location
        ps_script = """
        Add-Type -AssemblyName System.Device
        $loc = New-Object System.Device.Location.GeoCoordinateWatcher
        $loc.Start()
        Start-Sleep -Seconds 2
        if ($loc.Position.Location.IsUnknown) {
            Write-Output "UNKNOWN"
        } else {
            $lat = $loc.Position.Location.Latitude
            $lng = $loc.Position.Location.Longitude
            Write-Output "$lat,$lng"
        }
        $loc.Stop()
        """
        
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip() != "UNKNOWN":
            coords = result.stdout.strip().split(',')
            if len(coords) == 2:
                return {
                    'lat': float(coords[0]),
                    'lng': float(coords[1]),
                    'source': 'windows_location_api'
                }
    except Exception as e:
        print(f"Windows Location API failed: {e}")
    
    return None

if __name__ == '__main__':
    location = get_windows_location()
    if location:
        print(json.dumps(location, indent=2))
    else:
        print("Windows Location API not available")

