#!/usr/bin/env python3
"""
Test script for enhanced text features:
- Dynamic text sizing based on video dimensions
- Custom font support (Sunny Spells)
- Smart font selection
- Proper screen fitting

Usage: python test_enhanced_fonts.py
"""

import requests
import json
import time
from pathlib import Path

def test_font_listing():
    """Test the font listing API endpoint"""
    api_url = "http://localhost:5001"
    
    print("📝 Testing Font Listing API")
    print("=" * 40)
    
    try:
        response = requests.get(f"{api_url}/fonts/list")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Font API Success!")
            print(f"📊 Total Fonts: {result['total_fonts']}")
            print(f"✅ Available: {len(result['available_fonts'])}")
            print(f"❌ Missing: {len(result['missing_fonts'])}")
            
            print("\n🎨 Available Fonts by Style:")
            for style, count in result['font_styles'].items():
                print(f"  {style.title()}: {count} fonts")
            
            print("\n📋 Font Details:")
            for font in result['available_fonts']:
                status_icon = "🎨" if font['status'] == 'available' else "💻"
                size_info = f" ({font.get('file_size', 0) // 1024}KB)" if font.get('file_size') else ""
                print(f"  {status_icon} {font['name']} ({font['style']}) {size_info}")
                print(f"      {font['description']}")
            
            if result['missing_fonts']:
                print("\n⚠️ Missing Fonts:")
                for font in result['missing_fonts']:
                    print(f"  ❌ {font['name']} - {font['path']}")
            
            return result
            
        else:
            print(f"❌ Font API Failed (HTTP {response.status_code})")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"💥 Font API Error: {e}")
        return None

def test_enhanced_font_features():
    """Test enhanced text features with new font system"""
    
    # API endpoint
    api_url = "http://localhost:5001"
    
    # Test files - adjust paths as needed
    test_video = "C:/Users/Isaia/Documents/Coding/N8N/shared/videos/1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    test_music = "C:/Users/Isaia/Documents/Coding/N8N/soundcloud_music/04collective - Rusherz - Before You Go.mp3"
    
    print("\n🎨 Testing Enhanced Font Features")
    print("=" * 50)
    
    # First test font listing
    font_info = test_font_listing()
    if not font_info:
        print("❌ Font listing failed, aborting font tests")
        return
    
    # Test different font styles with new fonts
    font_tests = [
        {
            'name': 'Creative Font (Sunny Spells)',
            'text_lines': ['Creative Fun Video!', 'Sunny Spells Font'],
            'font_style': 'creative'
        },
        {
            'name': 'Futuristic Style (Edge of Galaxy)',
            'text_lines': ['SPACE ADVENTURE', 'Edge of Galaxy'],
            'font_style': 'creative'
        },
        {
            'name': 'Bold Mountain King',
            'text_lines': ['MOUNTAIN POWER', 'Strong & Bold'],
            'font_style': 'bold'
        },
        {
            'name': 'Auto Font Selection',
            'text_lines': ['This is fun and creative!', 'Happy celebration time'],
            'font_style': 'auto'  # Should auto-select creative
        },
        {
            'name': 'Clean Rony Siswadi',
            'text_lines': ['Professional Design', 'Modern Clean Look'],
            'font_style': 'clean'
        },
        {
            'name': 'Extra Bold Black Text',
            'text_lines': ['ULTIMATE IMPACT', 'BLACK WEIGHT'],
            'font_style': 'bold'
        },
        {
            'name': 'Long Text Sizing Test',
            'text_lines': ['This is a very long text line to test dynamic sizing with new fonts'],
            'font_style': 'modern'
        }
    ]
    
    # Test each font style
    for i, test in enumerate(font_tests, 1):
        print(f"\n🎬 Test {i}: {test['name']}")
        print(f"Text: {test['text_lines']}")
        print(f"Font Style: {test['font_style']}")
        
        payload = {
            'video_path': test_video,
            'music_path': test_music,
            'text_lines': test['text_lines'],
            'output_name': f"font_test_{i}_{test['font_style']}.mp4",
            'music_volume_db': -25.0,
            'preserve_audio': True,
            'smart_positioning': True,
            'font_style': test['font_style']
        }
        
        try:
            print("⏳ Processing...")
            start_time = time.time()
            
            response = requests.post(
                f"{api_url}/video/process-enhanced",
                json=payload,
                timeout=180  # 3 minutes
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS ({processing_time:.1f}s)")
                print(f"   Output: {result['output_name']}")
                print(f"   Size: {result['file_size_mb']} MB")
                print(f"   Font Style Used: {result['processing_settings']['font_style']}")
                
                # Check if file exists
                output_path = Path(result['output_path'])
                if output_path.exists():
                    print(f"   ✅ File verified: {output_path}")
                else:
                    print(f"   ❌ File missing: {output_path}")
                    
            else:
                print(f"❌ FAILED (HTTP {response.status_code})")
                print(f"   Error: {response.text}")
                
        except requests.exceptions.Timeout:
            print("⏰ TIMEOUT - Processing took too long")
        except Exception as e:
            print(f"💥 ERROR: {e}")
        
        print("-" * 40)
    
    print(f"\n🎉 Enhanced Font Testing Complete!")
    print("Check the output videos to see:")
    print("• Dynamic text sizing based on video dimensions")
    print("• Custom Sunny Spells font in creative style")
    print("• Smart font selection based on text content")
    print("• Proper text fitting within screen bounds")

if __name__ == "__main__":
    test_enhanced_font_features()
