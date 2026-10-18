#!/usr/bin/env python3

import requests
import json

def test_font_selection():
    """Test the intelligent font selection system"""
    
    print("🎯 TESTING FONT SELECTION LOGIC")
    print("=" * 50)
    
    # Use a test video file for font testing
    test_video = "c:/Users/Isaia/Documents/Coding/N8N/shared/videos/1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    
    test_cases = [
        {
            "text": "Happy Birthday Party Fun!",
            "expected_style": "creative",
            "description": "Should detect creative keywords"
        },
        {
            "text": "POWER UP YOUR STRENGTH",
            "expected_style": "bold", 
            "description": "Should detect bold keywords"
        },
        {
            "text": "Professional Business Services",
            "expected_style": "clean",
            "description": "Should detect clean/professional keywords"
        },
        {
            "text": "General information display",
            "expected_style": "modern",
            "description": "Should default to modern for general text"
        }
    ]
    
    success_count = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test['text']}")
        print(f"   Expected: {test['expected_style']} style")
        
        try:
            payload = {
                "text": test["text"],
                "video_path": test_video
            }
            response = requests.post('http://localhost:5001/fonts/test', 
                                   json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                selected_font = result.get('selected_font', {})
                detected_style = selected_font.get('style', 'unknown')
                font_name = selected_font.get('name', 'unknown')
                
                if detected_style == test['expected_style']:
                    print(f"   ✅ CORRECT! Detected {detected_style} style")
                    print(f"   🎨 Selected font: {font_name}")
                    success_count += 1
                else:
                    print(f"   ⚠️  Expected {test['expected_style']}, got {detected_style}")
                    print(f"   🎨 Selected font: {font_name}")
                    
            else:
                print(f"   ❌ API Error: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print(f"\n📊 RESULTS:")
    print(f"✅ Correct predictions: {success_count}/{len(test_cases)}")
    print(f"🎯 Accuracy: {(success_count/len(test_cases)*100):.1f}%")
    
    if success_count >= 3:
        print("🚀 Font selection system working excellently!")
        return True
    else:
        print("⚠️  Font selection needs tuning")
        return False

if __name__ == "__main__":
    test_font_selection()
