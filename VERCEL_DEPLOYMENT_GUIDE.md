# Vercel Deployment - Complete Guide

## ✅ Fixed Issues

1. **404 Not Found Error** - Fixed routing configuration
2. **500 Server Error** - Fixed serverless compatibility
3. **Database Configuration** - Added PostgreSQL support

## Current Configuration

### Option 1: Direct Flask App Entry (Recommended)
`vercel.json` now uses `backend/app.py` directly as the entry point.

### Option 2: API Wrapper (Alternative)
If Option 1 doesn't work, you can use `/api/index.py` wrapper.

## Required Setup

### 1. PostgreSQL Database (REQUIRED)

SQLite doesn't work on Vercel. You MUST set up PostgreSQL:

**Option A: Vercel Postgres**
1. Vercel Dashboard → Your Project → Storage
2. Create Postgres database
3. Copy connection string

**Option B: External PostgreSQL**
- Supabase: https://supabase.com (free tier)
- Neon: https://neon.tech (free tier)
- Railway: https://railway.app (free tier)

### 2. Environment Variables

Set in Vercel Dashboard → Project Settings → Environment Variables:

```
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

Generate secrets:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Deployment Steps

```bash
# 1. Install Vercel CLI (if needed)
npm i -g vercel

# 2. Login
vercel login

# 3. Deploy
vercel --prod
```

## Testing After Deployment

1. **Root endpoint:**
   ```
   GET https://your-app.vercel.app/
   ```

2. **Health check:**
   ```
   GET https://your-app.vercel.app/api/health
   ```

3. **API endpoints:**
   ```
   POST https://your-app.vercel.app/api/login
   GET https://your-app.vercel.app/api/get_devices
   ```

## Troubleshooting

### Still Getting 404?

1. **Check Vercel Functions:**
   - Dashboard → Deployment → Functions tab
   - Should show `backend/app.py` or `api/index.py`

2. **Check Build Logs:**
   - Look for import errors or missing dependencies

3. **Test Locally:**
   ```bash
   vercel dev
   ```

### Database Connection Issues?

1. **Verify DATABASE_URL:**
   - Format: `postgresql://user:password@host:port/dbname`
   - Test connection outside Vercel first

2. **Check Database Firewall:**
   - Allow connections from Vercel IPs
   - Most cloud providers have Vercel integration

### Import Errors?

1. **Verify requirements.txt:**
   - All dependencies must be listed
   - Check for version conflicts

2. **Check PYTHONPATH:**
   - Environment variable is set in vercel.json
   - Should be: `backend`

## Files Structure

```
project-root/
├── api/
│   └── index.py           ← Alternative entry point
├── backend/
│   ├── app.py             ← Main Flask app (Vercel entry point)
│   ├── models.py
│   ├── routes/
│   └── ...
├── vercel.json            ← Vercel configuration
├── requirements.txt       ← Python dependencies
└── .vercelignore          ← Files to exclude
```

## Quick Fixes Applied

✅ Added root route (`/`) in Flask app
✅ Fixed vercel.json routing
✅ Added error handling for serverless
✅ Made scheduler optional (skipped on Vercel)
✅ Added PostgreSQL support
✅ Enhanced import path resolution

## Next Steps

1. Set up PostgreSQL database
2. Configure environment variables
3. Deploy: `vercel --prod`
4. Test endpoints
5. Update frontend API URLs
