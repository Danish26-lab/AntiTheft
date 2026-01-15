# Agent-First Architecture (Prey Project Style)

## Overview

This system uses an **Agent-First Architecture** exactly like Prey Project, Absolute, and Find My Device. Devices are registered BEFORE users exist. User registration/login only LINKS an already-existing device to an account.

## Core Principles

1. **Devices First, Users Second**
   - Agent registers device on first startup (no user account needed)
   - Device exists as UNOWNED until user links it
   - User registration/login links the running agent device

2. **No Token Files**
   - No manual token downloads
   - No config.json editing required
   - Fully automatic registration

3. **Hardware Fingerprinting**
   - Stable, unique hardware fingerprint (hashed)
   - Based on UUID, serial numbers, MAC addresses
   - Device identified by fingerprint, not random ID

4. **Local Device Discovery**
   - Agent exposes localhost HTTP endpoint
   - Browser queries agent to discover device_id
   - Automatic linking during registration/login

## Architecture Flow

```
┌─────────────────┐
│  1. User        │
│     Installs    │
│     Agent       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. Agent       │
│     Starts      │
│     (first time)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. Agent       │
│     Detects     │
│     Hardware    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. Agent       │
│     Generates   │
│     Fingerprint │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  5. Agent       │
│     POST /api/  │
│     agent/      │
│     register    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  6. Backend     │
│     Creates     │
│     UNOWNED     │
│     Device      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  7. User        │
│     Registers   │
│     Account     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  8. Browser     │
│     Discovers   │
│     Device via  │
│     localhost   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  9. Backend     │
│     Links       │
│     Device to   │
│     User        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 10. Device      │
│     Appears in  │
│     Dashboard   │
└─────────────────┘
```

## Implementation Details

### 1. Device Fingerprinting

**Location:** `device_agent/fingerprint.py`

Generates stable SHA-256 hash from:
- Machine UUID (Windows: WMIC csproduct UUID)
- Hardware UUID (macOS: system_profiler)
- Machine ID (Linux: /etc/machine-id)
- Serial numbers (system, motherboard, BIOS)
- MAC addresses (sorted, hashed)
- Hostname + OS type (fallback)

**Example fingerprint source:**
```
uuid:12345678-1234-1234-1234-123456789ABC|serial:ABC123456|macs:00:11:22:33:44:55|AA:BB:CC:DD:EE:FF|hostname:MYPC|os:windows
```

**Fingerprint hash:**
```
a1b2c3d4e5f6... (SHA-256)
```

### 2. Agent Auto-Registration

**Location:** `device_agent/agent.py` → `_attempt_auto_registration()`

On agent startup:
1. Check if device already registered (has device_id in config.json)
2. If not registered:
   - Generate hardware fingerprint
   - Detect full hardware information
   - POST to `/api/agent/register` with fingerprint + hardware
   - Save device_id to config.json
3. Start local HTTP server for browser discovery

**No user account required!**

### 3. Backend Device Registration

**Endpoint:** `POST /api/agent/register`

**Logic:**
- Check if fingerprint_hash exists → return existing device_id
- If new → create UNOWNED device (user_id = NULL)
- Store all hardware information
- Return device_id to agent

**Device States:**
- **UNOWNED:** `user_id = NULL` (device registered but not linked)
- **OWNED:** `user_id = <user_id>` (device linked to user)

### 4. Device Linking

**During User Registration/Login:**

Browser:
1. Queries `http://127.0.0.1:9123/device-info` (agent's local server)
2. Gets `device_id` and `fingerprint_hash`
3. Sends `device_id` or `fingerprint_hash` to backend

Backend:
1. Finds device by `device_id` or `fingerprint_hash`
2. Checks if device is unowned (`user_id = NULL`)
3. Links device to user (`user_id = user.id`)
4. Logs linking action

### 5. Local Discovery Server

**Agent exposes:** `http://127.0.0.1:9123/device-info`

**Response:**
```json
{
  "device_id": "Danish-ABC12345",
  "fingerprint_hash": "a1b2c3d4...",
  "status": "registered"
}
```

**Security:**
- Only accessible from localhost (127.0.0.1)
- No authentication needed (local access only)
- CORS headers allow browser access

## Database Schema

### Devices Table

```sql
devices (
  id INTEGER PRIMARY KEY,
  device_id TEXT UNIQUE NOT NULL,
  fingerprint_hash TEXT UNIQUE,        -- NEW: Hardware fingerprint
  name TEXT NOT NULL,
  device_type TEXT,
  user_id INTEGER,                      -- CHANGED: Now nullable (unowned devices)
  registered_at TIMESTAMP,              -- NEW: When device was registered
  created_at TIMESTAMP,
  ...
  -- Hardware fields (serial_number, bios_*, motherboard_*, cpu_*, ram_*, network_*, mac_addresses)
)
```

### Key Changes

1. **fingerprint_hash:** Unique identifier for device (hashed for privacy)
2. **user_id:** Now nullable (devices can exist without owners)
3. **registered_at:** Timestamp of agent-first registration

## API Endpoints

### Agent Endpoints

**POST /api/agent/register**
- Agent registers itself (no user required)
- Payload: `{fingerprint_hash, os_info, hardware_info, agent_version}`
- Returns: `{device_id, message}`

### Device Linking Endpoints

**POST /api/register_user**
- User registration
- Can include `device_id` or `fingerprint_hash` to link device
- Automatically links device if provided

**POST /api/login**
- User login
- Can include `device_id` or `fingerprint_hash` to link device
- Automatically links unowned device if provided

## User Experience

### First Time Setup

1. **Install Agent**
   - Copy agent to device
   - Run: `python agent.py`
   - Agent automatically registers (device appears as UNOWNED)

2. **Create Account**
   - Open web dashboard
   - Click "Sign Up"
   - Browser automatically discovers running agent
   - Device is linked to your account
   - Device appears in dashboard instantly

### No Manual Steps!

- ❌ No token files to download
- ❌ No config.json editing
- ❌ No helper scripts
- ❌ No device ID copying
- ✅ Everything automatic

## Security

### Fingerprint Security

- **Hashed:** Raw hardware data never stored
- **Unique:** One fingerprint = one device
- **Stable:** Doesn't change (unless major hardware replacement)

### Device Linking Security

- **One-to-One:** One device can belong to one user
- **Prevent Duplicates:** Fingerprint ensures no duplicate devices
- **Ownership Verification:** Can't link device already owned by another user

### Local Server Security

- **Localhost Only:** Only accessible from 127.0.0.1
- **No Authentication:** Local access doesn't need auth
- **Read-Only:** Only exposes device_id, no sensitive data

## Comparison to Prey Project

| Feature | Prey Project | This System |
|---------|-------------|-------------|
| Agent-first registration | ✅ | ✅ |
| Hardware fingerprinting | ✅ | ✅ |
| Unowned devices | ✅ | ✅ |
| Automatic linking | ✅ | ✅ |
| Local discovery | ✅ | ✅ |
| Token files | ❌ | ❌ |
| Browser detection | ❌ | ❌ |

## Code Files

### Agent
- `device_agent/fingerprint.py` - Hardware fingerprinting
- `device_agent/hardware_detection.py` - Hardware detection
- `device_agent/agent.py` - Auto-registration + local server

### Backend
- `backend/models.py` - Device model (fingerprint_hash, nullable user_id)
- `backend/routes/device_routes.py` - `/api/agent/register` endpoint
- `backend/routes/user_routes.py` - Device linking on registration/login

### Frontend
- `frontend/src/utils/deviceDiscovery.js` - Local agent discovery
- `frontend/src/pages/SignUp.jsx` - Device linking on registration
- `frontend/src/pages/Login.jsx` - Device linking on login

## Migration Steps

1. **Run Database Migration:**
   ```bash
   python backend/migrate_agent_first_architecture.py
   ```

2. **Restart Backend:**
   - Backend will apply nullable user_id change

3. **Update Existing Agents:**
   - Agents will auto-register with fingerprint on next startup
   - Existing devices will be updated

## Deprecated Code (Can Be Removed)

The following token-based endpoints are deprecated but kept for backward compatibility:
- `POST /api/devices/agent/auto-register` (old token-based)
- `GET /api/devices/pending-link` (token polling)
- `DeviceLinkToken` model (not used in agent-first flow)

These can be removed in a future cleanup if not needed.

## Troubleshooting

### Agent doesn't register
- Check agent logs for fingerprint/hardware detection errors
- Verify backend is accessible
- Check firewall allows outbound connections

### Device not linking on registration
- Verify agent is running (check localhost:9123)
- Check browser console for discovery errors
- Agent must be running BEFORE user registration

### Fingerprint collision (unlikely)
- SHA-256 collision probability is negligible
- If happens, device_id will be unique (hostname-based)
