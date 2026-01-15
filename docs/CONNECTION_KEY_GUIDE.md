# 🔑 Connection Key Usage Guide

This guide explains how to connect a physical device to a manually created device entry using a connection key.

## 📋 Overview

When you create a device manually from the web dashboard, you get a **connection key**. Use this key on your physical device to connect it to the dashboard entry.

## 🚀 Step-by-Step Instructions

### Step 1: Create Device in Dashboard

1. Open your web dashboard: `http://localhost:3000`
2. Navigate to **Devices** page
3. Click the **"+ NEW DEVICE"** button (green button in the top right)
4. Fill in the form:
   - **Device Name**: e.g., "My iPhone", "Work Laptop"
   - **Device ID**: e.g., "my-iphone-13", "work-laptop-01" (lowercase, no spaces)
   - **Device Type**: Select from dropdown (Laptop, iPhone, Android, etc.)
5. Click **"Create Device"**
6. **IMPORTANT**: Copy the **Connection Key** shown in the success message!
   - The key looks like: `xKj9mN2pQr5sT8vW1yZ4aB7cD0eF3gH6`

### Step 2: Connect Physical Device

#### For Windows/Mac/Linux Devices:

1. Open a terminal/command prompt on your device
2. Navigate to the `device_agent` folder:
   ```bash
   cd device_agent
   ```
3. Run the registration script with the connection key:
   ```bash
   python register_device.py --connect-key YOUR_CONNECTION_KEY_HERE
   ```
   
   Example:
   ```bash
   python register_device.py --connect-key xKj9mN2pQr5sT8vW1yZ4aB7cD0eF3gH6
   ```

4. The script will:
   - Connect to the backend
   - Use the connection key to link your physical device to the dashboard entry
   - Save configuration to `config.json`

5. Start the agent:
   ```bash
   python agent.py
   ```

#### For iPhone/iPad (iOS):

1. Open **Pythonista** app on your iPhone
2. Navigate to the `device_agent` folder in Pythonista
3. Open the `ios_register_device.py` file
4. Run it with the connection key parameter:
   
   In Pythonista's console, you can edit the script to include:
   ```python
   # At the top of ios_register_device.py, you can set:
   CONNECTION_KEY = "YOUR_CONNECTION_KEY_HERE"
   ```
   
   Or modify the script call to pass arguments (Pythonista supports argparse)

5. Alternatively, you can modify `ios_register_device.py` directly:
   - Find the `main()` function
   - Set `args.connect_key = "YOUR_CONNECTION_KEY_HERE"` before calling `register_device()`

6. After registration, run:
   ```python
   python ios_agent.py
   ```

### Step 3: Verify Connection

1. Go back to the web dashboard
2. Refresh the **Devices** page
3. Your device should now show:
   - Status changed from "pending" to "active"
   - Device location updates
   - Real-time activity logs

## 📝 Alternative Method: Edit Config File

Instead of using command line arguments, you can edit the config file directly:

1. **For Windows/Mac/Linux:**
   - Edit `device_agent/config.json`
   - Add the connection key:
   ```json
   {
     "device_id": "your-device-id",
     "user_email": "admin@antitheft.com",
     "report_interval": 300,
     "check_commands_interval": 60,
     "connection_key": "YOUR_CONNECTION_KEY_HERE"
   }
   ```
   - Then run: `python register_device.py` (without --connect-key)

2. **For iOS:**
   - Edit `device_agent/ios_config.json`
   - Add the connection key in the same way

## ⚠️ Important Notes

- **Connection keys are one-time use**: After a device successfully connects, the key is automatically cleared
- **Keep the key secure**: Don't share it publicly as it allows connecting to your device entry
- **Device ID matching**: The physical device's ID should match or will be updated to match the dashboard entry
- **Status changes**: Device status changes from "pending" → "active" when connected

## 🔧 Troubleshooting

### "Invalid connection key" error
- Make sure you copied the entire key (it's quite long)
- Check that you haven't already used the key (it's one-time use)
- Verify the device entry still exists in the dashboard

### Device doesn't appear after connection
- Check that the backend server is running (`http://localhost:5000`)
- Verify network connectivity
- Check the registration script output for errors
- Refresh the dashboard page

### Connection key expired/used
- If a key was already used, you need to create a new device entry
- Or manually set a new connection key in the database (for advanced users)

## 💡 Tips

- **Save the connection key** in a secure place until you've successfully connected
- **Test connection** before closing the success message
- **Use descriptive device IDs** to easily identify devices
- **Group devices** by purpose (e.g., `work-laptop-01`, `home-iphone-13`)

