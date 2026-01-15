#!/usr/bin/env python3
"""
Register this device via the native agent using a short-lived device_link_token.
No email, no config edits. Intended to run automatically from the agent.
"""
import os
import platform
import socket
import subprocess
import requests
from pathlib import Path

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000/api')
TOKEN_ENV = 'DEVICE_LINK_TOKEN'
TOKEN_FILE = Path(__file__).parent / 'device_link_token.txt'


def read_token():
    token = os.getenv(TOKEN_ENV)
    if token:
        return token.strip()
    if TOKEN_FILE.exists():
        try:
            return TOKEN_FILE.read_text(encoding='utf-8').strip()
        except Exception:
            return None
    return None


def clear_token():
    if TOKEN_FILE.exists():
        try:
            TOKEN_FILE.unlink()
        except Exception:
            pass


def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL, timeout=5)
        return out.strip()
    except Exception:
        return ""


def detect_windows():
    os_name = "Windows"
    os_version = platform.version()
    brand = run_cmd("wmic computersystem get manufacturer").splitlines()
    model = run_cmd("wmic computersystem get model").splitlines()
    cpu = run_cmd("wmic cpu get name").splitlines()
    brand = brand[1].strip() if len(brand) > 1 else ""
    model = model[1].strip() if len(model) > 1 else ""
    cpu_info = cpu[1].strip() if len(cpu) > 1 else ""
    return os_name, os_version, brand, model, cpu_info


def detect_mac():
    os_name = "macOS"
    os_version = run_cmd("sw_vers -productVersion") or platform.mac_ver()[0]
    hw = run_cmd("system_profiler SPHardwareDataType")
    brand = "Apple"
    model = ""
    cpu_info = ""
    for line in hw.splitlines():
        l = line.strip()
        if l.lower().startswith("model identifier"):
            model = l.split(":", 1)[-1].strip()
        if l.lower().startswith("chip") or l.lower().startswith("processor name"):
            cpu_info = l.split(":", 1)[-1].strip()
    return os_name, os_version, brand, model, cpu_info


def detect_linux():
    os_name = "Linux"
    os_version = run_cmd("lsb_release -d").split(":", 1)[-1].strip() if run_cmd("which lsb_release") else platform.release()
    brand = ""
    model = ""
    cpu_info = ""
    hw = run_cmd("hostnamectl")
    for line in hw.splitlines():
        l = line.strip().lower()
        if l.startswith("hardware model"):
            model = line.split(":", 1)[-1].strip()
        if l.startswith("hardware vendor"):
            brand = line.split(":", 1)[-1].strip()
    if not brand or not model:
        dmi_brand = run_cmd("sudo dmidecode -s system-manufacturer")
        if dmi_brand:
            brand = dmi_brand.strip()
        dmi_model = run_cmd("sudo dmidecode -s system-product-name")
        if dmi_model:
            model = dmi_model.strip()
    cpu_info = run_cmd("lscpu | grep 'Model name'").split(":", 1)[-1].strip()
    return os_name, os_version, brand, model, cpu_info


def collect_hardware():
    sys_name = platform.system().lower()
    hostname = socket.gethostname()
    arch = platform.machine()
    if sys_name == "windows":
        os_name, os_version, brand, model, cpu_info = detect_windows()
    elif sys_name == "darwin":
        os_name, os_version, brand, model, cpu_info = detect_mac()
    else:
        os_name, os_version, brand, model, cpu_info = detect_linux()

    device_id = f"{hostname}-{sys_name}"
    device_class = "desktop" if sys_name in ["windows", "linux", "darwin"] else "mobile"

    return {
        "device_id": device_id,
        "os_name": os_name,
        "os_version": os_version,
        "architecture": arch,
        "device_class": device_class,
        "brand": brand,
        "model": model,
        "cpu_info": cpu_info,
        "hostname": hostname,
        "platform": platform.platform(),
    }


def register_with_token():
    token = read_token()
    if not token:
        print("No device_link_token found in env or device_link_token.txt. Skipping.")
        return False

    info = collect_hardware()
    payload = {
        "device_link_token": token,
        **info
    }
    try:
        resp = requests.post(f"{API_BASE_URL}/devices/agent-register", json=payload, timeout=10)
        if resp.status_code in (200, 201):
            print("[SUCCESS] Device registered via token.")
            clear_token()
            return True
        else:
            print(f"[ERROR] Registration failed: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to register via token: {e}")
        return False


def main():
    ok = register_with_token()
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())

