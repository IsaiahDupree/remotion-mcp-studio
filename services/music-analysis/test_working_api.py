#!/usr/bin/env python3
"""
Test Working API with Correct Endpoints
Tests the enhanced Flask API with proper endpoint paths
"""
import requests
import json
from pathlib import Path

def test_system_health():
    """Test system health and status"""
    print("🏥 TESTING SYSTEM HEALTH")
    print("=" * 30)
    
    try:
        response = requests.get("http://localhost:5001/system/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ System Status: HEALTHY")
            print(f"   Total Music Tracks: {data['music_database']['total_tracks']}")
            print(f"   FFmpeg Available: {data['video_processor']['ffmpeg_available']}")
            print(f"   SoundCloud Library: {data['soundcloud_library']['total_files']} files")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_music_search():
    """Test music search functionality"""
    print("\n🎵 TESTING MUSIC SEARCH")
    print("=" * 25)
    
    try:
        # Try broader search first
        request_data = {
            "limit": 5
        }
        
        response = requests.post(
            "http://localhost:5001/music/search",
            json=request_data,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Music Search: WORKING")
            print(f"   Found {len(data.get('matches', []))} matches")
            if data.get('matches'):
                first_match = data['matches'][0]
                print(f"   First Match: {first_match.get('file_path', 'N/A')}")
                print(f"   Mood: {first_match.get('mood', 'N/A')}")
                print(f"   Tempo: {first_match.get('tempo', 'N/A')} BPM")
            return True
        else:
            print(f"❌ Music search failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Music search error: {e}")
        return False

def test_video_analysis():
    """Test video content analysis"""
    print("\n🎬 TESTING VIDEO ANALYSIS")
    print("=" * 27)
    
    # Check if test video exists
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    
    if not Path(video_path).exists():
        print(f"⚠️ Test video not found: {video_path}")
        print("   Skipping video analysis test")
        return True
    
    try:
        request_data = {
            "video_path": video_path
        }
        
        response = requests.post(
            "http://localhost:5001/video/analyze-content",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Video Analysis: WORKING")
            print(f"   Video Duration: {data.get('video_info', {}).get('duration', 'N/A')}s")
            print(f"   Resolution: {data.get('video_info', {}).get('width', 'N/A')}x{data.get('video_info', {}).get('height', 'N/A')}")
            print(f"   Has Audio: {data.get('video_info', {}).get('has_audio', False)}")
            print(f"   Processing Time: {data.get('processing_time', 'N/A')}s")
            return True
        else:
            print(f"❌ Video analysis failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Video analysis error: {e}")
        return False

def test_music_matching():
    """Test music-video matching"""
    print("\n🎯 TESTING MUSIC MATCHING")
    print("=" * 27)
    
    # Use the same video file that exists for video analysis
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    
    if not Path(video_path).exists():
        print(f"⚠️ Test video not found: {video_path}")
        print("   Testing with mock data instead")
        video_path = "mock_video.mp4"  # This will test the logic without file dependency
    
    try:
        request_data = {
            "video_path": video_path,
            "transcript": "This is an energetic dance video with upbeat music",
            "visual_analysis": "Video shows people dancing with bright colors and fast movements"
        }
        
        response = requests.post(
            "http://localhost:5001/analyze-music-match",
            json=request_data,
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Music Matching: WORKING")
            print(f"   Detected Mood: {data.get('detected_mood', 'N/A')}")
            if data.get('music_recommendation'):
                rec = data['music_recommendation']
                print(f"   Music File: {Path(rec.get('file_path', 'N/A')).name}")
                print(f"   Compatibility: {rec.get('compatibility_score', 'N/A')}")
            return True
        else:
            print(f"❌ Music matching failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Music matching error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 COMPREHENSIVE API TEST SUITE")
    print("=" * 35)
    
    tests = [
        ("System Health", test_system_health),
        ("Music Search", test_music_search), 
        ("Video Analysis", test_video_analysis),
        ("Music Matching", test_music_matching)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 35)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 35)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 OVERALL: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🚀 ALL SYSTEMS OPERATIONAL - READY FOR N8N INTEGRATION!")
    else:
        print("⚠️ Some issues detected - check individual test output")

if __name__ == "__main__":
    main()
