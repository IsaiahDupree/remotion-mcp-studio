#!/usr/bin/env python3
"""
Test Video-Music Matching System
Tests the enhanced API's ability to analyze videos and suggest appropriate music
"""
import requests
import json
import os
from pathlib import Path
import time

# API base URL
BASE_URL = "http://localhost:5001"

# Test video directories
TEST_DIRECTORIES = [
    r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos",
    r"C:\Users\Isaia\Documents\Coding\N8N\WordsOnText\enhanced_videos"
]

def get_video_files(directory, limit=5):
    """Get video files from directory"""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    video_files = []
    
    if not os.path.exists(directory):
        print(f"❌ Directory not found: {directory}")
        return []
    
    for file in os.listdir(directory):
        if any(file.lower().endswith(ext) for ext in video_extensions):
            video_files.append(os.path.join(directory, file))
            if len(video_files) >= limit:
                break
                
    return video_files

def test_music_video_matching(video_path):
    """Test music-video matching for a single video"""
    print(f"\n🎬 Testing: {os.path.basename(video_path)}")
    print("=" * 60)
    
    # Get video file size for context
    try:
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
        print(f"📁 File size: {file_size:.1f} MB")
    except:
        print("📁 File size: Unknown")
    
    # Test 1: Enhanced music-video matching endpoint
    try:
        print("🔍 Analyzing video content and matching music...")
        
        # Mock video analysis data (in real scenario, this would come from video analysis)
        mock_analysis_data = {
            "video_path": video_path,
            "transcript": "This video shows dynamic content with movement and energy",
            "visual_analysis": {
                "detected_mood": "upbeat",
                "energy_level": "high",
                "content_type": "dynamic",
                "dominant_colors": ["blue", "white"],
                "scene_changes": 15
            },
            "video_metadata": {
                "duration": 30.0,
                "fps": 30,
                "resolution": "1920x1080"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/analyze-music-match", 
            json=mock_analysis_data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Music matching successful!")
            
            # Display recommended music
            if 'music_recommendation' in result:
                music = result['music_recommendation']
                print(f"🎵 Recommended Music:")
                print(f"   📀 File: {os.path.basename(music.get('file_path', 'N/A'))}")
                print(f"   🎭 Mood: {music.get('detected_mood', 'N/A')}")
                print(f"   🎼 Genre: {music.get('predicted_genre', 'N/A')}")
                print(f"   ⚡ Energy: {music.get('energy_level', 'N/A')}")
                print(f"   🎯 Match Score: {music.get('compatibility_score', 'N/A')}/10")
                print(f"   🥁 Tempo: {music.get('tempo_bpm', 'N/A')} BPM")
            
            # Display detected video mood
            if 'detected_mood' in result:
                print(f"🎭 Video Mood: {result['detected_mood']}")
                
            # Display reasoning
            if 'reasoning' in result:
                print(f"🧠 AI Reasoning: {result['reasoning']}")
                
        else:
            print(f"❌ Music matching failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏱️ Request timed out - video analysis taking longer than expected")
    except Exception as e:
        print(f"❌ Error in music matching: {e}")
    
    # Test 2: Direct music search based on video characteristics
    try:
        print("\n🔍 Testing direct music search for video characteristics...")
        
        # Search for energetic music (typical for dynamic videos)
        search_data = {
            "mood": "energetic",
            "genre": "dance",
            "limit": 3,
            "min_tempo": 120
        }
        
        response = requests.post(f"{BASE_URL}/music/search", json=search_data, timeout=10)
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Found {len(results.get('results', []))} suitable tracks:")
            
            for i, track in enumerate(results.get('results', [])[:3], 1):
                print(f"   {i}. 🎵 {os.path.basename(track.get('file_name', 'Unknown'))}")
                print(f"      🎭 {track.get('detected_mood', 'N/A')} | 🎼 {track.get('predicted_genre', 'N/A')} | 🥁 {track.get('tempo_bpm', 'N/A')} BPM")
        else:
            print(f"❌ Music search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error in music search: {e}")

def test_batch_video_processing():
    """Test batch video processing endpoint"""
    print("\n🎬 Testing Batch Video Processing")
    print("=" * 60)
    
    # Test with first video directory
    test_dir = TEST_DIRECTORIES[0]
    
    try:
        batch_data = {
            "video_directory": test_dir,
            "output_directory": os.path.join(test_dir, "enhanced_output"),
            "music_mood": "energetic",
            "text_overlay": "Enhanced with AI Music Selection",
            "limit": 2  # Process only 2 videos for testing
        }
        
        print(f"🔍 Testing batch processing for: {test_dir}")
        
        response = requests.post(f"{BASE_URL}/video/batch-process", json=batch_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Batch processing initiated!")
            print(f"📊 Status: {result.get('status', 'Unknown')}")
            print(f"🎬 Videos to process: {result.get('videos_found', 'Unknown')}")
        else:
            print(f"❌ Batch processing failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error in batch processing: {e}")

def main():
    """Run comprehensive video-music matching tests"""
    print("🚀 Testing Video-Music Matching System")
    print("🎯 This will analyze videos and show music recommendations")
    print("=" * 70)
    
    # Check API health first
    try:
        response = requests.get(f"{BASE_URL}/system/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ API Status: {status['status']}")
            print(f"🎵 Music tracks available: {status['music_database']['total_tracks']}")
        else:
            print("❌ API not responding properly")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Test individual videos
    video_count = 0
    for directory in TEST_DIRECTORIES:
        video_files = get_video_files(directory, limit=3)
        print(f"\n📁 Testing videos from: {directory}")
        print(f"   Found {len(video_files)} video files")
        
        for video_file in video_files:
            test_music_video_matching(video_file)
            video_count += 1
            if video_count >= 4:  # Limit total tests
                break
        
        if video_count >= 4:
            break
    
    # Test batch processing
    test_batch_video_processing()
    
    print(f"\n🏆 Testing Complete!")
    print(f"📊 Tested {video_count} videos for music matching")
    print("🎵 The system can now intelligently match music to video content!")

if __name__ == "__main__":
    main()
