# Flask Video Enhancement API - Deployment & N8N Integration Guide

## 🚀 Quick Start After Vacation

### Prerequisites
1. **Environment Setup**
   ```bash
   # Ensure Python 3.8+ is installed
   python --version
   
   # Install required dependencies
   pip install flask requests python-dotenv openai moviepy pillow numpy opencv-python
   ```

2. **Environment Variables**
   - Ensure `.env` file exists with your OpenAI API key:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### 🔧 System Startup Procedure

1. **Navigate to Project Directory**
   ```bash
   cd C:\Users\Isaia\Documents\WordsOnText
   ```

2. **Start the Flask API**
   ```bash
   python flask_app.py
   ```

3. **Verify System Status**
   - Check console for successful initialization messages:
   ```
   ✅ Enhanced video processor initialized
   ✅ Intelligent music matcher initialized  
   ✅ Local music selector initialized
   ✅ Music enhancer initialized
   ✅ Text styler initialized
   🚀 SmartVideoProcessor initialized successfully
   ```

4. **Test API Health**
   ```bash
   curl http://localhost:5003/health
   ```

---

## 🐳 Docker Deployment

### Prerequisites for Docker
1. **Docker Desktop installed and running**
   ```bash
   docker --version
   docker-compose --version
   ```

2. **Environment file configured**
   ```bash
   # Copy template and edit with your API key
   copy .env.docker .env
   # Edit .env file with your OpenAI API key
   ```

### 🚀 Docker Quick Start

**Option 1: Use Startup Scripts**
```bash
# Windows PowerShell
.\start_docker.ps1

# Windows Batch
start_docker.bat
```

**Option 2: Manual Docker Commands**
```bash
# Navigate to project
cd C:\Users\Isaia\Documents\WordsOnText

# Stop existing containers
docker-compose -f docker-compose.flask.yml down

# Build and start
docker-compose -f docker-compose.flask.yml build
docker-compose -f docker-compose.flask.yml up -d

# Verify health
curl http://localhost:5003/health
```

### 🔧 Docker Management

**Container Operations:**
```bash
# View running containers
docker-compose -f docker-compose.flask.yml ps

# View logs
docker-compose -f docker-compose.flask.yml logs -f flask-video-api

# Stop containers
docker-compose -f docker-compose.flask.yml down

# Restart containers
docker-compose -f docker-compose.flask.yml restart

# Shell access
docker exec -it flask-video-enhancement-api bash
```

**Volume Mounts:**
- **Shared Videos:** `C:/Users/Isaia/Documents/Coding/N8N/shared/videos` → `/app/shared`
- **Enhanced Videos:** `./enhanced_videos` → `/app/enhanced_videos`
- **Music Library:** `./music_library` → `/app/music_library`
- **Processing Logs:** `./processing_log.csv` → `/app/processing_log.csv`

### 🏥 Docker Health Monitoring

**Built-in Health Check:**
```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' flask-video-enhancement-api

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' flask-video-enhancement-api
```

**Resource Limits:**
- **Memory:** 2GB limit, 1GB reserved
- **CPU:** 1.0 limit, 0.5 reserved
- **Health Check:** Every 30 seconds
- **Auto-restart:** Unless stopped manually

---

## 📡 API Endpoints Reference

### Base URL
```
http://localhost:5003
```

### 1. Health Check
**GET** `/health`
```bash
curl -X GET "http://localhost:5003/health"
```

**Response:**
```json
{
  "status": "healthy",
  "openai_api_configured": true,
  "shared_videos_dir": "C:\\Users\\Isaia\\Documents\\Coding\\N8N\\shared\\videos",
  "output_dir": "enhanced_videos",
  "timestamp": "2025-07-02T22:01:44.185000"
}
```

### 2. Music Analysis
**GET** `/analyze/music-match/<video_filename>`
```bash
curl -X GET "http://localhost:5003/analyze/music-match/your_video.mp4"
```

**Response:**
```json
{
  "video_filename": "your_video.mp4",
  "video_analysis": {
    "content_type": "entertainment",
    "visual_mood": "calm",
    "energy_level": "low",
    "duration": 15.487,
    "themes": ["nighttime", "parking lot", "vehicles"]
  },
  "music_recommendations": {
    "best_match": {
      "music_name": "craetion - Summer Sky",
      "music_path": "music_library\\general\\craetion - Summer Sky.aac",
      "compatibility_score": 0.65,
      "mood_match": "good",
      "energy_match": "fair",
      "theme_match": "poor",
      "reasoning": "The video has a calm visual mood..."
    },
    "total_tracks_analyzed": 6,
    "all_matches": [...]
  }
}
```

### 3. Smart Video Processing
**POST** `/process/smart-video`

**Request Body:**
```json
{
  "video_filename": "your_video.mp4",
  "music_path": "music_library\\general\\craetion - Summer Sky.aac",
  "config": {
    "music_volume": 0.003162,
    "text_style": "modern",
    "min_compatibility_score": 0.6
  }
}
```

**Response:**
```json
{
  "success": true,
  "video_filename": "your_video.mp4",
  "music_used": "craetion - Summer Sky.aac",
  "compatibility_score": 0.65,
  "text_overlay": "Amazing Content",
  "processing_time_seconds": 16.12,
  "output_filename": "your_video_smart_enhanced.mp4",
  "download_url": "/download/your_video_smart_enhanced.mp4",
  "transcript_preview": "..."
}
```

### 4. Download Enhanced Video
**GET** `/download/<filename>`
```bash
curl -X GET "http://localhost:5003/download/your_video_smart_enhanced.mp4" --output enhanced_video.mp4
```

---

## 🔗 N8N Integration Examples

### 1. N8N HTTP Request Node - Music Analysis

**Node Configuration:**
- **Method:** GET
- **URL:** `http://localhost:5003/analyze/music-match/{{$json["video_filename"]}}`
- **Headers:** `Content-Type: application/json`

**N8N Workflow Example:**
```json
{
  "meta": {
    "instanceId": "your_instance_id"
  },
  "nodes": [
    {
      "parameters": {
        "url": "http://localhost:5003/analyze/music-match/{{$json[\"video_filename\"]}}",
        "options": {}
      },
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [820, 240],
      "id": "music_analysis_node",
      "name": "Analyze Music Match"
    }
  ]
}
```

### 2. N8N HTTP Request Node - Video Processing

**Node Configuration:**
- **Method:** POST
- **URL:** `http://localhost:5003/process/smart-video`
- **Headers:** `Content-Type: application/json`
- **Body:** 
```json
{
  "video_filename": "{{$json[\"video_filename\"]}}",
  "music_path": "{{$json[\"best_music_path\"]}}",
  "config": {
    "music_volume": 0.003162,
    "text_style": "modern",
    "min_compatibility_score": 0.6
  }
}
```

### 3. Complete N8N Workflow

```json
{
  "nodes": [
    {
      "parameters": {
        "url": "http://localhost:5003/analyze/music-match/{{$json[\"video_filename\"]}}",
        "options": {}
      },
      "type": "n8n-nodes-base.httpRequest",
      "name": "1. Analyze Music Match",
      "id": "analyze_node"
    },
    {
      "parameters": {
        "url": "http://localhost:5003/process/smart-video",
        "method": "POST",
        "body": {
          "video_filename": "={{$json[\"video_filename\"]}}",
          "music_path": "={{$json[\"music_recommendations\"][\"best_match\"][\"music_path\"]}}",
          "config": {
            "music_volume": 0.003162,
            "text_style": "modern",
            "min_compatibility_score": 0.6
          }
        },
        "options": {}
      },
      "type": "n8n-nodes-base.httpRequest",
      "name": "2. Process Video",
      "id": "process_node"
    },
    {
      "parameters": {
        "url": "http://localhost:5003/download/{{$json[\"output_filename\"]}}",
        "options": {
          "response": {
            "response": {
              "neverError": true,
              "responseFormat": "file"
            }
          }
        }
      },
      "type": "n8n-nodes-base.httpRequest",
      "name": "3. Download Result",
      "id": "download_node"
    }
  ],
  "connections": {
    "analyze_node": {
      "main": [["process_node"]]
    },
    "process_node": {
      "main": [["download_node"]]
    }
  }
}
```

---

## 🎚️ Volume Level Reference

| dB Level | Linear Value | Use Case |
|----------|--------------|----------|
| -20dB    | 0.01        | Noticeable background music |
| -25dB    | 0.003162    | **Recommended** - Subtle enhancement |
| -28dB    | 0.004       | Very quiet background music |
| -30dB    | 0.001       | Barely audible |

---

## 🗂️ Directory Structure

```
WordsOnText/
├── flask_app.py                 # Main Flask API server
├── smart_video_processor.py     # Core video processing logic
├── music_video_matcher.py       # AI-powered music matching
├── enhanced_video_processor.py  # Video enhancement utilities
├── local_music_selector.py      # Local music library management
├── .env                         # Environment variables (OpenAI API key)
├── enhanced_videos/             # Output directory for processed videos
├── music_library/               # Local music tracks
│   ├── general/                 # General music tracks
│   └── electronic/              # Electronic music tracks
├── shared/                      # Shared directory for input videos
└── processing_log.csv           # Processing history log
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

1. **Flask App Won't Start**
   ```bash
   # Check if port 5003 is already in use
   netstat -an | findstr :5003
   
   # Kill existing Python processes if needed
   taskkill /F /IM python.exe
   ```

2. **OpenAI API Errors**
   ```bash
   # Verify API key is set
   echo $env:OPENAI_API_KEY  # Windows PowerShell
   
   # Test API connection
   curl -H "Authorization: Bearer $API_TOKEN" https://api.openai.com/v1/models
   ```

3. **Missing Dependencies**
   ```bash
   # Install all required packages
   pip install -r requirements.txt
   
   # Or install individually
   pip install flask requests python-dotenv openai moviepy pillow numpy opencv-python
   ```

4. **Video Processing Fails**
   - Check FFmpeg installation: `ffmpeg -version`
   - Verify input video exists in shared directory
   - Check logs in console output

### Error Codes Reference

| Error Code | Description | Solution |
|------------|-------------|----------|
| 404        | Video file not found | Check video filename and path |
| 500        | Processing error | Check console logs for details |
| 503        | Service unavailable | Restart Flask app |

---

## 📊 Monitoring & Logs

### Log Files
- **Console Output:** Real-time processing status
- **processing_log.csv:** Historical processing records
- **Flask Access Log:** HTTP request logging

### Key Log Messages
```
✅ SmartVideoProcessor initialized successfully  # System ready
🎵 Adding background music: track_name.aac      # Music processing started
📝 Adding text overlay: Amazing Content         # Text overlay started
✅ Video Processing Successful!                 # Processing completed
```

---

## 🚀 Production Deployment

### For Production Use:
1. **Use Production WSGI Server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5003 flask_app:app
   ```

2. **Add Authentication**
   - Implement API key validation
   - Add rate limiting
   - Enable HTTPS

3. **Monitoring**
   - Set up health check endpoints
   - Monitor processing times
   - Track API usage

---

## 📞 Support

If you encounter issues:
1. Check this documentation
2. Review console logs
3. Test individual components
4. Verify environment setup

**System Requirements:**
- Python 3.8+
- FFmpeg installed
- OpenAI API key
- 8GB+ RAM recommended
- Fast storage for video processing

---

*Last Updated: July 2, 2025*
*Version: 1.0.0*
