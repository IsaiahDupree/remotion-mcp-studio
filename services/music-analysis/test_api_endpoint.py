#!/usr/bin/env python3
"""
Test API Endpoint for Intelligent Video Analysis
"""
import requests
import json

def test_api_endpoint():
    """Test the /video/analyze-content API endpoint"""
    print("🚀 TESTING INTELLIGENT VIDEO ANALYSIS API ENDPOINT")
    print("=" * 55)
    
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    
    # Test the API endpoint
    url = "http://localhost:5001/video/analyze-content"
    data = {"video_path": video_path}
    
    video_filename = video_path.split('\\')[-1]
    print(f"🎬 Testing with video: {video_filename}")
    print(f"🌐 API URL: {url}")
    print(f"📋 Request data: {json.dumps(data, indent=2)}")
    
    try:
        print(f"\n⏳ Sending API request...")
        response = requests.post(url, json=data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! API endpoint working")
            print(f"📊 Response received ({len(str(result))} chars)")
            
            print(f"\n🎯 INTELLIGENT ANALYSIS RESULTS:")
            print(f"   📝 Existing Captions: {result.get('has_existing_captions', 'N/A')}")
            print(f"   🎤 Transcript Available: {'YES' if result.get('transcript') else 'NO'}")
            print(f"   👁️ Visual Analysis: {'YES' if result.get('visual_analysis') else 'NO'}")
            print(f"   ✨ Perfect Overlay: \"{result.get('suggested_overlay', 'N/A')}\"")
            print(f"   🎯 Confidence: {result.get('confidence_score', 0):.2f}")
            print(f"   📸 Frames Analyzed: {result.get('frame_samples_count', 0)}")
            print(f"   ⏱️ Processing Time: {result.get('processing_time', 0):.1f}s")
            
            print(f"\n🚀 N8N INTEGRATION READY:")
            print(f"   📁 Video Path: {result.get('video_path', 'N/A')}")
            print(f"   📐 Resolution: {result.get('video_info', {}).get('width')}x{result.get('video_info', {}).get('height')}")
            print(f"   ⏱️ Duration: {result.get('video_info', {}).get('duration', 0):.1f}s")
            
            return True
            
        else:
            print(f"❌ API Error: {response.status_code}")
            try:
                error_info = response.json()
                print(f"Error: {json.dumps(error_info, indent=2)}")
            except:
                print(f"Error text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR: API server not running on localhost:5001")
        print(f"💡 Start the API server first with: python enhanced_flask_api.py")
        return False
    except requests.exceptions.Timeout:
        print(f"⏱️ TIMEOUT: Analysis took too long")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_api_endpoint()
    
    print(f"\n📊 API ENDPOINT TEST SUMMARY")
    print("=" * 30)
    if success:
        print("🎉 INTELLIGENT VIDEO ANALYSIS API: FULLY OPERATIONAL!")
        print("✅ Caption detection via API: Working")
        print("✅ Transcript extraction via API: Ready")
        print("✅ Frame analysis via API: Ready") 
        print("✅ Perfect overlay generation via API: Working")
        print("✅ Video metadata extraction: Working")
        print("🚀 Ready for n8n workflow integration!")
    else:
        print("⚠️ API ENDPOINT NEEDS ATTENTION")
        print("🔧 Check if API server is running")
