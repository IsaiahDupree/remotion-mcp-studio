#!/usr/bin/env python3

import requests
import json
import traceback
from pathlib import Path

def quick_500_debug():
    """Quick debug script to isolate 500 error causes"""
    
    print("🚨 QUICK 500 ERROR DEBUGGING")
    print("=" * 40)
    
    base_url = "http://localhost:5001"
    test_video = "/home/node/shared/videos/1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    
    # Test 1: Simple font test (most likely to 500)
    print("\n1️⃣ Testing Font Selection API...")
    try:
        payload = {
            "text": "Simple Test Text",
            "video_path": test_video
        }
        response = requests.post(f"{base_url}/fonts/test", json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Font Test: {result.get('selected_font', {}).get('name', 'unknown')}")
        elif response.status_code == 500:
            print(f"❌ Font Test 500 ERROR:")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}")
        else:
            print(f"⚠️ Font Test HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Font Test Exception: {str(e)}")
    
    # Test 2: Enhanced video processing (second most likely to 500)
    print("\n2️⃣ Testing Enhanced Video Processing...")
    try:
        payload = {
            "video_path": test_video,
            "music_path": "/home/node/soundcloud_music/04collective - Rusherz - Before You Go.mp3",
            "text_lines": ["Debug Test", "500 Error Check"],
            "output_name": "debug_500_test.mp4",
            "font_style": "clean",
            "music_volume_db": -25,
            "preserve_audio": True
        }
        
        response = requests.post(f"{base_url}/video/process-enhanced", json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Video Processing: {result.get('success', False)}")
        elif response.status_code == 500:
            print(f"❌ Video Processing 500 ERROR:")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
                if 'traceback' in error_data:
                    print(f"   Traceback: {error_data['traceback'][:300]}...")
            except:
                print(f"   Raw response: {response.text[:300]}")
        else:
            print(f"⚠️ Video Processing HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Video Processing Exception: {str(e)}")
    
    # Test 3: Music analysis (can cause 500 with invalid input)
    print("\n3️⃣ Testing Music Analysis...")
    try:
        payload = {
            "video_path": test_video,
            "transcript": "test content",
            "visual_analysis": "general video"
        }
        
        response = requests.post(f"{base_url}/analyze-music-match", json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Music Analysis: {result.get('detected_mood', 'unknown')}")
        elif response.status_code == 500:
            print(f"❌ Music Analysis 500 ERROR:")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}")
        else:
            print(f"⚠️ Music Analysis HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Music Analysis Exception: {str(e)}")
    
    # Test 4: Check file access (common cause of 500s)
    print("\n4️⃣ File Access Checks...")
    
    # Check video file
    video_path_local = "c:/Users/Isaia/Documents/Coding/N8N/shared/videos/1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    if Path(video_path_local).exists():
        print(f"✅ Test video exists: {Path(video_path_local).stat().st_size / 1024 / 1024:.1f} MB")
    else:
        print(f"❌ Test video missing: {video_path_local}")
    
    # Check music file
    music_path_local = "c:/Users/Isaia/Documents/Coding/N8N/soundcloud_music/04collective - Rusherz - Before You Go.mp3"
    if Path(music_path_local).exists():
        print(f"✅ Test music exists: {Path(music_path_local).stat().st_size / 1024 / 1024:.1f} MB")
    else:
        print(f"❌ Test music missing: {music_path_local}")
    
    # Check fonts directory
    fonts_dir = "c:/Users/Isaia/Documents/Coding/N8N/shared/fonts"
    if Path(fonts_dir).exists():
        font_files = list(Path(fonts_dir).rglob("*.ttf")) + list(Path(fonts_dir).rglob("*.otf"))
        print(f"✅ Fonts directory: {len(font_files)} font files")
    else:
        print(f"❌ Fonts directory missing: {fonts_dir}")
    
    print(f"\n🔧 COMMON 500 ERROR FIXES:")
    print(f"   1. Restart Flask API: docker-compose restart video-generator")
    print(f"   2. Check Docker volumes are mounted correctly")
    print(f"   3. Verify FFmpeg is accessible in container")
    print(f"   4. Check OpenAI API key is embedded in enhanced_flask_api.py")
    print(f"   5. Ensure sufficient disk space in output directories")
    print(f"   6. Verify file permissions for shared directories")

if __name__ == "__main__":
    quick_500_debug()
