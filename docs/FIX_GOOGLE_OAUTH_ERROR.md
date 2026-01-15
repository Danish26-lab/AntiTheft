# 🔧 Fix Google OAuth "no registered origin" Error

## The Problem

You're seeing: **"Access blocked: Authorization Error - no registered origin"**

This happens because Google OAuth needs to know which websites are allowed to use your OAuth client ID.

## Solution: Configure Authorized Origins in Google Cloud Console

### Step 1: Go to Google Cloud Console

1. Open: https://console.cloud.google.com/
2. Select your project (or create one if needed)
3. Navigate to: **APIs & Services** > **Credentials**

### Step 2: Find Your OAuth 2.0 Client ID

1. Look for the client ID: `913466167374-2t1no6si29f0phe28pef83oaolv836pm.apps.googleusercontent.com`
2. Click on it to edit

### Step 3: Add Authorized JavaScript Origins

In the **Authorized JavaScript origins** section, click **+ ADD URI** and add:

```
http://localhost:3000
http://127.0.0.1:3000
```

### Step 4: Add Authorized Redirect URIs

In the **Authorized redirect URIs** section, click **+ ADD URI** and add:

```
http://localhost:3000
http://localhost:3000/login
http://127.0.0.1:3000
http://127.0.0.1:3000/login
```

### Step 5: Save Changes

Click **SAVE** at the bottom of the page.

### Step 6: Wait a Few Minutes

Google's changes can take 1-5 minutes to propagate. Wait a bit, then try again.

## For Production

When deploying to production, add your production domain:

**Authorized JavaScript origins:**
```
https://yourdomain.com
```

**Authorized redirect URIs:**
```
https://yourdomain.com
https://yourdomain.com/login
```

## Quick Checklist

- [ ] Added `http://localhost:3000` to Authorized JavaScript origins
- [ ] Added `http://localhost:3000` to Authorized redirect URIs
- [ ] Saved changes in Google Cloud Console
- [ ] Waited 1-5 minutes for changes to propagate
- [ ] Restarted frontend server
- [ ] Tried Google Sign-In again

## Still Not Working?

1. **Check the exact error:**
   - Look at the browser console (F12)
   - Check the error message details

2. **Verify client ID:**
   - Make sure the client ID in your code matches Google Cloud Console
   - Check `frontend/src/pages/Login.jsx` - should have: `913466167374-2t1no6si29f0phe28pef83oaolv836pm.apps.googleusercontent.com`

3. **Clear browser cache:**
   - Sometimes cached OAuth settings cause issues
   - Try incognito/private browsing mode

4. **Check OAuth consent screen:**
   - Go to APIs & Services > OAuth consent screen
   - Make sure it's configured (even for testing)

## Alternative: Use Different OAuth Flow

If you continue having issues, we can switch to a different OAuth implementation. Let me know!

