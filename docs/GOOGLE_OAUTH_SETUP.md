# 🔐 Google OAuth Setup Guide

## Configuration

The Google OAuth client ID has been configured:
- **Client ID:** `913466167374-2t1no6si29f0phe28pef83oaolv836pm.apps.googleusercontent.com`

## Setup Steps

### 1. Install Dependencies

```bash
# Backend dependencies
pip install -r requirements.txt

# This will install:
# - google-auth>=2.23.0
# - google-auth-oauthlib>=1.1.0
# - google-auth-httplib2>=0.1.1
```

### 2. Configure Google OAuth (Optional - already set)

The client ID is already configured in the code. If you want to use environment variables:

```bash
# In .env file (optional)
GOOGLE_CLIENT_ID=913466167374-2t1no6si29f0phe28pef83oaolv836pm.apps.googleusercontent.com
```

### 3. Configure Authorized JavaScript Origins

In your Google Cloud Console:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services > Credentials
3. Find your OAuth 2.0 Client ID
4. Add authorized JavaScript origins:
   - `http://localhost:3000` (for development)
   - `http://localhost:5000` (for backend if needed)
5. Add authorized redirect URIs:
   - `http://localhost:3000` (for development)

### 4. How It Works

1. **User clicks "Sign in with Google"** on the login page
2. **Google OAuth popup** appears
3. **User selects Google account** and grants permission
4. **Frontend receives ID token** from Google
5. **Frontend sends token to backend** (`/api/google_login`)
6. **Backend verifies token** with Google
7. **Backend creates/updates user** in database
8. **Backend returns JWT token** to frontend
9. **User is logged in** and redirected to dashboard

## Features

- ✅ Automatic user creation if account doesn't exist
- ✅ Seamless login with Google account
- ✅ Secure token verification
- ✅ Works with existing user accounts

## Testing

1. Start the backend:
   ```bash
   cd backend
   python app.py
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Go to login page: `http://localhost:3000/login`
4. Click "Sign in with Google" button
5. Select your Google account
6. You should be logged in automatically!

## Troubleshooting

### "Invalid Google token" error
- Make sure the client ID matches in Google Cloud Console
- Check that authorized origins include `http://localhost:3000`
- Verify the token hasn't expired

### Button doesn't appear
- Check browser console for errors
- Make sure Google script loaded: `https://accounts.google.com/gsi/client`
- Verify client ID is correct

### Backend verification fails
- Install Google auth libraries: `pip install google-auth google-auth-oauthlib google-auth-httplib2`
- Check backend logs for detailed error messages
- Verify network connectivity to Google servers

## Security Notes

- The ID token is verified server-side for security
- User accounts are created automatically on first Google login
- Existing users can also use Google login if email matches
- JWT tokens are used for session management (same as regular login)

