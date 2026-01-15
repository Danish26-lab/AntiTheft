# Fix: Lock Screen Not Appearing After Clicking Confirm

## Quick Diagnosis

Run this to check everything:
```bash
cd device_agent
python check_agent_status.py
```

## Most Common Issue: Agent Not Running

**The agent MUST be running to receive lock commands!**

### Step 1: Start the Agent
```bash
cd device_agent
python agent.py
```

You should see:
```
🤖 Device Agent Starting...
Device ID: Danish-windows
User: admin@antitheft.com
API URL: http://localhost:5000/api
```

### Step 2: Keep It Running
**Don't close the terminal!** The agent must stay running in the background.

## How It Works

1. **You click "Confirm"** in dashboard
2. **Backend** sets device status to `'locked'`
3. **Agent checks** every 10 seconds for status changes
4. **Agent detects** status changed from `'active'` to `'locked'`
5. **Agent launches** lock screen
6. **Lock screen appears** on your computer

## Troubleshooting Steps

### Step 1: Verify Agent is Running
```bash
# Check if agent process is running
tasklist | findstr python
```

You should see `python.exe` or `pythonw.exe` running.

### Step 2: Check Agent Logs
Look at the agent console output. You should see:
- `📡 Status check: Current=active, Server=locked` (when status changes)
- `🔔 COMMAND DETECTED: LOCK` (when command detected)
- `🔒 Executing LOCK command` (when executing)
- `✅ Lock screen process started (PID: xxxx)` (when launched)

### Step 3: Test Lock Screen Directly
```bash
cd device_agent
python test_lock_command.py
```

If this works, the lock screen script is fine. The issue is with agent-backend communication.

### Step 4: Check Backend Status
Make sure backend is running:
```bash
cd backend
python app.py
```

### Step 5: Verify Device Status
Run the status checker:
```bash
cd device_agent
python check_agent_status.py
```

This will show:
- If backend is connected
- Current device status
- Recent lock commands in logs

## Common Problems

### Problem 1: Agent Not Running
**Solution:** Start the agent and keep it running
```bash
cd device_agent
python agent.py
```

### Problem 2: Agent Not Detecting Status Change
**Wait up to 10 seconds** - the agent checks every 10 seconds.

**Check agent console** for:
- `Status check: Current=active, Server=locked`
- If you don't see this, the agent might not be checking properly

### Problem 3: Lock Screen Process Fails
**Check agent logs** for:
- `❌ Lock screen process exited immediately`
- This means the lock screen script had an error

**Solution:** Test the lock screen directly:
```bash
cd device_agent
python prey_lock_screen.py test123 "Test message"
```

### Problem 4: Backend Not Running
**Solution:** Start the backend:
```bash
cd backend
python app.py
```

## Expected Behavior

When you click "Confirm":

1. ✅ Dashboard shows: "Screen lock command sent!"
2. ✅ Backend sets device status to 'locked' (check database or logs)
3. ✅ Agent detects status change (within 10 seconds)
   - Look for: `📡 Status check: Current=active, Server=locked`
4. ✅ Agent executes lock command
   - Look for: `🔔 COMMAND DETECTED: LOCK`
   - Look for: `🔒 Executing LOCK command`
5. ✅ Lock screen launches
   - Look for: `✅ Lock screen process started (PID: xxxx)`
6. ✅ Lock screen appears on your computer

## Still Not Working?

1. **Check agent is running:**
   ```bash
   cd device_agent
   python agent.py
   ```

2. **Check backend is running:**
   ```bash
   cd backend
   python app.py
   ```

3. **Test lock screen directly:**
   ```bash
   cd device_agent
   python test_lock_command.py
   ```

4. **Check agent logs:**
   - Look at the agent console output
   - Check `device_agent/agent.log` file

5. **Run status checker:**
   ```bash
   cd device_agent
   python check_agent_status.py
   ```

## Quick Test

1. Start agent: `cd device_agent && python agent.py`
2. In another terminal, test lock: `cd device_agent && python test_lock_command.py`
3. If test works but dashboard doesn't, the issue is agent-backend communication
4. Check agent console for error messages

