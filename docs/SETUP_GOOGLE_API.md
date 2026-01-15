# 🚀 Quick Setup: Google API Keys

## Step 1: Create Frontend Environment File

Create a file named `.env` in the `frontend` folder with this content:

```env
VITE_GOOGLE_MAPS_API_KEY=AIzaSyDxWLNVkWMwKjXj6dZwiv4d2CFqz0B9RIQ
```

**File location:** `frontend/.env`

## Step 2: Restart Frontend

After creating the `.env` file, restart your frontend server:

```bash
# Stop the current frontend (Ctrl+C)
# Then restart:
cd frontend
npm run dev
```

## Step 3: Verify It Works

1. Go to `http://localhost:3000/dashboard`
2. Check if the map loads (you should see Google Maps)
3. If maps load successfully, the API key is working! ✅

## What This Enables

- ✅ **Google Maps** - Display device locations on maps
- ✅ **Location Picker** - Select geofence locations visually
- ✅ **Map View** - Interactive maps in dashboard and device details

## Current API Keys

| Service | Key/ID | Status |
|---------|--------|--------|
| Google Maps API | `AIzaSyDxWLNVkWMwKjXj6dZwiv4d2CFqz0B9RIQ` | ✅ Ready to use |
| Google OAuth | `913466167374-2t1no6si29f0phe28pef83oaolv836pm.apps.googleusercontent.com` | ✅ Configured |

## Next Steps

1. **Enable Google Maps API in Google Cloud Console:**
   - Go to https://console.cloud.google.com/
   - APIs & Services > Library
   - Search "Maps JavaScript API"
   - Click "Enable"

2. **Test the integration:**
   - Register a device
   - View it on the dashboard
   - Maps should display device locations

## Troubleshooting

**Maps not showing?**
- Make sure `.env` file is in the `frontend` folder (not root)
- Restart frontend after creating `.env`
- Check browser console for errors
- Verify API key is enabled in Google Cloud Console

**Need help?**
See `GOOGLE_API_SETUP.md` for detailed configuration guide.

