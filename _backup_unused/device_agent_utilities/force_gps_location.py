#!/usr/bin/env python3
"""
Force GPS location update - clears cache and gets fresh GPS location
"""

import subprocess
import json
import sys
from pathlib import Path

def force_gps_location():
    """Force Windows to get a fresh GPS location"""
    try:
        # PowerShell script to force GPS location with longer wait
        ps_script = """
        Add-Type -AssemblyName System.Device -ErrorAction SilentlyContinue
        if ([System.Device.Location.GeoCoordinateWatcher]::IsSupported) {
            # Use High accuracy for best GPS precision
            $loc = New-Object System.Device.Location.GeoCoordinateWatcher([System.Device.Location.GeoPositionAccuracy]::High)
            
            # Stop any existing watcher first
            $loc.Stop()
            Start-Sleep -Seconds 1
            
            # Start fresh
            $loc.Start()
            $maxWait = 90  # Wait up to 90 seconds for GPS fix
            $waited = 0
            
            Write-Host "Waiting for GPS fix (this may take up to 90 seconds)..."
            
            # Wait for GPS to get accurate fix
            while ($loc.Status -ne 'Ready' -and $loc.Status -ne 'NoData' -and $waited -lt $maxWait) {
                Start-Sleep -Seconds 2
                $waited += 2
                if ($waited % 10 -eq 0) {
                    Write-Host "Still waiting... ($waited seconds)"
                }
            }
            
            if ($loc.Status -eq 'Ready' -and -not $loc.Position.Location.IsUnknown) {
                $lat = $loc.Position.Location.Latitude
                $lng = $loc.Position.Location.Longitude
                $acc = $loc.Position.Location.HorizontalAccuracy
                
                Write-Host "GPS Location obtained!"
                Write-Host "Latitude: $lat"
                Write-Host "Longitude: $lng"
                Write-Host "Accuracy: $acc meters"
                
                if ($acc -gt 0 -and $acc -lt 5000) {
                    Write-Output "$lat,$lng,$acc"
                } else {
                    Write-Output "UNKNOWN"
                }
            } else {
                Write-Host "GPS not available or timed out"
                Write-Output "UNKNOWN"
            }
            $loc.Stop()
        } else {
            Write-Host "Windows Location API not supported on this system"
            Write-Output "NOT_SUPPORTED"
        }
        """
        
        print("🔄 Forcing GPS location update...")
        print("   This may take up to 90 seconds for accurate GPS fix...")
        print()
        
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=95
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
                        print(f"\n✅ GPS Location obtained:")
                        print(f"   Latitude: {location['lat']:.6f}")
                        print(f"   Longitude: {location['lng']:.6f}")
                        print(f"   Accuracy: {accuracy:.1f} meters")
                        
                        if accuracy < 50:
                            print(f"   Status: ✅ EXCELLENT GPS accuracy")
                        elif accuracy < 100:
                            print(f"   Status: ✅ HIGH GPS accuracy")
                        elif accuracy < 500:
                            print(f"   Status: ⚠️ Moderate GPS accuracy")
                        else:
                            print(f"   Status: ⚠️ Low GPS accuracy (may be WiFi triangulation)")
                        
                        return location
                    else:
                        print(f"\n✅ Location obtained: {location}")
                        return location
            else:
                print("\n❌ Could not get GPS location")
                print("   Make sure:")
                print("   1. Windows Location Services is enabled")
                print("   2. Your device has GPS capability")
                print("   3. You're in an area with GPS signal")
                return None
        else:
            print(f"\n❌ Error: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("\n❌ GPS location request timed out")
        print("   Try again or check Windows Location Services")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

if __name__ == '__main__':
    location = force_gps_location()
    if location:
        print(f"\n📍 Location: {location['lat']:.6f}, {location['lng']:.6f}")
        print("\nThis location will be used in the next status report.")
    else:
        print("\n⚠️ Could not get GPS location. The device agent will use IP geolocation (less accurate).")

