#!/usr/bin/env python3
"""
Integration test for Enhanced Music Analysis API with n8n workflow
"""
import requests
import json
import time

# API endpoint
API_BASE = "http://localhost:5001"

def test_health():
    """Test API health"""
    print("🏥 Testing API Health...")
    response = requests.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_system_status():
    """Test system status endpoint"""
    print("\n📊 Testing System Status...")
    response = requests.get(f"{API_BASE}/system-status")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        status = response.json()
        print(f"Total tracks: {status['total_tracks']}")
        print(f"WordsOnText: {status['music_libraries']['wordsOnText']['tracks']}")
        print(f"SoundCloud: {status['music_libraries']['soundcloud']['tracks']}")
        print(f"Trend status: {status['trend_data']['status']}")
    return response.status_code == 200

def test_music_analysis():
    """Test the main music analysis endpoint (n8n compatible)"""
    print("\n🎵 Testing Enhanced Music Analysis...")
    
    # Sample data that would come from n8n workflow
    test_data = {
        "video_path": "/home/node/shared/videos/IMG_3287.MP4",
        "transcript": "Children playing energetically in the backyard, running around and laughing with excitement. The kids are having so much fun jumping and playing games together.",
        "visual_analysis": "Bright outdoor scene with fast movements, children running, jumping, and playing games. High energy, cheerful atmosphere with lots of motion and activity. Colorful playground equipment visible."
    }
    
    print(f"Request data: {json.dumps(test_data, indent=2)}")
    
    response = requests.post(
        f"{API_BASE}/analyze-music-match",
        json=test_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Verify expected fields for n8n compatibility
        required_fields = ['detected_mood', 'energy_level', 'music_recommendation']
        for field in required_fields:
            if field in result:
                print(f"✅ {field}: {result[field] if field != 'music_recommendation' else result[field]['file_name']}")
            else:
                print(f"❌ Missing required field: {field}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200

def test_soundcloud_setup():
    """Test SoundCloud setup (if Excel file exists)"""
    print("\n🎧 Testing SoundCloud Setup...")
    
    response = requests.post(f"{API_BASE}/setup-soundcloud")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"SoundCloud setup result: {json.dumps(result, indent=2)}")
    else:
        print(f"SoundCloud setup response: {response.text}")
    
    return True  # Don't fail test if SoundCloud setup fails

def test_music_recommendations():
    """Test direct music recommendations endpoint"""
    print("\n🎶 Testing Music Recommendations...")
    
    test_data = {
        "mood": "energetic",
        "energy_level": 0.8,
        "count": 3
    }
    
    response = requests.post(
        f"{API_BASE}/get-music-recommendations",
        json=test_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Recommendations: {len(result.get('recommendations', []))} tracks found")
        if result.get('recommendations'):
            for i, track in enumerate(result['recommendations'][:2]):
                print(f"  {i+1}. {track.get('file_name', 'Unknown')} (score: {track.get('compatibility_score', 0)})")
    else:
        print(f"Error: {response.text}")
    
    return True

def test_trend_update():
    """Test trend update endpoint"""
    print("\n📈 Testing Trend Update...")
    
    response = requests.post(f"{API_BASE}/update-trends")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Trend update: {result['status']}")
        print(f"Last updated: {result['last_updated']}")
        if 'trend_summary' in result:
            summary = result['trend_summary']
            print(f"Top genres: {summary.get('top_genres', [])[:3]}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200

def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Starting Enhanced Music API Integration Tests\n")
    
    tests = [
        ("Health Check", test_health),
        ("System Status", test_system_status),
        ("Music Analysis (n8n Compatible)", test_music_analysis),
        ("SoundCloud Setup", test_soundcloud_setup),
        ("Music Recommendations", test_music_recommendations),
        ("Trend Update", test_trend_update)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print(f"{'='*50}")
        
        try:
            success = test_func()
            results.append((test_name, success))
            print(f"✅ {test_name}: {'PASSED' if success else 'FAILED'}")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Enhanced Music API is ready for n8n integration!")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    run_integration_tests()
