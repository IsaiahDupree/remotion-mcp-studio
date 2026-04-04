#!/usr/bin/env python3
"""
Simple Test - Check API and test video processing
"""
import requests
import json
import time
from pathlib import Path

def test_api_connection():
    """Test if API is reachable"""
    print("🌐 Testing API Connection...")
    try:
        response = requests.get("http://localhost:5001/system/status", timeout=5)
        if response.status_code == 200:
            print("✅ API is running!")
            return True
        else:
            print(f"⚠️ API responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API not reachable: {e}")
        return False

def test_video_with_text_and_music():
    """Test video processing with text overlay and background music"""
    print("\n🎬 Testing Video Processing...")
    
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    output_path = r"C:\Users\Isaia\Documents\Coding\N8N\output\test_enhanced_video.mp4"
    
    if not Path(video_path).exists():
        print(f"❌ Video file not found: {video_path}")
        return False
    
    # Test data for video processing
    request_data = {
        "video_path": video_path,
        "output_path": output_path,
        "text_overlay": "Enhanced Video Test",
        "text_position": "bottom_center",
        "preserve_audio": False,  # Replace with music
        "music_volume": -20
    }
    
    print(f"📋 Processing request:")
    print(f"   Video: {Path(video_path).name}")
    print(f"   Text: {request_data['text_overlay']}")
    print(f"   Output: {Path(output_path).name}")
    
    try:
        print("⏳ Sending processing request...")
        response = requests.post(
            "http://localhost:5001/video/process",
            json=request_data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Video processing successful!")
            print(f"   📁 Output file: {result.get('output_path', 'Unknown')}")
            print(f"   ⏱️ Processing time: {result.get('processing_time', 0):.1f}s")
            print(f"   📐 Dimensions: {result.get('width')}x{result.get('height')}")
            
            # Check if output file exists
            if Path(result.get('output_path', '')).exists():
                file_size = Path(result.get('output_path')).stat().st_size / (1024 * 1024)
                print(f"   💾 Output size: {file_size:.1f} MB")
                print("🎉 Complete video processing working!")
                return True
            else:
                print("⚠️ Output file not found")
                return False
                
        else:
            print(f"❌ Processing failed with status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Error text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️ Request timed out (120s)")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    """Run simple tests"""
    print("🔬 SIMPLE SYSTEM TEST")
    print("=" * 25)
    
    # Test 1: API Connection
    api_ok = test_api_connection()
    
    if not api_ok:
        print("\n❌ API not available. Make sure Flask server is running.")
        print("💡 Run: python enhanced_flask_api.py")
        return
    
    # Test 2: Video Processing
    video_ok = test_video_with_text_and_music()
    
    print(f"\n📊 TEST RESULTS")
    print("=" * 15)
    print(f"API Connection: {'✅ PASS' if api_ok else '❌ FAIL'}")
    print(f"Video Processing: {'✅ PASS' if video_ok else '❌ FAIL'}")
    
    if api_ok and video_ok:
        print(f"\n🎉 SYSTEM IS WORKING!")
        print("🚀 Ready for video processing with text and music")
    else:
        print(f"\n⚠️ SYSTEM NEEDS ATTENTION")

if __name__ == "__main__":
    main()
