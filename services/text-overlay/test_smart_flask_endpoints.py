#!/usr/bin/env python3
"""
Test the new intelligent music matching Flask endpoints
"""

import requests
import json
import time

# Flask app configuration
BASE_URL = "http://localhost:5003"
TEST_VIDEO = "v12044gd0000cu2t04nog65p7djql4g0.MP4"

def test_music_analysis_endpoint():
    """Test the music analysis endpoint"""
    print("🎵 Testing Music Analysis Endpoint")
    print("=" * 50)
    
    url = f"{BASE_URL}/analyze/music-match/{TEST_VIDEO}"
    
    try:
        print(f"📡 Sending request to: {url}")
        response = requests.get(url, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Music Analysis Successful!")
            print(f"📹 Video: {data.get('video_filename')}")
            print(f"🎭 Content Type: {data.get('video_analysis', {}).get('content_type')}")
            print(f"😊 Mood: {data.get('video_analysis', {}).get('visual_mood')}")
            print(f"⚡ Energy: {data.get('video_analysis', {}).get('energy_level')}")
            print(f"📊 Tracks Analyzed: {data.get('music_recommendations', {}).get('total_tracks_analyzed')}")
            
            best_match = data.get('music_recommendations', {}).get('best_match')
            if best_match:
                print(f"🏆 Best Match: {best_match.get('music_path')}")
                print(f"💯 Score: {best_match.get('compatibility_score'):.2f}")
                print(f"💭 Reasoning: {best_match.get('reasoning', 'N/A')[:100]}...")
            
            return data
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_smart_processing_endpoint(analysis_data=None):
    """Test the smart video processing endpoint"""
    print("\n🎬 Testing Smart Video Processing Endpoint")
    print("=" * 50)
    
    url = f"{BASE_URL}/process/smart-video"
    
    # Prepare request data
    request_data = {
        "video_filename": TEST_VIDEO,
        "config": {
            "min_compatibility_score": 0.6,
            "music_volume": 0.04,
            "text_style": "modern"
        }
    }
    
    # If we have analysis data, use the best music
    if analysis_data:
        best_match = analysis_data.get('music_recommendations', {}).get('best_match')
        if best_match:
            request_data["music_path"] = best_match.get('music_path')
            print(f"🎵 Using recommended music: {best_match.get('music_path')}")
    
    try:
        print(f"📡 Sending request to: {url}")
        print(f"📦 Request data: {json.dumps(request_data, indent=2)}")
        
        response = requests.post(url, 
                               json=request_data, 
                               timeout=300,  # 5 minutes for processing
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Smart Video Processing Successful!")
                print(f"📹 Input: {data.get('video_filename')}")
                print(f"📤 Output: {data.get('output_filename')}")
                print(f"🎵 Music Used: {data.get('music_used')}")
                print(f"💯 Compatibility: {data.get('compatibility_score', 0):.2f}")
                print(f"📝 Text Overlay: {data.get('text_overlay')}")
                print(f"⏱️ Processing Time: {data.get('processing_time_seconds')}s")
                print(f"📥 Download URL: {data.get('download_url')}")
                return data
            else:
                print(f"❌ Processing failed: {data.get('error')}")
                return None
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main test function"""
    print("🚀 Testing Smart Flask Endpoints")
    print("=" * 60)
    
    # Test 1: Music Analysis
    analysis_result = test_music_analysis_endpoint()
    
    if analysis_result:
        # Test 2: Smart Processing with recommended music
        time.sleep(2)  # Brief pause
        processing_result = test_smart_processing_endpoint(analysis_result)
        
        if processing_result:
            print("\n🎉 All tests completed successfully!")
            print("=" * 60)
            print("✅ Music analysis working")
            print("✅ Smart video processing working")
            print("✅ Intelligent music matching integrated")
            print("\n🔗 API Usage:")
            print(f"   GET  {BASE_URL}/analyze/music-match/<video_filename>")
            print(f"   POST {BASE_URL}/process/smart-video")
        else:
            print("\n⚠️ Music analysis worked, but processing failed")
    else:
        print("\n❌ Music analysis failed - cannot test processing")

if __name__ == "__main__":
    main()
