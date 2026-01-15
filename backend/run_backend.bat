@echo off
REM Simple backend startup script that always works
cd /d "%~dp0"
set FLASK_APP=app.py
python app.py
