#!/usr/bin/env python3
"""
Comprehensive Music Recommendation Demo
Shows the full capability of the music selection system
"""
import requests
import json
import os

BASE_URL = "http://localhost:5001"

def show_music_by_mood():
    """Show music recommendations for each available mood"""
    print("🎭 MUSIC RECOMMENDATIONS BY MOOD")
    print("=" * 60)
    
    moods = ["energetic", "upbeat", "neutral", "bright", "calm"]
    
    for mood in moods:
        print(f"\n🎵 {mood.upper()} MUSIC:")
        print("-" * 30)
        
        search_data = {"mood": mood, "limit": 3}
        
        try:
            response = requests.post(f"{BASE_URL}/music/search", json=search_data, timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                tracks = results.get('results', [])
                
                if tracks:
                    for i, track in enumerate(tracks, 1):
                        filename = os.path.basename(track.get('file_name', 'Unknown'))
                        genre = track.get('predicted_genre', 'N/A')
                        tempo = track.get('tempo_bpm', 'N/A')
                        energy = track.get('energy_level', 'N/A')
                        
                        print(f"   {i}. 🎵 {filename}")
                        print(f"      📊 Genre: {genre} | Tempo: {tempo} BPM | Energy: {energy}")
                else:
                    print("   No tracks found for this mood")
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def show_music_by_genre():
    """Show music recommendations for each available genre"""
    print("\n🎼 MUSIC RECOMMENDATIONS BY GENRE")
    print("=" * 60)
    
    genres = ["dance", "electronic", "pop", "general", "downtempo"]
    
    for genre in genres:
        print(f"\n🎼 {genre.upper()} MUSIC:")
        print("-" * 30)
        
        search_data = {"genre": genre, "limit": 3}
        
        try:
            response = requests.post(f"{BASE_URL}/music/search", json=search_data, timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                tracks = results.get('results', [])
                
                if tracks:
                    for i, track in enumerate(tracks, 1):
                        filename = os.path.basename(track.get('file_name', 'Unknown'))
                        mood = track.get('detected_mood', 'N/A')
                        tempo = track.get('tempo_bpm', 'N/A')
                        
                        print(f"   {i}. 🎵 {filename}")
                        print(f"      📊 Mood: {mood} | Tempo: {tempo} BPM")
                else:
                    print("   No tracks found for this genre")
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def show_music_by_tempo():
    """Show music recommendations by tempo ranges"""
    print("\n🥁 MUSIC RECOMMENDATIONS BY TEMPO")
    print("=" * 60)
    
    tempo_ranges = [
        {"name": "SLOW (60-90 BPM)", "min_tempo": 60, "max_tempo": 90},
        {"name": "MODERATE (90-120 BPM)", "min_tempo": 90, "max_tempo": 120},
        {"name": "FAST (120-150 BPM)", "min_tempo": 120, "max_tempo": 150},
        {"name": "VERY FAST (150+ BPM)", "min_tempo": 150, "max_tempo": 200}
    ]
    
    for tempo_range in tempo_ranges:
        print(f"\n🥁 {tempo_range['name']}:")
        print("-" * 40)
        
        search_data = {
            "min_tempo": tempo_range["min_tempo"],
            "max_tempo": tempo_range["max_tempo"],
            "limit": 2
        }
        
        try:
            response = requests.post(f"{BASE_URL}/music/search", json=search_data, timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                tracks = results.get('results', [])
                
                if tracks:
                    for i, track in enumerate(tracks, 1):
                        filename = os.path.basename(track.get('file_name', 'Unknown'))
                        mood = track.get('detected_mood', 'N/A')
                        tempo = track.get('tempo_bpm', 'N/A')
                        genre = track.get('predicted_genre', 'N/A')
                        
                        print(f"   {i}. 🎵 {filename}")
                        print(f"      📊 {mood} | {genre} | {tempo} BPM")
                else:
                    print("   No tracks found in this tempo range")
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def show_video_scenario_recommendations():
    """Show music recommendations for specific video scenarios"""
    print("\n🎬 VIDEO SCENARIO MUSIC RECOMMENDATIONS")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "CORPORATE TRAINING VIDEO",
            "description": "Professional, informative content",
            "search": {"mood": "neutral", "genre": "general", "max_tempo": 120}
        },
        {
            "name": "FITNESS/WORKOUT VIDEO", 
            "description": "High energy, motivational content",
            "search": {"mood": "energetic", "min_tempo": 130, "genre": "dance"}
        },
        {
            "name": "PRODUCT DEMO VIDEO",
            "description": "Upbeat but not overwhelming",
            "search": {"mood": "upbeat", "genre": "pop", "max_tempo": 140}
        },
        {
            "name": "RELAXATION/MEDITATION VIDEO",
            "description": "Calm, peaceful content", 
            "search": {"mood": "calm", "genre": "downtempo", "max_tempo": 85}
        },
        {
            "name": "PARTY/EVENT HIGHLIGHTS",
            "description": "Fun, celebratory content",
            "search": {"mood": "energetic", "genre": "dance", "min_tempo": 120}
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🎬 {scenario['name']}")
        print(f"💡 {scenario['description']}")
        print("-" * 50)
        
        search_data = {**scenario["search"], "limit": 2}
        
        try:
            response = requests.post(f"{BASE_URL}/music/search", json=search_data, timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                tracks = results.get('results', [])
                
                if tracks:
                    print(f"🎵 PERFECT MATCHES:")
                    for i, track in enumerate(tracks, 1):
                        filename = os.path.basename(track.get('file_name', 'Unknown'))
                        mood = track.get('detected_mood', 'N/A')
                        tempo = track.get('tempo_bpm', 'N/A')
                        genre = track.get('predicted_genre', 'N/A')
                        energy = track.get('energy_level', 'N/A')
                        
                        print(f"   {i}. 🎵 {filename}")
                        print(f"      📊 {mood} {genre} | {tempo} BPM | Energy: {energy}")
                else:
                    print("   ❌ No perfect matches found")
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Run comprehensive music recommendation demo"""
    print("🎵 COMPREHENSIVE MUSIC RECOMMENDATION DEMO")
    print("🚀 Showcasing the full power of the music selection system")
    print("=" * 70)
    
    # Show system stats first
    try:
        response = requests.get(f"{BASE_URL}/music/database/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"📊 Database: {stats['total_tracks']} tracks, {stats['total_duration_hours']} hours")
        print()
    except:
        pass
    
    # Run all demonstrations
    show_music_by_mood()
    show_music_by_genre() 
    show_music_by_tempo()
    show_video_scenario_recommendations()
    
    print(f"\n🏆 DEMO COMPLETE!")
    print("✅ The system can intelligently match music to ANY video content!")
    print("🎯 Ready to enhance your n8n video workflows with perfect music selection!")

if __name__ == "__main__":
    main()
