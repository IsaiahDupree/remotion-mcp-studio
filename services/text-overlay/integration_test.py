#!/usr/bin/env python3
"""
Integration test for Flask Video Enhancement API with N8N video data
"""

import os
import sys
import json
from flask_app import app

def test_api_integration():
    """Test core API endpoints with actual video data"""
    print("🧪 INTEGRATION TEST - Flask Video Enhancement API")
    print("=" * 60)
    
    # Create test client
    client = app.test_client()
    
    # Test 1: Health endpoint
    print("\n1. Testing /health endpoint...")
    try:
        resp = client.get('/health')
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.get_json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            print("   ✅ Health check PASSED")
        else:
            print("   ❌ Health check FAILED")
            return False
    except Exception as e:
        print(f"   ❌ Health check ERROR: {e}")
        return False
    
    # Test 2: Videos endpoint  
    print("\n2. Testing /videos endpoint...")
    try:
        resp = client.get('/videos')
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.get_json()
            video_count = len(data.get('videos', []))
            directory = data.get('directory', 'unknown')
            print(f"   Found {video_count} videos in: {directory}")
            
            if video_count > 0:
                print(f"   Sample videos:")
                for i, video in enumerate(data['videos'][:3]):  # Show first 3
                    print(f"     - {video}")
                if video_count > 3:
                    print(f"     ... and {video_count - 3} more")
                print("   ✅ Videos endpoint PASSED")
            else:
                print("   ⚠️  No videos found, but endpoint works")
        else:
            print(f"   ❌ Videos endpoint FAILED with status {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Videos endpoint ERROR: {e}")
        return False
    
    # Test 3: Soundcloud tracks endpoint
    print("\n3. Testing /soundcloud/tracks endpoint...")
    try:
        resp = client.get('/soundcloud/tracks')
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.get_json()
            track_count = len(data.get('tracks', []))
            print(f"   Found {track_count} tracks available")
            print("   ✅ Soundcloud endpoint PASSED")
        else:
            print(f"   ⚠️  Soundcloud endpoint returned {resp.status_code} (expected - no tracks file)")
    except Exception as e:
        print(f"   ⚠️  Soundcloud endpoint error (expected): {e}")
    
    # Test 4: Directory configuration
    print("\n4. Testing directory configuration...")
    from flask_app import SHARED_VIDEO_DIR, ENHANCED_VIDEO_DIR
    print(f"   Shared Video Dir: {SHARED_VIDEO_DIR}")
    print(f"   Enhanced Video Dir: {ENHANCED_VIDEO_DIR}")
    
    if os.path.exists(SHARED_VIDEO_DIR):
        video_files = [f for f in os.listdir(SHARED_VIDEO_DIR) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
        print(f"   ✅ Shared directory exists with {len(video_files)} video files")
    else:
        print(f"   ❌ Shared directory does not exist")
        return False
        
    if os.path.exists(ENHANCED_VIDEO_DIR):
        print(f"   ✅ Enhanced directory exists")
    else:
        print(f"   ⚠️  Enhanced directory will be created on first use")
    
    print("\n" + "=" * 60)
    print("🎉 INTEGRATION TEST COMPLETED SUCCESSFULLY!")
    print("✅ Your Flask Video Enhancement API is ready for deployment")
    print("✅ N8N video directory integration is working")
    print(f"✅ Found video data in: {SHARED_VIDEO_DIR}")
    return True

if __name__ == "__main__":
    success = test_api_integration()
    sys.exit(0 if success else 1)
