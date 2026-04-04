#!/usr/bin/env python3
"""
Test Simple API
"""
import requests
import json
from pathlib import Path

def test_api():
    """Test the simple API"""
    print("🔬 TESTING SIMPLE API")
    print("=" * 25)
    
    # Test health endpoint
    try:
        print("⏳ Testing /system/status...")
        response = requests.get("http://localhost:5001/system/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ API Health: WORKING")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test video processing
    print("\n⏳ Testing video processing...")
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    output_path = r"C:\Users\Isaia\Documents\Coding\N8N\output\simple_api_test.mp4"
    
    if not Path(video_path).exists():
        print(f"❌ Test video not found: {video_path}")
        return False
    
    request_data = {
        "video_path": video_path,
        "output_path": output_path,
        "text_overlay": "Simple API Test"
    }
    
    try:
        response = requests.post(
            "http://localhost:5001/video/process-simple",
            json=request_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Video Processing: SUCCESS")
            print(f"   Output: {Path(result['output_path']).name}")
            print(f"   Time: {result.get('processing_time', 0):.1f}s")
            
            # Check if file exists
            if Path(result['output_path']).exists():
                file_size = Path(result['output_path']).stat().st_size / (1024 * 1024)
                print(f"   Size: {file_size:.1f} MB")
                return True
            else:
                print("⚠️ Output file not created")
                return False
        else:
            print(f"❌ Processing failed: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error.get('error')}")
            except:
                print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Processing error: {e}")
        return False

def main():
    success = test_api()
    print(f"\n📊 RESULT: {'🎉 SUCCESS' if success else '❌ FAILED'}")

if __name__ == "__main__":
    main()
