#!/usr/bin/env python3
"""
Quick Video Processing Test - Direct FFmpeg check
"""
import subprocess
import os
from pathlib import Path

def test_ffmpeg_directly():
    """Test FFmpeg directly without API"""
    print("🔧 TESTING FFMPEG DIRECTLY")
    print("=" * 40)
    
    # Check if FFmpeg is available
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        print("✅ FFmpeg is available")
        print(f"Version: {result.stdout.split('version')[1].split(' ')[1] if 'version' in result.stdout else 'Unknown'}")
    except Exception as e:
        print(f"❌ FFmpeg error: {e}")
        return False
    
    return True

def test_simple_video_operation():
    """Test a simple video operation"""
    print(f"\n🎬 TESTING SIMPLE VIDEO OPERATION")
    print("=" * 40)
    
    # Check if test video exists
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\0024d0ff50d04b2eba719fec130a0b74.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Test video not found: {video_path}")
        return False
    
    print(f"✅ Test video found: {Path(video_path).name}")
    
    # Get video info
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            import json
            info = json.loads(result.stdout)
            
            # Find video stream
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    print(f"📊 Resolution: {stream.get('width')}x{stream.get('height')}")
                    print(f"📊 Duration: {float(stream.get('duration', 0)):.1f} seconds")
                    print(f"📊 FPS: {stream.get('r_frame_rate', 'N/A')}")
                    break
            
            return True
        else:
            print(f"❌ FFprobe failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting video info: {e}")
        return False

def test_music_file():
    """Test if music file exists"""
    print(f"\n🎵 TESTING MUSIC FILE")
    print("=" * 40)
    
    music_path = r"C:\Users\Isaia\Documents\Coding\N8N\soundcloud_music\04collective - Rusherz - Before You Go.mp3"
    
    if os.path.exists(music_path):
        file_size = os.path.getsize(music_path) / (1024 * 1024)
        print(f"✅ Music file found: {Path(music_path).name}")
        print(f"📊 Size: {file_size:.1f} MB")
        return True
    else:
        print(f"❌ Music file not found: {music_path}")
        return False

def main():
    """Run quick tests"""
    print("🚀 QUICK VIDEO PROCESSING TEST")
    print("🎯 Testing components individually")
    print("=" * 50)
    
    ffmpeg_ok = test_ffmpeg_directly()
    video_ok = test_simple_video_operation()
    music_ok = test_music_file()
    
    print(f"\n📋 TEST RESULTS:")
    print(f"   FFmpeg: {'✅' if ffmpeg_ok else '❌'}")
    print(f"   Video File: {'✅' if video_ok else '❌'}")
    print(f"   Music File: {'✅' if music_ok else '❌'}")
    
    if ffmpeg_ok and video_ok and music_ok:
        print(f"\n🎉 ALL COMPONENTS READY!")
        print("✅ Video processing should work")
    else:
        print(f"\n⚠️ Some components need attention")

if __name__ == "__main__":
    main()
