@echo off
echo ================================================================
echo Starting ENHANCED n8n Setup (Cloned + Enhanced Flask API)
echo ================================================================
echo.
echo This will run ALONGSIDE your existing n8n setup on different ports
echo.

echo Current running containers (ORIGINAL setup):
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"
echo.

echo Step 1: Building and starting enhanced containers...
docker-compose -f docker-compose.enhanced.yml up --build -d

echo.
echo Step 2: Waiting for containers to initialize...
timeout /t 20 /nobreak > nul

echo.
echo ================================================================
echo CONTAINER STATUS:
echo ================================================================
echo.
echo ORIGINAL SETUP (should still be running):
docker ps --filter "name=n8n-n8n-1" --filter "name=n8n-flaskdrive-1" --filter "name=n8n-postgres-1" --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"

echo.
echo ENHANCED SETUP (new):
docker-compose -f docker-compose.enhanced.yml ps

echo.
echo ================================================================
echo SERVICE URLS:
echo ================================================================
echo.
echo ORIGINAL SETUP:
echo   n8n (original):     http://localhost:5678
echo   FlaskDrive:         http://localhost:5000
echo   Video Generator:    http://localhost:5001
echo.
echo ENHANCED SETUP:
echo   n8n (enhanced):     http://localhost:5679
echo   FlaskDrive:         http://localhost:5005
echo   Video Generator:    http://localhost:5004
echo   Enhanced Flask API: http://localhost:5003  ^<-- NEW!
echo.
echo ================================================================
echo USEFUL COMMANDS:
echo ================================================================
echo View enhanced logs:    docker-compose -f docker-compose.enhanced.yml logs -f
echo Stop enhanced setup:   docker-compose -f docker-compose.enhanced.yml down
echo Check enhanced health: curl http://localhost:5003/health
echo.

echo Testing Enhanced Flask API health...
timeout /t 3 /nobreak > nul
curl http://localhost:5003/health

echo.
echo ================================================================
echo SETUP COMPLETE! You now have BOTH setups running simultaneously:
echo - Original n8n setup on ports 5678, 5000, 5001
echo - Enhanced n8n setup on ports 5679, 5002, 5003, 5004
echo ================================================================
