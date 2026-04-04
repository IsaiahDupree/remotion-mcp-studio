#!/usr/bin/env python3

import requests
import json
import time

def test_all_endpoints():
    """Test all API endpoints to identify 500 errors"""
    
    print("🔍 DEBUGGING 500 ERRORS - ENDPOINT TESTING")
    print("=" * 55)
    
    base_url = "http://localhost:5001"
    
    # Test endpoints with their expected methods and payloads
    endpoints = [
        {
            "name": "System Status",
            "method": "GET",
            "url": f"{base_url}/system/status",
            "payload": None
        },
        {
            "name": "Font List", 
            "method": "GET",
            "url": f"{base_url}/fonts/list",
            "payload": None
        },
        {
            "name": "Music Search",
            "method": "POST", 
            "url": f"{base_url}/music/search",
            "payload": {"query": "electronic", "limit": 5}
        },
        {
            "name": "Font Test",
            "method": "POST",
            "url": f"{base_url}/fonts/test", 
            "payload": {
                "text": "Test Font Selection",
                "video_path": "c:/Users/Isaia/Documents/Coding/N8N/shared/videos/1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
            }
        },
        {
            "name": "Music Analysis",
            "method": "POST",
            "url": f"{base_url}/analyze-music-match",
            "payload": {
                "video_path": "c:/Users/Isaia/Documents/Coding/N8N/shared/videos/1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4",
                "transcript": "test video content",
                "visual_analysis": "general video content"
            }
        },
        {
            "name": "OpenAI Video Analysis",
            "method": "POST", 
            "url": f"{base_url}/video/analyze-with-openai",
            "payload": {
                "video_path": "c:/Users/Isaia/Documents/Coding/N8N/shared/videos/1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4",
                "analysis_type": "overlay_text"
            }
        },
        {
            "name": "Enhanced Video Processing",
            "method": "POST",
            "url": f"{base_url}/video/process-enhanced", 
            "payload": {
                "video_path": "c:/Users/Isaia/Documents/Coding/N8N/shared/videos/1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4",
                "music_path": "c:/Users/Isaia/Documents/Coding/N8N/soundcloud_music/04collective - Rusherz - Before You Go.mp3",
                "text_lines": ["Error Test", "Debug Mode"],
                "output_name": "debug_test.mp4",
                "font_style": "clean",
                "music_volume_db": -25
            }
        }
    ]
    
    results = {}
    
    for endpoint in endpoints:
        print(f"\n🔍 Testing: {endpoint['name']}")
        print(f"   {endpoint['method']} {endpoint['url']}")
        
        try:
            start_time = time.time()
            
            if endpoint['method'] == 'GET':
                response = requests.get(endpoint['url'], timeout=15)
            else:
                response = requests.post(endpoint['url'], 
                                      json=endpoint['payload'], 
                                      timeout=15)
                                      
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS: {response.status_code} ({response_time:.1f}s)")
                results[endpoint['name']] = 'SUCCESS'
                
            elif response.status_code == 500:
                print(f"   ❌ 500 ERROR: Internal Server Error ({response_time:.1f}s)")
                print(f"   📄 Response: {response.text[:300]}...")
                results[endpoint['name']] = '500_ERROR'
                
            else:
                print(f"   ⚠️  HTTP {response.status_code}: ({response_time:.1f}s)")
                print(f"   📄 Response: {response.text[:200]}...")
                results[endpoint['name']] = f'HTTP_{response.status_code}'
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ TIMEOUT: Request took longer than 15s")
            results[endpoint['name']] = 'TIMEOUT'
            
        except requests.exceptions.ConnectionError:
            print(f"   🔌 CONNECTION ERROR: Cannot reach API")
            results[endpoint['name']] = 'CONNECTION_ERROR'
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)[:100]}...")
            results[endpoint['name']] = 'ERROR'
    
    # Summary
    print(f"\n📊 ENDPOINT TEST SUMMARY")
    print("=" * 30)
    
    success_count = len([r for r in results.values() if r == 'SUCCESS'])
    error_500_count = len([r for r in results.values() if r == '500_ERROR'])
    total = len(results)
    
    print(f"✅ Successful: {success_count}/{total}")
    print(f"❌ 500 Errors: {error_500_count}/{total}")
    print(f"⚠️  Other Issues: {total - success_count - error_500_count}/{total}")
    
    if error_500_count > 0:
        print(f"\n🚨 500 ERRORS DETECTED:")
        for name, result in results.items():
            if result == '500_ERROR':
                print(f"   • {name}")
                
        print(f"\n🔧 TROUBLESHOOTING STEPS:")
        print(f"   1. Check Flask API logs for detailed error messages")
        print(f"   2. Verify all file paths exist and are accessible")
        print(f"   3. Check FFmpeg installation and PATH")
        print(f"   4. Verify OpenAI API key configuration")
        print(f"   5. Check disk space and permissions")
        
    else:
        print(f"\n🎉 All endpoints working correctly!")
    
    return results

if __name__ == "__main__":
    test_all_endpoints()
