#!/usr/bin/env python3
"""
Test script for Enhanced Music & Video Processing API
"""
import requests
import json

# API base URL
BASE_URL = "http://localhost:5001"

def test_system_status():
    """Test system status endpoint"""
    print("🔍 Testing system status...")
    response = requests.get(f"{BASE_URL}/system/status")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ System Status: {data['status']}")
        print(f"📊 Music tracks: {data['music_database']['total_tracks']}")
        print(f"🎵 Top mood: {max(data['music_database']['moods'], key=data['music_database']['moods'].get)}")
        return True
    else:
        print(f"❌ System status failed: {response.status_code}")
        return False

def test_music_search():
    """Test music search endpoint"""
    print("\n🔍 Testing music search...")
    
    # Test search for energetic music
    search_data = {
        "mood": "energetic",
        "limit": 3
    }
    
    response = requests.post(f"{BASE_URL}/music/search", json=search_data)
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Found {len(results.get('results', []))} energetic tracks:")
        for track in results.get('results', [])[:3]:
            print(f"   🎵 {track.get('filename', 'Unknown')} (Mood: {track.get('detected_mood', 'N/A')}, BPM: {track.get('tempo_bpm', 'N/A')})")
        return True
    else:
        print(f"❌ Music search failed: {response.status_code}")
        try:
            print(f"Error: {response.json()}")
        except:
            print(f"Raw response: {response.text}")
        return False

def test_database_stats():
    """Test database stats endpoint"""
    print("\n🔍 Testing database stats...")
    response = requests.get(f"{BASE_URL}/music/database/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Database contains:")
        print(f"   📊 Total tracks: {stats['total_tracks']}")
        print(f"   ⏱️ Total duration: {stats['total_duration_hours']} hours")
        print(f"   💾 Total size: {stats['total_size_gb']} GB")
        print(f"   🎭 Moods: {', '.join(stats['moods'].keys())}")
        print(f"   🎼 Genres: {', '.join(stats['genres'].keys())}")
        return True
    else:
        print(f"❌ Database stats failed: {response.status_code}")
        return False

def main():
    """Run all API tests"""
    print("🚀 Testing Enhanced Music & Video Processing API")
    print("=" * 50)
    
    tests = [
        test_system_status,
        test_database_stats,
        test_music_search
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n🏆 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests PASSED! The Enhanced API is working perfectly!")
    else:
        print("⚠️ Some tests failed. Check the API logs for details.")

if __name__ == "__main__":
    main()
