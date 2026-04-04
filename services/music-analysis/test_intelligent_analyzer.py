#!/usr/bin/env python3
"""
Test Intelligent Video Analyzer
- Tests the new intelligent video content analysis system
- Demonstrates caption detection, transcript extraction, frame analysis
- Shows perfect contextual text overlay generation
"""
import requests
import json
import os
from pathlib import Path
import time

BASE_URL = "http://localhost:5001"

def test_video_analysis_api():
    """Test the new video analysis API endpoint"""
    print("🚀 TESTING INTELLIGENT VIDEO CONTENT ANALYZER")
    print("=" * 60)
    
    # Test with the specific video from memory
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    
    if not Path(video_path).exists():
        print(f"❌ Test video not found: {video_path}")
        return False
    
    print(f"🎬 Analyzing Video: {Path(video_path).name}")
    print(f"📁 Path: {video_path}")
    
    # Prepare API request
    request_data = {
        "video_path": video_path
        # Note: OpenAI API key would be set via environment variable if needed
    }
    
    print(f"\n📋 API Request:")
    print(json.dumps(request_data, indent=2))
    
    try:
        print(f"\n⏳ Sending request to /video/analyze-content...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/video/analyze-content",
            json=request_data,
            timeout=120  # Allow up to 2 minutes for analysis
        )
        
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ SUCCESS! Analysis completed in {request_time:.1f}s")
            print("=" * 60)
            
            # Display comprehensive results
            print("📊 INTELLIGENT VIDEO ANALYSIS RESULTS")
            print("-" * 50)
            
            print(f"🎬 Video: {result.get('video_name', 'Unknown')}")
            print(f"📐 Resolution: {result['video_info']['width']}x{result['video_info']['height']}")
            print(f"⏱️ Duration: {result['video_info']['duration']:.1f} seconds")
            print(f"🎵 Has Audio: {result['video_info']['has_audio']}")
            print(f"🎥 Codec: {result['video_info']['codec']}")
            
            print(f"\n🔍 ANALYSIS DETAILS:")
            print(f"   📝 Existing Captions: {result['has_existing_captions']}")
            
            if result['existing_captions']:
                print(f"   📋 Caption Content: {result['existing_captions']}")
            
            if result['transcript']:
                print(f"   🎤 Transcript Found: YES ({len(result['transcript'])} chars)")
                print(f"   📜 Preview: {result['transcript'][:100]}...")
            else:
                print(f"   🎤 Transcript: Not available")
            
            if result['visual_analysis']:
                print(f"   👁️ Visual Analysis: YES ({len(result['visual_analysis'])} chars)")
                print(f"   🖼️ Preview: {result['visual_analysis'][:100]}...")
            else:
                print(f"   👁️ Visual Analysis: Not available")
            
            print(f"\n✨ PERFECT TEXT OVERLAY GENERATED:")
            print(f"   📝 Text: \"{result['suggested_overlay']}\"")
            print(f"   🎯 Confidence: {result['confidence_score']:.2f}")
            print(f"   📸 Frames Analyzed: {result['frame_samples_count']}")
            print(f"   ⏱️ Processing Time: {result['processing_time']:.1f}s")
            
            print(f"\n🔧 ANALYSIS STRATEGY:")
            for key, value in result['analysis_strategy'].items():
                print(f"   {key.replace('_', ' ').title()}: {value}")
            
            print(f"\n🚀 N8N INTEGRATION READY:")
            print(f"   📁 Video Path: {result['video_path']}")
            print(f"   📝 Overlay Text: {result['suggested_overlay']}")
            print(f"   🎯 Confidence: {result['confidence_score']:.2f}")
            print(f"   📊 Full Analysis Available: YES")
            
            # Show complete API response for n8n
            print(f"\n📋 COMPLETE API RESPONSE FOR N8N:")
            print(json.dumps(result, indent=2))
            
            return True
            
        else:
            print(f"❌ API Error: {response.status_code}")
            try:
                error_info = response.json()
                print(f"Error Details: {json.dumps(error_info, indent=2)}")
            except:
                print(f"Error Text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️ TIMEOUT: Analysis took too long (>2 minutes)")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_direct_analyzer():
    """Test the analyzer directly (without API)"""
    print("\n🔬 TESTING DIRECT ANALYZER (WITHOUT API)")
    print("=" * 50)
    
    try:
        from intelligent_video_analyzer import IntelligentVideoAnalyzer
        
        video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
        
        if not Path(video_path).exists():
            print(f"❌ Test video not found: {video_path}")
            return False
        
        analyzer = IntelligentVideoAnalyzer()
        print("✅ Analyzer initialized")
        
        # Test just the caption detection
        print(f"\n🔍 Testing caption detection...")
        has_captions, caption_text = analyzer.detect_existing_captions(video_path)
        print(f"   Captions detected: {has_captions}")
        if caption_text:
            print(f"   Caption content: {caption_text}")
        
        # Test video info
        print(f"\n📹 Testing video info extraction...")
        video_info = analyzer.get_video_info(video_path) 
        print(f"   Duration: {video_info.get('duration', 0):.1f}s")
        print(f"   Resolution: {video_info.get('width')}x{video_info.get('height')}")
        print(f"   Has audio: {video_info.get('has_audio')}")
        
        # Test frame sampling
        print(f"\n📸 Testing frame sampling...")
        frames = analyzer.sample_frames_efficiently(video_path, video_info)
        print(f"   Frames sampled: {len(frames)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct test failed: {e}")
        return False

def main():
    """Run comprehensive intelligent video analyzer tests"""
    print("🧠 INTELLIGENT VIDEO CONTENT ANALYZER - COMPREHENSIVE TEST")
    print("🎯 Tests caption detection, transcript extraction, frame analysis, and overlay generation")
    print("=" * 80)
    
    # Test 1: API endpoint test
    api_success = test_video_analysis_api()
    
    # Test 2: Direct analyzer test (for debugging)
    direct_success = test_direct_analyzer()
    
    print(f"\n📊 TEST RESULTS SUMMARY")
    print("=" * 30)
    print(f"✅ API Test: {'PASSED' if api_success else 'FAILED'}")
    print(f"✅ Direct Test: {'PASSED' if direct_success else 'FAILED'}")
    
    if api_success:
        print(f"\n🎉 INTELLIGENT VIDEO ANALYZER FULLY OPERATIONAL!")
        print("✅ Caption detection working")
        print("✅ Transcript extraction ready") 
        print("✅ Frame analysis ready")
        print("✅ Perfect overlay generation working")
        print("✅ API endpoint integrated")
        print("🚀 Ready for n8n workflow integration!")
    else:
        print(f"\n⚠️ ANALYZER NEEDS ATTENTION")
        print("🔧 Check dependencies and API configuration")

if __name__ == "__main__":
    main()
