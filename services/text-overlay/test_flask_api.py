#!/usr/bin/env python3
"""
Test script for the Flask Video Enhancement API

This script tests various endpoints of the Flask API to ensure everything works correctly.
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:5000"
TEST_VIDEO_PATH = "IMG_2553.MP4"  # Relative to shared_data directory

def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   Shared videos dir: {data['shared_videos_dir']}")
            print(f"   SoundCloud Excel exists: {data['soundcloud_excel_exists']}")
            print(f"   OpenAI API configured: {data['openai_api_configured']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_list_videos():
    """Test listing available videos"""
    print("\nTesting video listing...")
    try:
        response = requests.get(f"{API_BASE_URL}/videos")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['count']} videos")
            for video in data['videos'][:3]:  # Show first 3
                print(f"   - {video['filename']} ({video['size_mb']} MB)")
            return True
        else:
            print(f"❌ Video listing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Video listing error: {str(e)}")
        return False

def test_list_soundcloud_tracks():
    """Test listing SoundCloud tracks"""
    print("\nTesting SoundCloud tracks listing...")
    try:
        response = requests.get(f"{API_BASE_URL}/soundcloud/tracks")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['count']} SoundCloud tracks")
            for track in data['tracks'][:3]:  # Show first 3
                print(f"   - {track['title']} by {track['artist']}")
            return True
        else:
            print(f"❌ SoundCloud tracks listing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ SoundCloud tracks error: {str(e)}")
        return False

def test_process_video():
    """Test processing a single video"""
    print(f"\nTesting video processing for: {TEST_VIDEO_PATH}")
    
    # Payload for video processing
    payload = {
        "video_path": TEST_VIDEO_PATH,
        "add_music": True,
        "position": "TOP",
        "custom_text": "API Test Video",
        "speech_emphasis": 0.6
    }
    
    try:
        print("Sending processing request...")
        response = requests.post(
            f"{API_BASE_URL}/process/video",
            json=payload,
            timeout=300  # 5 minutes timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Video processing successful!")
                print(f"   Output: {data.get('output_path', 'Unknown')}")
                print(f"   Text overlay: {data.get('text_overlay', 'None')}")
                print(f"   Processing time: {data.get('processing_time_seconds', 0):.1f}s")
                print(f"   Music added: {data.get('music_added', False)}")
                if data.get('download_url'):
                    print(f"   Download URL: {API_BASE_URL}{data['download_url']}")
                return True
            else:
                print(f"❌ Video processing failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Video processing request failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Video processing timed out (this is normal for large videos)")
        return False
    except Exception as e:
        print(f"❌ Video processing error: {str(e)}")
        return False

def test_recent_logs():
    """Test getting recent processing logs"""
    print("\nTesting recent logs...")
    try:
        response = requests.get(f"{API_BASE_URL}/logs/recent?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved {data['count']} recent log entries")
            for log in data['logs']:
                print(f"   - {log.get('timestamp', 'Unknown time')}: {log.get('video_filename', 'Unknown file')} -> {log.get('success', False)}")
            return True
        else:
            print(f"❌ Recent logs failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Recent logs error: {str(e)}")
        return False

def main():
    """Run all API tests"""
    print("=== Flask Video Enhancement API Test Suite ===")
    print(f"Testing API at: {API_BASE_URL}")
    
    tests = [
        ("Health Check", test_health_check),
        ("List Videos", test_list_videos),
        ("List SoundCloud Tracks", test_list_soundcloud_tracks),
        ("Recent Logs", test_recent_logs),
        ("Process Video", test_process_video),  # This one takes time, so do it last
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        try:
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print(f"\n❌ Test interrupted by user")
            results[test_name] = False
            break
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("=== TEST SUMMARY ===")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
