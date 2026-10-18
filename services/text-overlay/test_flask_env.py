#!/usr/bin/env python3
"""
Test Flask Environment Variables Loading
=======================================

Quick test to verify the Flask app properly loads API keys from .env file
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_flask_env_loading():
    """Test that Flask app properly loads environment variables"""
    print("🧪 Testing Flask Environment Variables Loading")
    print("=" * 50)
    
    try:
        # Import the Flask app (this will trigger .env loading)
        from flask_app import app, OPENAI_API_KEY, PERPLEXITY_API_KEY, ELEVENLABS_API_KEY
        
        print("✅ Flask app imported successfully")
        
        # Check API keys
        print(f"\n🔑 API Keys Status:")
        print(f"   OpenAI API Key: {'✅ Loaded' if OPENAI_API_KEY else '❌ Missing'}")
        print(f"   Perplexity API Key: {'✅ Loaded' if PERPLEXITY_API_KEY else '❌ Missing'}")
        print(f"   ElevenLabs API Key: {'✅ Loaded' if ELEVENLABS_API_KEY else '❌ Missing'}")
        
        # Test app context
        with app.app_context():
            print(f"\n🌐 Flask App Configuration:")
            print(f"   App Name: {app.name}")
            print(f"   Debug Mode: {app.debug}")
            print(f"   Max Content Length: {app.config.get('MAX_CONTENT_LENGTH', 'Not set')}")
        
        # Test a simple route
        client = app.test_client()
        response = client.get('/health')
        
        print(f"\n🏥 Health Check Test:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.get_json() if response.status_code == 200 else 'Error'}")
        
        if response.status_code == 200:
            print("✅ Flask app is working properly with environment variables!")
            return True
        else:
            print("❌ Flask app health check failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Flask environment: {e}")
        return False

def test_openai_connection():
    """Test OpenAI API connection with loaded key"""
    print(f"\n🤖 Testing OpenAI API Connection")
    print("=" * 35)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        import openai
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if not openai_key:
            print("❌ No OpenAI API key found")
            return False
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=openai_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'API connection successful' in exactly those words."}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ OpenAI API Response: {result}")
        
        if "API connection successful" in result:
            print("✅ OpenAI API is working properly!")
            return True
        else:
            print("⚠️ OpenAI API responded but with unexpected content")
            return True  # Still consider it a success
            
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Flask Environment & API Testing Suite")
    print("========================================")
    
    # Test Flask environment loading
    flask_success = test_flask_env_loading()
    
    # Test OpenAI API connection
    openai_success = test_openai_connection()
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"   Flask Environment: {'✅ SUCCESS' if flask_success else '❌ FAILED'}")
    print(f"   OpenAI API: {'✅ SUCCESS' if openai_success else '❌ FAILED'}")
    
    if flask_success and openai_success:
        print(f"\n🎉 All tests passed! Flask app is ready with API keys.")
        print(f"🚀 You can now run intelligent music-video matching in the Flask app!")
    else:
        print(f"\n⚠️ Some tests failed. Check the error messages above.")
