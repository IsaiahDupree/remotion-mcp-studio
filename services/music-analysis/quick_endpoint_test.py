#!/usr/bin/env python3
"""
Quick endpoint tests to verify all major functions work
"""
import requests
import json

def test_music_matching():
    """Test music matching endpoint"""
    print("🎯 Testing Music Matching...")
    
    data = {
        "video_path": "mock_video.mp4",  # Mock path for testing
        "transcript": "upbeat energetic dance music",
        "visual_analysis": "fast paced dancing with bright colors"
    }
    
    try:
        response = requests.post("http://localhost:5001/analyze-music-match", json=data, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Detected mood: {result.get('detected_mood')}")
            if result.get('music_recommendation'):
                print(f"✅ Music file: {result['music_recommendation'].get('file_path', 'N/A')}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_music_search():
    """Test music search endpoint"""
    print("\n🎵 Testing Music Search...")
    
    data = {"limit": 3}
    
    try:
        response = requests.post("http://localhost:5001/music/search", json=data, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Found {len(result.get('matches', []))} matches")
            if result.get('matches'):
                first = result['matches'][0]
                print(f"✅ First track: {first.get('file_path', 'N/A')}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_health():
    """Test health endpoints"""
    print("\n🏥 Testing Health...")
    
    try:
        response = requests.get("http://localhost:5001/health", timeout=5)
        print(f"Health Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Service: {result.get('service')}")
            print(f"✅ Status: {result.get('status')}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    print("🚀 QUICK ENDPOINT TESTS")
    print("=" * 25)
    test_health()
    test_music_search()
    test_music_matching()
    print("\n🎯 Tests completed!")
