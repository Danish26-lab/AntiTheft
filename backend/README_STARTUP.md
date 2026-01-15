# Backend Startup Guide

## Quick Start

The backend can be started in two ways:

### Method 1: Direct Python (Recommended)
```bash
cd backend
python app.py
```

### Method 2: Flask CLI
```bash
cd backend
flask run
```

## Fixing "No flask entrypoint found" Error

If you see the error:
```
Error: No flask entrypoint found. Add an 'app' script in pyproject.toml or define an entrypoint in one of: app.py, src/app.py
```

**Solutions:**

1. **Use Method 1** (Direct Python) - This always works:
   ```bash
   python app.py
   ```

2. **Set FLASK_APP environment variable:**
   ```bash
   set FLASK_APP=app.py
   flask run
   ```

3. **The pyproject.toml file** has been created with the entrypoint. If using `flask run`, make sure you're in the `backend` directory.

## Using start_all.bat

The `start_all.bat` script uses Method 1 (direct Python), so it should work without issues.

## Troubleshooting

- **Unicode errors**: Fixed by removing emoji characters from print statements
- **Database path issues**: The app automatically handles Windows paths with spaces
- **Port already in use**: Make sure port 5000 is not being used by another application
