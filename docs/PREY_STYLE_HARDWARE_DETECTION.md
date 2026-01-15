# Prey Project-Style Hardware Detection

## Overview

The system now uses **native hardware detection** exactly like Prey Project. It detects real hardware information using OS-specific commands, NOT browser-based detection.

## Implementation

### ✅ Completed Features

1. **Native Hardware Detection Module** (`device_agent/hardware_detection.py`)
   - Windows: Uses WMIC commands to detect system, BIOS, motherboard, CPU, RAM, network
   - macOS: Uses `system_profiler` and system commands
   - Linux: Uses `dmidecode`, `lscpu`, `ip link`, etc.
   - Detects: Vendor, Model, Serial Number, BIOS, Motherboard, CPU, RAM, Network Interfaces, MAC addresses

2. **Database Schema** (Updated)
   - Added 14 new hardware fields to `Device` model
   - Fields: serial_number, bios_vendor, bios_version, motherboard_*, cpu_*, ram_*, network_interfaces, mac_addresses
   - Migration script: `backend/migrate_add_hardware_fields.py` (already run)

3. **Backend API Endpoint**
   - `POST /api/devices/agent/register`
   - Accepts comprehensive hardware information payload
   - Creates or updates device with all hardware details
   - No JWT required (agent-based authentication)

4. **Agent Auto-Registration**
   - Agent automatically detects hardware on startup
   - Sends full hardware info to backend
   - Uses UUID-based device_id (more stable than hostname)
   - Falls back to basic registration if hardware detection fails

5. **Frontend Display**
   - Hardware tab in Device Detail page
   - Displays all hardware info in Prey Project style:
     - System Information
     - Motherboard
     - BIOS
     - CPU
     - RAM
     - Network Interfaces with MAC addresses

## Usage

### Running the Agent

1. **Start the agent:**
   ```bash
   cd device_agent
   python agent.py
   ```

2. **The agent will:**
   - Automatically detect hardware using native OS commands
   - Register with the backend via `/api/devices/agent/register`
   - Send comprehensive hardware information
   - Update the device record with all hardware details

### Viewing Hardware Info

1. Open the web dashboard
2. Go to Devices page
3. Click on a device
4. Click "Hardware Information" tab
5. View all detected hardware details

## Hardware Information Detected

### System
- Vendor (ASUS, Acer, HP, Dell, etc.)
- Model name
- Serial number
- Device ID (UUID-based on Windows)

### BIOS
- Vendor (AMI, Phoenix, Apple, etc.)
- Version
- Release date

### Motherboard
- Vendor
- Model
- Serial number

### CPU
- Full model name
- Number of cores
- Number of threads
- Speed (MHz/GHz)

### RAM
- Total capacity (MB/GB)

### Network
- All network interfaces
- MAC addresses
- IP addresses per interface

## Permissions Required

### Windows
- No special permissions needed
- Uses built-in WMIC commands

### macOS
- No special permissions needed
- Uses standard system commands

### Linux
- Some commands require `sudo` (dmidecode)
- Agent should run with appropriate permissions
- If `sudo` not available, some info may be "Unknown"

## Testing

Test hardware detection directly:
```bash
cd device_agent
python hardware_detection.py
```

This will output JSON with all detected hardware information.

## Architecture

```
┌─────────────────┐
│  agent.py       │
│  (starts up)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ hardware_       │
│ detection.py    │
│ (detects HW)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ POST /api/      │
│ devices/agent/  │
│ register        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Backend         │
│ (stores in DB)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Frontend        │
│ (displays HW)   │
└─────────────────┘
```

## Notes

- **Browser-based detection is NOT used** - only native OS commands
- Device ID is UUID-based on Windows (from WMIC csproduct UUID)
- Hardware info is automatically collected and sent on agent startup
- All hardware fields are optional (gracefully handles missing data)
- Network interfaces stored as JSON array in database
- MAC addresses stored as JSON array in database

## Troubleshooting

### Hardware info shows "Unknown"
- Check if agent has proper permissions (especially on Linux)
- Verify hardware detection module is available
- Check agent logs for hardware detection errors

### Agent registration fails
- Ensure backend is running
- Check user email in config.json matches registered user
- Verify API endpoint is accessible

### Migration issues
- Run migration script manually: `python backend/migrate_add_hardware_fields.py`
- Check database file permissions
- Verify SQLite database exists

## Future Enhancements

- GPU detection (Windows: WMIC path win32_VideoController)
- Storage information (disk size, model)
- Battery information (for laptops)
- Screen resolution (native OS detection)