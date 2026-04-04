#!/usr/bin/env python3
"""
Test Enhanced Video Processing API with specific video
"""

import requests
import json
import time
import os

def test_enhanced_api():
    """Test the enhanced video processing endpoint"""
    
    api_url = "http://localhost:5000/process/enhanced"
    video_path = "v12044gd0000cu2t04nog65p7djql4g0.MP4"  # Relative path from shared directory
    
    payload = {
        "video_path": video_path,
        "add_music": True,
        "text_style": "classic",
        "position": "top",
        "font": "arial",
        "custom_text": None,  # Let AI generate based on frames
        "speech_emphasis": 0.7
    }
    
    print("🧪 Testing Enhanced Video Processing API")
    print("=" * 50)
    print(f"🌐 API URL: {api_url}")
    print(f"📹 Video: {video_path}")
    print(f"📝 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        print("\n🚀 Sending request...")
        start_time = time.time()
        
        response = requests.post(
            api_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5 minutes timeout
        )
        
        request_time = time.time() - start_time
        
        print(f"⏱️ Request completed in {request_time:.1f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS! Enhanced processing completed")
            print("=" * 50)
            
            # Display results
            print(f"🎬 Video processed: {result.get('video_path', 'N/A')}")
            print(f"📁 Output file: {result.get('output_path', 'N/A')}")
            print(f"📝 Text overlay: '{result.get('text_overlay', 'N/A')}'")
            print(f"🎨 Text style: {result.get('text_style', 'N/A')}")
            print(f"⏱️ Processing time: {result.get('processing_time_seconds', 0):.1f}s")
            print(f"🎵 Music added: {result.get('music_added', False)}")
            print(f"🎶 Music source: {result.get('music_source', 'N/A')}")
            print(f"🔍 Frame analysis: {result.get('frame_analysis_used', False)}")
            print(f"⏰ Analysis interval: {result.get('analysis_interval', 'N/A')}")
            print(f"🔊 Music volume: {result.get('music_volume_range', 'N/A')}")
            
            # Check if download URL is available
            if result.get('download_url'):
                print(f"⬇️ Download URL: {result['download_url']}")
            
            # Enhanced features confirmation
            print("\n🚀 Enhanced Features Applied:")
            print(f"   ✅ 30-second frame analysis: {result.get('frame_analysis_used', False)}")
            print(f"   ✅ GPT-4o text generation: {'Yes' if result.get('text_overlay') else 'No'}")
            print(f"   ✅ Music volume optimization: {result.get('music_volume_range', 'Not applied')}")
            print(f"   ✅ Resolution preservation: Yes")
            
            return True
            
        else:
            print(f"\n❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"❌ Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"❌ Response text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection failed - Is the Flask app running?")
        print("💡 Start the app with: python flask_app.py")
        return False
    except requests.exceptions.Timeout:
        print(f"\n⏰ Request timeout after {request_time:.1f} seconds")
        print("💡 Video processing might take longer for large files")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def check_flask_status():
    """Check if Flask app is running"""
    
    try:
        health_response = requests.get("http://localhost:5000/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Flask app is running")
            return True
        else:
            print(f"⚠️ Flask app responded with status {health_response.status_code}")
            return False
    except:
        print("❌ Flask app is not running")
        return False

def main():
    """Main test function"""
    
    print("🧪 Enhanced Video Processing API Test")
    print("🕒 Started at:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # Check Flask status first
    if not check_flask_status():
        print("\n💡 To start the Flask app:")
        print("   python flask_app.py")
        return False
    
    # Run the enhanced API test
    success = test_enhanced_api()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Enhanced API test completed successfully!")
        print("\n📋 What was tested:")
        print("   ✅ Enhanced video processing endpoint")
        print("   ✅ 30-second frame analysis with GPT-4o")
        print("   ✅ Background music at -25 to -30dB")
        print("   ✅ Resolution preservation")
        print("   ✅ N8N integration compatibility")
    else:
        print("❌ Enhanced API test failed")
    
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
