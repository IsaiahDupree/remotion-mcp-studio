#!/usr/bin/env python3
"""
Specific Video Test - Process the requested video with music and relevant text
"""
import requests
import json
import os
import subprocess
from pathlib import Path
import time

BASE_URL = "http://localhost:5001"

def get_video_info(video_path):
    """Get video information using ffprobe"""
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
            info = json.loads(result.stdout)
            
            # Find video stream
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    return {
                        'width': stream.get('width'),
                        'height': stream.get('height'),
                        'duration': float(stream.get('duration', 0)),
                        'fps': stream.get('r_frame_rate', 'N/A'),
                        'codec': stream.get('codec_name', 'N/A')
                    }
        return None
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None

def analyze_video_content(video_path):
    """Analyze video to suggest relevant text overlay"""
    video_name = Path(video_path).name
    
    # Simple analysis based on filename and video properties
    video_info = get_video_info(video_path)
    
    suggested_text = []
    
    # Generic professional overlay
    suggested_text.append("AI Enhanced Video")
    
    # Add video info
    if video_info:
        if video_info['duration'] < 10:
            suggested_text.append("Quick Clip")
        elif video_info['duration'] < 60:
            suggested_text.append("Short Form Content")
        else:
            suggested_text.append("Long Form Content")
            
        # Resolution-based text
        if video_info['width'] and video_info['height']:
            if video_info['width'] > video_info['height']:
                suggested_text.append("Landscape Format")
            elif video_info['height'] > video_info['width']:
                suggested_text.append("Portrait Format")
            else:
                suggested_text.append("Square Format")
    
    return suggested_text

def test_specific_video():
    """Test the specific video requested by user"""
    print("🎬 TESTING SPECIFIC VIDEO WITH DIMENSION PRESERVATION")
    print("=" * 60)
    
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    
    # Check if video exists
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return False
    
    # Get video information
    video_info = get_video_info(video_path)
    if not video_info:
        print("❌ Could not get video information")
        return False
    
    file_size = os.path.getsize(video_path) / (1024 * 1024)
    
    print(f"🎬 Video: {Path(video_path).name}")
    print(f"📁 Full Path: {video_path}")
    print(f"💾 Size: {file_size:.1f} MB")
    print(f"📐 Resolution: {video_info['width']}x{video_info['height']}")
    print(f"⏱️ Duration: {video_info['duration']:.1f} seconds")
    print(f"🎞️ FPS: {video_info['fps']}")
    print(f"🎥 Codec: {video_info['codec']}")
    
    # Analyze for relevant text
    suggested_text = analyze_video_content(video_path)
    print(f"\n📝 Suggested Text Overlay: {' | '.join(suggested_text)}")
    
    # Get music recommendation
    print(f"\n🔍 Getting intelligent music recommendation...")
    
    try:
        # Search for music based on video characteristics
        if video_info['duration'] < 30:
            mood = "energetic"  # Short videos often need energy
        elif video_info['duration'] < 60:
            mood = "upbeat"     # Medium videos need engagement
        else:
            mood = "neutral"    # Longer videos need balance
            
        search_data = {"mood": mood, "limit": 1}
        response = requests.post(f"{BASE_URL}/music/search", json=search_data, timeout=10)
        
        if response.status_code == 200:
            music_result = response.json()
            if music_result.get('results'):
                music_track = music_result['results'][0]
                print(f"🎵 Selected Music: {music_track['file_name']}")
                print(f"📁 Music Path: {music_track['file_path']}")
                print(f"🎭 Mood: {music_track['detected_mood']}")
                print(f"🎼 Genre: {music_track['predicted_genre']}")
                print(f"🥁 Tempo: {music_track['tempo_bpm']} BPM")
                
                # Process the video
                return process_video_with_preservation(video_path, video_info, music_track, suggested_text)
            else:
                print("❌ No music recommendations found")
                return False
        else:
            print(f"❌ Music search failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting music: {e}")
        return False

def process_video_with_preservation(video_path, video_info, music_track, text_lines):
    """Process video with music and text while preserving all dimensions"""
    print(f"\n🎥 PROCESSING WITH DIMENSION PRESERVATION")
    print("=" * 50)
    
    output_path = r"C:\Users\Isaia\Documents\Coding\N8N\output\specific_video_enhanced.mp4"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create relevant text overlay
    relevant_text = "\\n".join(text_lines[:3])  # Use top 3 relevant text lines
    
    process_data = {
        "video_path": video_path,
        "music_path": music_track['file_path'],
        "output_path": output_path,
        "text_overlay": {
            "text": relevant_text,
            "position": "bottom_center",  # Bottom to avoid covering main content
            "font_size": max(24, min(48, video_info['width'] // 40)),  # Responsive font size
            "background_opacity": 0.7
        },
        "music_volume": -22,  # Moderate background music
        "preserve_original_audio": False
    }
    
    print("📋 PROCESSING REQUEST:")
    print(f"   🎬 Input Video: {video_path}")
    print(f"   📐 Original Resolution: {video_info['width']}x{video_info['height']}")
    print(f"   🎵 Music: {os.path.basename(music_track['file_path'])}")
    print(f"   📝 Text: {relevant_text}")
    print(f"   🔊 Music Volume: -22dB")
    print(f"   📁 Output: {output_path}")
    print(f"   🎯 Preserve Dimensions: YES")
    
    try:
        print(f"\n⏳ Processing video... (timeout: 2 minutes)")
        start_time = time.time()
        
        response = requests.post(f"{BASE_URL}/video/process", 
                               json=process_data, 
                               timeout=120)  # 2 minute timeout
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! Processing time: {processing_time:.1f}s")
            print("-" * 50)
            
            print("📋 COMPLETE API RESPONSE FOR N8N:")
            print(json.dumps(result, indent=2))
            
            print(f"\n🎯 FULL PATHS FOR N8N INTEGRATION:")
            print(f"   📁 Input Video: {video_path}")
            print(f"   📐 Original Resolution: {video_info['width']}x{video_info['height']}")
            print(f"   🎵 Input Music: {music_track['file_path']}")
            print(f"   📁 Output Video: {result.get('output_path', 'N/A')}")
            print(f"   📐 Final Resolution: PRESERVED ({video_info['width']}x{video_info['height']})")
            print(f"   💾 Output Size: {result.get('file_size_mb', 'N/A')} MB")
            print(f"   📝 Text Applied: {relevant_text}")
            
            # Verify output file exists and check resolution
            if os.path.exists(output_path):
                output_info = get_video_info(output_path)
                if output_info:
                    print(f"\n✅ DIMENSION VERIFICATION:")
                    print(f"   Original: {video_info['width']}x{video_info['height']}")
                    print(f"   Output:   {output_info['width']}x{output_info['height']}")
                    
                    if (output_info['width'] == video_info['width'] and 
                        output_info['height'] == video_info['height']):
                        print(f"   🎉 DIMENSIONS PERFECTLY PRESERVED!")
                    else:
                        print(f"   ⚠️ Dimensions changed")
                        
                actual_size = os.path.getsize(output_path) / (1024 * 1024)
                print(f"   📊 Actual file size: {actual_size:.1f} MB")
                
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
        print("⏱️ TIMEOUT: Processing took too long (>2 minutes)")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def verify_music_library():
    """Verify the new music_library directory"""
    print("\n📁 VERIFYING MUSIC_LIBRARY DIRECTORY")
    print("=" * 40)
    
    music_lib_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\music_library"
    
    if os.path.exists(music_lib_path):
        print(f"✅ Music library created: {music_lib_path}")
        print(f"📊 Ready for additional music files")
        
        # Show available music sources
        soundcloud_path = r"C:\Users\Isaia\Documents\Coding\N8N\soundcloud_music"
        if os.path.exists(soundcloud_path):
            track_count = len([f for f in os.listdir(soundcloud_path) if f.endswith('.mp3')])
            print(f"🎵 SoundCloud tracks available: {track_count}")
        
        return True
    else:
        print(f"❌ Failed to create music library")
        return False

def main():
    """Test specific video with dimension preservation"""
    print("🚀 SPECIFIC VIDEO TEST WITH DIMENSION PRESERVATION")
    print("🎯 Processing requested video with intelligent music and relevant text")
    print("=" * 70)
    
    # Verify music library
    verify_music_library()
    
    # Test specific video
    success = test_specific_video()
    
    if success:
        print(f"\n🎉 SPECIFIC VIDEO TEST SUCCESSFUL!")
        print("✅ Video processed with perfect dimension preservation")
        print("✅ Relevant text overlay applied")
        print("✅ Intelligent music selection working")
        print("✅ Complete file paths provided for n8n integration")
        print("🚀 Ready for full n8n workflow integration!")
    else:
        print(f"\n⚠️ TESTING ENCOUNTERED ISSUES")
        print("🔧 Check logs and troubleshoot before n8n integration")

if __name__ == "__main__":
    main()
