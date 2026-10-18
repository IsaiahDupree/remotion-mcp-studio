#!/usr/bin/env python3
"""
One-time OAuth2 setup to get a YouTube upload refresh token.
Runs a local server on port 8085 to catch the redirect code.

Usage:
    python3 get_youtube_token.py

It will open the auth URL, catch the code, and print the refresh token.
"""

import json
import urllib.request
import urllib.parse
import http.server
import threading
import webbrowser

import os
CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI  = "http://localhost:8085/oauth2callback"
PORT          = 8085

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

auth_code_received = threading.Event()
auth_code = None


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authorization successful! You can close this tab.</h1>")
            auth_code_received.set()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No code received")

    def log_message(self, format, *args):
        pass  # suppress server logs


def exchange_code(code: str):
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()

    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())

    if "refresh_token" not in result:
        print("Error:", result)
        return None

    return result["refresh_token"]


def main():
    # Start local callback server
    server = http.server.HTTPServer(("localhost", PORT), CallbackHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    # Build auth URL
    params = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    })
    auth_url = f"https://accounts.google.com/o/oauth2/auth?{params}"

    print("Opening browser for YouTube authorization...")
    print(f"URL: {auth_url}")
    webbrowser.open(auth_url)

    print("Waiting for authorization (complete in browser)...")
    auth_code_received.wait(timeout=120)
    server.shutdown()

    if not auth_code:
        print("No code received. Timed out.")
        return

    print("Code received. Exchanging for refresh token...")
    refresh_token = exchange_code(auth_code)
    if refresh_token:
        print()
        print("SUCCESS! YouTube refresh token:")
        print(refresh_token)
        print()
        # Auto-write to upload_youtube.py
        import re
        from pathlib import Path
        upload_py = Path(__file__).parent / "upload_youtube.py"
        content = upload_py.read_text()
        new_content = re.sub(
            r'GOOGLE_REFRESH_TOKEN\s*=\s*"[^"]*"',
            f'GOOGLE_REFRESH_TOKEN = "{refresh_token}"',
            content
        )
        upload_py.write_text(new_content)
        print(f"Auto-updated GOOGLE_REFRESH_TOKEN in upload_youtube.py")


if __name__ == "__main__":
    main()
