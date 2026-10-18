@echo off
echo ================================================================
echo ALL N8N SERVICES OVERVIEW
echo ================================================================
echo.

echo DOCKER CONTAINERS STATUS:
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}"

echo.
echo ================================================================
echo SERVICE ENDPOINTS:
echo ================================================================
echo.
echo ORIGINAL SETUP:
echo   n8n:            http://localhost:5678
echo   FlaskDrive:     http://localhost:5000  
echo   Video Gen:      http://localhost:5001
echo.
echo ENHANCED SETUP:
echo   n8n:            http://localhost:5679
echo   FlaskDrive:     http://localhost:5005
echo   Video Gen:      http://localhost:5004
echo   Enhanced API:   http://localhost:5003  ^<-- Your new Flask API
echo.
echo ================================================================
echo QUICK HEALTH CHECKS:
echo ================================================================

echo Checking Original FlaskDrive...
curl -s -o /dev/null -w "FlaskDrive (5000): %%{http_code}\n" http://localhost:5000/ || echo FlaskDrive (5000): DOWN

echo Checking Enhanced FlaskDrive...  
curl -s -o /dev/null -w "FlaskDrive Enhanced (5005): %%{http_code}\n" http://localhost:5005/ || echo FlaskDrive Enhanced (5002): DOWN

echo Checking Enhanced Flask API...
curl -s -o /dev/null -w "Enhanced API (5003): %%{http_code}\n" http://localhost:5003/health || echo Enhanced API (5003): DOWN

echo.
echo ================================================================
