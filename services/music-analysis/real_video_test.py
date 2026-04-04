#!/usr/bin/env python3
"""
Real Video File Music Matching Test
"""
import requests
import json
import os

BASE_URL = "http://localhost:5001"

def test_specific_videos():
    """Test music suggestions for actual video files"""
    
    # Real video files to test
    test_videos = [
        {
            "path": r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\0024d0ff50d04b2eba719fec130a0b74.mp4",
            "description": "Dynamic video content",
            "expected_mood": "energetic"
        },
        {
            "path": r"C:\Users\Isaia\Documents\Coding\N8N\WordsOnText\enhanced_videos\IMG_2401_enhanced_complete.mp4", 
            "description": "Enhanced video with text overlay",
            "expected_mood": "upbeat"
        }
    ]
    
    print("🎬 TESTING REAL VIDEO FILES")
    print("=" * 50)
    
    for video in test_videos:
        if os.path.exists(video["path"]):
            print(f"\n📁 Video: {os.path.basename(video['path'])}")
            print(f"🎯 Type: {video['description']}")
            
            # Get file size
            try:
                size_mb = os.path.getsize(video["path"]) / (1024 * 1024)
                print(f"📊 Size: {size_mb:.1f} MB")
            except:
                print("📊 Size: Unknown")
            
            # Search for appropriate music
            search_data = {
                "mood": video["expected_mood"],
                "limit": 2
            }
            
            try:
                response = requests.post(f"{BASE_URL}/music/search", json=search_data, timeout=10)
                
                if response.status_code == 200:
                    results = response.json()
                    tracks = results.get('results', [])
                    
                    print(f"🎵 RECOMMENDED MUSIC ({video['expected_mood']}):")
                    for i, track in enumerate(tracks[:2], 1):
                        filename = os.path.basename(track.get('file_name', 'Unknown'))
                        print(f"   {i}. {filename}")
                        print(f"      🎭 {track.get('detected_mood')} | 🎼 {track.get('predicted_genre')} | 🥁 {track.get('tempo_bpm')} BPM")
                else:
                    print(f"❌ Search failed: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"❌ Video not found: {video['path']}")

if __name__ == "__main__":
    test_specific_videos()
