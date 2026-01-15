# 🔧 Device Setup After Registration

## Problem

When you register a new account, your device won't be automatically detected because the device agent's `config.json` file still has the old/default email address.

## Why This Happens

The device agent uses the `user_email` field in `config.json` to register your device with your account. When you create a new account, the device agent doesn't automatically know about it.

## Solution

After registering a new account, you need to update the `user_email` in your device agent's configuration file.

### Method 1: Using the Helper Script (Recommended)

1. Open a terminal/command prompt
2. Navigate to the `device_agent` folder:
   ```bash
   cd device_agent
   ```
3. Run the update script with your registered email:
   ```bash
   python update_config_email.py your-email@example.com
   ```
4. Restart the device agent:
   ```bash
   python agent.py
   ```

### Method 2: Manual Update

1. Navigate to the `device_agent` folder
2. Open `config.json` in a text editor
3. Find the `user_email` field
4. Update it to match your registered email:
   ```json
   {
     "device_id": "YourDevice-windows",
     "user_email": "your-email@example.com",
     "report_interval": 300,
     "check_commands_interval": 0.2
   }
   ```
5. Save the file
6. Restart the device agent

## Verification

After updating the config and restarting the agent:

1. Check the agent logs - you should see:
   ```
   Device registration successful: Device registered successfully by agent
   ```

2. Go to your dashboard at `http://localhost:3000/devices`
   - Your device should appear in the devices list
   - The device status should be "active"

3. If the device doesn't appear:
   - Check that the email in `config.json` exactly matches your registered email
   - Check the agent logs for error messages
   - Make sure the backend server is running

## Troubleshooting

### Error: "User with email X not found"

This means the email in `config.json` doesn't match any registered account.

**Solution:**
- Make sure you've completed the registration process
- Verify the email in `config.json` exactly matches the email you used to register
- Check for typos or case sensitivity issues

### Device Still Not Appearing

1. **Check agent logs** - Look for error messages in `device_agent/agent.log`
2. **Verify backend is running** - Make sure the backend server is accessible at `http://localhost:5000`
3. **Check network connectivity** - The agent needs to connect to the backend API
4. **Verify device_id** - Make sure the device_id in config.json is unique

## Quick Reference

```bash
# Update email in config
cd device_agent
python update_config_email.py your-email@example.com

# Start the agent
python agent.py

# Check agent status
python check_agent_status.py
```

## Notes

- The device agent automatically registers your device when it starts (if `user_email` is set correctly)
- You only need to update the email once after creating a new account
- If you change your account email, you'll need to update `config.json` again

