# FlaskDrive - Google Drive Upload Service for n8n

This Flask microservice provides a robust API for uploading large video files to Google Drive directly from n8n workflows. It handles chunked uploads to support large files and returns direct download links.

## Recent Updates (May 2025)

### Enhanced Response Format
- Improved JSON response format with comprehensive metadata
- Added support for preserving original video metadata
- Standardized HTTP 200 responses with proper content type headers

### New API Endpoints
- Added `/file-info/<file_id>` endpoint to retrieve file metadata
- Added `/search?q=<query>` endpoint to search for files by name
- Enhanced error handling and authentication flow

### n8n Integration Utilities
- Created utility code nodes for data extraction and URL transformation
- Added support for direct usercontent.google.com download links
- Improved compatibility with n8n's binary data handling

## Setup Instructions

### 1. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services
2. Enable the Google Drive API
3. Create OAuth 2.0 Client ID:
   - Navigate to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Select "Web application" as the application type
   - Add authorized redirect URIs (e.g., `http://localhost:5000/oauth2callback`)
   - Download the JSON client secret file
4. Rename the downloaded file to `client_secret.json` or update the path in docker-compose.yml

### 2. Configuration

The service is configured through environment variables in the Docker Compose file:

- `FLASK_ENV`: Set to `production` for production use
- `FLASK_SECRET_KEY`: Secret key for Flask sessions
- `MAX_CONTENT_LENGTH`: Maximum upload size (default: 10GB)
- `OAUTHLIB_INSECURE_TRANSPORT`: Set to 1 for development only

### 3. Running the Service

1. Make sure you have Docker and Docker Compose installed
2. Ensure your OAuth client secret file is correctly referenced in docker-compose.yml
3. Start the services:

```bash
docker-compose up -d
```

4. The Flask service will be available at `http://localhost:5000` and within the Docker network at `http://flaskdrive:5000`
5. On first run, visit `http://localhost:5000` to complete the OAuth authorization flow

## API Endpoints

### Upload File to Google Drive

**Endpoint:** `POST /upload`

**Request:**

- Content-Type: `multipart/form-data`
- Body:
  - `file`: The file to upload (required)
  - `folder_id`: Google Drive folder ID to upload to (optional)

**Response:**

```json
{
  "id": "1aBcDeFgHiJkLmNoPqRsTuVwXyZ",
  "name": "video.mp4",
  "mimeType": "video/mp4",
  "size": "1048576",
  "download_link": "https://drive.google.com/uc?export=download&id=1aBcDeFgHiJkLmNoPqRsTuVwXyZ",
  "view_link": "https://drive.google.com/file/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ/view",
  "success": true
}
```

### Health Check

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "healthy",
  "service": "flaskdrive",
  "authenticated": true,
  "auth_url": null
}
```

### Status Check

**Endpoint:** `GET /status`

**Response:**

```json
{
  "authenticated": true,
  "credentials_file": true,
  "token_file": true,
  "auth_url": null
}
```

## Using with n8n

1. In n8n, create a new workflow or import the provided sample workflow
2. Use the HTTP Request node to send files to the Flask service:
   - URL: `http://flaskdrive:5000/upload`
   - Method: `POST`
   - Binary Data: Enable and select the binary property containing your file
3. The response will contain file ID and download links that you can use in subsequent nodes

## Performance Considerations

- The service uses 16MB chunks for uploads, which balances memory usage with upload speed
- For very large files (>10GB), consider adjusting the `MAX_CONTENT_LENGTH` environment variable
- The service automatically creates shareable links for the uploaded files

## Troubleshooting

1. **Service not accessible from n8n:**
   - Ensure both services are on the same Docker network
   - Check that the Flask service is running with `docker-compose ps`

2. **Upload fails with 401 Unauthorized:**
   - Visit `http://localhost:5000` in your browser to complete the OAuth flow
   - Check the Flask service logs with `docker-compose logs flaskdrive`
   - Ensure the file size doesn't exceed the configured maximum

3. **OAuth errors:**
   - Verify that your `client_secret.json` file is correctly mounted in the container
   - Check that the redirect URI in Google Cloud Console matches the one in your app
   - Make sure the Google Drive API is enabled for your project
