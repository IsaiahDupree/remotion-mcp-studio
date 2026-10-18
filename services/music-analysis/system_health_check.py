#!/usr/bin/env python3
"""
Complete System Health Check
Verifies all components are working before testing video processing
"""
import requests
import json
import os
from pathlib import Path
import time

def check_api_health():
    """Check if the Flask API is running and healthy"""
    print("🌐 CHECKING API HEALTH")
    print("=" * 25)
    
    try:
        response = requests.get("http://localhost:5001/system/status", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            print("✅ API Server: RUNNING")
            print(f"   📡 Port: 5001")
            print(f"   🎵 Music System: {'OK' if status_data.get('music_system_status') == 'healthy' else 'ERROR'}")
            print(f"   🎬 Video Processor: {'OK' if status_data.get('video_processor_status') == 'healthy' else 'ERROR'}")
            print(f"   🧠 Intelligence: {'OK' if status_data.get('intelligent_analyzer_status') == 'healthy' else 'ERROR'}")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API Server: NOT RUNNING")
        print("💡 Start with: python start_enhanced_api.py")
        return False
    except Exception as e:
        print(f"❌ API Health Check Failed: {e}")
        return False

def check_files():
    """Check if required files exist"""
    print("\n📁 CHECKING FILES")
    print("=" * 20)
    
    # Check test video
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    if Path(video_path).exists():
        file_size = os.path.getsize(video_path) / (1024 * 1024)
        print(f"✅ Test Video: Found ({file_size:.1f} MB)")
    else:
        print("❌ Test Video: Missing")
        return False
    
    # Check output directory
    output_dir = r"C:\Users\Isaia\Documents\Coding\N8N\output"
    if Path(output_dir).exists():
        print("✅ Output Directory: Found")
    else:
        print("🔧 Creating output directory...")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        print("✅ Output Directory: Created")
    
    # Check music library
    music_dir = r"C:\Users\Isaia\Documents\Coding\N8N\shared\music_library"
    if Path(music_dir).exists():
        music_files = list(Path(music_dir).glob("*.mp3"))
        print(f"✅ Music Library: Found ({len(music_files)} tracks)")
    else:
        print("⚠️ Music Library: Empty")
    
    return True

def test_simple_video_processing():
    """Test basic video processing with text overlay"""
    print("\n🎬 TESTING SIMPLE VIDEO PROCESSING")
    print("=" * 35)
    
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    output_path = r"C:\Users\Isaia\Documents\Coding\N8N\output\health_check_simple.mp4"
    
    # Test simple text overlay only
    request_data = {
        "video_path": video_path,
        "output_path": output_path,
        "text_overlay": "Health Check Test",
        "preserve_audio": True,
        "text_position": "bottom_center"
    }
    
    print("⏳ Processing video with text overlay only...")
    try:
        response = requests.post(
            "http://localhost:5001/video/process",
            json=request_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Simple Processing: SUCCESS")
            print(f"   📁 Output: {Path(result['output_path']).name}")
            print(f"   ⏱️ Processing Time: {result.get('processing_time', 0):.1f}s")
            return True
        else:
            print(f"❌ Processing Failed: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error.get('error', 'Unknown')}")
            except:
                print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️ Processing Timeout (60s)")
        return False
    except Exception as e:
        print(f"❌ Processing Error: {e}")
        return False

def test_music_video_processing():
    """Test video processing with music and text"""
    print("\n🎵 TESTING MUSIC + VIDEO PROCESSING")
    print("=" * 35)
    
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    output_path = r"C:\Users\Isaia\Documents\Coding\N8N\output\health_check_music.mp4"
    
    # First get a music recommendation
    print("🔍 Getting music recommendation...")
    try:
        music_response = requests.post(
            "http://localhost:5001/music/search",
            json={"query": "background neutral", "limit": 1},
            timeout=10
        )
        
        if music_response.status_code == 200:
            music_data = music_response.json()
            if music_data and len(music_data) > 0:
                music_file = music_data[0].get('filepath')
                print(f"✅ Music Found: {Path(music_file).name}")
            else:
                print("⚠️ No music found, using default")
                music_file = None
        else:
            print("⚠️ Music search failed, continuing without music")
            music_file = None
    except:
        print("⚠️ Music search error, continuing without music")
        music_file = None
    
    # Test with music and text
    request_data = {
        "video_path": video_path,
        "output_path": output_path,
        "music_path": music_file,
        "text_overlay": "Music + Text Test",
        "preserve_audio": False,
        "text_position": "bottom_center",
        "music_volume": -20
    }
    
    print("⏳ Processing video with music + text...")
    try:
        response = requests.post(
            "http://localhost:5001/video/process",
            json=request_data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Music Processing: SUCCESS")
            print(f"   📁 Output: {Path(result['output_path']).name}")
            print(f"   ⏱️ Processing Time: {result.get('processing_time', 0):.1f}s")
            return True
        else:
            print(f"❌ Music Processing Failed: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error.get('error', 'Unknown')}")
            except:
                print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️ Music Processing Timeout (120s)")
        return False
    except Exception as e:
        print(f"❌ Music Processing Error: {e}")
        return False

def main():
    """Run complete system health check and tests"""
    print("🏥 COMPLETE SYSTEM HEALTH CHECK & TEST")
    print("🎯 API + Files + Simple Processing + Music Processing")
    print("=" * 60)
    
    # Wait for API to fully start
    print("⏳ Waiting for API to fully initialize...")
    time.sleep(10)
    
    # Step 1: Check API Health
    api_ok = check_api_health()
    
    # Step 2: Check Files
    files_ok = check_files()
    
    if not api_ok or not files_ok:
        print("\n❌ SYSTEM NOT READY")
        print("🔧 Fix issues above before testing")
        return
    
    # Step 3: Test Simple Processing
    simple_ok = test_simple_video_processing()
    
    # Step 4: Test Music Processing
    music_ok = test_music_video_processing()
    
    # Summary
    print(f"\n📊 HEALTH CHECK SUMMARY")
    print("=" * 25)
    print(f"✅ API Health: {'PASS' if api_ok else 'FAIL'}")
    print(f"✅ Files Check: {'PASS' if files_ok else 'FAIL'}")
    print(f"✅ Simple Processing: {'PASS' if simple_ok else 'FAIL'}")
    print(f"✅ Music Processing: {'PASS' if music_ok else 'FAIL'}")
    
    if api_ok and files_ok and simple_ok and music_ok:
        print(f"\n🎉 ALL SYSTEMS OPERATIONAL!")
        print("🚀 Ready for full video processing workflows")
    else:
        print(f"\n⚠️ SOME SYSTEMS NEED ATTENTION")
        print("🔧 Check individual test results above")

if __name__ == "__main__":
    main()
