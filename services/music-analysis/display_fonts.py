#!/usr/bin/env python3

import requests
import json
from pathlib import Path

def display_font_system():
    """Display comprehensive font system status"""
    
    print("🎨 CUSTOM FONT SYSTEM STATUS")
    print("=" * 60)
    
    try:
        # Get font listing
        response = requests.get('http://localhost:5001/fonts/list')
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"📊 Total Fonts Available: {data['total_fonts']}")
            print(f"🎯 Font Styles: {', '.join(data['font_styles'].keys())}")
            print()
            
            # Group fonts by style
            fonts_by_style = {}
            for font in data['available_fonts']:
                style = font['style']
                if style not in fonts_by_style:
                    fonts_by_style[style] = []
                fonts_by_style[style].append(font)
            
            # Display each style group
            style_icons = {
                'creative': '🌟',
                'bold': '💪', 
                'clean': '✨',
                'modern': '🔮'
            }
            
            for style, fonts in fonts_by_style.items():
                icon = style_icons.get(style, '📝')
                print(f"{icon} {style.upper()} FONTS ({len(fonts)} available):")
                
                for font in fonts:
                    status_icon = "✅" if font['status'] == 'available' else "🖥️"
                    size_info = f"({font.get('file_size', 0)//1024}KB)" if font.get('file_size') else "(system)"
                    
                    print(f"   {status_icon} {font['name']} {size_info}")
                    print(f"      📝 {font['description']}")
                    
                    if font['status'] == 'available':
                        font_path = Path(font['path'])
                        if font_path.exists():
                            print(f"      📁 {font_path.name}")
                        else:
                            print(f"      ❌ File not found: {font['path']}")
                    print()
                
            # Missing fonts check
            if data.get('missing_fonts'):
                print("❌ MISSING FONTS:")
                for missing in data['missing_fonts']:
                    print(f"   • {missing}")
            else:
                print("✅ ALL FONTS LOADED SUCCESSFULLY!")
                
            print(f"\n🚀 Font system ready for video processing!")
            return True
            
        else:
            print(f"❌ Failed to get font list: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_font_selection():
    """Test font selection logic"""
    
    print("\n🎯 FONT SELECTION TESTING")
    print("=" * 40)
    
    test_cases = [
        {"text": "Happy Birthday Party!", "expected": "creative"},
        {"text": "POWER UP YOUR BUSINESS", "expected": "bold"},
        {"text": "Professional Services", "expected": "clean"},
        {"text": "General Information", "expected": "modern"}
    ]
    
    for test in test_cases:
        try:
            payload = {"text": test["text"]}
            response = requests.post('http://localhost:5001/fonts/test', json=payload)
            
            if response.status_code == 200:
                result = response.json()
                selected_font = result.get('selected_font', {})
                detected_style = selected_font.get('style', 'unknown')
                
                match_icon = "✅" if detected_style == test["expected"] else "⚠️"
                print(f"{match_icon} '{test['text']}'")
                print(f"   Expected: {test['expected']} | Got: {detected_style}")
                print(f"   Font: {selected_font.get('name', 'unknown')}")
                
            else:
                print(f"❌ Test failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing '{test['text']}': {str(e)}")
    
    return True

if __name__ == "__main__":
    display_font_system()
    test_font_selection()
