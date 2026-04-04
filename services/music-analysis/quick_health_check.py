#!/usr/bin/env python3
"""
Quick Health Check - Test API and video processing
"""
import requests
import time
import json
from pathlib import Path

def wait_for_api(max_wait=60):
    """Wait for API to be available"""
    print("⏳ Waiting for API to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get("http://localhost:5001/system/status", timeout=5)
            if response.status_code == 200:
                print("✅ API is ready!")
                return True
        except:
            pass
        
        print(".", end="", flush=True)
        time.sleep(2)
    
    print("\n❌ API not ready after 60 seconds")
    return False

def test_health():
    """Test API health"""
    try:
        response = requests.get("http://localhost:5001/system/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print("\n🏥 SYSTEM HEALTH CHECK")
            print("=" * 25)
            print(f"✅ API Status: {status.get('status', 'unknown')}")
            print(f"✅ Music Tracks: {status.get('music_database', {}).get('total_tracks', 0)}")
            print(f"✅ FFmpeg: {'Available' if status.get('video_processor', {}).get('ffmpeg_available') else 'Not Available'}")
            print(f"✅ Intelligence: {'Ready' if status.get('intelligent_analyzer_status') == 'healthy' else 'Loading'}")
            return True
        else:
            print(f"❌ API Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False

def test_video_processing():
    """Test simple video processing"""
    print("\n🎬 TESTING VIDEO PROCESSING")
    print("=" * 30)
    
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    output_path = r"C:\Users\Isaia\Documents\Coding\N8N\output\quick_test.mp4"
    
    if not Path(video_path).exists():
        print(f"❌ Test video not found: {video_path}")
        return False
    
    request_data = {
        "video_path": video_path,
        "output_path": output_path,
        "text_overlay": "Quick Test",
        "text_position": "bottom_center",
        "preserve_audio": True
    }
    
    print("⏳ Processing video (text overlay only)...")
    try:
        response = requests.post(
            "http://localhost:5001/video/process",
            json=request_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Video processing successful!")
            print(f"   📁 Output: {Path(result['output_path']).name}")
            print(f"   ⏱️ Time: {result.get('processing_time', 0):.1f}s")
            return True
        else:
            print(f"❌ Processing failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Processing error: {e}")
        return False

def main():
    """Run quick health check"""
    print("🔬 QUICK SYSTEM HEALTH CHECK")
    print("=" * 30)
    
    # Wait for API
    if not wait_for_api():
        return
    
    # Test health
    health_ok = test_health()
    
    # Test video processing
    if health_ok:
        video_ok = test_video_processing()
    else:
        video_ok = False
    
    print(f"\n📊 RESULTS")
    print("=" * 10)
    print(f"API Health: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Video Processing: {'✅ PASS' if video_ok else '❌ FAIL'}")
    
    if health_ok and video_ok:
        print("\n🎉 SYSTEM IS OPERATIONAL!")
    else:
        print("\n⚠️ SYSTEM NEEDS ATTENTION")

if __name__ == "__main__":
    main()
