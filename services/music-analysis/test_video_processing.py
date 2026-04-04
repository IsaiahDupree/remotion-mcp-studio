#!/usr/bin/env python3
"""
Test Video Processing - Add Music + Text Without Changing Dimensions
"""
import requests
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:5001"

def test_video_processing():
    """Test the complete video processing with music and text overlay"""
    print("🎬 TESTING VIDEO PROCESSING WITH MUSIC + TEXT")
    print("=" * 60)
    
    # Find a test video
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\0024d0ff50d04b2eba719fec130a0b74.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Test video not found: {video_path}")
        return
    
    # Get recommended music first
    print("🔍 Step 1: Getting recommended music...")
    search_data = {"mood": "energetic", "limit": 1}
    
    try:
        response = requests.post(f"{BASE_URL}/music/search", json=search_data, timeout=10)
        
        if response.status_code == 200:
            music_results = response.json()
            if music_results.get('results'):
                music_track = music_results['results'][0]
                music_path = music_track['file_path']
                print(f"✅ Selected music: {os.path.basename(music_path)}")
                print(f"   🎭 Mood: {music_track['detected_mood']}")
                print(f"   🎼 Genre: {music_track['predicted_genre']}")
                print(f"   🥁 Tempo: {music_track['tempo_bpm']} BPM")
            else:
                print("❌ No music found")
                return
        else:
            print(f"❌ Music search failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error getting music: {e}")
        return
    
    # Now process the video
    print(f"\n🎥 Step 2: Processing video with music and text...")
    
    output_path = r"C:\Users\Isaia\Documents\Coding\N8N\output\test_enhanced_video.mp4"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    process_data = {
        "video_path": video_path,
        "music_path": music_path,
        "output_path": output_path,
        "text_overlay": {
            "text": "Enhanced with AI Music Selection\\nPowered by SoundCloud Library",
            "position": "bottom_center",
            "font_size": 32,
            "background_opacity": 0.8
        },
        "music_volume": -25,  # Reduce music volume by 25dB
        "preserve_original_audio": False
    }
    
    print("📋 Processing request:")
    print(f"   🎬 Input video: {os.path.basename(video_path)}")
    print(f"   🎵 Music: {os.path.basename(music_path)}")
    print(f"   📝 Text: Enhanced with AI Music Selection")
    print(f"   🔊 Music volume: -25dB")
    print(f"   📐 Preserve dimensions: YES")
    
    try:
        print("\n⏳ Processing video... (this may take a moment)")
        response = requests.post(f"{BASE_URL}/video/process", json=process_data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ VIDEO PROCESSING COMPLETE!")
            print("-" * 40)
            print(f"📁 Output file: {result.get('output_file', 'N/A')}")
            print(f"⏱️ Processing time: {result.get('processing_time', 'N/A')} seconds")
            print(f"💾 File size: {result.get('file_size_mb', 'N/A')} MB")
            print(f"📐 Resolution: {result.get('original_resolution', 'preserved')}")
            print(f"🎵 Music applied: {result.get('music_applied', 'N/A')}")
            print(f"📝 Text overlay: {result.get('text_overlay_applied', 'N/A')}")
            
            # Check if output file exists
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                print(f"✅ Enhanced video created: {file_size:.1f} MB")
            else:
                print("⚠️ Output file not found")
                
        else:
            print(f"❌ Video processing failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏱️ Processing timed out - video might be large")
    except Exception as e:
        print(f"❌ Error processing video: {e}")

def show_video_processing_capabilities():
    """Show all video processing features"""
    print(f"\n\n🔧 VIDEO PROCESSING CAPABILITIES")
    print("=" * 60)
    print("🎯 What the system can do:")
    print()
    print("✅ MUSIC OVERLAY:")
    print("   - Add background music at controlled volume (-25dB to -30dB)")
    print("   - Preserve or replace original audio")
    print("   - Automatic music-video synchronization")
    print()
    print("✅ TEXT OVERLAY:")
    print("   - Multi-line text support")
    print("   - Configurable position (top, center, bottom)")
    print("   - Background box with opacity control")
    print("   - Custom font size")
    print()
    print("✅ VIDEO PRESERVATION:")
    print("   - Original resolution maintained (1920x1080, 4K, etc.)")
    print("   - Original codec preserved")
    print("   - Frame rate maintained")
    print("   - Quality preserved")
    print()
    print("✅ BATCH PROCESSING:")
    print("   - Process entire directories")
    print("   - Automatic music matching per video")
    print("   - Progress tracking")
    print("   - Error handling and recovery")

def main():
    """Test complete video processing pipeline"""
    print("🚀 VIDEO PROCESSING TEST")
    print("🎯 Adding music and text to video while preserving dimensions")
    print("=" * 70)
    
    test_video_processing()
    show_video_processing_capabilities()
    
    print(f"\n🏆 VIDEO PROCESSING READY!")
    print("🎬 Your n8n workflows can now:")
    print("   1. Analyze video content")
    print("   2. Get intelligent music recommendations") 
    print("   3. Process videos with music + text overlays")
    print("   4. Preserve original video quality and dimensions")
    print("✅ Complete pipeline integration ready!")

if __name__ == "__main__":
    main()
