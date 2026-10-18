# Video Generator Service

A Flask microservice that combines audio files with a static image to produce a video file. This service is designed to work with the n8n podcast creator workflow.

## Features

- Combines multiple audio files into a single audio track
- Creates a video using a static image and audio
- Returns a path to the generated video file
- Containerized with Docker for easy deployment

## API Endpoints

### Generate Video

**URL**: `/generate-video`
**Method**: `POST`
**Content Type**: `application/json`

**Request Body**:

```json
[
  {
    "audioPaths": [
      "/tmp/audio_1749258034150_0_data.mp3",
      "/tmp/audio_1749258034150_1_data.mp3"
    ]
  },
  {
    "imagePath": "/tmp/cover_1749258031268.png"
  }
]
```

**Response**:

```json
{
  "success": true,
  "videoPath": "/tmp/video-generator/output/video_12345678-1234-1234-1234-123456789012.mp4"
}
```

### Health Check

**URL**: `/health`
**Method**: `GET`

**Response**:

```json
{
  "status": "healthy"
}
```

## Integration with n8n

To integrate this service with your n8n podcast creator workflow:

1. Add an HTTP Request node to your n8n workflow
2. Configure it to make a POST request to `http://video-generator:5000/generate-video`
3. Set the body to include the paths to your audio files and cover image
4. Use the returned video path in subsequent steps of your workflow

## Docker Setup

Add the following service to your `docker-compose.yml`:

```yaml
video-generator:
  build:
    context: ./services/video-generator
  volumes:
    - /tmp:/tmp
  ports:
    - "5000:5000"
  restart: unless-stopped
```

Make sure the `/tmp` directory is shared between this container and any other containers that need to access the generated files.

## Local Development

### Prerequisites

- Python 3.9+
- FFmpeg

### Installation

```bash
pip install -r requirements.txt
```

### Running

```bash
python app.py
```

The service will be available at `http://localhost:5000`.

## Note

This service expects the input file paths to be accessible within the container. When running in Docker, make sure to mount the appropriate volumes.
