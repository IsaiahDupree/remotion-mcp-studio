#!/usr/bin/env python3
"""Test video processing with specific music and volume settings"""

import requests
import json

def test_video_processing():
    """Test the smart video processing endpoint"""
    
    # API endpoint
    url = "http://localhost:5003/process/smart-video"
    
    # Request data
    # Note: -25dB = 10^(-25/20) ≈ 0.003162 as linear volume factor
    data = {
        "video_filename": "v12044gd0000cu2t04nog65p7djql4g0.MP4",
        "music_path": "music_library\\general\\craetion - Summer Sky.aac",
        "config": {
            "music_volume": 0.003162,  # -25dB level
            "text_style": "modern",
            "min_compatibility_score": 0.6
        }
    }
    
    print("🎬 Testing Smart Video Processing")
    print("=" * 50)
    print(f"🎵 Music: craetion - Summer Sky")
    print(f"🔊 Volume: -25dB (0.003162 linear)")
    print(f"📡 Sending request to: {url}")
    print(f"📦 Request data:")
    print(json.dumps(data, indent=2))
    print()
    
    try:
        # Make the request
        response = requests.post(url, json=data, timeout=300)  # 5 minute timeout
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Video Processing Successful!")
            print(f"📹 Input Video: {result.get('video_filename')}")
            print(f"🎵 Music Used: {result.get('music_used')}")
            print(f"💯 Compatibility Score: {result.get('compatibility_score')}")
            print(f"📝 Text Overlay: {result.get('text_overlay')}")
            print(f"⏱️ Processing Time: {result.get('processing_time_seconds')}s")
            print(f"📁 Output File: {result.get('output_filename')}")
            print(f"🔗 Download URL: {result.get('download_url')}")
            print(f"📜 Transcript Preview: {result.get('transcript_preview')}")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error: {response.text}")
    
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (processing may still be running)")
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is Flask app running?")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_video_processing()
