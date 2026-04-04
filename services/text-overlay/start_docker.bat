@echo off
echo.
echo 🐳 Starting Flask Video Enhancement API in Docker...
echo =================================================

:: Check if Docker is running
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)
echo ✅ Docker is running

:: Check if .env file exists
if not exist ".env" (
    echo ⚠️  .env file not found. Creating from template...
    copy ".env.docker" ".env"
    echo 📝 Please edit .env file and add your OpenAI API key
    pause
)

:: Stop existing containers
echo 🛑 Stopping existing containers...
docker-compose -f docker-compose.flask.yml down

:: Build and start
echo 🏗️  Building Docker image...
docker-compose -f docker-compose.flask.yml build

echo 🚀 Starting Flask API container...
docker-compose -f docker-compose.flask.yml up -d

:: Wait for service
echo ⏳ Waiting for Flask API to start...
timeout /t 10 /nobreak >nul

:: Test health endpoint
curl -f http://localhost:5003/health >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo 🎉 Flask Video Enhancement API is running!
    echo =================================================
    echo 🌐 API Base URL: http://localhost:5003
    echo 🔍 Health Check: http://localhost:5003/health
    echo 📚 API Documentation: See DEPLOYMENT_GUIDE.md
    echo.
    echo 🔧 Docker Management Commands:
    echo   View logs:    docker-compose -f docker-compose.flask.yml logs -f
    echo   Stop:         docker-compose -f docker-compose.flask.yml down
    echo   Restart:      docker-compose -f docker-compose.flask.yml restart
    echo.
    echo 🔗 Ready for N8N integration!
) else (
    echo ❌ Flask API failed to start
    echo 🔍 Check logs with: docker-compose -f docker-compose.flask.yml logs
)

pause
