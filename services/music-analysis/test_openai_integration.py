#!/usr/bin/env python3
"""
Test OpenAI Integration with Embedded API Key
"""
import requests
import json
import time

def test_openai_analysis():
    """Test the OpenAI-powered video analysis endpoint"""
    
    # Test video path
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    
    # API endpoint
    url = "http://localhost:5001/video/analyze-with-openai"
    
    # Test data
    test_data = {
        "video_path": video_path,
        "use_openai": True
    }
    
    print("🚀 Testing OpenAI Video Analysis...")
    print(f"📹 Test Video: {video_path}")
    print(f"🔗 Endpoint: {url}")
    
    try:
        # Send request
        start_time = time.time()
        response = requests.post(url, json=test_data, timeout=120)
        request_time = time.time() - start_time
        
        print(f"⏱️ Request completed in {request_time:.1f}s")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS - OpenAI Analysis Results:")
            print("=" * 50)
            
            # Core results
            print(f"🎯 Suggested Overlay: '{result.get('suggested_overlay', 'N/A')}'")
            print(f"🎲 Confidence Score: {result.get('confidence_score', 0):.2f}")
            print(f"🤖 Used OpenAI: {result.get('used_openai_analysis', False)}")
            print(f"⏰ Processing Time: {result.get('processing_time', 0):.1f}s")
            
            # Video info
            video_info = result.get('video_info', {})
            print(f"📺 Duration: {video_info.get('duration', 0):.1f}s")
            print(f"📐 Resolution: {video_info.get('resolution', 'N/A')}")
            
            # Analysis details
            print(f"📝 Has Captions: {result.get('has_existing_captions', False)}")
            print(f"🎤 Transcript Length: {len(result.get('transcript', '') or '')}")
            print(f"👁️ Visual Analysis: {bool(result.get('visual_analysis'))}")
            print(f"🖼️ Frame Samples: {result.get('frame_samples_count', 0)}")
            
            # Show transcript preview
            transcript = result.get('transcript', '')
            if transcript:
                preview = transcript[:100] + "..." if len(transcript) > 100 else transcript
                print(f"📋 Transcript Preview: {preview}")
            
            # Show visual analysis preview
            visual = result.get('visual_analysis', '')
            if visual:
                preview = visual[:100] + "..." if len(visual) > 100 else visual
                print(f"🔍 Visual Analysis Preview: {preview}")
            
            return True
            
        else:
            print(f"❌ FAILED - HTTP {response.status_code}")
            try:
                error_info = response.json()
                print(f"Error: {error_info}")
            except:
                print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ REQUEST TIMEOUT - Analysis took too long")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 CONNECTION ERROR - Is the Flask API running?")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def test_api_health():
    """Quick health check of the API"""
    try:
        response = requests.get("http://localhost:5001/system/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ API Health: {status.get('status', 'Unknown')}")
            print(f"📊 Music Database: {status.get('music_database', {}).get('track_count', 0)} tracks")
            return True
        else:
            print(f"❌ API Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Health Check Error: {e}")
        return False

if __name__ == "__main__":
    print("🎬 OPENAI INTEGRATION TEST")
    print("=" * 40)
    
    # Test API health first
    if test_api_health():
        print("\n" + "=" * 40)
        # Test OpenAI analysis
        success = test_openai_analysis()
        
        print("\n" + "=" * 40)
        if success:
            print("🎉 ALL TESTS PASSED!")
            print("✅ OpenAI integration is working correctly")
        else:
            print("❌ TESTS FAILED")
            print("⚠️ Check API logs for details")
    else:
        print("❌ API not healthy - skipping OpenAI test")
