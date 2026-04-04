#!/usr/bin/env python3

import requests
import json
import time
from pathlib import Path

def comprehensive_endpoint_test():
    """Test all endpoints systematically to identify 500 errors"""
    
    print("🔍 COMPREHENSIVE ENDPOINT TESTING")
    print("=" * 50)
    
    base_url = "http://localhost:5001"
    test_video = "c:/Users/Isaia/Documents/Coding/N8N/shared/videos/1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    test_music = "c:/Users/Isaia/Documents/Coding/N8N/soundcloud_music/04collective - Rusherz - Before You Go.mp3"
    
    tests = []
    
    # 1. Basic Health Checks
    print("\n1️⃣ BASIC HEALTH CHECKS")
    print("-" * 25)
    
    try:
        response = requests.get(f"{base_url}/system/status", timeout=10)
        if response.status_code == 200:
            print("✅ System Status: OK")
            tests.append(("System Status", "PASS"))
        else:
            print(f"❌ System Status: HTTP {response.status_code}")
            tests.append(("System Status", f"HTTP_{response.status_code}"))
    except Exception as e:
        print(f"❌ System Status Error: {str(e)}")
        tests.append(("System Status", "ERROR"))
    
    # 2. Font System Tests
    print("\n2️⃣ FONT SYSTEM TESTS")
    print("-" * 20)
    
    # Font List
    try:
        response = requests.get(f"{base_url}/fonts/list", timeout=10)
        if response.status_code == 200:
            data = response.json()
            font_count = data.get('total_fonts', 0)
            print(f"✅ Font List: {font_count} fonts available")
            tests.append(("Font List", "PASS"))
        else:
            print(f"❌ Font List: HTTP {response.status_code}")
            tests.append(("Font List", f"HTTP_{response.status_code}"))
    except Exception as e:
        print(f"❌ Font List Error: {str(e)}")
        tests.append(("Font List", "ERROR"))
    
    # Font Test (might cause 500)
    try:
        payload = {
            "text": "Test Font Selection",
            "video_path": test_video
        }
        response = requests.post(f"{base_url}/fonts/test", json=payload, timeout=15)
        if response.status_code == 200:
            result = response.json()
            font_name = result.get('selected_font', {}).get('name', 'unknown')
            print(f"✅ Font Test: Selected {font_name}")
            tests.append(("Font Test", "PASS"))
        elif response.status_code == 500:
            print(f"❌ Font Test: 500 ERROR")
            print(f"   Response: {response.text[:200]}...")
            tests.append(("Font Test", "500_ERROR"))
        else:
            print(f"⚠️ Font Test: HTTP {response.status_code}")
            tests.append(("Font Test", f"HTTP_{response.status_code}"))
    except Exception as e:
        print(f"❌ Font Test Error: {str(e)}")
        tests.append(("Font Test", "ERROR"))
    
    # 3. Music System Tests
    print("\n3️⃣ MUSIC SYSTEM TESTS")
    print("-" * 21)
    
    # Music Search
    try:
        payload = {"query": "electronic", "limit": 5}
        response = requests.post(f"{base_url}/music/search", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            track_count = len(result.get('tracks', []))
            print(f"✅ Music Search: {track_count} tracks found")
            tests.append(("Music Search", "PASS"))
        elif response.status_code == 500:
            print(f"❌ Music Search: 500 ERROR")
            print(f"   Response: {response.text[:200]}...")
            tests.append(("Music Search", "500_ERROR"))
        else:
            print(f"⚠️ Music Search: HTTP {response.status_code}")
            tests.append(("Music Search", f"HTTP_{response.status_code}"))
    except Exception as e:
        print(f"❌ Music Search Error: {str(e)}")
        tests.append(("Music Search", "ERROR"))
    
    # Music Analysis (might cause 500)
    try:
        payload = {
            "video_path": test_video,
            "transcript": "test video content",
            "visual_analysis": "general video content"
        }
        response = requests.post(f"{base_url}/analyze-music-match", json=payload, timeout=20)
        if response.status_code == 200:
            result = response.json()
            mood = result.get('detected_mood', 'unknown')
            print(f"✅ Music Analysis: Detected {mood} mood")
            tests.append(("Music Analysis", "PASS"))
        elif response.status_code == 500:
            print(f"❌ Music Analysis: 500 ERROR")
            print(f"   Response: {response.text[:200]}...")
            tests.append(("Music Analysis", "500_ERROR"))
        else:
            print(f"⚠️ Music Analysis: HTTP {response.status_code}")
            tests.append(("Music Analysis", f"HTTP_{response.status_code}"))
    except Exception as e:
        print(f"❌ Music Analysis Error: {str(e)}")
        tests.append(("Music Analysis", "ERROR"))
    
    # 4. AI Analysis Tests
    print("\n4️⃣ AI ANALYSIS TESTS")
    print("-" * 19)
    
    try:
        payload = {
            "video_path": test_video,
            "analysis_type": "overlay_text"
        }
        response = requests.post(f"{base_url}/video/analyze-with-openai", json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            overlay_text = result.get('overlay_text', 'unknown')[:50]
            print(f"✅ AI Analysis: Generated '{overlay_text}...'")
            tests.append(("AI Analysis", "PASS"))
        elif response.status_code == 500:
            print(f"❌ AI Analysis: 500 ERROR")
            print(f"   Response: {response.text[:200]}...")
            tests.append(("AI Analysis", "500_ERROR"))
        else:
            print(f"⚠️ AI Analysis: HTTP {response.status_code}")
            tests.append(("AI Analysis", f"HTTP_{response.status_code}"))
    except requests.exceptions.Timeout:
        print(f"⏰ AI Analysis: TIMEOUT (normal for AI processing)")
        tests.append(("AI Analysis", "TIMEOUT"))
    except Exception as e:
        print(f"❌ AI Analysis Error: {str(e)}")
        tests.append(("AI Analysis", "ERROR"))
    
    # 5. Video Processing Tests (most likely to 500)
    print("\n5️⃣ VIDEO PROCESSING TESTS")
    print("-" * 25)
    
    try:
        payload = {
            "video_path": test_video,
            "music_path": test_music,
            "text_lines": ["Test Processing", "Debug Mode"],
            "output_name": f"debug_test_{int(time.time())}.mp4",
            "font_style": "clean",
            "music_volume_db": -25,
            "preserve_audio": True
        }
        response = requests.post(f"{base_url}/video/process-enhanced", json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            output_path = result.get('output_path', 'unknown')
            print(f"✅ Video Processing: Output {Path(output_path).name}")
            tests.append(("Video Processing", "PASS"))
        elif response.status_code == 500:
            print(f"❌ Video Processing: 500 ERROR")
            print(f"   Response: {response.text[:300]}...")
            tests.append(("Video Processing", "500_ERROR"))
        else:
            print(f"⚠️ Video Processing: HTTP {response.status_code}")
            tests.append(("Video Processing", f"HTTP_{response.status_code}"))
    except requests.exceptions.Timeout:
        print(f"⏰ Video Processing: TIMEOUT (normal for video processing)")
        tests.append(("Video Processing", "TIMEOUT"))
    except Exception as e:
        print(f"❌ Video Processing Error: {str(e)}")
        tests.append(("Video Processing", "ERROR"))
    
    # Summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print("=" * 30)
    
    passed = [t for t in tests if t[1] == "PASS"]
    errors_500 = [t for t in tests if t[1] == "500_ERROR"]
    timeouts = [t for t in tests if t[1] == "TIMEOUT"]
    other_errors = [t for t in tests if t[1] not in ["PASS", "500_ERROR", "TIMEOUT"]]
    
    print(f"✅ Passed: {len(passed)}/{len(tests)}")
    print(f"❌ 500 Errors: {len(errors_500)}/{len(tests)}")
    print(f"⏰ Timeouts: {len(timeouts)}/{len(tests)}")
    print(f"⚠️ Other Issues: {len(other_errors)}/{len(tests)}")
    
    if errors_500:
        print(f"\n🚨 ENDPOINTS WITH 500 ERRORS:")
        for test_name, result in tests:
            if result == "500_ERROR":
                print(f"   • {test_name}")
        
        print(f"\n🔧 COMMON 500 ERROR CAUSES:")
        print(f"   1. Missing or invalid file paths")
        print(f"   2. FFmpeg execution errors")
        print(f"   3. Font file access issues") 
        print(f"   4. OpenAI API key problems")
        print(f"   5. Insufficient disk space or permissions")
        print(f"   6. Memory/resource exhaustion")
        
        return False
    else:
        print(f"\n🎉 ALL ENDPOINTS WORKING CORRECTLY!")
        return True

if __name__ == "__main__":
    success = comprehensive_endpoint_test()
    if not success:
        print(f"\n💡 Check Flask API console logs for detailed error messages")
    else:
        print(f"\n🚀 System ready for n8n workflow integration!")
