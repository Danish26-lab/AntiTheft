@echo off
REM Smart Anti-Theft System - Start All Services (Windows Batch)
REM Easy one-click startup for all services

echo.
echo ========================================
echo  Smart Anti-Theft System Startup
echo ========================================
echo.

REM Get the script directory
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

echo Starting Backend Server...
start "Backend Server" cmd /k "cd /d %PROJECT_ROOT%backend && python app.py"

timeout /t 3 /nobreak >nul

echo Starting Frontend Server...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo Starting Device Agent...
start "Device Agent" cmd /k "cd device_agent && python agent.py"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo  All Services Started!
echo ========================================
echo.
echo Access Points:
echo   - Dashboard:  http://localhost:3000
echo   - QR Scanner: http://192.168.0.19:3000/qr-scanner
echo   - Backend:    http://localhost:5000
echo.
echo Default Login:
echo   - Email:    admin@antitheft.com
echo   - Password: admin123
echo.
echo Services Running:
echo   - Backend Server (Port 5000)
echo   - Frontend Server (Port 3000)
echo   - Device Agent (Monitoring for commands)
echo.
echo All services are running in separate windows.
echo Close those windows to stop the services.
echo.
echo IMPORTANT: Keep the "Device Agent" window open!
echo   The agent must be running to receive lock commands.
echo.
pause
