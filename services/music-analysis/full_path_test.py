#!/usr/bin/env python3
"""
Full Path Test - Process different videos and return complete paths for n8n
"""
import requests
import json
import os
import glob
from pathlib import Path
import time

BASE_URL = "http://localhost:5001"

def find_all_videos():
    """Find all available videos for testing"""
    print("🔍 SCANNING FOR ALL AVAILABLE VIDEOS")
    print("=" * 50)
    
    video_directories = [
        r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos",
        r"C:\Users\Isaia\Documents\Coding\N8N\WordsOnText\enhanced_videos",
        r"C:\Users\Isaia\Documents\Coding\N8N\output"
    ]
    
    all_videos = []
    extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.webm']
    
    for directory in video_directories:
        if os.path.exists(directory):
            print(f"📁 Scanning: {directory}")
            for ext in extensions:
                pattern = os.path.join(directory, ext)
                videos = glob.glob(pattern)
                for video in videos:
                    file_size = os.path.getsize(video) / (1024 * 1024)
                    all_videos.append({
                        'path': video,
                        'name': os.path.basename(video),
                        'directory': directory,
                        'size_mb': round(file_size, 1)
                    })
                    print(f"   ✅ {os.path.basename(video)} ({file_size:.1f} MB)")
        else:
            print(f"❌ Directory not found: {directory}")
    
    print(f"\n📊 TOTAL VIDEOS FOUND: {len(all_videos)}")
    return all_videos

def find_all_music():
    """Find all available music tracks"""
    print(f"\n🎵 SCANNING FOR ALL AVAILABLE MUSIC")
    print("=" * 50)
    
    music_directories = [
        r"C:\Users\Isaia\Documents\Coding\N8N\soundcloud_music",
        r"C:\Users\Isaia\Documents\Coding\N8N\music_library"
    ]
    
    all_music = []
    extensions = ['*.mp3', '*.wav', '*.flac', '*.m4a', '*.ogg']
    
    for directory in music_directories:
        if os.path.exists(directory):
            print(f"📁 Scanning: {directory}")
            track_count = 0
            for ext in extensions:
                pattern = os.path.join(directory, ext)
                tracks = glob.glob(pattern)
                for track in tracks[:5]:  # Show first 5 per directory
                    file_size = os.path.getsize(track) / (1024 * 1024)
                    all_music.append({
                        'path': track,
                        'name': os.path.basename(track),
                        'directory': directory,
                        'size_mb': round(file_size, 1)
                    })
                    if track_count < 3:  # Only print first 3 for brevity
                        print(f"   ✅ {os.path.basename(track)} ({file_size:.1f} MB)")
                    track_count += 1
                    
                if len(tracks) > 5:
                    print(f"   ... and {len(tracks) - 5} more tracks")
                    
        else:
            print(f"❌ Directory not found: {directory}")
    
    print(f"\n📊 TOTAL MUSIC TRACKS AVAILABLE: {len(all_music)}")
    return all_music

def test_with_different_video(videos, music_tracks):
    """Test processing with a different video"""
    print(f"\n🎬 TESTING WITH DIFFERENT VIDEO")
    print("=" * 50)
    
    if not videos:
        print("❌ No videos available for testing")
        return False
    
    # Choose a different video (not the first one we used)
    test_video = None
    for video in videos:
        if "0024d0ff50d04b2eba719fec130a0b74" not in video['name']:
            test_video = video
            break
    
    if not test_video:
        test_video = videos[0]  # Fallback to first video
    
    print(f"🎬 Selected Video: {test_video['name']}")
    print(f"📁 Full Path: {test_video['path']}")
    print(f"💾 Size: {test_video['size_mb']} MB")
    
    # Get recommended music
    print(f"\n🔍 Getting music recommendation...")
    
    try:
        search_data = {"mood": "upbeat", "limit": 1}
        response = requests.post(f"{BASE_URL}/music/search", json=search_data, timeout=10)
        
        if response.status_code == 200:
            music_result = response.json()
            if music_result.get('results'):
                music_track = music_result['results'][0]
                print(f"🎵 Selected Music: {music_track['file_name']}")
                print(f"📁 Full Path: {music_track['file_path']}")
                print(f"🎭 Mood: {music_track['detected_mood']}")
                print(f"🎼 Genre: {music_track['predicted_genre']}")
                
                # Now process the video
                return test_video_processing_with_paths(test_video, music_track)
            else:
                print("❌ No music recommendations found")
                return False
        else:
            print(f"❌ Music search failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting music: {e}")
        return False

def test_video_processing_with_paths(video_info, music_info):
    """Test video processing and return all paths"""
    print(f"\n🎥 PROCESSING VIDEO WITH FULL PATHS")
    print("=" * 50)
    
    output_path = r"C:\Users\Isaia\Documents\Coding\N8N\output\test_different_video.mp4"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Process data with full paths
    process_data = {
        "video_path": video_info['path'],
        "music_path": music_info['file_path'],
        "output_path": output_path,
        "text_overlay": {
            "text": f"Video: {video_info['name']}\\nMusic: {os.path.basename(music_info['file_name'])}",
            "position": "top_center",
            "font_size": 36
        },
        "music_volume": -20
    }
    
    print("📋 FULL PROCESSING REQUEST:")
    print(f"   🎬 Input Video: {process_data['video_path']}")
    print(f"   🎵 Input Music: {process_data['music_path']}")
    print(f"   📁 Output Path: {process_data['output_path']}")
    print(f"   📝 Text Overlay: Yes")
    
    try:
        print(f"\n⏳ Processing video (timeout: 90s)...")
        start_time = time.time()
        
        response = requests.post(f"{BASE_URL}/video/process", 
                               json=process_data, 
                               timeout=90)
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! Processing time: {processing_time:.1f}s")
            print("-" * 40)
            
            # Show all paths n8n will receive
            print("📋 COMPLETE API RESPONSE FOR N8N:")
            print(json.dumps(result, indent=2))
            
            print(f"\n🎯 KEY PATHS FOR N8N:")
            print(f"   📁 Input Video: {process_data['video_path']}")
            print(f"   🎵 Input Music: {process_data['music_path']}")
            print(f"   📁 Output Video: {result.get('output_path', 'N/A')}")
            print(f"   💾 Output Size: {result.get('file_size_mb', 'N/A')} MB")
            
            return True
            
        else:
            print(f"❌ FAILED: {response.status_code}")
            try:
                error_info = response.json()
                print(f"Error details: {json.dumps(error_info, indent=2)}")
            except:
                print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️ TIMEOUT: Processing took too long (>90s)")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def show_directory_structure():
    """Show complete directory structure for n8n"""
    print(f"\n📂 COMPLETE DIRECTORY STRUCTURE FOR N8N")
    print("=" * 60)
    
    directories = {
        "Videos": r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos",
        "Enhanced Videos": r"C:\Users\Isaia\Documents\Coding\N8N\WordsOnText\enhanced_videos",
        "SoundCloud Music": r"C:\Users\Isaia\Documents\Coding\N8N\soundcloud_music",
        "Music Library": r"C:\Users\Isaia\Documents\Coding\N8N\music_library",
        "Output": r"C:\Users\Isaia\Documents\Coding\N8N\output",
        "Cache": r"C:\Users\Isaia\Documents\Coding\N8N\cache"
    }
    
    for name, path in directories.items():
        print(f"📁 {name}:")
        print(f"   Path: {path}")
        if os.path.exists(path):
            try:
                files = os.listdir(path)
                print(f"   Status: ✅ ({len(files)} items)")
            except:
                print(f"   Status: ✅ (access restricted)")
        else:
            print(f"   Status: ❌ (not found)")
        print()

def main():
    """Run comprehensive path testing"""
    print("🚀 FULL PATH VIDEO PROCESSING TEST")
    print("🎯 Testing with different videos + returning complete paths for n8n")
    print("=" * 70)
    
    # Find all available media
    videos = find_all_videos()
    music = find_all_music()
    
    # Show directory structure
    show_directory_structure()
    
    # Test with different video
    if videos:
        success = test_with_different_video(videos, music)
        
        if success:
            print(f"\n🎉 FULL PATH TESTING SUCCESSFUL!")
            print("✅ All file paths properly returned")
            print("✅ Video processing with different video works")
            print("✅ Ready for n8n integration with complete paths")
        else:
            print(f"\n⚠️ TESTING ISSUES DETECTED")
            print("🔧 May need debugging before n8n integration")
    else:
        print(f"\n❌ NO VIDEOS FOUND FOR TESTING")

if __name__ == "__main__":
    main()
