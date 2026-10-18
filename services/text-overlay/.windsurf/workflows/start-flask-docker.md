---
description: Start Flask Video Enhancement API in Docker
---

# Start Flask Video Enhancement API in Docker

Follow these steps to run the video processing API in Docker:

## 1. Navigate to project directory
```bash
cd C:\Users\Isaia\Documents\WordsOnText
```

## 2. Check Docker status
```bash
docker version
```

## 3. Verify environment file
```bash
# Check if .env file exists with OpenAI API key
type .env
```

// turbo
## 4. Stop any existing containers
```bash
docker-compose -f docker-compose.flask.yml down
```

// turbo  
## 5. Build Docker image
```bash
docker-compose -f docker-compose.flask.yml build
```

// turbo
## 6. Start Flask API in Docker
```bash
docker-compose -f docker-compose.flask.yml up -d
```

## 7. Verify container is running
```bash
docker-compose -f docker-compose.flask.yml ps
```

## 8. Check health endpoint
```bash
curl http://localhost:5003/health
```

## 9. View logs (optional)
```bash
docker-compose -f docker-compose.flask.yml logs -f flask-video-api
```

## Alternative: Use startup script
```bash
# Windows PowerShell
.\start_docker.ps1

# Windows Batch
start_docker.bat
```

## Success!
Your Flask API is now running in Docker at `http://localhost:5003`

## Docker Management Commands
- **View logs:** `docker-compose -f docker-compose.flask.yml logs -f`
- **Stop:** `docker-compose -f docker-compose.flask.yml down`  
- **Restart:** `docker-compose -f docker-compose.flask.yml restart`
- **Shell access:** `docker exec -it flask-video-enhancement-api bash`

## N8N Integration
Use the same HTTP Request configurations with:
- **Base URL:** `http://localhost:5003` (same as local)
- **All endpoints** work identically in Docker
- **Shared volumes** for video processing maintained
