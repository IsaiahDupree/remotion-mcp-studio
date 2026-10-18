#!/usr/bin/env python3
"""
Auto-Authorization Script for Flask Drive
Creates permanent OAuth token without manual intervention
"""

import os
import pickle
import json
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_FILE = os.path.join('data', 'token.pickle')
REDIRECT_URI = 'http://localhost:5002/oauth2callback'

def create_permanent_auth():
    """Create permanent authorization token"""
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    print("🔐 Flask Drive Auto-Authorization Setup")
    print("=" * 50)
    
    # Check if client secret exists
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"❌ Error: {CLIENT_SECRET_FILE} not found!")
        return False
    
    print(f"✅ Found client secrets: {CLIENT_SECRET_FILE}")
    
    # Check if token already exists and is valid
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
            if creds and creds.valid:
                print("✅ Valid token already exists!")
                return True
            elif creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired token...")
                creds.refresh(Request())
                with open(TOKEN_FILE, 'wb') as token:
                    pickle.dump(creds, token)
                print("✅ Token refreshed successfully!")
                return True
    
    # Need to create new authorization
    print("\n🚀 Creating new authorization...")
    print("This will open your browser for one-time setup.")
    print("After this, authorization will be permanent!")
    
    # Create the flow
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    # Get authorization URL
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    print(f"\n🌐 Please visit this URL to authorize:")
    print(f"{auth_url}")
    print("\nAfter authorization, you'll be redirected to localhost:5002")
    print("Copy the FULL redirect URL and paste it here:")
    
    # Get authorization code from user
    authorization_response = input("\nPaste the full redirect URL here: ").strip()
    
    # Exchange authorization code for token
    try:
        flow.fetch_token(authorization_response=authorization_response)
        creds = flow.credentials
        
        # Save the credentials for future use
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        
        print("✅ Authorization successful!")
        print(f"✅ Token saved to: {TOKEN_FILE}")
        print("🎯 Flask Drive is now permanently authorized!")
        return True
        
    except Exception as e:
        print(f"❌ Authorization failed: {str(e)}")
        return False

def check_auth_status():
    """Check current authorization status"""
    print("\n📊 Authorization Status:")
    print("-" * 30)
    
    if not os.path.exists(CLIENT_SECRET_FILE):
        print("❌ Client secrets: Missing")
        return False
    else:
        print("✅ Client secrets: Found")
    
    if not os.path.exists(TOKEN_FILE):
        print("❌ Auth token: Missing")
        return False
    
    try:
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
            if creds and creds.valid:
                print("✅ Auth token: Valid")
                return True
            elif creds and creds.expired:
                print("⚠️  Auth token: Expired (can refresh)")
                return False
            else:
                print("❌ Auth token: Invalid")
                return False
    except Exception as e:
        print(f"❌ Auth token: Error - {str(e)}")
        return False

if __name__ == "__main__":
    print("🔐 Flask Drive Authorization Manager")
    print("=" * 40)
    
    # Check current status
    is_authorized = check_auth_status()
    
    if is_authorized:
        print("\n🎯 Already authorized! No action needed.")
    else:
        print("\n🚀 Setting up authorization...")
        success = create_permanent_auth()
        if success:
            print("\n🎉 Setup complete! Flask Drive is ready to use.")
        else:
            print("\n❌ Setup failed. Please try again.")
