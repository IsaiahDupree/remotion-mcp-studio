@echo off
echo.
echo ===================================================
echo CHECKING ALL SERVICES - ORIGINAL AND ENHANCED SETUP
echo ===================================================
echo.

echo DOCKER CONTAINERS STATUS:
docker ps -a
echo.

echo ===================================================
echo ORIGINAL ENVIRONMENT HEALTH CHECKS:
echo ===================================================
echo.

echo N8N (Original) - Port 5678:
curl -s -o nul -w "%%{http_code}\n" http://localhost:5678 || echo DOWN
echo.

echo FlaskDrive (Original) - Port 5000:
curl -s -o nul -w "%%{http_code}\n" http://localhost:5000 || echo DOWN
echo.

echo ===================================================
echo ENHANCED ENVIRONMENT HEALTH CHECKS:
echo ===================================================
echo.

echo N8N (Enhanced) - Port 5679:
curl -s -o nul -w "%%{http_code}\n" http://localhost:5679 || echo DOWN
echo.

echo FlaskDrive (Enhanced) - Port 5005:
curl -s -o nul -w "%%{http_code}\n" http://localhost:5005 || echo DOWN
echo.

echo Enhanced Flask API - Port 5003:
curl -s http://localhost:5003/health || echo DOWN
echo.

echo Video Generator (Enhanced) - Port 5004:
curl -s http://localhost:5004/health || echo DOWN
echo.

echo ===================================================
echo POSTGRES DATABASE CHECKS:
echo ===================================================
echo.

echo Original Postgres - Port 5432:
docker exec n8n-postgres-1 pg_isready -h localhost -p 5432 || echo DOWN
echo.

echo Enhanced Postgres - Port 5433:
docker exec music_system-postgres-enhanced-1 pg_isready -h localhost -p 5432 || echo DOWN
echo.

echo ===================================================
echo SERVICE URLS:
echo ===================================================
echo.
echo Original N8N:          http://localhost:5678
echo Original FlaskDrive:   http://localhost:5000
echo.
echo Enhanced N8N:          http://localhost:5679
echo Enhanced FlaskDrive:   http://localhost:5005
echo Enhanced Flask API:    http://localhost:5003
echo Enhanced Video Gen:    http://localhost:5004
echo.

echo ===================================================
echo NEXT STEPS:
echo ===================================================
echo.
echo 1. Access N8N interfaces to import workflows
echo 2. Test the enhanced Flask API endpoints
echo 3. Run end-to-end video processing pipeline
echo.
