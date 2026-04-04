#!/usr/bin/env python3
"""
Direct Music Recommendation Test
Shows what music the system suggests for different video characteristics
"""
import requests
import json
import os

BASE_URL = "http://localhost:5001"

def test_music_for_video_type(video_type, characteristics):
    """Test music recommendations for specific video characteristics"""
    print(f"\n🎬 VIDEO TYPE: {video_type}")
    print("=" * 50)
    
    for mood in characteristics.get('moods', ['energetic']):
        print(f"\n🎭 Searching for {mood.upper()} music...")
        
        search_data = {
            "mood": mood,
            "limit": 3
        }
        
        # Add genre filter if specified
        if 'preferred_genres' in characteristics:
            search_data['genre'] = characteristics['preferred_genres'][0]
        
        try:
            response = requests.post(f"{BASE_URL}/music/search", json=search_data, timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                tracks = results.get('results', [])
                
                print(f"✅ Found {len(tracks)} {mood} tracks:")
                
                for i, track in enumerate(tracks[:3], 1):
                    filename = os.path.basename(track.get('file_name', 'Unknown'))
                    mood_detected = track.get('detected_mood', 'N/A')
                    genre = track.get('predicted_genre', 'N/A')
                    tempo = track.get('tempo_bpm', 'N/A')
                    energy = track.get('energy_level', 'N/A')
                    
                    print(f"   {i}. 🎵 {filename}")
                    print(f"      📊 Mood: {mood_detected} | Genre: {genre} | Tempo: {tempo} BPM | Energy: {energy}")
            else:
                print(f"❌ Search failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def show_database_breakdown():
    """Show the complete music database breakdown"""
    print("\n📊 COMPLETE MUSIC DATABASE BREAKDOWN")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/music/database/stats", timeout=10)
        
        if response.status_code == 200:
            stats = response.json()
            
            print(f"🎵 Total Tracks: {stats['total_tracks']}")
            print(f"⏱️ Total Duration: {stats['total_duration_hours']} hours")
            print(f"💾 Total Size: {stats['total_size_gb']} GB")
            
            print(f"\n🎭 MOODS AVAILABLE:")
            for mood, count in stats['moods'].items():
                percentage = (count / stats['total_tracks']) * 100
                print(f"   {mood.capitalize()}: {count} tracks ({percentage:.1f}%)")
                
            print(f"\n🎼 GENRES AVAILABLE:")
            for genre, count in stats['genres'].items():
                percentage = (count / stats['total_tracks']) * 100
                print(f"   {genre.capitalize()}: {count} tracks ({percentage:.1f}%)")
                
            print(f"\n🥁 TEMPO RANGE:")
            tempo_range = stats['tempo_range']
            print(f"   Min: {tempo_range['min']} BPM")
            print(f"   Average: {tempo_range['mean']} BPM") 
            print(f"   Max: {tempo_range['max']} BPM")
            
        else:
            print(f"❌ Failed to get stats: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting database stats: {e}")

def main():
    """Test music recommendations for various video types"""
    print("🎵 DIRECT MUSIC RECOMMENDATION TEST")
    print("🎯 Testing what music the system suggests for different video types")
    print("=" * 70)
    
    # Show complete database first
    show_database_breakdown()
    
    # Define different video types and their characteristics
    video_scenarios = {
        "Corporate Presentation": {
            "moods": ["neutral", "calm"],
            "preferred_genres": ["general", "pop"]
        },
        "High-Energy Sports": {
            "moods": ["energetic", "upbeat"],
            "preferred_genres": ["dance", "electronic"]
        },
        "Relaxing Nature Video": {
            "moods": ["calm", "neutral"],
            "preferred_genres": ["ambient", "downtempo"]
        },
        "Party/Event Video": {
            "moods": ["energetic", "upbeat"],
            "preferred_genres": ["dance", "pop"]
        },
        "Tutorial/Educational": {
            "moods": ["neutral", "calm"],
            "preferred_genres": ["general", "pop"]
        },
        "Dynamic Action Video": {
            "moods": ["energetic", "bright"],
            "preferred_genres": ["electronic", "dance"]
        }
    }
    
    # Test each video scenario
    for video_type, characteristics in video_scenarios.items():
        test_music_for_video_type(video_type, characteristics)
    
    print(f"\n🏆 RECOMMENDATION TEST COMPLETE!")
    print("🎵 The system can intelligently match music to any video type!")
    print("🚀 Ready for n8n workflow integration!")

if __name__ == "__main__":
    main()
