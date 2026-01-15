# 📱 Connect iPhone Without Pythonista

**Your Computer IP: `192.168.0.19`**

You don't need Pythonista! Here are easy ways to connect your iPhone:

## Method 1: Use iOS Camera App (Easiest!) 📷

1. **Get QR Code from Dashboard**
   - Create device in web dashboard
   - QR code modal appears automatically

2. **Scan with iPhone Camera**
   - Open Camera app on your iPhone
   - Point at QR code (iOS detects QR codes automatically)
   - Tap the notification banner that appears
   - Copy the connection key text

3. **Connect Using Web Interface**
   - Open Safari on your iPhone
   - Go to: `http://192.168.0.19:3000/qr-scanner`
   - Paste the connection key
   - Click "Connect Device"

## Method 2: Standalone HTML Page (Works Offline!)

1. **Get the HTML file**
   - File is at: `device_agent/ios_web_connect.html`
   - Transfer it to your iPhone (via AirDrop, email, or cloud)

2. **Open on iPhone**
   - Open the HTML file in Safari
   - Click "Start Scanner" 
   - Allow camera access
   - Point at QR code
   - OR paste connection key manually

3. **API URL is already configured**
   - The HTML file is set to use: `http://192.168.0.19:5000`
   - No changes needed!

## Method 3: Manual Key Entry

1. **Get Connection Key**
   - Create device in dashboard
   - Copy the connection key (or scan QR with camera to get the text)

2. **Open Web Interface**
   - Go to: `http://YOUR_COMPUTER_IP:3000/qr-scanner` on iPhone
   - Paste the key in the "Connection Key" field
   - Click "Connect Device"

## Finding Your Computer's IP Address

**Windows:**
```bash
ipconfig
# Look for "IPv4 Address" under your active network adapter
```

**Mac/Linux:**
```bash
ifconfig
# Look for "inet" address
```

**Example:** If your IP is `192.168.1.100`, use:
- Web interface: `http://192.168.1.100:3000/qr-scanner`
- API: `http://192.168.1.100:5000/api`

## Quick Steps Summary

1. ✅ Create device in dashboard → Get QR code
2. ✅ Scan QR with iPhone Camera → Copy the key text
3. ✅ Open `http://192.168.0.19:3000/qr-scanner` on iPhone
4. ✅ Paste key → Click "Connect"
5. ✅ Done! Your iPhone appears in dashboard

## Troubleshooting

- **Can't access web page?** Make sure iPhone and computer are on same WiFi network
- **Connection failed?** Check that backend server is running on port 5000
- **Camera not working?** Use manual key entry instead
- **QR code not detected?** Make sure QR code is clear and well-lit

