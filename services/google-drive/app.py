from flask import Flask, request, jsonify, redirect, url_for, session
import io, os, json, pickle, datetime
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import google.auth.transport.requests

# Allow insecure transport for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# OAuth 2.0 configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_FILE = os.path.join('data', 'token.pickle')

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Load or create credentials
def get_credentials():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
            if creds and creds.valid:
                return creds
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(google.auth.transport.requests.Request())
                with open(TOKEN_FILE, 'wb') as token:
                    pickle.dump(creds, token)
                return creds
    return None

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# -- 16 MiB chunks = plays well with n8n memory limits
CHUNK = 16 * 1024 * 1024

@app.route('/')
def index():
    creds = get_credentials()
    if not creds:
        return redirect(url_for('authorize'))
    return jsonify({"status": "authenticated", "message": "Ready to upload files"})

@app.route('/authorize')
def authorize():
    # Check if already authorized
    creds = get_credentials()
    if creds:
        return jsonify({
            "status": "already_authorized",
            "message": "Already authenticated with Google Drive",
            "redirect": url_for('index')
        })
    
    # Create the flow using the client secrets file
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    
    # Generate URL for request authorization
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    # Store the state in the session for later verification
    session['state'] = state
    
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    # Verify state matches to prevent CSRF attacks
    state = session.get('state', None)
    if state is None:
        return jsonify({"error": "State parameter missing"}), 400
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    
    # Use the authorization server's response to fetch the OAuth 2.0 tokens
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    
    # Save credentials for future use
    credentials = flow.credentials
    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(credentials, token)
    
    return redirect(url_for('index'))

@app.route("/upload", methods=["POST"])
def upload():
    # Check if we have valid credentials
    creds = get_credentials()
    if not creds:
        return jsonify({"error": "Not authenticated", "auth_url": url_for('authorize', _external=True)}), 401
    
    if "file" not in request.files:
        return jsonify({"error": "No file field"}), 400

    file = request.files["file"]
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    body = {"name": file.filename, "mimeType": file.mimetype}

    # Optional: Add to a specific folder if folder_id is provided
    folder_id = request.form.get('folder_id')
    if folder_id:
        body['parents'] = [folder_id]

    # Read file in memory-efficient way
    media = MediaIoBaseUpload(io.BytesIO(file.read()),
                           mimetype=file.mimetype,
                           chunksize=CHUNK,
                           resumable=True)

    req = drive.files().create(body=body, media_body=media, fields="id,name,mimeType,size")
    resp = None
    
    # Track upload progress
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    file_id = resp["id"]
    
    # Create shareable link
    drive.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'},
        fields='id'
    ).execute()
    
    # Get direct download link
    dl_link = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    # Get view link
    view_link = f"https://drive.google.com/file/d/{file_id}/view"
    
    # Get additional metadata from the request if available
    video_path = request.form.get('videoPath', None)
    video_name = request.form.get('videoName', None)
    detected_at = request.form.get('detectedAt', None)
    original_file_size = request.form.get('fileSize', None)
    
    # Format response for n8n compatibility with the requested schema
    response_data = {
        # Original video metadata (if provided)
        "videoPath": video_path,
        "videoName": video_name or file.filename.split('.')[0],
        "fileSize": original_file_size or resp.get("size", 0),
        "detectedAt": detected_at,
        
        # Additional metadata for compatibility
        "fileName": "upload",
        "mimeType": "application/json",
        "binaryId": request.form.get('binaryId', ''),
        "success": True,
        "extractedAt": datetime.datetime.now().isoformat(),
        
        # Google Drive file information (previously null values now populated)
        "id": file_id,
        "download_link": dl_link,
        "view_link": view_link,
        "name": resp.get("name", file.filename),
        "size": resp.get("size", 0)
    }
    
    # Return a standard 200 JSON response for n8n compatibility
    # This ensures n8n treats it as JSON data, not as a file download
    response = jsonify(response_data)
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response, 200

@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint"""
    creds = get_credentials()
    return jsonify({
        "status": "healthy", 
        "service": "flaskdrive",
        "authenticated": creds is not None,
        "auth_url": url_for('authorize', _external=True) if creds is None else None
    }), 200

@app.route("/status", methods=["GET"])
def status():
    """Detailed status endpoint"""
    creds = get_credentials()
    return jsonify({
        "authenticated": creds is not None,
        "credentials_file": os.path.exists(CLIENT_SECRET_FILE),
        "token_file": os.path.exists(TOKEN_FILE),
        "auth_url": url_for('authorize', _external=True) if creds is None else None
    })

@app.route("/file-info/<file_id>", methods=["GET"])
def file_info(file_id):
    """Get information about a file by its ID"""
    # Check if we have valid credentials
    creds = get_credentials()
    if not creds:
        return jsonify({"error": "Not authenticated", "auth_url": url_for('authorize', _external=True)}), 401
    
    try:
        # Connect to Google Drive API
        drive = build("drive", "v3", credentials=creds, cache_discovery=False)
        
        # Get file metadata
        file_metadata = drive.files().get(
            fileId=file_id, 
            fields="id,name,mimeType,size,webContentLink,webViewLink"
        ).execute()
        
        # Format response for n8n compatibility
        response_data = {
            "id": file_metadata.get("id"),
            "name": file_metadata.get("name"),
            "mimeType": file_metadata.get("mimeType"),
            "size": file_metadata.get("size"),
            "download_link": f"https://drive.google.com/uc?export=download&id={file_id}",
            "view_link": file_metadata.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view",
            "success": True,
            "retrievedAt": datetime.datetime.now().isoformat()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False,
            "id": file_id
        }), 404

@app.route("/search", methods=["GET"])
def search_files():
    """Search for files in Google Drive by name"""
    # Check if we have valid credentials
    creds = get_credentials()
    if not creds:
        return jsonify({"error": "Not authenticated", "auth_url": url_for('authorize', _external=True)}), 401
    
    # Get query parameters
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400
    
    try:
        # Connect to Google Drive API
        drive = build("drive", "v3", credentials=creds, cache_discovery=False)
        
        # Search for files matching the query
        # Format the query to search by name
        search_query = f"name contains '{query}'"
        
        # Execute the search
        results = drive.files().list(
            q=search_query,
            spaces='drive',
            fields="files(id, name, mimeType, size, webContentLink, webViewLink)",
            orderBy="createdTime desc"
        ).execute()
        
        # Get the files from the results
        files = results.get('files', [])
        
        # Format the response
        response_data = {
            "files": [],
            "count": len(files),
            "query": query,
            "success": True,
            "retrievedAt": datetime.datetime.now().isoformat()
        }
        
        # Add each file to the response
        for file in files:
            file_id = file.get('id')
            response_data['files'].append({
                "id": file_id,
                "name": file.get("name"),
                "mimeType": file.get("mimeType"),
                "size": file.get("size"),
                "download_link": f"https://drive.google.com/uc?export=download&id={file_id}",
                "view_link": file.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view"
            })
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False,
            "query": query
        }), 500

if __name__ == "__main__":
    # Check if client secret file exists
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"Warning: {CLIENT_SECRET_FILE} not found. OAuth flow will fail.")
        print("Please place your OAuth client secret JSON file in the correct location.")
    
    # For development only - in production, this should be False
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    # Allow for non-HTTPS OAuth flow in development
    if debug_mode:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
