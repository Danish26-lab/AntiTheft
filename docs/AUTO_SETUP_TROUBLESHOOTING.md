# 🔧 Auto-Setup Troubleshooting Guide

## Quick Test

1. **Test the auto-setup endpoint:**
   ```bash
   cd device_agent
   python test_auto_setup.py
   ```
   
   This will show you if the backend can detect recent user registrations.

## How Auto-Setup Works

1. **User registers** a new account with email (e.g., `user@example.com`)
2. **Agent is running** with old email (e.g., `admin@antitheft.com`)
3. **Agent checks** for config updates:
   - Every 5 seconds for the first 5 minutes after startup
   - Every 10 seconds after that
   - Immediately when registration fails
4. **Backend detects** recent user registration (within last 30 minutes)
5. **Agent updates** `config.json` automatically
6. **Agent registers** device with new account
7. **Device appears** in dashboard

## Common Issues

### Issue 1: Agent Not Running
**Symptom:** Device never appears in dashboard

**Solution:**
```bash
cd device_agent
python agent.py
```

Make sure the agent is running when you register a new account.

### Issue 2: Agent Has Wrong Email
**Symptom:** Agent logs show "User not found" error

**Solution:**
The agent should auto-update, but if it doesn't:
```bash
cd device_agent
python update_config_email.py your-email@example.com
```

### Issue 3: Backend Not Running
**Symptom:** Agent can't connect to backend

**Solution:**
Make sure backend is running:
```bash
cd backend
python app.py
```

Or use the start script:
```bash
python start_all.py
```

### Issue 4: Timing Issue
**Symptom:** User registered but agent hasn't detected it yet

**Solution:**
- Wait up to 10 seconds (agent checks every 5-10 seconds)
- Or restart the agent to trigger immediate check
- Or manually run: `python test_auto_setup.py` to verify backend can see the registration

## Manual Verification Steps

1. **Check agent is running:**
   ```bash
   # Look for agent process or check agent.log
   tail -f device_agent/agent.log
   ```

2. **Check current config:**
   ```bash
   cat device_agent/config.json
   ```

3. **Test auto-setup endpoint:**
   ```bash
   python device_agent/test_auto_setup.py
   ```

4. **Check backend logs:**
   Look for messages like:
   - "Suggesting auto-setup: device_id=..."
   - Recent user registrations

5. **Check agent logs for:**
   - "🔄 Auto-setup detected: Found recently registered user..."
   - "✅ Config auto-updated successfully!"
   - "✅ Device registration successful after auto-update!"

## Expected Behavior

When auto-setup works correctly, you should see in agent logs:

```
🔍 Checking for automatic configuration updates...
🔄 Auto-setup detected: Found recently registered user user@example.com
   Current config email: admin@antitheft.com
   Attempting automatic configuration update...
✅ Config auto-updated successfully!
   Attempting automatic device registration...
✅ Device registration successful after auto-update!
```

## Still Not Working?

1. **Verify backend is accessible:**
   ```bash
   curl http://localhost:5000/api/check_config_update/YourDeviceId
   ```

2. **Check agent logs:**
   ```bash
   tail -n 50 device_agent/agent.log
   ```

3. **Verify user was created:**
   Check the database or backend logs to confirm the user exists

4. **Try manual update:**
   ```bash
   python device_agent/update_config_email.py your-email@example.com
   python device_agent/agent.py
   ```

