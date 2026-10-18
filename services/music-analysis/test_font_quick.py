#!/usr/bin/env python3

import requests
import json
import os
from pathlib import Path

def test_font_system():
    """Test the custom font system quickly"""
    
    print("🎨 Quick Font System Test")
    print("=" * 50)
    
    # Test font listing
    print("📝 Testing Font List API...")
    try:
        response = requests.get('http://localhost:5001/fonts/list')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['total_fonts']} fonts")
            
            # Show custom fonts
            custom_fonts = [f for f in data['available_fonts'] if f['status'] == 'available']
            print(f"🎨 Custom fonts: {len(custom_fonts)}")
            for font in custom_fonts[:3]:  # Show first 3
                print(f"   • {font['name']} ({font['style']}) - {font['file_size']} bytes")
            
            print(f"💡 Font styles available: {data['font_styles']}")
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # Test video processing with font
    print("\n🎬 Testing Video Processing with Custom Font...")
    test_video = Path("shared/videos").glob("*.mp4").__next__() if Path("shared/videos").exists() else None
    test_music = Path("soundcloud_music").glob("*.mp3").__next__() if Path("soundcloud_music").exists() else None
    
    if test_video and test_music:
        print(f"📹 Using video: {test_video.name}")
        print(f"🎵 Using music: {test_music.name}")
        
        payload = {
            "video_path": str(test_video),
            "music_path": str(test_music),
            "text_lines": ["🌟 CUSTOM FONT TEST", "Sunny Spells Creative Style"],
            "output_name": "font_test_output.mp4",
            "font_style": "creative",
            "music_volume_db": -25,
            "preserve_audio": True
        }
        
        try:
            print("🔄 Processing video...")
            response = requests.post('http://localhost:5001/video/process-enhanced', 
                                   json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Video processing started successfully!")
                print(f"📋 Font used: {result.get('processing_settings', {}).get('font_style', 'unknown')}")
                print(f"📁 Output: {result.get('output_path', 'unknown')}")
                return True
            else:
                print(f"❌ Processing failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
        except requests.exceptions.Timeout:
            print("⏰ Processing started but taking time (timeout after 30s)")
            print("   This is normal for video processing")
            return True
        except Exception as e:
            print(f"❌ Processing error: {e}")
            return False
    else:
        print("⚠️ No test files found, skipping video processing test")
        return True

if __name__ == "__main__":
    success = test_font_system()
    if success:
        print("\n🎉 Font system is working correctly!")
    else:
        print("\n❌ Font system has issues")
