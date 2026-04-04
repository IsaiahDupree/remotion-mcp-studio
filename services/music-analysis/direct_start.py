#!/usr/bin/env python3
"""
Direct startup script for the enhanced Flask API
"""
import os
import sys

# OpenAI API key should be set via environment variable
# os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    try:
        print("Starting enhanced Flask API...")
        # Import at runtime to ensure environment variables are set
        import enhanced_flask_api
        # Get the app from the module
        app = enhanced_flask_api.app
        # Run the Flask app directly
        app.run(host="0.0.0.0", port=5001, debug=True)
    except Exception as e:
        print(f"Error starting Flask app: {e}")
        import traceback
        traceback.print_exc()
