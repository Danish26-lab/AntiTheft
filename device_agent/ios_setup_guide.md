# 📱 iOS Device Setup Guide

This guide will help you connect your iPhone/iPad to the Anti-Theft System.

## Prerequisites

You have **3 options** for running the iOS agent:

### Option 1: Pythonista (Recommended for iOS)
Pythonista is a paid iOS app ($9.99) that allows you to run Python scripts on your iPhone/iPad.

**Download:** [Pythonista 3 on App Store](https://apps.apple.com/app/pythonista-3/id1085978097)

### Option 2: Shortcuts App (Free)
Use Apple's Shortcuts app to automate location reporting (basic support).

### Option 3: Python Script (Mac/Linux)
Run the Python script on a Mac that can access your iPhone's location.

## Setup Instructions

### Method 1: Using Pythonista (Full Support)

1. **Install Pythonista** from the App Store

2. **Transfer Files to Pythonista:**
   - Use iTunes File Sharing or AirDrop to copy these files to Pythonista:
     - `ios_agent.py`
     - `ios_register_device.py`
     - `ios_config.json` (created after registration)

3. **Register Your Device:**
   ```python
   # In Pythonista, run:
   exec(open('ios_register_device.py').read())
   ```
   Or tap the file and run it.

4. **Start the Agent:**
   ```python
   # In Pythonista, run:
   exec(open('ios_agent.py').read())
   ```
   
   **Note:** Pythonista can run in the background using the "Action Extension" or by setting up a scheduled task.

### Method 2: Using Shortcuts App (Basic)

1. **Create a Shortcut:**
   - Open Shortcuts app
   - Tap "+" to create new shortcut
   - Add "Get Current Location"
   - Add "Get Contents of URL" action:
     ```
     POST http://YOUR_BACKEND_URL/api/update_location/YOUR_DEVICE_ID
     Method: POST
     Headers: Content-Type: application/json
     Request Body:
     {
       "lat": [Location Latitude],
       "lng": [Location Longitude],
       "status": "active"
     }
     ```
   - Save shortcut as "Report Location"

2. **Automate the Shortcut:**
   - Set up automation to run periodically
   - Or run manually when needed

### Method 3: Python Script (Mac/Linux)

1. **Install Python dependencies:**
   ```bash
   pip install requests
   ```

2. **Register device:**
   ```bash
   cd device_agent
   python ios_register_device.py
   ```

3. **Run agent:**
   ```bash
   python ios_agent.py
   ```

## Configuration

After registration, a `ios_config.json` file is created with:
```json
{
  "device_id": "your-device-id-ios",
  "user_email": "your-email@example.com"
}
```

## Features

### ✅ Supported Features:
- **Location Reporting:** Uses GPS (CoreLocation) for accurate location
- **Status Updates:** Reports device status to backend
- **Remote Commands:** Receives lock, alarm, wipe commands
- **WiFi Geofencing:** Monitors WiFi connection for geofence breaches
- **Automatic Registration:** Appears in web dashboard automatically

### ⚠️ Limitations:
- **Screen Lock:** iOS doesn't allow programmatic screen lock from Python
- **Data Wipe:** Requires manual action via Find My iPhone
- **Background Execution:** Pythonista has limited background execution

## Troubleshooting

### Agent Not Reporting Location:
1. Check location permissions in Settings > Privacy > Location Services
2. Ensure backend server is running at `http://localhost:5000`
3. Check network connection

### Device Not Appearing in Dashboard:
1. Verify registration completed successfully
2. Check `ios_config.json` exists and has correct device_id
3. Ensure agent is running and reporting status

### Location Inaccurate:
- The agent uses GPS when available (Pythonista)
- Falls back to IP geolocation (less accurate)
- For best accuracy, use Pythonista with location permissions enabled

## Advanced: Scheduled Execution

### Pythonista Automation:
1. Open Pythonista
2. Go to Settings > Extensions
3. Set up "Action Extension" for iOS agent
4. Schedule using iOS Shortcuts automation

### Cron Job (Mac/Linux):
```bash
# Run every 5 minutes
*/5 * * * * cd /path/to/device_agent && python ios_agent.py
```

## Security Notes

- Store credentials securely
- Use HTTPS in production
- Enable device passcode
- Use two-factor authentication for accounts

## Support

For issues or questions:
1. Check logs in `ios_agent.log`
2. Verify backend API is accessible
3. Test network connectivity
4. Check device registration status

---

**Ready to secure your iPhone! 📱🔒**

