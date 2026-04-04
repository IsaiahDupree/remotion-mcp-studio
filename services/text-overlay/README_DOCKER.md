# 🐳 Flask Video Enhancement API - Docker Setup

## Quick Start

### Option 1: One-Click Scripts
```bash
# Windows PowerShell
.\start_docker.ps1

# Windows Batch  
.\start_docker.bat
```

### Option 2: Manual Commands
```bash
# 1. Copy environment template
copy .env.docker .env

# 2. Edit .env with your OpenAI API key
notepad .env

# 3. Build and start
docker-compose -f docker-compose.flask.yml build
docker-compose -f docker-compose.flask.yml up -d

# 4. Test
curl http://localhost:5003/health
```

## ✅ Verify Running

Check the API is working:
```bash
# Health check
curl http://localhost:5003/health

# List videos 
curl http://localhost:5003/analyze/videos

# View containers
docker-compose -f docker-compose.flask.yml ps
```

## 🔧 Management Commands

```bash
# View logs
docker-compose -f docker-compose.flask.yml logs -f

# Stop containers
docker-compose -f docker-compose.flask.yml down

# Restart
docker-compose -f docker-compose.flask.yml restart

# Shell access
docker exec -it flask-video-enhancement-api bash
```

## 🎯 N8N Integration

Your N8N workflows can connect to:
- **Base URL:** `http://localhost:5003`
- **Same endpoints** as local Flask app
- **Shared video processing** directories mounted

## 🚀 Success!

When you see this response from `/health`:
```json
{
  "status": "healthy",
  "components": {
    "smart_video_processor": "initialized",
    "music_enhancer": "ready",
    "text_styler": "ready"
  }
}
```

Your Docker Flask API is **ready for video processing**! 🎬
