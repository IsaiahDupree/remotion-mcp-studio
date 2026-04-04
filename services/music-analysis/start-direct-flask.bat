@echo off
echo Starting Direct Flask API with N8N integration...
echo.

cd /d %~dp0\..
docker-compose -f music_system/docker-compose.direct-start.yml up -d
echo.
echo Services:
echo  - Direct Flask API: http://localhost:5001
echo  - N8N: http://localhost:5678
echo  - FlaskDrive: http://localhost:4563
echo.
echo Check logs with: docker-compose -f music_system/docker-compose.direct-start.yml logs -f direct-start-api
echo Stop services with: docker-compose -f music_system/docker-compose.direct-start.yml down
echo.
echo Press any key to check API status...
pause > nul
curl http://localhost:5001/health
echo.
