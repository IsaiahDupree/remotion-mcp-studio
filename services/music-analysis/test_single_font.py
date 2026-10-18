#!/usr/bin/env python3
"""
Test single font video processing
"""

import requests
import json
from pathlib import Path

def test_single_font_video():
    """Test video processing with a single custom font"""
    
    api_url = "http://localhost:5001"
    
    # Test video and music files
    test_video = "C:/Users/Isaia/Documents/Coding/N8N/shared/videos/1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    test_music = "C:/Users/Isaia/Documents/Coding/N8N/soundcloud_music/04collective - Rusherz - Before You Go.mp3"
    
    print("🎨 Testing Single Custom Font Video Processing")
    print("=" * 55)
    
    # Check if files exist
    if not Path(test_video).exists():
        print(f"❌ Test video not found: {test_video}")
        return
    
    if not Path(test_music).exists():
        print(f"❌ Test music not found: {test_music}")
        return
    
    print("✅ Test files found")
    
    # Test with Sunny Spells font (creative style)
    payload = {
        "video_path": test_video,
        "music_path": test_music,
        "text_lines": ["🌟 SUNNY SPELLS FONT", "Creative & Fun Style"],
        "output_name": "sunny_spells_test.mp4",
        "music_volume_db": -25.0,
        "preserve_audio": True,
        "smart_positioning": True,
        "font_style": "creative"
    }
    
    print(f"🎬 Processing video with creative font...")
    print(f"   Text: {payload['text_lines']}")
    print(f"   Font Style: {payload['font_style']}")
    
    try:
        response = requests.post(f"{api_url}/video/process-enhanced", json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Video processing SUCCESS!")
            print(f"📁 Output: {result.get('output_path', 'Unknown')}")
            print(f"📊 File Size: {result.get('file_size_mb', 0)} MB")
            print(f"⏱️ Processing Time: {result.get('processing_time_seconds', 0)} seconds")
            
            # Font information
            settings = result.get('processing_settings', {})
            print(f"🎨 Font Style Used: {settings.get('font_style', 'Unknown')}")
            
            # Check if output file exists
            output_path = result.get('output_path')
            if output_path and Path(output_path).exists():
                file_size = Path(output_path).stat().st_size / (1024 * 1024)
                print(f"✅ Output file verified: {file_size:.2f} MB")
                return True
            else:
                print("❌ Output file not found")
                return False
                
        else:
            print(f"❌ Processing failed (HTTP {response.status_code})")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Processing error: {e}")
        return False

if __name__ == "__main__":
    success = test_single_font_video()
    if success:
        print("\n🎉 Font integration test PASSED!")
    else:
        print("\n❌ Font integration test FAILED!")
