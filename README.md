# 🛡️ Smart Anti-Theft and Device Security System

A full-stack web-based Anti-Theft and Security Monitoring System that tracks, monitors, and protects devices in real time — inspired by Prey Project.

## ✨ Features

- **Real-time Device Tracking** - GPS/IP-based location tracking
- **Remote Actions** - Lock, alarm, or wipe devices remotely
- **Activity Logging** - Comprehensive logs of all device activities
- **Geofencing** - GPS and WiFi-based geofencing alerts
- **Breach Monitoring** - Integration with HaveIBeenPwned API
- **Web Dashboard** - Modern React-based admin interface
- **Background Agent** - Automatic device status reporting
- **Email Alerts** - Notifications for security events
- **Multi-Platform Support** - Windows, Mac, Linux, and **iOS (iPhone/iPad)**

## 🏗️ Project Structure

```
smart-antitheft-system/
│
├── backend/
│   ├── app.py                 # Flask application entry point
│   ├── models.py              # Database models
│   ├── routes/
│   │   ├── device_routes.py   # Device management endpoints
│   │   ├── user_routes.py     # User authentication endpoints
│   │   ├── breach_routes.py   # Breach detection endpoints
│   │   └── automation_routes.py  # Automation rules endpoints
│   └── utils/
│       ├── email_alert.py      # Email notification system
│       ├── geofence.py         # Geofencing logic
│       └── scheduler.py        # Background job scheduler
│
├── frontend/
│   ├── src/
│   │   ├── pages/             # React pages
│   │   ├── components/        # Reusable components
│   │   ├── App.jsx            # Main app component
│   │   └── main.jsx           # Entry point
│   └── package.json
│
├── device_agent/
│   ├── agent.py               # Background device agent (Windows/Mac/Linux)
│   ├── ios_agent.py           # iOS device agent (iPhone/iPad)
│   ├── register_device.py     # Device registration script
│   ├── ios_register_device.py # iOS device registration
│   ├── config.json            # Agent configuration
│   ├── ios_config.json        # iOS agent configuration
│   ├── ios_setup_guide.md     # iOS setup instructions
│   └── requirements.txt
│
├── database/
│   └── antitheft.db           # SQLite database (created automatically)
│
├── requirements.txt           # Python dependencies
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### ⚡ Easy One-Click Start (Recommended!)

**Windows (PowerShell):**
```powershell
.\start_all.ps1
```

**Windows (Batch):**
```batch
start_all.bat
```

**Mac/Linux:**
```bash
python3 start_all.py
```

This will start both backend and frontend automatically!

### Manual Setup (Alternative)

### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create .env file (copy from .env.example)
cp .env.example .env

# Run Flask backend
cd backend
python app.py
```

The backend will run on `http://localhost:5000`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will run on `http://localhost:3000`

### 3. Device Agent Setup

```bash
cd device_agent

# Install agent dependencies
pip install -r requirements.txt

# Edit config.json with your device details
# Then run the agent
python agent.py
```

## 🔐 Default Credentials

- **Email:** admin@antitheft.com
- **Password:** admin123

## 📡 API Endpoints

### Authentication
- `POST /api/register_user` - Register new user
- `POST /api/login` - Authenticate and get JWT token
- `GET /api/me` - Get current user info

### Devices
- `POST /api/register_device` - Register new device
- `POST /api/update_location` - Update device location (agent)
- `GET /api/get_devices` - Get all user devices
- `GET /api/get_device_status/:device_id` - Get device status
- `POST /api/trigger_action` - Execute remote action (lock/alarm/wipe)
- `POST /api/mark_as_missing` - Mark device as missing
- `GET /api/get_activity_logs` - Get device activity logs

### Breach Detection
- `GET /api/detect_breach` - Check for credential breaches
- `GET /api/get_breach_reports` - Get breach reports
- `POST /api/mark_breach_resolved` - Mark breach as resolved

### Automation
- `POST /api/automation_task` - Create automation rule
- `GET /api/automation_tasks` - Get automation rules
- `PUT /api/automation_task/:id` - Update automation rule
- `DELETE /api/automation_task/:id` - Delete automation rule

## 🎯 Usage

### Registering a Device

**For Windows/Mac/Linux:**
1. Run `python device_agent/register_device.py` to register
2. Start the agent: `python device_agent/agent.py`
3. View registered devices in the dashboard

**For iPhone/iPad (iOS):**
1. See `device_agent/ios_setup_guide.md` for detailed instructions
2. Install Pythonista app from App Store
3. Transfer and run `ios_register_device.py` in Pythonista
4. Run `ios_agent.py` to start tracking
5. Your iPhone will appear in the web dashboard

### Remote Actions

1. Navigate to the **Devices** page
2. Click **Lock**, **Alarm**, or **Wipe** on any device card
3. The command will be sent to the device agent
4. The agent will execute the command locally

### Breach Monitoring

1. Navigate to **Breach Report** page
2. Click **Check for Breaches**
3. The system checks your email against HaveIBeenPwned database
4. View any detected breaches with severity levels

### Geofencing

1. Create an automation rule with type `geofence`
2. Configure safe zone center and radius
3. Receive alerts when device leaves the zone

## 🔧 Configuration

### Email Alerts

Edit `.env` file with your SMTP credentials:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Google Maps

Add your Google Maps API key to `frontend/.env`:

```env
VITE_GOOGLE_MAPS_API_KEY=AIzaSyDxWLNVkWMwKjXj6dZwiv4d2CFqz0B9RIQ
```

**Note:** Create the `.env` file in the `frontend` folder, then restart the frontend server.

### Device Agent

Edit `device_agent/config.json`:

```json
{
  "device_id": "your-device-id",
  "user_email": "your-email@example.com",
  "report_interval": 300,
  "check_commands_interval": 60
}
```

## 📊 Background Jobs

The system includes automated background jobs:

- **Daily Status Update** - Marks inactive devices (>24h)
- **Weekly Breach Check** - Scans all users for breaches
- **Weekly Summary** - Email summary to all users
- **Geofence Check** - Monitors geofence rules every 5 minutes

## 🛠️ Development

### Running in Development Mode

```bash
# Backend (with auto-reload)
export FLASK_ENV=development
python backend/app.py

# Frontend (with hot reload)
cd frontend
npm run dev
```

### Database

The SQLite database is automatically created on first run. To reset:

```bash
rm database/antitheft.db
python backend/app.py  # Recreates database
```

## 🔒 Security Notes

- Change default admin credentials in production
- Use strong SECRET_KEY and JWT_SECRET_KEY
- Enable HTTPS in production
- Secure SMTP credentials
- Regularly update dependencies

## 📝 License

This project is provided as-is for educational and demonstration purposes.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

**⚠️ Disclaimer:** This is a demonstration system. For production use, implement additional security measures, proper error handling, and compliance with local privacy laws.

