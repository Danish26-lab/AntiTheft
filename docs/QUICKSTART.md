# 🚀 Quick Start Guide

## Installation

### Option 1: Automated Setup (Recommended)

```bash
python setup.py
```

This will install all dependencies for backend, frontend, and device agent.

### Option 2: Manual Setup

#### 1. Backend Setup

```bash
pip install -r requirements.txt
```

#### 2. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

#### 3. Device Agent Setup

```bash
pip install -r device_agent/requirements.txt
```

## Running the Application

### 1. Start Backend Server

```bash
cd backend
python app.py
```

Backend will run on `http://localhost:5000`

### 2. Start Frontend (New Terminal)

```bash
cd frontend
npm run dev
```

Frontend will run on `http://localhost:3000`

### 3. Run Device Agent (New Terminal - Optional)

```bash
cd device_agent
python agent.py
```

## First Login

- **URL:** http://localhost:3000
- **Email:** admin@antitheft.com
- **Password:** admin123

## Testing Device Registration

1. Start the device agent on any device
2. The agent will automatically register the device
3. View it in the Devices page on the dashboard

## Configuration

### Email Alerts (Optional)

Edit `.env` file:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Google Maps (Optional)

Add to `.env`:
```env
VITE_GOOGLE_MAPS_API_KEY=your-api-key
```

## Troubleshooting

### Database not found
The database is created automatically on first run. If issues occur:
```bash
rm database/antitheft.db
cd backend
python app.py
```

### Port already in use
Change ports in:
- Backend: `backend/app.py` (line 45)
- Frontend: `frontend/vite.config.js` (line 7)

### CORS errors
Make sure backend is running before frontend.

## Next Steps

- Register a device using the agent
- Test remote actions (Lock, Alarm, Wipe)
- Check for security breaches
- Set up geofencing rules
- Configure email alerts

For detailed documentation, see `README.md`.

