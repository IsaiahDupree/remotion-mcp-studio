#!/usr/bin/env python3
"""
Start Enhanced Flask API Server
Runs the enhanced API with intelligent video analysis capabilities
"""
import sys
import os

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 STARTING ENHANCED FLASK API SERVER")
    print("🧠 Intelligent Video Content Analysis Enabled")
    print("🎵 Music System Integration Active")
    print("=" * 50)
    
    try:
        from enhanced_flask_api import app
        
        print("✅ Flask app imported successfully")
        print("🌐 Starting server on http://localhost:5001")
        print("📡 Available endpoints:")
        print("   - /video/analyze-content (NEW!)")
        print("   - /video/process")
        print("   - /music/search")
        print("   - /system/status")
        print("🚀 Ready for n8n integration!")
        print("=" * 50)
        
        # Start the Flask app
        app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
        
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
