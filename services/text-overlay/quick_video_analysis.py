#!/usr/bin/env python3
"""
Quick Video Analysis for Specific File
=====================================

Quick analysis of the user's specific video to demonstrate the intelligent matching system.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def analyze_specific_video():
    """Analyze the specific video and show music compatibility"""
    
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\v12044gd0000cu2t04nog65p7djql4g0.MP4"
    
    print("🎬 Quick Video Analysis Demo")
    print("=" * 35)
    print(f"📹 Video: {Path(video_path).name}")
    
    try:
        # Initialize matcher
        from music_video_matcher import MusicVideoMatcher
        
        print("🤖 Initializing AI Music Matcher...")
        matcher = MusicVideoMatcher()
        
        # Step 1: Analyze video context
        print(f"\n📋 Step 1: Analyzing video content...")
        video_context = matcher.analyze_video_context(video_path)
        
        print(f"✅ Video Analysis Complete:")
        print(f"   Content Type: {video_context.content_type}")
        print(f"   Visual Mood: {video_context.visual_mood}")
        print(f"   Energy Level: {video_context.energy_level}")
        print(f"   Themes: {', '.join(video_context.themes)}")
        print(f"   Duration: {video_context.duration:.1f} seconds")
        
        # Step 2: Check available music
        print(f"\n🎵 Step 2: Checking music library...")
        if matcher.music_selector.music_index:
            print(f"✅ Found {len(matcher.music_selector.music_index)} music tracks")
            
            # Show first few tracks
            print(f"📚 Sample tracks:")
            for i, track in enumerate(matcher.music_selector.music_index[:3]):
                print(f"   {i+1}. {track['name']} ({track['genre']})")
            
            # Step 3: Find best music match
            print(f"\n🎯 Step 3: Finding optimal music match...")
            best_music = matcher.get_best_music_for_video(video_path, min_score=0.5)
            
            if best_music:
                print(f"✅ Best Match Found: {Path(best_music).name}")
                
                # Get detailed match info
                matches = matcher.create_match_index_for_video(video_path)
                if matches:
                    top_match = matches[0]
                    print(f"🏆 Match Details:")
                    print(f"   Compatibility Score: {top_match.compatibility_score:.2f}/1.0")
                    print(f"   Mood Match: {top_match.mood_match}")
                    print(f"   Energy Match: {top_match.energy_match}")
                    print(f"   Reasoning: {top_match.reasoning}")
            else:
                print("⚠️ No music meets minimum compatibility threshold")
                
        else:
            print("❌ No music tracks found in library")
            
        print(f"\n✅ Analysis complete! The AI system has:")
        print(f"   • Analyzed your video's visual content and mood")
        print(f"   • Evaluated all available music tracks for compatibility")
        print(f"   • Selected the best matching background music")
        print(f"   • Ready to enhance your video with intelligent music selection!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return False

if __name__ == "__main__":
    success = analyze_specific_video()
    
    if success:
        print(f"\n🚀 Ready to process your video with intelligent music matching!")
    else:
        print(f"\n⚠️ Analysis failed. Check error messages above.")
