@echo off
echo 🔐 Flask Drive Permanent Authorization Setup
echo ==========================================
echo.
cd /d "%~dp0"

echo 📋 Checking current setup...
python auto_auth.py

echo.
echo 🚀 Restarting Flask Drive container to apply changes...
cd ..\custom-code-nodes\video-processing\docker-config
docker-compose restart flaskdrive

echo.
echo ⏳ Waiting for Flask Drive to restart...
timeout /t 5 /nobreak >nul

echo.
echo 🌐 Testing Flask Drive status...
curl http://localhost:5002/health

echo.
echo ✅ Setup complete! 
echo 📍 Flask Drive: http://localhost:5002
echo 📍 N8N Interface: http://localhost:5678
echo.
pause
