# Lock Screen Troubleshooting Guide

## Issue: Nothing happens after clicking "Confirm" in the lock modal

### Quick Fixes

1. **Make sure the device agent is running:**
   ```bash
   cd device_agent
   python agent.py
   ```
   The agent must be running to receive lock commands!

2. **Check agent logs:**
   Look for messages like:
   - `🔔 COMMAND DETECTED: LOCK`
   - `🔒 Executing LOCK command`
   - `✅ Custom lock screen launched`

3. **Test lock command directly:**
   ```bash
   cd device_agent
   python test_lock_command.py
   ```
   This will test if the lock screen works without waiting for the backend.

4. **Verify lock screen files exist:**
   - `device_agent/prey_lock_screen.py` (Prey-style lock screen)
   - `device_agent/lock_screen.py` (fallback lock screen)

### How It Works

1. **Frontend** → Sends lock command to backend with password
2. **Backend** → Sets device status to 'locked' and logs the command
3. **Device Agent** → Checks for status changes every 10 seconds
4. **Agent** → Detects status change and launches lock screen

### Common Issues

#### Issue 1: Agent not running
**Solution:** Start the agent:
```bash
cd device_agent
python agent.py
```

#### Issue 2: Agent not detecting status change
**Solution:** The agent now checks every 10 seconds (was 60 seconds). Wait up to 10 seconds after clicking "Confirm".

#### Issue 3: Lock screen not launching
**Solution:** Test directly:
```bash
cd device_agent
python test_lock_command.py
```

If this works, the issue is with the agent-backend communication.

#### Issue 4: Lock screen appears but can't type password
**Solution:** This is a Windows API issue. The lock screen should still work - try clicking on the password field first.

### Debugging Steps

1. **Check if backend received the command:**
   - Look at backend console/logs
   - Check database: device status should be 'locked'

2. **Check if agent is checking for commands:**
   - Look at agent console/logs
   - Should see: `📡 Status check: Current=active, Server=locked`

3. **Check if lock screen script exists:**
   ```bash
   ls device_agent/prey_lock_screen.py
   ls device_agent/lock_screen.py
   ```

4. **Check agent logs:**
   ```bash
   cat device_agent/agent.log
   ```
   Look for error messages or command detection logs.

### Expected Behavior

When you click "Confirm":
1. ✅ Frontend shows: "Screen lock command sent!"
2. ✅ Backend sets device status to 'locked'
3. ✅ Agent detects status change (within 10 seconds)
4. ✅ Agent launches lock screen
5. ✅ Lock screen appears on your device
6. ✅ Enter password to unlock

### Still Not Working?

1. **Check agent is running:**
   ```bash
   # In device_agent directory
   python agent.py
   ```

2. **Check backend is running:**
   ```bash
   # In backend directory
   python app.py
   ```

3. **Test lock screen directly:**
   ```bash
   cd device_agent
   python prey_lock_screen.py test123 "Test message"
   ```

4. **Check logs:**
   - `device_agent/agent.log` - Agent logs
   - Backend console - Backend logs

### Contact

If none of these solutions work, check:
- Python version (should be 3.7+)
- tkinter installed (usually comes with Python)
- Windows permissions (may need admin for some features)

