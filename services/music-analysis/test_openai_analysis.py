#!/usr/bin/env python3
"""
Test OpenAI Video Analysis Endpoint
- Caption detection
- Transcript extraction 
- Frame sampling
- AI-powered overlay generation
"""
import requests
import json
import time

API_BASE = "http://localhost:5001"

def test_openai_analysis():
    """Test the OpenAI video analysis endpoint"""
    print("🎬 TESTING OPENAI VIDEO ANALYSIS")
    print("=" * 50)
    
    # Test video from shared directory
    video_path = 'C:/Users/Isaia/Documents/Coding/N8N/shared/videos/1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4'
    
    data = {
        'video_path': video_path,
        'openai_api_key': 'test'  # Will use fallback if OpenAI key not available
    }
    
    print(f"📹 Video: {video_path.split('/')[-1]}")
    print("🔍 Starting analysis...")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/video/analyze-with-openai",
            json=data,
            timeout=90
        )
        elapsed = time.time() - start_time
        
        print(f"⏱️ Request completed in {elapsed:.1f}s")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ OPENAI ANALYSIS SUCCESS!")
            print("=" * 40)
            
            # Display comprehensive results
            print(f"📋 Has existing captions: {result.get('has_existing_captions', 'N/A')}")
            print(f"📝 Transcript length: {len(result.get('transcript', '') or '')} chars")
            print(f"👁️ Visual analysis length: {len(result.get('visual_analysis', '') or '')} chars")
            print(f"🖼️ Frame samples: {result.get('frame_samples_count', 'N/A')}")
            print(f"⏱️ Processing time: {result.get('processing_time', 0):.1f}s")
            
            print(f"\n🎯 SUGGESTED OVERLAY:")
            print(f'"{result.get("suggested_overlay", "N/A")}"')
            
            print(f"\n📈 Analysis Details:")
            print(f"   Confidence score: {result.get('confidence_score', 'N/A')}")
            print(f"   Used OpenAI: {result.get('used_openai_analysis', 'N/A')}")
            print(f"   Video duration: {result.get('video_duration', 'N/A')}")
            print(f"   Video resolution: {result.get('video_resolution', 'N/A')}")
            
            # Show transcript preview if available
            transcript = result.get('transcript', '')
            if transcript:
                print(f"\n📝 Transcript Preview:")
                print(f'"{transcript[:200]}..." ({len(transcript)} total chars)')
            
            # Show visual analysis preview if available
            visual = result.get('visual_analysis', '')
            if visual:
                print(f"\n👁️ Visual Analysis Preview:")
                print(f'"{visual[:200]}..." ({len(visual)} total chars)')
                
        else:
            print(f"\n❌ ERROR Response:")
            print(f"Status: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"\n❌ Request Exception: {str(e)}")

def test_with_real_openai_key():
    """Test with a real OpenAI key if available"""
    print("\n🤖 TESTING WITH REAL OPENAI KEY")
    print("=" * 50)
    
    # You can set your OpenAI API key here for testing
    openai_key = None  # Replace with your actual key: "sk-..."
    
    if not openai_key:
        print("⚠️ No OpenAI key provided - will test fallback functionality")
        return
    
    video_path = 'C:/Users/Isaia/Documents/Coding/N8N/shared/videos/1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4'
    
    data = {
        'video_path': video_path,
        'openai_api_key': openai_key
    }
    
    try:
        print("🔍 Testing with real OpenAI integration...")
        response = requests.post(
            f"{API_BASE}/video/analyze-with-openai",
            json=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ REAL OPENAI SUCCESS!")
            print(f"🎯 AI-Generated Overlay: \"{result.get('suggested_overlay')}\"")
            print(f"📈 AI Analysis Quality: {result.get('used_openai_analysis')}")
        else:
            print(f"❌ OpenAI test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ OpenAI test exception: {e}")

if __name__ == "__main__":
    print("🚀 OPENAI VIDEO ANALYSIS TESTING")
    print("=" * 60)
    print("Testing the enhanced video analysis pipeline:")
    print("• Caption detection in existing videos")
    print("• Transcript extraction using Whisper")
    print("• Smart frame sampling based on video length")
    print("• AI-powered overlay text generation")
    print("• Fallback mechanisms for robust operation")
    print("=" * 60)
    
    # Test the analysis endpoint
    test_openai_analysis()
    
    # Test with real OpenAI if key available
    test_with_real_openai_key()
    
    print("\n🎯 TESTING COMPLETE!")
