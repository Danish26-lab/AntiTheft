#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prey Project-style Native Hardware Detection
Detects real hardware information using OS-specific commands
"""

import subprocess
import platform
import socket
import json
import re
import uuid
from typing import Dict, List, Optional, Tuple


def run_cmd(cmd: str, timeout: int = 10) -> str:
    """Execute a shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # Capture stderr but ignore it
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout
        )
        if result.returncode != 0:
            return ""
        output = result.stdout
        # Clean up WMIC output - remove extra blank lines but preserve content
        lines = []
        for line in output.splitlines():
            line = line.strip()
            if line:  # Only keep non-empty lines
                lines.append(line)
        return '\n'.join(lines)
    except Exception as e:
        # Debug: print error for troubleshooting (uncomment to debug)
        # import sys
        # print(f"Command failed: {cmd} - {e}", file=sys.stderr)
        return ""


def parse_wmic_output(output: str) -> Dict[str, str]:
    """Parse WMIC output into dictionary"""
    result = {}
    lines = output.splitlines()
    if len(lines) < 2:
        return result
    
    headers = [h.strip() for h in lines[0].split() if h.strip()]
    values = [v.strip() for v in lines[1].split(None, len(headers) - 1) if v.strip()]
    
    for i, header in enumerate(headers):
        if i < len(values):
            result[header] = values[i]
    
    return result


def detect_windows_hardware() -> Dict:
    """Detect hardware on Windows using WMIC commands"""
    sys_name = platform.system()
    hostname = socket.gethostname()
    
    # System Product Information (Vendor, Model, Serial)
    csproduct = run_cmd("wmic csproduct get vendor,name,identifyingnumber /format:list")
    vendor = ""
    model = ""
    serial_number = ""
    if csproduct:
        for line in csproduct.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("Vendor="):
                vendor = line.split("=", 1)[-1].strip()
            elif line.startswith("Name="):
                model = line.split("=", 1)[-1].strip()
            elif line.startswith("IdentifyingNumber="):
                serial_number = line.split("=", 1)[-1].strip()
    
    # BIOS Information
    bios = run_cmd("wmic bios get manufacturer,version,releasedate /format:list")
    bios_vendor = ""
    bios_version = ""
    bios_date = ""
    if bios:
        for line in bios.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("Manufacturer="):
                bios_vendor = line.split("=", 1)[-1].strip()
            elif line.startswith("Version="):
                bios_version = line.split("=", 1)[-1].strip()
            elif line.startswith("ReleaseDate="):
                bios_date = line.split("=", 1)[-1].strip()
    
    # Motherboard Information
    baseboard = run_cmd("wmic baseboard get product,manufacturer,serialnumber /format:list")
    motherboard_vendor = ""
    motherboard_model = ""
    motherboard_serial = ""
    if baseboard:
        for line in baseboard.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("Manufacturer="):
                motherboard_vendor = line.split("=", 1)[-1].strip()
            elif line.startswith("Product="):
                motherboard_model = line.split("=", 1)[-1].strip()
            elif line.startswith("SerialNumber="):
                motherboard_serial = line.split("=", 1)[-1].strip()
    
    # CPU Information
    cpu = run_cmd("wmic cpu get name,numberofcores,numberoflogicalprocessors,maxclockspeed /format:list")
    cpu_model = ""
    cpu_cores = 0
    cpu_threads = 0
    cpu_speed_mhz = 0
    if cpu:
        for line in cpu.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("Name="):
                cpu_model = line.split("=", 1)[-1].strip()
            elif line.startswith("NumberOfCores="):
                try:
                    cpu_cores = int(line.split("=", 1)[-1].strip())
                except:
                    pass
            elif line.startswith("NumberOfLogicalProcessors="):
                try:
                    cpu_threads = int(line.split("=", 1)[-1].strip())
                except:
                    pass
            elif line.startswith("MaxClockSpeed="):
                try:
                    cpu_speed_mhz = int(line.split("=", 1)[-1].strip())
                except:
                    pass
    
    # RAM Information
    memory = run_cmd("wmic memorychip get capacity /format:list")
    total_ram_mb = 0
    if memory:
        for line in memory.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("Capacity="):
                try:
                    capacity_str = line.split("=", 1)[-1].strip()
                    if capacity_str:
                        capacity_bytes = int(capacity_str)
                        total_ram_mb += capacity_bytes // (1024 * 1024)  # Convert bytes to MB
                except:
                    pass
    
    # Network Interfaces and MAC Addresses
    network_interfaces = []
    mac_addresses = []
    
    # Get network adapters
    nics = run_cmd("wmic nic where \"NetEnabled='True'\" get name,macaddress,netconnectionid /format:list")
    current_adapter = {}
    if nics:
        for line in nics.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("Name="):
                current_adapter["name"] = line.split("=", 1)[-1].strip()
            elif line.startswith("MACAddress="):
                mac = line.split("=", 1)[-1].strip()
                if mac and mac != "" and mac != "00:00:00:00:00:00":
                    current_adapter["mac"] = mac
                    if mac not in mac_addresses:
                        mac_addresses.append(mac)
            elif line.startswith("NetConnectionID="):
                current_adapter["connection_id"] = line.split("=", 1)[-1].strip()
                if current_adapter.get("name"):
                    network_interfaces.append(current_adapter.copy())
                current_adapter = {}
    
    # Get IP addresses for each interface
    ipconfig = run_cmd("ipconfig /all")
    for adapter in network_interfaces:
        adapter["ip_addresses"] = []
        adapter_name = adapter.get("connection_id", adapter.get("name", ""))
        if adapter_name:
            # Parse ipconfig output to find IPs for this adapter
            in_section = False
            for line in ipconfig.splitlines():
                if adapter_name in line:
                    in_section = True
                elif in_section and "IPv4 Address" in line:
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if ip_match:
                        adapter["ip_addresses"].append(ip_match.group(1))
                elif in_section and "---" in line:
                    in_section = False
    
    # OS Information
    os_version = platform.version()
    os_name = f"Windows {platform.release()}"
    
    # Generate unique device ID
    try:
        # Try to get Windows machine GUID (more stable than hostname)
        machine_guid = run_cmd('wmic csproduct get uuid /format:list')
        uuid_str = ""
        for line in machine_guid.splitlines():
            if "UUID=" in line:
                uuid_str = line.split("=", 1)[-1].strip()
                break
        
        if uuid_str and uuid_str != "":
            device_id = uuid_str
        else:
            # Fallback to hostname-based ID
            device_id = f"{hostname}-{serial_number[:8] if serial_number else 'windows'}"
    except:
        device_id = f"{hostname}-{platform.machine()}"
    
    return {
        "device_id": device_id,
        "os_info": {
            "os_name": os_name,
            "os_version": os_version,
            "hostname": hostname,
            "architecture": platform.machine()
        },
        "system_info": {
            "vendor": vendor or "Unknown",
            "model": model or "Unknown",
            "serial_number": serial_number or "Unknown"
        },
        "bios_info": {
            "vendor": bios_vendor or "Unknown",
            "version": bios_version or "Unknown",
            "date": bios_date or "Unknown"
        },
        "motherboard_info": {
            "vendor": motherboard_vendor or "Unknown",
            "model": motherboard_model or "Unknown",
            "serial_number": motherboard_serial or "Unknown"
        },
        "cpu_info": {
            "model": cpu_model or "Unknown",
            "cores": cpu_cores,
            "threads": cpu_threads,
            "speed_mhz": cpu_speed_mhz,
            "speed_ghz": round(cpu_speed_mhz / 1000.0, 2) if cpu_speed_mhz > 0 else 0
        },
        "ram_info": {
            "total_mb": total_ram_mb,
            "total_gb": round(total_ram_mb / 1024.0, 2) if total_ram_mb > 0 else 0
        },
        "network_info": {
            "interfaces": network_interfaces,
            "mac_addresses": mac_addresses
        }
    }


def detect_macos_hardware() -> Dict:
    """Detect hardware on macOS using system_profiler"""
    sys_name = platform.system()
    hostname = socket.gethostname()
    
    # System Information
    hw_data = run_cmd("system_profiler SPHardwareDataType")
    vendor = "Apple"
    model = ""
    serial_number = ""
    cpu_model = ""
    cpu_cores = 0
    
    for line in hw_data.splitlines():
        line = line.strip()
        if "Model Name:" in line:
            model = line.split(":", 1)[-1].strip()
        if "Model Identifier:" in line:
            model_id = line.split(":", 1)[-1].strip()
            if not model:
                model = model_id
        if "Serial Number (system):" in line or "Serial Number:" in line:
            serial_number = line.split(":", 1)[-1].strip()
        if "Chip:" in line or "Processor Name:" in line:
            cpu_model = line.split(":", 1)[-1].strip()
        if "Total Number of Cores:" in line:
            try:
                cpu_cores = int(line.split(":", 1)[-1].strip())
            except:
                pass
    
    # Memory Information
    mem_data = run_cmd("system_profiler SPHardwareDataType | grep Memory")
    total_ram_mb = 0
    for line in mem_data.splitlines():
        if "Memory:" in line:
            mem_str = line.split(":", 1)[-1].strip()
            # Parse "16 GB" format
            mem_match = re.search(r'(\d+)\s*GB', mem_str, re.IGNORECASE)
            if mem_match:
                total_ram_mb = int(mem_match.group(1)) * 1024
            else:
                mem_match = re.search(r'(\d+)\s*MB', mem_str, re.IGNORECASE)
                if mem_match:
                    total_ram_mb = int(mem_match.group(1))
    
    # Network Interfaces
    network_data = run_cmd("system_profiler SPNetworkDataType")
    network_interfaces = []
    mac_addresses = []
    
    current_if = {}
    for line in network_data.splitlines():
        line = line.strip()
        if "Type:" in line and ":" in line:
            if current_if.get("name"):
                network_interfaces.append(current_if.copy())
            current_if = {"type": line.split(":", 1)[-1].strip()}
        elif "Hardware (MAC) Address:" in line or "Ethernet Address:" in line:
            mac = line.split(":", 1)[-1].strip()
            if mac and mac != "":
                current_if["mac"] = mac
                if mac not in mac_addresses:
                    mac_addresses.append(mac)
        elif line.endswith(":") and len(line) > 2 and not line.startswith(" "):
            current_if["name"] = line.rstrip(":")
        elif "IP Address:" in line:
            ip = line.split(":", 1)[-1].strip()
            if "ip_addresses" not in current_if:
                current_if["ip_addresses"] = []
            if ip:
                current_if["ip_addresses"].append(ip)
    
    if current_if.get("name"):
        network_interfaces.append(current_if)
    
    # BIOS/Firmware Information
    firmware = run_cmd(r"system_profiler SPHardwareDataType | grep -i 'boot rom\|efi version\|smc version'")
    bios_vendor = "Apple"
    bios_version = ""
    for line in firmware.splitlines():
        if "Boot ROM Version:" in line or "EFI Version:" in line:
            bios_version = line.split(":", 1)[-1].strip()
    
    # Motherboard (not directly available on Mac, use model)
    motherboard_vendor = "Apple"
    motherboard_model = model
    
    # CPU Speed
    cpu_speed = run_cmd("sysctl -n machdep.cpu.brand_string")
    cpu_speed_mhz = 0
    if cpu_speed:
        cpu_model = cpu_speed.strip()
        # Try to extract speed from model string
        speed_match = re.search(r'(\d+\.?\d*)\s*GHz', cpu_model, re.IGNORECASE)
        if speed_match:
            cpu_speed_mhz = int(float(speed_match.group(1)) * 1000)
    
    # OS Version
    os_version = run_cmd("sw_vers -productVersion")
    os_name = f"macOS {os_version}"
    
    # Generate device ID
    if serial_number:
        device_id = f"macos-{serial_number}"
    else:
        device_id = f"{hostname}-macos"
    
    return {
        "device_id": device_id,
        "os_info": {
            "os_name": os_name,
            "os_version": os_version,
            "hostname": hostname,
            "architecture": platform.machine()
        },
        "system_info": {
            "vendor": vendor,
            "model": model or "Unknown",
            "serial_number": serial_number or "Unknown"
        },
        "bios_info": {
            "vendor": bios_vendor,
            "version": bios_version or "Unknown",
            "date": "Unknown"
        },
        "motherboard_info": {
            "vendor": motherboard_vendor,
            "model": motherboard_model or "Unknown",
            "serial_number": "Unknown"
        },
        "cpu_info": {
            "model": cpu_model or "Unknown",
            "cores": cpu_cores,
            "threads": cpu_cores,  # macOS doesn't always report threads separately
            "speed_mhz": cpu_speed_mhz,
            "speed_ghz": round(cpu_speed_mhz / 1000.0, 2) if cpu_speed_mhz > 0 else 0
        },
        "ram_info": {
            "total_mb": total_ram_mb,
            "total_gb": round(total_ram_mb / 1024.0, 2) if total_ram_mb > 0 else 0
        },
        "network_info": {
            "interfaces": network_interfaces,
            "mac_addresses": mac_addresses
        }
    }


def detect_linux_hardware() -> Dict:
    """Detect hardware on Linux using dmidecode, lscpu, etc."""
    sys_name = platform.system()
    hostname = socket.gethostname()
    
    # System Information (dmidecode -t system)
    system_dmi = run_cmd("sudo dmidecode -t system 2>/dev/null || dmidecode -t system 2>/dev/null")
    vendor = "Unknown"
    model = "Unknown"
    serial_number = "Unknown"
    
    for line in system_dmi.splitlines():
        line = line.strip()
        if "Manufacturer:" in line:
            vendor = line.split(":", 1)[-1].strip()
        if "Product Name:" in line or "Version:" in line:
            if model == "Unknown":
                model = line.split(":", 1)[-1].strip()
        if "Serial Number:" in line:
            serial_number = line.split(":", 1)[-1].strip()
    
    # BIOS Information (dmidecode -t bios)
    bios_dmi = run_cmd("sudo dmidecode -t bios 2>/dev/null || dmidecode -t bios 2>/dev/null")
    bios_vendor = "Unknown"
    bios_version = "Unknown"
    bios_date = "Unknown"
    
    for line in bios_dmi.splitlines():
        line = line.strip()
        if "Vendor:" in line:
            bios_vendor = line.split(":", 1)[-1].strip()
        if "Version:" in line:
            bios_version = line.split(":", 1)[-1].strip()
        if "Release Date:" in line:
            bios_date = line.split(":", 1)[-1].strip()
    
    # Motherboard Information (dmidecode -t baseboard)
    mb_dmi = run_cmd("sudo dmidecode -t baseboard 2>/dev/null || dmidecode -t baseboard 2>/dev/null")
    motherboard_vendor = "Unknown"
    motherboard_model = "Unknown"
    motherboard_serial = "Unknown"
    
    for line in mb_dmi.splitlines():
        line = line.strip()
        if "Manufacturer:" in line:
            motherboard_vendor = line.split(":", 1)[-1].strip()
        if "Product Name:" in line:
            motherboard_model = line.split(":", 1)[-1].strip()
        if "Serial Number:" in line:
            motherboard_serial = line.split(":", 1)[-1].strip()
    
    # CPU Information (lscpu)
    cpu_info = run_cmd("lscpu")
    cpu_model = "Unknown"
    cpu_cores = 0
    cpu_threads = 0
    cpu_speed_mhz = 0
    
    for line in cpu_info.splitlines():
        line = line.strip()
        if "Model name:" in line:
            cpu_model = line.split(":", 1)[-1].strip()
        if "CPU(s):" in line and "Core(s)" not in line and "Socket(s)" not in line:
            try:
                cpu_threads = int(line.split(":", 1)[-1].strip())
            except:
                pass
        if "Core(s) per socket:" in line:
            try:
                cores_per_socket = int(line.split(":", 1)[-1].strip())
                sockets = 1
                for sock_line in cpu_info.splitlines():
                    if "Socket(s):" in sock_line:
                        try:
                            sockets = int(sock_line.split(":", 1)[-1].strip())
                        except:
                            pass
                cpu_cores = cores_per_socket * sockets
            except:
                pass
        if "CPU max MHz:" in line:
            try:
                cpu_speed_mhz = int(float(line.split(":", 1)[-1].strip()))
            except:
                pass
        elif "CPU MHz:" in line and cpu_speed_mhz == 0:
            try:
                cpu_speed_mhz = int(float(line.split(":", 1)[-1].strip()))
            except:
                pass
    
    # RAM Information (free -m)
    mem_info = run_cmd("free -m")
    total_ram_mb = 0
    for line in mem_info.splitlines():
        if "Mem:" in line:
            parts = line.split()
            if len(parts) >= 2:
                try:
                    total_ram_mb = int(parts[1])
                except:
                    pass
    
    # Network Interfaces (ip link)
    network_interfaces = []
    mac_addresses = []
    
    ip_link = run_cmd("ip link show")
    current_if = {}
    for line in ip_link.splitlines():
        line = line.strip()
        if line.startswith(("1:", "2:", "3:", "4:", "5:", "6:", "7:", "8:", "9:")):
            if current_if.get("name"):
                network_interfaces.append(current_if.copy())
            parts = line.split(":", 2)
            if len(parts) >= 3:
                current_if = {"name": parts[1].strip()}
        elif "link/ether" in line:
            mac_match = re.search(r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})', line)
            if mac_match:
                mac = mac_match.group(1)
                current_if["mac"] = mac
                if mac not in mac_addresses:
                    mac_addresses.append(mac)
    
    if current_if.get("name"):
        network_interfaces.append(current_if)
    
    # Get IP addresses for interfaces
    ip_addr = run_cmd("ip addr show")
    for adapter in network_interfaces:
        adapter["ip_addresses"] = []
        adapter_name = adapter.get("name", "")
        if adapter_name:
            in_section = False
            for line in ip_addr.splitlines():
                if adapter_name in line and "inet " in line:
                    ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                    if ip_match:
                        adapter["ip_addresses"].append(ip_match.group(1))
    
    # OS Information
    os_version = run_cmd("lsb_release -d 2>/dev/null | cut -f2") or platform.release()
    os_name = f"Linux {os_version}"
    
    # Generate device ID
    if serial_number and serial_number != "Unknown":
        device_id = f"linux-{serial_number[:16]}"
    else:
        device_id = f"{hostname}-linux"
    
    return {
        "device_id": device_id,
        "os_info": {
            "os_name": os_name,
            "os_version": os_version,
            "hostname": hostname,
            "architecture": platform.machine()
        },
        "system_info": {
            "vendor": vendor,
            "model": model,
            "serial_number": serial_number
        },
        "bios_info": {
            "vendor": bios_vendor,
            "version": bios_version,
            "date": bios_date
        },
        "motherboard_info": {
            "vendor": motherboard_vendor,
            "model": motherboard_model,
            "serial_number": motherboard_serial
        },
        "cpu_info": {
            "model": cpu_model,
            "cores": cpu_cores,
            "threads": cpu_threads,
            "speed_mhz": cpu_speed_mhz,
            "speed_ghz": round(cpu_speed_mhz / 1000.0, 2) if cpu_speed_mhz > 0 else 0
        },
        "ram_info": {
            "total_mb": total_ram_mb,
            "total_gb": round(total_ram_mb / 1024.0, 2) if total_ram_mb > 0 else 0
        },
        "network_info": {
            "interfaces": network_interfaces,
            "mac_addresses": mac_addresses
        }
    }


def detect_hardware() -> Dict:
    """
    Main function to detect hardware based on OS
    Returns comprehensive hardware information exactly like Prey Project
    """
    sys_name = platform.system().lower()
    
    if sys_name == "windows":
        return detect_windows_hardware()
    elif sys_name == "darwin":
        return detect_macos_hardware()
    else:
        return detect_linux_hardware()


if __name__ == "__main__":
    # Test hardware detection
    hardware = detect_hardware()
    print(json.dumps(hardware, indent=2))