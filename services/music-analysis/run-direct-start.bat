@echo off
echo Building and running enhanced Flask API Docker container...
echo.

REM Stop and remove existing container if it exists
echo Cleaning up any existing containers...
docker stop direct-start-api 2>nul
docker rm direct-start-api 2>nul

REM Build the Docker image
echo Building Docker image...
docker build -t direct-start-api -f Dockerfile.direct-start .

REM Run the container with necessary volume mounts and network settings
echo Starting container...
docker run -d --name direct-start-api ^
  -p 5001:5001 ^
  -v //c/Users/Isaia/Documents/Coding/N8N/soundcloud_music:/app/soundcloud_music:ro ^
  -v //c/Users/Isaia/Documents/Coding/N8N/shared/videos:/app/shared/videos:ro ^
  -v //c/Users/Isaia/Documents/Coding/N8N/shared/fonts:/app/shared/fonts:ro ^
  -v //c/Users/Isaia/Documents/Coding/N8N/cache:/app/cache:rw ^
  --add-host=host.docker.internal:host-gateway ^
  direct-start-api

echo.
echo Waiting for container to start...
timeout /t 3 /nobreak > nul

REM Check if container is running
docker ps | findstr direct-start-api

if %ERRORLEVEL% NEQ 0 (
  echo Container failed to start. Checking logs:
  docker logs direct-start-api
) else (
  echo.
  echo Container started! API should be available at http://localhost:5001
  echo.
  echo Check container status with: docker ps
  echo Check logs with: docker logs -f direct-start-api
  echo.
  echo Checking API health status...
  timeout /t 2 /nobreak > nul
  curl http://localhost:5001/health
)
