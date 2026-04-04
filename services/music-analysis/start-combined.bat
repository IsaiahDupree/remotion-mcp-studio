@echo off
echo ======================================================
echo Starting Combined n8n + Flask API Docker Environment
echo ======================================================
echo.

echo Step 1: Stopping any existing containers...
docker-compose -f docker-compose.combined.yml down

echo.
echo Step 2: Building and starting containers...
docker-compose -f docker-compose.combined.yml up --build -d

echo.
echo Step 3: Waiting for containers to initialize...
timeout /t 15 /nobreak > nul

echo.
echo ======================================================
echo Status Check:
echo ======================================================
docker-compose -f docker-compose.combined.yml ps

echo.
echo ======================================================
echo Service URLs:
echo ======================================================
echo n8n:            http://localhost:5678
echo Flask API:      http://localhost:5001
echo FlaskDrive:     http://localhost:4563
echo.
echo ======================================================
echo Useful commands:
echo ======================================================
echo View logs:      docker-compose -f docker-compose.combined.yml logs -f
echo Stop services:  docker-compose -f docker-compose.combined.yml down
echo Check health:   curl http://localhost:5001/health
echo.

echo Checking API health...
curl http://localhost:5001/health
