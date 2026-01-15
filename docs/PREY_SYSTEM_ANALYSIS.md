# Prey Anti-Theft System Analysis

## Overview
Prey is an anti-theft application that tracks and locates lost or stolen devices. The system consists of a client agent installed on devices (Windows, Mac, Linux) that communicates with a remote control panel server.

## System Architecture

### Directory Structure
```
C:\Windows\Prey\
├── prey.conf              # Main configuration file
├── prey.log               # Main application log
├── winsvc.log             # Windows service log
├── prey_restarts.log      # Restart timestamps
├── commands.db            # SQLite database for commands/storage
├── wpxsvc.exe             # Windows service executable (Go-based)
├── Uninstall.exe          # Uninstaller
└── versions/              # Versioned installations
    ├── 1.13.22/           # Previous version
    └── 1.13.24/           # Current version (latest)
        ├── bin/           # Executables
        ├── lib/           # Core libraries
        └── node_modules/  # Dependencies
```

### Current Configuration
- **API Key**: `cd2c7bebaca836003c38a7f4`
- **Device Key**: `75a0d6`
- **Control Panel Host**: `solid.preyproject.com`
- **Protocol**: HTTPS
- **Current Version**: 1.13.24
- **Node.js Version**: v22.17.1

## Core Components

### 1. Windows Service (wpxsvc.exe)
- **Language**: Go
- **Purpose**: Monitors and manages the Prey agent process
- **Functions**:
  - Monitors if the Prey Node.js process is running
  - Automatically restarts the agent if it crashes
  - Checks for service updates
  - Provides health check endpoints
  - Manages firewall rules
  - Removes old "fenix" scheduler tasks

### 2. Main Agent (Node.js Application)
- **Entry Point**: `lib/agent/cli.js`
- **Main Module**: `lib/agent/index.js`
- **Runtime**: Node.js v22.17.1

#### Key Modules:

**a) Control Panel Communication (`lib/agent/control-panel/`)**
- **WebSockets**: Real-time bidirectional communication
- **HTTP API**: RESTful API for sending reports and receiving commands
- **Long Polling**: Fallback communication method
- **Setup**: Device registration and configuration

**b) Actions (`lib/agent/actions/`)**
Remote actions that can be triggered from the control panel:
- **Alarm**: Play sound alerts (mpg123.exe, unmuter.exe, voladjust.exe)
- **Alert**: Flash screen notifications
- **Lock**: Lock the device screen (prey-lock.exe, new-prey-lock.exe)
- **Screenshot**: Capture screen (preyshot.exe)
- **Webcam**: Capture photos (prey-webcam.exe, snapshot.exe)
- **File Retrieval**: Upload specific files
- **Log Retrieval**: Upload log files
- **Wipe**: Delete files (wipe-win.exe)
- **Full Wipe**: Complete disk wipe (dskwipe.exe)
- **Factory Reset**: Reset to factory settings (factory-reset.ps1)
- **Disk Encryption**: Manage encryption status
- **Sync Settings**: Synchronize configuration

**c) Providers (`lib/agent/providers/`)**
Data collection modules:
- **Geo**: Location tracking (WiFi, GPS, GeoIP)
- **Hardware**: System specifications and hardware info
- **Network**: Network interfaces and connections
- **Screenshot**: Screen capture
- **Webcam**: Camera access
- **Users**: Logged-in users
- **Processes**: Running processes
- **Files**: File system information
- **Bandwidth**: Network usage
- **Connections**: Active network connections
- **LAN**: Local network information
- **System**: OS information
- **Indicators**: System status indicators

**d) Triggers (`lib/agent/triggers/`)**
Event-based monitoring:
- **Connection**: Network connectivity changes
- **Location**: Location updates
- **Power**: Battery/power status
- **Network**: Network interface changes
- **Hostname**: Computer name changes
- **Status**: Periodic status checks
- **Auto-connect**: Automatic WiFi connection (wifion.exe)

**e) Reports (`lib/agent/reports/`)**
Data reporting to control panel:
- **Specs**: Hardware specifications
- **Status**: Current device status
- **Actions**: Action execution reports
- **Stolen**: Theft mode reports

**f) Commands (`lib/agent/commands.js`)**
Command processing and execution:
- Parses commands from control panel
- Executes actions
- Watches for new commands
- Stores pending commands

**g) Updater (`lib/agent/updater.js`)**
Automatic updates:
- Checks for new versions
- Downloads updates from `downloads.preyproject.com`
- Validates checksums (SHA)
- Installs new versions
- Manages version directories

**h) Hooks (`lib/agent/hooks.js`)**
Event system for inter-module communication

**i) Storage (`lib/agent/utils/storage/`)**
SQLite database for:
- Configuration persistence
- Command storage
- Device state

## System Workflow

### 1. Startup Sequence
1. Windows service (`wpxsvc.exe`) starts on boot
2. Service checks if Prey agent process is running
3. If not running, starts: `node.exe lib/agent/cli.js`
4. Agent loads configuration from `prey.conf`
5. Agent initializes:
   - Loads control panel connection
   - Sets up WebSocket connection
   - Starts triggers (monitoring)
   - Begins periodic status reports

### 2. Communication Flow
1. **WebSocket Connection**: Primary real-time communication
   - Connects to `wss://solid.preyproject.com`
   - Receives commands instantly
   - Sends status updates

2. **HTTP API**: Fallback and reporting
   - Sends reports (specs, status, actions)
   - Receives configuration updates
   - Health checks

3. **Long Polling**: Legacy fallback method

### 3. Command Execution
1. Control panel sends command via WebSocket
2. Agent receives command in `commands.js`
3. Command is parsed and validated
4. Appropriate action is executed
5. Results are reported back to control panel

### 4. Location Tracking
Multiple strategies (in order):
1. **WiFi Location**: Scans nearby WiFi networks, sends to geolocation service
2. **GPS/Windows Geolocation**: Uses Windows location APIs
3. **GeoIP**: IP-based location as fallback

### 5. Update Process
1. Updater checks for new versions every 3 hours (if enabled)
2. Downloads new version ZIP from `downloads.preyproject.com`
3. Validates SHA checksum
4. Extracts to `versions/[version]/`
5. Updates `current` symlink
6. Restarts agent with new version

## Windows-Specific Components

### Executables in `lib/system/windows/bin/`:
- **wpxsvc.exe**: Windows service (monitor)
- **autowc.exe**: Auto WiFi connection
- **autowcxp.exe**: Auto WiFi connection (XP)
- **safexec.exe**: Safe execution wrapper
- **updater.exe**: Update manager
- **wlanscan.exe**: WiFi network scanner
- **wapi.dll**: Windows API library
- **wzcapis.dll**: WiFi API library

### Registry Management
- Stores configuration in Windows Registry
- Manages service registration
- Handles permissions

## Security Features

1. **Encryption**: RSA encryption for sensitive data
2. **Authentication**: API key + Device key authentication
3. **Firewall Rules**: Automatically manages Windows Firewall
4. **Permissions**: Requests necessary OS permissions
5. **Secure Communication**: HTTPS/WSS only

## Logging

- **prey.log**: Main application log (very large, 1.6MB+)
- **winsvc.log**: Service monitoring log
- **prey_restarts.log**: Timestamps of restarts

## Database

- **commands.db**: SQLite database
  - Stores configuration
  - Command queue
  - Device state
  - Hardware tracking

## Configuration File Structure

```ini
# Main settings
auto_connect = [true/false]
auto_update = true
send_crash_reports = true
try_proxy = [proxy URL]

# Control Panel
[control-panel]
host = solid.preyproject.com
protocol = https
api_key = [your API key]
device_key = [your device key]
send_status_info = true
location_aware = true
```

## Key Features

1. **Remote Tracking**: Real-time location updates
2. **Remote Control**: Execute actions remotely
3. **Data Protection**: File retrieval, wipe, lock
4. **Stealth Mode**: Runs as system service
5. **Auto-Recovery**: Service auto-restarts agent
6. **Multi-Strategy Location**: WiFi, GPS, GeoIP
7. **Hardware Tracking**: Detects hardware changes
8. **Cross-Platform**: Windows, Mac, Linux support

## Monitoring & Maintenance

The Windows service (`wpxsvc.exe`) continuously:
- Monitors agent health
- Checks for updates
- Reports status to control panel
- Manages process lifecycle
- Handles errors gracefully

## Version Management

- Multiple versions stored in `versions/` directory
- `current` symlink points to active version
- Old versions retained for rollback capability
- Automatic cleanup of old versions

## Network Communication

- **Outbound Only**: Agent initiates all connections
- **No Inbound Ports**: Uses WebSocket/HTTP polling
- **Proxy Support**: Can use HTTP proxy
- **Auto-Connect**: Can connect to open WiFi if offline

## Error Handling

- Graceful shutdown on signals
- Automatic restart on crashes
- Network error recovery
- Crash report submission (if enabled)

## Dependencies

Major Node.js packages:
- `ws`: WebSocket client
- `needle`: HTTP client
- `systeminformation`: System info
- `sqlite3`: Database
- `node-schedule`: Task scheduling
- `archiver`: File compression
- And many more...

## Development Notes

- Open source: https://github.com/prey/prey-node-client
- License: GPLv3
- Written in: Node.js (agent), Go (Windows service)
- Cross-platform architecture with OS-specific modules
