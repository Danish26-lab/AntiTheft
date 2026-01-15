# Vercel Deployment Guide

## Quick Start

Your Flask backend is now configured for Vercel deployment. The entrypoint error has been fixed.

## Files Created for Vercel

1. **`vercel.json`** - Vercel configuration
2. **`backend/api/index.py`** - Serverless function entry point

## Deployment Steps

### 1. Install Vercel CLI (if not already installed)
```bash
npm i -g vercel
```

### 2. Login to Vercel
```bash
vercel login
```

### 3. Deploy
```bash
vercel
```

Or deploy to production:
```bash
vercel --prod
```

## Important Notes

### ⚠️ Database Configuration

**CRITICAL:** Vercel uses serverless functions that are stateless. SQLite file-based databases will NOT work properly on Vercel because:
- Each serverless function invocation may run on a different instance
- The file system is read-only except for `/tmp`
- SQLite files can't be persisted between requests

**Solutions:**

1. **Use PostgreSQL (Recommended)**
   - Use Vercel Postgres or external PostgreSQL service (Supabase, Neon, Railway, etc.)
   - Update `DATABASE_URL` environment variable in Vercel dashboard
   - Example: `DATABASE_URL=postgresql://user:pass@host:5432/dbname`

2. **Use Vercel Postgres**
   - Add Postgres in Vercel dashboard
   - Update your code to use PostgreSQL adapter for SQLAlchemy
   - Install: `pip install psycopg2-binary` or `pip install pg8000`

3. **Environment Variables**
   - Set in Vercel Dashboard → Project → Settings → Environment Variables
   - Required:
     - `DATABASE_URL` (PostgreSQL connection string)
     - `SECRET_KEY` (Flask secret key)
     - `JWT_SECRET_KEY` (JWT secret key)

### Database Migration

If switching to PostgreSQL, update your database connection in `backend/app.py`:

```python
# The app already uses DATABASE_URL environment variable
# Just update it in Vercel dashboard to a PostgreSQL URL
db_url = os.getenv('DATABASE_URL')
# If not set, falls back to SQLite (won't work on Vercel)
```

### File Structure for Vercel

```
your-project/
├── vercel.json              ← Vercel config
├── requirements.txt         ← Python dependencies (must be in root)
├── backend/
│   ├── app.py              ← Flask app
│   ├── api/
│   │   └── index.py        ← Vercel entrypoint
│   ├── models.py
│   ├── routes/
│   └── ...
└── ...
```

## Testing Locally

You can test the Vercel deployment locally:

```bash
vercel dev
```

This will:
- Simulate Vercel's serverless environment
- Test your API routes
- Help debug any issues before production deployment

## API Routes

All routes under `/api/*` will be handled by your Flask app:
- `/api/health` - Health check
- `/api/login` - User login
- `/api/register_user` - User registration
- `/api/get_devices` - Get devices
- `/api/agent/register` - Agent registration
- etc.

## Troubleshooting

### Error: "No flask entrypoint found"
✅ **Fixed** - The `backend/api/index.py` file exports the Flask app correctly.

### Error: "Database locked" or SQLite errors
⚠️ **Expected** - SQLite doesn't work on Vercel. Switch to PostgreSQL.

### Error: Module not found
- Ensure `requirements.txt` is in the project root
- All dependencies must be listed in `requirements.txt`
- Vercel installs packages from root `requirements.txt`

### Environment Variables Not Working
- Set them in Vercel Dashboard → Project Settings → Environment Variables
- Redeploy after adding environment variables
- Use `.env.local` for `vercel dev` (local testing)

## Next Steps

1. **Set up PostgreSQL database** (Vercel Postgres or external)
2. **Update environment variables** in Vercel dashboard
3. **Deploy**: `vercel --prod`
4. **Update frontend** API URLs to point to your Vercel deployment
5. **Test all endpoints**

## Alternative: Keep SQLite for Development

You can keep SQLite for local development and use PostgreSQL on Vercel:

```python
# In backend/app.py
db_url = os.getenv('DATABASE_URL')

# If DATABASE_URL is not set (local dev), use SQLite
if not db_url:
    # Local SQLite database (development only)
    # ... SQLite setup code ...
else:
    # Use provided DATABASE_URL (production - PostgreSQL)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
```

This way:
- Local development uses SQLite (fast, no setup)
- Vercel production uses PostgreSQL (works on serverless)
