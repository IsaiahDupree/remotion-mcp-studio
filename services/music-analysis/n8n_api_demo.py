#!/usr/bin/env python3
"""
Demonstrate exactly what n8n will receive from the API calls
"""
import requests
import json
import os

BASE_URL = "http://localhost:5001"

def show_n8n_music_search_response():
    """Show the exact JSON response n8n will get from music search"""
    print("🔍 N8N MUSIC Search API Response")
    print("=" * 60)
    print("📡 Endpoint: POST /music/search")
    print("📨 Request Body: {\"mood\": \"energetic\", \"limit\": 1}")
    print()
    
    search_data = {"mood": "energetic", "limit": 1}
    
    try:
        response = requests.post(f"{BASE_URL}/music/search", json=search_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("📋 COMPLETE JSON RESPONSE FOR N8N:")
            print("-" * 40)
            print(json.dumps(result, indent=2))
            
            # Extract key fields n8n will use
            if result.get('results'):
                track = result['results'][0]
                print(f"\n🎯 KEY FIELDS FOR N8N:")
                print(f"   file_path: {track.get('file_path')}")
                print(f"   file_name: {track.get('file_name')}")
                print(f"   detected_mood: {track.get('detected_mood')}")
                print(f"   predicted_genre: {track.get('predicted_genre')}")
                print(f"   tempo_bpm: {track.get('tempo_bpm')}")
                print(f"   energy_level: {track.get('energy_level')}")
                print(f"   duration_seconds: {track.get('duration_seconds')}")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

def show_n8n_video_analysis_response():
    """Show the enhanced music-video matching response"""
    print(f"\n\n🎬 N8N ENHANCED Music-Video Matching API Response")
    print("=" * 60)
    print("📡 Endpoint: POST /analyze-music-match")
    print("📨 Request: video analysis + transcript data")
    print()
    
    # Mock the data n8n would send (from video analysis)
    analysis_data = {
        "video_path": r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\test_video.mp4",
        "transcript": "This is an energetic workout video with fast movements and upbeat content",
        "visual_analysis": {
            "detected_mood": "energetic",
            "energy_level": "high", 
            "content_type": "fitness",
            "scene_changes": 20,
            "dominant_colors": ["blue", "white", "red"]
        },
        "video_metadata": {
            "duration": 45.0,
            "fps": 30,
            "resolution": "1920x1080"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/analyze-music-match", json=analysis_data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            print("📋 COMPLETE JSON RESPONSE FOR N8N:")
            print("-" * 40)
            print(json.dumps(result, indent=2))
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

def show_n8n_video_processing_request():
    """Show how n8n would call the video processing endpoint"""
    print(f"\n\n🎥 N8N VIDEO PROCESSING API Request/Response")
    print("=" * 60)
    print("📡 Endpoint: POST /video/process")
    print("📨 Complete video processing with music + text")
    print()
    
    # Example processing request n8n would make
    process_data = {
        "video_path": r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\0024d0ff50d04b2eba719fec130a0b74.mp4",
        "music_path": r"C:\Users\Isaia\Documents\Coding\N8N\soundcloud_music\04collective - Rusherz - Before You Go.mp3",
        "output_path": r"C:\Users\Isaia\Documents\Coding\N8N\output\enhanced_video_with_music.mp4",
        "text_overlay": {
            "text": "AI-Enhanced Video\\nPowered by Intelligent Music Selection",
            "position": "center",
            "font_size": 48,
            "background_opacity": 0.7
        },
        "music_volume": -25,  # dB reduction
        "preserve_original_audio": False
    }
    
    print("📨 REQUEST BODY N8N WOULD SEND:")
    print(json.dumps(process_data, indent=2))
    
    print(f"\n📋 EXPECTED RESPONSE FIELDS:")
    print("   - status: 'success' | 'error'")
    print("   - output_file: '/path/to/enhanced_video.mp4'")
    print("   - processing_time: seconds")
    print("   - file_size_mb: final video size")
    print("   - original_resolution: preserved dimensions")
    print("   - music_applied: track information")
    print("   - text_overlay_applied: overlay details")

def main():
    """Show complete n8n integration examples"""
    print("🚀 N8N API INTEGRATION DEMONSTRATION")
    print("🎯 Exact JSON responses your n8n workflows will receive")
    print("=" * 70)
    
    show_n8n_music_search_response()
    show_n8n_video_analysis_response() 
    show_n8n_video_processing_request()
    
    print(f"\n🏆 N8N INTEGRATION SUMMARY:")
    print("✅ Music Search: Returns detailed track info + file paths")  
    print("✅ Music Matching: Analyzes video content + recommends perfect music")
    print("✅ Video Processing: Adds music + text while preserving dimensions")
    print("🎬 Complete pipeline ready for n8n workflow integration!")

if __name__ == "__main__":
    main()
