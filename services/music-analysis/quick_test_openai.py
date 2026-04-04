#!/usr/bin/env python3
"""
Quick Test for OpenAI Integration
"""
import requests
import json
import os

def test_openai_simple():
    """Simple test of OpenAI endpoint with minimal data"""
    
    url = "http://localhost:5001/video/analyze-with-openai"
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    
    test_data = {
        "video_path": video_path,
        "use_openai": True
    }
    
    print(f"🔗 Testing: {url}")
    print(f"📹 Video: {os.path.basename(video_path)}")
    
    try:
        response = requests.post(url, json=test_data, timeout=60)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS!")
            print(f"🎯 Overlay: '{result.get('suggested_overlay', 'N/A')}'")
            print(f"🤖 Used OpenAI: {result.get('used_openai_analysis', False)}")
            print(f"⏰ Time: {result.get('processing_time', 0):.1f}s")
        else:
            print(f"❌ FAILED: {response.status_code}")
            try:
                error = response.json()
                print(f"Error: {error}")
            except:
                print(f"Error: {response.text[:200]}")
                
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_openai_simple()
