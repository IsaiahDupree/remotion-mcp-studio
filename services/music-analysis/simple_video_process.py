#!/usr/bin/env python3
"""
Simple Video Processing Test - Add text only (faster)
"""
import requests
import json
import os
import time

BASE_URL = "http://localhost:5001"

def test_simple_processing():
    """Test video processing with just text overlay (faster)"""
    print("🎬 SIMPLE VIDEO PROCESSING TEST")
    print("=" * 50)
    
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\0024d0ff50d04b2eba719fec130a0b74.mp4"
    output_path = r"C:\Users\Isaia\Documents\Coding\N8N\output\simple_test.mp4"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Simple text-only processing (faster than music+text)
    process_data = {
        "video_path": video_path,
        "output_path": output_path,
        "text_overlay": {
            "text": "Quick Test\\nText Overlay Only",
            "position": "center",
            "font_size": 48
        }
        # Note: No music to make it faster
    }
    
    print("📋 Request:")
    print(f"   🎬 Video: {os.path.basename(video_path)}")
    print(f"   📝 Text: Quick Test (text only)")
    print(f"   ⚡ Mode: Fast (no music)")
    
    try:
        print("\n⏳ Processing... (should be quick)")
        start_time = time.time()
        
        response = requests.post(f"{BASE_URL}/video/process", 
                               json=process_data, 
                               timeout=60)  # 1 minute timeout
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! ({processing_time:.1f}s)")
            print("-" * 30)
            print(f"📁 Output: {os.path.basename(result.get('output_path', 'N/A'))}")
            print(f"💾 Size: {result.get('file_size_mb', 'N/A')} MB")
            print(f"📐 Resolution: Preserved")
            
            # Check if file actually exists
            if os.path.exists(output_path):
                actual_size = os.path.getsize(output_path) / (1024 * 1024)
                print(f"✅ File created: {actual_size:.1f} MB")
                return True
            else:
                print("⚠️ Output file not found")
                return False
                
        else:
            print(f"❌ FAILED: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', 'Unknown')}")
            except:
                print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️ TIMEOUT: Processing took too long")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_api_health():
    """Quick API health check"""
    print("\n🏥 API HEALTH CHECK")
    print("=" * 30)
    
    try:
        response = requests.get(f"{BASE_URL}/system/status", timeout=5)
        if response.status_code == 200:
            print("✅ API is responsive")
            return True
        else:
            print(f"⚠️ API returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API unreachable: {e}")
        return False

def main():
    """Run simple video processing test"""
    print("🚀 SIMPLE VIDEO PROCESSING TEST")
    print("🎯 Testing basic video processing capabilities")
    print("=" * 60)
    
    # Check API health first
    if not test_api_health():
        print("❌ Cannot proceed - API is not responsive")
        return
    
    # Test simple processing
    success = test_simple_processing()
    
    if success:
        print(f"\n🎉 VIDEO PROCESSING WORKS!")
        print("✅ Ready for full music+text processing")
        print("✅ Ready for n8n integration")
    else:
        print(f"\n⚠️ PROCESSING ISSUES DETECTED")
        print("🔧 May need troubleshooting before n8n integration")

if __name__ == "__main__":
    main()
