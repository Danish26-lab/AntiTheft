#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Device Fingerprinting for Prey Project-style Agent-First Architecture
Generates stable, unique hardware fingerprint for device identification
"""

import platform
import socket
import hashlib
import subprocess
import json
from typing import Dict, List


def run_cmd(cmd: str, timeout: int = 5) -> str:
    """Execute a shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout
        )
        if result.returncode != 0:
            return ""
        output = result.stdout
        lines = []
        for line in output.splitlines():
            line = line.strip()
            if line:
                lines.append(line)
        return '\n'.join(lines)
    except Exception:
        return ""


def get_windows_fingerprint_data() -> Dict[str, str]:
    """Collect fingerprint data from Windows"""
    data = {}
    
    # Machine UUID (most stable)
    uuid_cmd = run_cmd('wmic csproduct get uuid /format:list')
    for line in uuid_cmd.splitlines():
        if line.startswith("UUID="):
            data['machine_uuid'] = line.split("=", 1)[-1].strip()
            break
    
    # System serial number
    serial_cmd = run_cmd('wmic csproduct get identifyingnumber /format:list')
    for line in serial_cmd.splitlines():
        if line.startswith("IdentifyingNumber="):
            data['serial_number'] = line.split("=", 1)[-1].strip()
            break
    
    # BIOS serial (backup)
    bios_cmd = run_cmd('wmic bios get serialnumber /format:list')
    for line in bios_cmd.splitlines():
        if line.startswith("SerialNumber="):
            serial = line.split("=", 1)[-1].strip()
            if serial and serial.upper() not in ['TO BE FILLED BY O.E.M.', 'DEFAULT', 'NONE', '']:
                data['bios_serial'] = serial
            break
    
    # Motherboard serial
    mb_cmd = run_cmd('wmic baseboard get serialnumber /format:list')
    for line in mb_cmd.splitlines():
        if line.startswith("SerialNumber="):
            serial = line.split("=", 1)[-1].strip()
            if serial and serial.upper() not in ['TO BE FILLED BY O.E.M.', 'DEFAULT', 'NONE', '']:
                data['motherboard_serial'] = serial
            break
    
    # CPU ID (from registry - more stable than model name)
    cpu_id_cmd = run_cmd('wmic cpu get processorid /format:list')
    for line in cpu_id_cmd.splitlines():
        if line.startswith("ProcessorID="):
            data['cpu_id'] = line.split("=", 1)[-1].strip()
            break
    
    # MAC addresses (hashed for privacy)
    macs = []
    nic_cmd = run_cmd('wmic nic get macaddress /format:list')
    for line in nic_cmd.splitlines():
        if line.startswith("MACAddress="):
            mac = line.split("=", 1)[-1].strip()
            if mac and mac != "00:00:00:00:00:00" and len(mac) == 17:
                macs.append(mac)
    if macs:
        data['mac_addresses'] = sorted(set(macs))  # Sort for consistency
    
    # Hostname (less stable, but useful)
    data['hostname'] = socket.gethostname()
    
    return data


def get_macos_fingerprint_data() -> Dict[str, str]:
    """Collect fingerprint data from macOS"""
    data = {}
    
    # System serial (most stable)
    serial_cmd = run_cmd("system_profiler SPHardwareDataType | grep 'Serial Number (system):'")
    for line in serial_cmd.splitlines():
        if "Serial Number" in line:
            data['serial_number'] = line.split(":", 1)[-1].strip()
            break
    
    # Hardware UUID
    uuid_cmd = run_cmd("system_profiler SPHardwareDataType | grep 'Hardware UUID:'")
    for line in uuid_cmd.splitlines():
        if "Hardware UUID" in line:
            data['hardware_uuid'] = line.split(":", 1)[-1].strip()
            break
    
    # Platform UUID
    platform_uuid_cmd = run_cmd("ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID")
    if platform_uuid_cmd:
        for line in platform_uuid_cmd.splitlines():
            if "IOPlatformUUID" in line:
                # Extract UUID from the line
                import re
                uuid_match = re.search(r'"([0-9A-F-]{36})"', line)
                if uuid_match:
                    data['platform_uuid'] = uuid_match.group(1)
                break
    
    # MAC addresses (hashed)
    macs = []
    network_cmd = run_cmd("ifconfig | grep 'ether'")
    for line in network_cmd.splitlines():
        if "ether" in line:
            mac_match = re.search(r'([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})', line, re.IGNORECASE)
            if mac_match:
                mac = mac_match.group(1)
                if mac != "00:00:00:00:00:00":
                    macs.append(mac)
    if macs:
        data['mac_addresses'] = sorted(set(macs))
    
    # Hostname
    data['hostname'] = socket.gethostname()
    
    return data


def get_linux_fingerprint_data() -> Dict[str, str]:
    """Collect fingerprint data from Linux"""
    import re
    data = {}
    
    # Machine ID (most stable - systemd)
    try:
        machine_id_file = '/etc/machine-id'
        try:
            with open(machine_id_file, 'r') as f:
                machine_id = f.read().strip()
                if machine_id:
                    data['machine_id'] = machine_id
        except:
            pass
    except:
        pass
    
    # DMI system UUID
    uuid_cmd = run_cmd("sudo dmidecode -s system-uuid 2>/dev/null || dmidecode -s system-uuid 2>/dev/null")
    if uuid_cmd:
        data['system_uuid'] = uuid_cmd.strip()
    
    # System serial
    serial_cmd = run_cmd("sudo dmidecode -s system-serial-number 2>/dev/null || dmidecode -s system-serial-number 2>/dev/null")
    if serial_cmd and serial_cmd.upper() not in ['TO BE FILLED BY O.E.M.', 'DEFAULT', 'NONE', '']:
        data['serial_number'] = serial_cmd.strip()
    
    # Product UUID
    product_uuid_cmd = run_cmd("sudo dmidecode -s product-uuid 2>/dev/null || dmidecode -s product-uuid 2>/dev/null")
    if product_uuid_cmd:
        data['product_uuid'] = product_uuid_cmd.strip()
    
    # MAC addresses (hashed)
    macs = []
    ip_link = run_cmd("ip link show")
    for line in ip_link.splitlines():
        mac_match = re.search(r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})', line)
        if mac_match:
            mac = mac_match.group(1)
            if mac != "00:00:00:00:00:00":
                macs.append(mac)
    if macs:
        data['mac_addresses'] = sorted(set(macs))
    
    # Hostname
    data['hostname'] = socket.gethostname()
    
    return data


def generate_fingerprint() -> str:
    """
    Generate a stable, unique hardware fingerprint for device identification.
    Uses multiple hardware identifiers combined and hashed for privacy.
    
    Returns: SHA-256 hash of fingerprint data
    """
    sys_name = platform.system().lower()
    
    # Collect fingerprint data based on OS
    if sys_name == "windows":
        fingerprint_data = get_windows_fingerprint_data()
    elif sys_name == "darwin":
        fingerprint_data = get_macos_fingerprint_data()
    else:
        fingerprint_data = get_linux_fingerprint_data()
    
    # Build fingerprint string from available data (prioritize most stable)
    fingerprint_parts = []
    
    # Priority 1: Machine UUID / Hardware UUID (most stable)
    if fingerprint_data.get('machine_uuid'):
        fingerprint_parts.append(f"uuid:{fingerprint_data['machine_uuid']}")
    elif fingerprint_data.get('hardware_uuid'):
        fingerprint_parts.append(f"hwuuid:{fingerprint_data['hardware_uuid']}")
    elif fingerprint_data.get('platform_uuid'):
        fingerprint_parts.append(f"platform:{fingerprint_data['platform_uuid']}")
    elif fingerprint_data.get('system_uuid'):
        fingerprint_parts.append(f"sysuuid:{fingerprint_data['system_uuid']}")
    elif fingerprint_data.get('machine_id'):
        fingerprint_parts.append(f"machineid:{fingerprint_data['machine_id']}")
    elif fingerprint_data.get('product_uuid'):
        fingerprint_parts.append(f"product:{fingerprint_data['product_uuid']}")
    
    # Priority 2: Serial numbers
    if fingerprint_data.get('serial_number'):
        fingerprint_parts.append(f"serial:{fingerprint_data['serial_number']}")
    if fingerprint_data.get('motherboard_serial'):
        fingerprint_parts.append(f"mb:{fingerprint_data['motherboard_serial']}")
    if fingerprint_data.get('bios_serial'):
        fingerprint_parts.append(f"bios:{fingerprint_data['bios_serial']}")
    
    # Priority 3: CPU ID (Windows) or CPU info
    if fingerprint_data.get('cpu_id'):
        fingerprint_parts.append(f"cpu:{fingerprint_data['cpu_id']}")
    
    # Priority 4: MAC addresses (sorted for consistency, hashed)
    if fingerprint_data.get('mac_addresses'):
        mac_str = '|'.join(fingerprint_data['mac_addresses'])
        fingerprint_parts.append(f"macs:{mac_str}")
    
    # Priority 5: Hostname + OS (least stable, but better than nothing)
    if fingerprint_data.get('hostname'):
        fingerprint_parts.append(f"hostname:{fingerprint_data['hostname']}")
    
    fingerprint_parts.append(f"os:{sys_name}")
    
    # Combine and hash
    fingerprint_string = '|'.join(fingerprint_parts)
    
    # Hash for privacy and consistent length
    fingerprint_hash = hashlib.sha256(fingerprint_string.encode('utf-8')).hexdigest()
    
    return fingerprint_hash


def get_fingerprint_info() -> Dict:
    """
    Get fingerprint data for registration.
    Returns both hash and the data used (for logging/debugging).
    """
    sys_name = platform.system().lower()
    
    if sys_name == "windows":
        data = get_windows_fingerprint_data()
    elif sys_name == "darwin":
        data = get_macos_fingerprint_data()
    else:
        data = get_linux_fingerprint_data()
    
    fingerprint_hash = generate_fingerprint()
    
    return {
        'fingerprint_hash': fingerprint_hash,
        'os_type': sys_name,
        'hostname': data.get('hostname', socket.gethostname()),
        'has_machine_uuid': bool(data.get('machine_uuid') or data.get('hardware_uuid') or data.get('system_uuid')),
        'has_serial': bool(data.get('serial_number')),
        'mac_count': len(data.get('mac_addresses', []))
    }


if __name__ == "__main__":
    # Test fingerprint generation
    info = get_fingerprint_info()
    print(json.dumps(info, indent=2))
    print(f"\nFingerprint Hash: {info['fingerprint_hash']}")
