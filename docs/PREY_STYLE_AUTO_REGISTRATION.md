# Prey Project-Style Automatic Device Registration

## Overview

The system now works EXACTLY like Prey Project with fully automatic device registration. No manual config.json edits, no browser-based detection - only native hardware detection from the Python agent.

## Automatic Registration Flow

### 1. User Registration

When a user registers a new account:
1. Backend creates user account
2. Backend generates `device_link_token` (UUID, expires in 5 minutes)
3. Token is stored in database linked to `user_id`
4. Frontend receives token and automatically downloads `device_link_token.txt`

### 2. Agent Auto-Registration

On agent startup (`python agent.py`):

**Method 1: Token File (Primary)**
- Agent checks for `device_link_token.txt` in `device_agent/` folder
- If found, reads token
- Detects REAL hardware information using native OS commands
- Registers device with backend using token + hardware info
- Token is automatically marked as used

**Method 2: Polling (Backup)**
- If no token file found, agent polls backend: `GET /api/devices/pending-link?user_email=...`
- If pending token exists, uses it to register
- Only works if `user_email` is in `config.json` (optional)

### 3. Hardware Detection

The agent automatically detects REAL hardware using native OS commands:

**Windows:**
- WMIC commands for system, BIOS, motherboard, CPU, RAM, network
- Serial numbers, vendor, model, MAC addresses

**macOS:**
- `system_profiler SPHardwareDataType`
- `system_profiler SPNetworkDataType`
- `sw_vers`

**Linux:**
- `dmidecode`, `lscpu`, `free -m`, `ip link`
- `hostnamectl`, `lsb_release`

### 4. Device Registration

Device is automatically created with:
- Real hardware information (vendor, model, serial, BIOS, CPU, RAM, network)
- Automatic device naming: "ASUS TUF Gaming A15 – Windows 11"
- Linked to correct user account
- `device_type = "agent_device"`

### 5. Frontend Display

Device appears automatically in dashboard with:
- System information (vendor, model, serial)
- Motherboard details
- BIOS information
- CPU (model, cores, threads, speed)
- RAM (total capacity)
- Network interfaces with MAC addresses

## API Endpoints

### `GET /api/devices/pending-link`
- Agent polls this to check for pending tokens
- Parameter: `user_email` (optional)
- Returns: `{has_token: true/false, token: "...", expires_at: "..."}`

### `POST /api/devices/agent/auto-register`
- Agent registers device with token and hardware info
- Payload: `{device_link_token, os_info, system_info, bios_info, motherboard_info, cpu_info, ram_info, network_info}`
- Validates token, creates/updates device, marks token as used

## User Instructions

### For New Users:

1. **Sign up** on the web dashboard
2. Browser automatically downloads `device_link_token.txt`
3. **Save the file** to the `device_agent/` folder on your computer
4. **Start the agent**: `python agent.py`
5. Agent automatically:
   - Reads token file
   - Detects hardware
   - Registers device
   - Device appears in dashboard

### No Manual Configuration Required!

- No `config.json` edits needed
- No email/password setup in agent
- No helper scripts to run
- Everything is automatic

## Agent Startup Sequence

```
1. Agent starts
2. Check for device_link_token.txt file
   ├─ If found → Detect hardware → Register with token
   └─ If not found → Poll backend for pending tokens
       ├─ If token found → Detect hardware → Register
       └─ If no token → Use manual registration (requires config.json)
3. Load config.json (if exists)
4. Start normal agent operations
```

## Token File Location

The agent looks for the token file at:
- `device_agent/device_link_token.txt`

After successful registration, the token file is automatically deleted (one-time use).

## Device Naming Examples

- "ASUS TUF Gaming A15 FA507NU_FA507NU – Windows 11"
- "MacBook Air – macOS Sonoma"
- "Dell XPS 13 – Ubuntu 22.04"

Format: `{Vendor} {Model} – {OS Name}`

## Security

- Tokens expire after 5 minutes
- Tokens are single-use (marked as used after registration)
- Tokens are linked to specific user accounts
- Hardware info is collected locally (never exposed to browser)

## Troubleshooting

### Device doesn't appear after registration
- Check agent logs for registration errors
- Verify backend is running
- Ensure token file is in correct location
- Token may have expired (create new account or get new token)

### Hardware info shows "Unknown"
- Verify agent has proper permissions (especially Linux)
- Check hardware detection module is available
- Review agent logs for detection errors

### Token file not found
- Make sure file is saved to `device_agent/` folder
- Check file is named exactly `device_link_token.txt`
- Verify file contains only the token (no extra text)

## Differences from Browser-Based Detection

✅ **Uses native OS commands** - Real hardware detection  
✅ **No browser required** - Agent runs independently  
✅ **Automatic registration** - No manual setup  
✅ **Prey Project accuracy** - Same level of hardware detail  
❌ **No browser detection** - Removed completely  
❌ **No fake device info** - All data from real hardware  

## Implementation Files

- `backend/routes/user_routes.py` - Token generation on registration
- `backend/routes/device_routes.py` - Auto-registration endpoints
- `device_agent/agent.py` - Auto-registration logic
- `device_agent/hardware_detection.py` - Native hardware detection
- `frontend/src/pages/SignUp.jsx` - Token file download
- `frontend/src/pages/DeviceDetail.jsx` - Hardware info display
