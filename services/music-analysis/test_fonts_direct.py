#!/usr/bin/env python3
"""
Direct font system test
"""

import sys
from pathlib import Path
sys.path.append('.')

from enhanced_video_processor import EnhancedVideoProcessor

def test_font_system():
    """Test the font system directly"""
    
    print("🎨 Testing Font System Directly")
    print("=" * 40)
    
    try:
        processor = EnhancedVideoProcessor()
        fonts = processor.get_available_fonts()
        
        print(f"📊 Found {len(fonts)} fonts:")
        for font in fonts:
            font_path = Path(font['path'])
            exists = font_path.exists() if str(font_path).endswith(('.ttf', '.otf')) else "System Font"
            status = "✅" if (exists == "System Font" or exists) else "❌"
            print(f"  {status} {font['name']} ({font['style']})")
            print(f"      Path: {font['path']}")
            if exists != "System Font":
                print(f"      Exists: {exists}")
        
        # Test font selection
        print("\n🎯 Testing Font Selection:")
        test_cases = [
            ("Creative fun video!", "creative"),
            ("BOLD POWERFUL MESSAGE", "bold"), 
            ("Professional business presentation", "clean"),
            ("Modern design", "modern"),
            ("Auto selection test", "auto")
        ]
        
        for text, style in test_cases:
            selected = processor.select_best_font(text, style)
            print(f"  Text: '{text}' | Style: {style}")
            print(f"    → Selected: {selected['name']} ({selected['style']})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_font_system()
