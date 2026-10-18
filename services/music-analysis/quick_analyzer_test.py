#!/usr/bin/env python3
"""
Quick Intelligent Video Analyzer Test
"""
import os
from pathlib import Path

def quick_test():
    """Quick test of core analyzer functionality"""
    print("🔬 QUICK INTELLIGENT VIDEO ANALYZER TEST")
    print("=" * 45)
    
    try:
        from intelligent_video_analyzer import IntelligentVideoAnalyzer
        
        video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
        
        if not Path(video_path).exists():
            print(f"❌ Test video not found")
            return False
        
        print(f"🎬 Video: {Path(video_path).name}")
        
        # Initialize analyzer
        analyzer = IntelligentVideoAnalyzer()
        print("✅ Analyzer initialized")
        
        # Quick video info test
        video_info = analyzer.get_video_info(video_path)
        print(f"📹 Video Info: {video_info.get('width')}x{video_info.get('height')}, {video_info.get('duration', 0):.1f}s")
        
        # Quick caption detection test
        has_captions, _ = analyzer.detect_existing_captions(video_path)
        print(f"🔍 Captions: {'Found' if has_captions else 'None detected'}")
        
        # Quick frame sampling test
        frames = analyzer.sample_frames_efficiently(video_path, video_info)
        print(f"📸 Frame sampling: {len(frames)} frames sampled")
        
        # Quick overlay generation test
        overlay = analyzer.generate_perfect_overlay(None, None, video_info)
        print(f"✨ Generated overlay: \"{overlay}\"")
        
        print(f"\n🎯 CORE FUNCTIONALITY: WORKING!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n🚀 INTELLIGENT ANALYZER READY FOR API INTEGRATION!")
    else:
        print("\n⚠️ Need to check dependencies")
