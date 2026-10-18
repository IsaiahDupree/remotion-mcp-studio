#!/usr/bin/env python3
"""
Complete OAuth Authorization with callback URL
"""

import os
import pickle
from google_auth_oauthlib.flow import Flow

# Allow insecure transport for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_FILE = os.path.join('data', 'token.pickle')
REDIRECT_URI = 'http://localhost:5002/oauth2callback'

# Your callback URL
CALLBACK_URL = 'http://localhost:5002/oauth2callback?state=VClhhT4BZEBrH1E0QdoSbuNt2Mh9RM&code=4/0AVMBsJikmi6cLOWRGAGlmHZsvjE1lAits9YgHKY5FScswJErxfVybYzlb58btYW4Xig6RA&scope=https://www.googleapis.com/auth/drive.file'

def complete_authorization():
    """Complete the OAuth flow with the callback URL"""
    
    print("🔐 Completing Flask Drive Authorization...")
    print("=" * 50)
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    try:
        # Create the flow
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        print("✅ Created OAuth flow")
        
        # Complete the authorization with the callback URL
        flow.fetch_token(authorization_response=CALLBACK_URL)
        creds = flow.credentials
        
        print("✅ Successfully exchanged code for token")
        
        # Save the credentials for future use
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        
        print(f"✅ Token saved to: {TOKEN_FILE}")
        print("🎯 Flask Drive is now permanently authorized!")
        
        # Test the credentials
        from googleapiclient.discovery import build
        service = build('drive', 'v3', credentials=creds)
        
        # Test by getting user info
        about = service.about().get(fields="user").execute()
        user_email = about.get('user', {}).get('emailAddress', 'Unknown')
        
        print(f"✅ Authenticated as: {user_email}")
        print("🚀 Google Drive API is working!")
        
        return True
        
    except Exception as e:
        print(f"❌ Authorization failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = complete_authorization()
    if success:
        print("\n🎉 Authorization complete!")
        print("🔥 Flask Drive is ready for permanent use!")
    else:
        print("\n❌ Authorization failed. Please check the error above.")
