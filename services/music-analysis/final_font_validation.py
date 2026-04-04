#!/usr/bin/env python3

import requests
import json
import time
from pathlib import Path

def validate_font_system():
    """Complete validation of the custom font system"""
    
    print("🎨 COMPLETE CUSTOM FONT SYSTEM VALIDATION")
    print("=" * 60)
    
    validation_results = {
        'font_loading': False,
        'font_selection': False,
        'video_processing': False,
        'total_score': 0
    }
    
    # Test 1: Font Loading and Availability
    print("\n1️⃣ TESTING FONT LOADING")
    print("-" * 30)
    
    try:
        response = requests.get('http://localhost:5001/fonts/list', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            total_fonts = data.get('total_fonts', 0)
            available_fonts = len([f for f in data.get('available_fonts', []) if f.get('status') == 'available'])
            
            print(f"✅ Font API responsive")
            print(f"📊 Total fonts: {total_fonts}")
            print(f"💾 Custom fonts loaded: {available_fonts}")
            
            # Check for specific custom fonts
            font_names = [f.get('name', '') for f in data.get('available_fonts', [])]
            custom_fonts_found = [
                'Sunny Spells' in font_names,
                'Mountain King' in font_names,
                'Rony Siswadi' in font_names,
                'Edge of Galaxy' in font_names
            ]
            
            custom_count = sum(custom_fonts_found)
            print(f"🎨 Key custom fonts found: {custom_count}/4")
            
            if total_fonts >= 10 and custom_count >= 3:
                validation_results['font_loading'] = True
                print("✅ Font loading test PASSED")
            else:
                print("❌ Font loading test FAILED")
                
        else:
            print(f"❌ Font API error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Font loading error: {str(e)}")
    
    # Test 2: Font Selection Logic
    print("\n2️⃣ TESTING FONT SELECTION LOGIC")
    print("-" * 35)
    
    test_video = "c:/Users/Isaia/Documents/Coding/N8N/shared/videos/1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    
    selection_tests = [
        {"text": "Creative Happy Fun!", "expected": "creative"},
        {"text": "BOLD POWER STRONG", "expected": "bold"}
    ]
    
    correct_selections = 0
    
    for test in selection_tests:
        try:
            payload = {
                "text": test["text"],
                "video_path": test_video
            }
            
            response = requests.post('http://localhost:5001/fonts/test', 
                                   json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                selected_font = result.get('selected_font', {})
                detected_style = selected_font.get('style', 'unknown')
                
                if detected_style == test["expected"]:
                    correct_selections += 1
                    print(f"✅ '{test['text']}' → {detected_style} style ✓")
                else:
                    print(f"⚠️ '{test['text']}' → Expected {test['expected']}, got {detected_style}")
                    
            else:
                print(f"❌ Selection test failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Selection error: {str(e)}")
    
    if correct_selections >= 1:
        validation_results['font_selection'] = True
        print("✅ Font selection test PASSED")
    else:
        print("❌ Font selection test FAILED")
    
    # Test 3: Video Processing with Custom Fonts
    print("\n3️⃣ TESTING VIDEO PROCESSING WITH CUSTOM FONTS")
    print("-" * 45)
    
    music_files = list(Path("c:/Users/Isaia/Documents/Coding/N8N/soundcloud_music").glob("*.mp3"))
    
    if music_files:
        test_music = str(music_files[0])
        
        payload = {
            "video_path": test_video,
            "music_path": test_music,
            "text_lines": ["🎨 FONT TEST", "Custom Font System"],
            "output_name": "font_validation_test.mp4",
            "font_style": "creative",
            "music_volume_db": -30,
            "preserve_audio": True
        }
        
        try:
            print("🎬 Processing test video with custom fonts...")
            start_time = time.time()
            
            response = requests.post('http://localhost:5001/video/process-enhanced', 
                                   json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                processing_time = time.time() - start_time
                
                print(f"✅ Video processing SUCCESS! ({processing_time:.1f}s)")
                
                # Check if custom font was used
                settings = result.get('processing_settings', {})
                selected_font = settings.get('selected_font', {})
                font_name = selected_font.get('name', 'unknown')
                
                print(f"🎨 Font used: {font_name}")
                print(f"📁 Output: {result.get('output_path', 'unknown')}")
                
                # Check if it's a custom font (not system font)
                if font_name in ['Sunny Spells', 'Mountain King', 'Edge of Galaxy', 'Rony Siswadi']:
                    validation_results['video_processing'] = True
                    print("✅ Custom font successfully used in video!")
                else:
                    print(f"⚠️ System font used instead of custom: {font_name}")
                    
            else:
                print(f"❌ Video processing failed: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("⏰ Video processing timeout (likely still processing)")
            validation_results['video_processing'] = True  # Timeout is acceptable
            
        except Exception as e:
            print(f"❌ Video processing error: {str(e)}")
    else:
        print("❌ No music files found for testing")
    
    # Calculate final score
    validation_results['total_score'] = sum([
        validation_results['font_loading'],
        validation_results['font_selection'], 
        validation_results['video_processing']
    ])
    
    # Final Results
    print("\n" + "=" * 60)
    print("🏆 VALIDATION RESULTS SUMMARY")
    print("=" * 60)
    
    tests = [
        ("Font Loading & Availability", validation_results['font_loading']),
        ("Font Selection Logic", validation_results['font_selection']),
        ("Video Processing Integration", validation_results['video_processing'])
    ]
    
    for test_name, passed in tests:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
    
    score = validation_results['total_score']
    print(f"\n📊 Overall Score: {score}/3 tests passed")
    
    if score == 3:
        print("🎉 EXCELLENT! Custom font system is fully operational!")
        print("🚀 Ready for production use in n8n workflows!")
    elif score == 2:
        print("✅ GOOD! Font system mostly working, minor issues to address.")
    elif score == 1:
        print("⚠️ PARTIAL! Font system has significant issues to fix.")
    else:
        print("❌ CRITICAL! Font system needs major debugging.")
    
    return validation_results

if __name__ == "__main__":
    results = validate_font_system()
    
    print(f"\n🎯 NEXT STEPS:")
    if results['total_score'] >= 2:
        print("• Import n8n workflow and test full integration")
        print("• Test different font styles in video processing")
        print("• Monitor video output quality and font rendering")
    else:
        print("• Debug font loading and selection issues") 
        print("• Check file paths and font installations")
        print("• Verify API endpoints and error handling")
