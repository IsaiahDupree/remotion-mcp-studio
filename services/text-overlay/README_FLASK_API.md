# Video Enhancement Flask API for N8N Integration

This Flask application provides a REST API for processing videos with AI-generated text overlays and background music, specifically designed for integration with N8N workflows through Docker containers.

## Features

- **AI-Powered Text Overlays**: Generate contextual text overlays using OpenAI's GPT-4 and Whisper
- **Background Music Integration**: Add SoundCloud tracks from Excel spreadsheets
- **CSV Logging**: Comprehensive logging of all processing results
- **Docker Deployment**: Easy containerization for N8N integration
- **REST API**: Full REST API for workflow automation
- **Batch Processing**: Process multiple videos simultaneously
- **Health Monitoring**: Built-in health checks and monitoring

## Quick Start

### 1. Environment Setup

Create a `.env` file with your OpenAI API key:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Docker Deployment

```bash
# Build and start the services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs video-enhancer-api
```

### 3. Access Points

- **Flask API**: http://localhost:5000
- **N8N Interface**: http://localhost:5678 (admin/changeme)
- **Health Check**: http://localhost:5000/health

## API Endpoints

### Health Check
```http
GET /health
```
Returns service status and configuration.

### List Available Videos
```http
GET /videos
```
Returns all videos available in the shared directory.

### List SoundCloud Tracks
```http
GET /soundcloud/tracks
```
Returns available tracks from the Excel spreadsheet.

### Process Single Video
```http
POST /process/video
Content-Type: application/json

{
    "video_path": "video.mp4",
    "add_music": true,
    "position": "TOP",
    "custom_text": "Optional custom text",
    "speech_emphasis": 0.6
}
```

### Process Multiple Videos (Batch)
```http
POST /process/batch
Content-Type: application/json

{
    "video_paths": ["video1.mp4", "video2.mp4"],
    "add_music": true,
    "position": "TOP",
    "speech_emphasis": 0.6
}
```

### Download Processed Video
```http
GET /download/<filename>
```

### Get Processing Logs
```http
GET /logs/csv          # Download full CSV log
GET /logs/recent?limit=10  # Get recent logs as JSON
```

## Directory Structure

```
/app/
├── flask_app.py              # Main Flask application
├── enhance_video_fast.py     # Video processing logic
├── video_enhancer/           # Video enhancement modules
├── enhanced_videos/          # Output directory
├── soundcloud_tracks.xlsx    # SoundCloud tracks database
├── processing_log.csv        # CSV processing logs
└── shared_data/             # Input videos directory
```

## N8N Integration Examples

### Example 1: Webhook Triggered Processing

```json
{
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300],
      "parameters": {
        "httpMethod": "POST",
        "path": "process-video"
      }
    },
    {
      "name": "Process Video",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300],
      "parameters": {
        "url": "http://video-enhancer-api:5000/process/video",
        "method": "POST",
        "jsonParameters": true,
        "parametersJson": "{\n  \"video_path\": \"{{$json.video_path}}\",\n  \"add_music\": true,\n  \"position\": \"TOP\",\n  \"speech_emphasis\": 0.6\n}"
      }
    }
  ]
}
```

### Example 2: Batch Processing Workflow

```json
{
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [250, 300],
      "parameters": {
        "interval": "hours",
        "hoursInterval": 6
      }
    },
    {
      "name": "List Videos",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300],
      "parameters": {
        "url": "http://video-enhancer-api:5000/videos",
        "method": "GET"
      }
    },
    {
      "name": "Process Batch",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300],
      "parameters": {
        "url": "http://video-enhancer-api:5000/process/batch",
        "method": "POST",
        "jsonParameters": true,
        "parametersJson": "{\n  \"video_paths\": {{$json.videos}},\n  \"add_music\": true,\n  \"position\": \"TOP\"\n}"
      }
    }
  ]
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI features | Required |
| `SHARED_VIDEOS_DIR` | Directory containing input videos | `/shared_data` |
| `OUTPUT_DIR` | Directory for processed videos | `/app/enhanced_videos` |
| `SOUNDCLOUD_EXCEL_PATH` | Path to SoundCloud tracks Excel | `/app/soundcloud_tracks.xlsx` |
| `CSV_LOG_PATH` | Path to CSV processing log | `/app/processing_log.csv` |

### SoundCloud Excel Format

The Excel file should contain these columns:
- `URL`: SoundCloud track URL
- `Title`: Track title
- `Artist`: Artist name
- `Duration`: Track duration
- `Genre`: Music genre
- `BPM`: Beats per minute
- `Mood`: Track mood/style

## CSV Logging Format

Each processed video is logged with:
- `timestamp`: Processing timestamp
- `video_filename`: Original video filename
- `transcript`: Video transcript (truncated)
- `text_overlay`: Applied text overlay
- `music_url`: Selected music URL
- `processing_time_seconds`: Processing duration
- `success`: Processing success status
- `error_message`: Any error messages

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_key_here

# Run Flask app
python flask_app.py
```

### Testing

```bash
# Test health endpoint
curl http://localhost:5000/health

# Test video processing
curl -X POST http://localhost:5000/process/video \
  -H "Content-Type: application/json" \
  -d '{"video_path": "test_video.mp4", "add_music": true}'
```

## Troubleshooting

### Common Issues

1. **FFMPEG Not Found**: Ensure ffmpeg is installed in the container
2. **OpenAI API Errors**: Check API key and quota
3. **File Permissions**: Ensure proper volume permissions in Docker
4. **Memory Issues**: Increase Docker memory limits for large videos

### Logs

```bash
# Check container logs
docker-compose logs video-enhancer-api

# Check processing logs
curl http://localhost:5000/logs/recent?limit=20
```

## Performance Considerations

- **Video Size**: Large videos may require more processing time
- **Concurrent Requests**: API can handle multiple requests but processing is CPU-intensive
- **Memory Usage**: Each video processing instance uses significant memory
- **Storage**: Ensure adequate disk space for output files

## Security

- API runs as non-root user in container
- Input validation on all endpoints
- Secure filename handling
- Environment variable configuration
- Health check monitoring

For production deployment, consider:
- Authentication/authorization
- Rate limiting
- HTTPS termination
- Monitoring and alerting
- Backup strategies
