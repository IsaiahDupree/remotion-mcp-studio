#!/usr/bin/env python3
"""
Test just the enhanced processing endpoint to debug the issue
"""
import requests
import json
import time
import os
from pathlib import Path

def test_enhanced_processing():
    """Test enhanced video processing with detailed error reporting"""
    
    base_url = "http://localhost:5001"
    test_video = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    output_dir = r"C:\Users\Isaia\Documents\Coding\N8N\cache\processed_videos"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate unique output filename
    timestamp = int(time.time())
    output_filename = f"debug_enhanced_video_{timestamp}.mp4"
    output_path = os.path.join(output_dir, output_filename)
    
    url = f"{base_url}/video/process-enhanced"
    
    data = {
        "video_path": test_video,
        "output_path": output_path,
        "primary_text": "Learn Smarter with AI",
        "secondary_text": "AI-Powered Enhancement",
        "text_position": "top_center",
        "music_volume_db": -25,
        "preserve_audio": True,
        "smart_placement": True
    }
    
    print("🔧 DEBUGGING ENHANCED PROCESSING")
    print("=" * 50)
    print(f"📹 Video: {Path(test_video).name}")
    print(f"📁 Output: {output_path}")
    print(f"🎯 Primary Text: {data['primary_text']}")
    print(f"🔗 Endpoint: {url}")
    
    try:
        print("\n📤 Sending request...")
        start_time = time.time()
        
        response = requests.post(url, json=data, timeout=300)
        processing_time = time.time() - start_time
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"⏱️ Response Time: {processing_time:.1f}s")
        
        # Get response content
        try:
            result = response.json()
            print(f"📄 Response JSON:")
            print(json.dumps(result, indent=2))
        except:
            print(f"📄 Response Text:")
            print(response.text)
        
        if response.status_code == 200:
            print("\n✅ Enhanced processing SUCCESS!")
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
                print(f"📦 Output file size: {file_size:.2f} MB")
            else:
                print("⚠️ Output file not found")
        else:
            print(f"\n❌ Enhanced processing FAILED with status {response.status_code}")
        
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (5 minutes)")
    except Exception as e:
        print(f"❌ Request error: {e}")

def test_system_status():
    """Check system status first"""
    print("🔍 SYSTEM STATUS CHECK")
    print("=" * 30)
    
    try:
        response = requests.get("http://localhost:5001/system/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ API Status: {status.get('status', 'Unknown')}")
            print(f"📊 FFmpeg: {status.get('ffmpeg_available', False)}")
            print(f"🎵 Music DB: {status.get('music_database', {}).get('track_count', 0)} tracks")
            return True
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return False

if __name__ == "__main__":
    # Check system status first
    if test_system_status():
        print("\n" + "=" * 50)
        test_enhanced_processing()
    else:
        print("❌ System not healthy - skipping enhanced processing test")
