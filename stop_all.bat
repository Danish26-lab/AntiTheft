@echo off
REM Stop All Services Script
echo Stopping all services...

REM Kill Python processes
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Backend Server*" 2>nul
taskkill /F /IM python.exe /FI "COMMANDLINE eq *app.py*" 2>nul

REM Kill Node processes  
taskkill /F /IM node.exe /FI "WINDOWTITLE eq Frontend Server*" 2>nul
taskkill /F /IM node.exe /FI "COMMANDLINE eq *vite*" 2>nul

REM Kill by port (using netstat and taskkill)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000" ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul

echo.
echo All services stopped.
pause

