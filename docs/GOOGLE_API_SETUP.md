# 🔑 Google API Configuration Guide

## API Keys Configured

### 1. Google Maps API Key
- **Key:** `AIzaSyDxWLNVkWMwKjXj6dZwiv4d2CFqz0B9RIQ`
- **Purpose:** Display maps, geocoding, and location services
- **Status:** ✅ Configured in `frontend/.env`

### 2. Google OAuth Client ID
- **Client ID:** `913466167374-2t1no6si29f0phe28pef83oaolv836pm.apps.googleusercontent.com`
- **Purpose:** Google Sign-In authentication
- **Status:** ✅ Configured in code

## Setup Instructions

### Frontend Environment Variables

The Google Maps API key is already configured in `frontend/.env`:

```env
VITE_GOOGLE_MAPS_API_KEY=AIzaSyDxWLNVkWMwKjXj6dZwiv4d2CFqz0B9RIQ
```

**Note:** After adding/changing `.env` file, restart the frontend dev server:
```bash
cd frontend
npm run dev
```

### Google Maps API Setup

1. **Enable Google Maps JavaScript API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to APIs & Services > Library
   - Search for "Maps JavaScript API"
   - Click "Enable"

2. **Restrict API Key (Recommended for Production):**
   - Go to APIs & Services > Credentials
   - Click on your API key
   - Under "Application restrictions":
     - Select "HTTP referrers (web sites)"
     - Add: `http://localhost:3000/*`
     - Add: `http://localhost:5000/*`
   - Under "API restrictions":
     - Select "Restrict key"
     - Enable: "Maps JavaScript API"

### Gmail API Setup (If Needed)

If you want to use Gmail API instead of SMTP:

1. **Enable Gmail API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to APIs & Services > Library
   - Search for "Gmail API"
   - Click "Enable"

2. **Create OAuth2 Credentials:**
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Web application"
   - Authorized redirect URIs:
     - `http://localhost:5000/api/gmail/callback`
   - Save the Client ID and Client Secret

3. **Update Backend Configuration:**
   ```env
   GMAIL_CLIENT_ID=your-client-id
   GMAIL_CLIENT_SECRET=your-client-secret
   GMAIL_API_KEY=AIzaSyDxWLNVkWMwKjXj6dZwiv4d2CFqz0B9RIQ
   ```

## Current Configuration

### What's Working Now:
- ✅ Google Maps integration (using the API key)
- ✅ Google Sign-In (using OAuth Client ID)
- ✅ Email alerts via SMTP (Gmail SMTP)

### What You Can Add:
- 📧 Gmail API for advanced email features
- 🗺️ Places API for location search
- 📍 Geocoding API for address conversion

## Testing

1. **Test Google Maps:**
   - Go to Dashboard or Device Detail page
   - Maps should load and display device locations

2. **Test Google Sign-In:**
   - Go to Login page
   - Click "Sign in with Google"
   - Should authenticate successfully

3. **Test Email Alerts:**
   - Configure SMTP in `.env`:
     ```env
     SMTP_SERVER=smtp.gmail.com
     SMTP_PORT=587
     SMTP_USER=your-email@gmail.com
     SMTP_PASSWORD=your-app-password
     ```
   - Trigger a device alert
   - Check email inbox

## Troubleshooting

### Maps Not Loading
- Check browser console for API key errors
- Verify API key is enabled in Google Cloud Console
- Check that Maps JavaScript API is enabled
- Verify API key restrictions allow your domain

### Google Sign-In Not Working
- Verify OAuth Client ID is correct
- Check authorized JavaScript origins in Google Cloud Console
- Ensure `http://localhost:3000` is added to authorized origins

### API Key Errors
- Make sure the API key has the correct APIs enabled
- Check API key restrictions match your usage
- Verify billing is enabled (required for Google Maps API)

## Security Notes

- ⚠️ **Never commit `.env` files to version control**
- ⚠️ **Restrict API keys in production**
- ⚠️ **Use environment variables, not hardcoded keys**
- ⚠️ **Enable API key restrictions in Google Cloud Console**

