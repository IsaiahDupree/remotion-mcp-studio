#!/usr/bin/env python3
"""
Test Music-Video Matching System
===============================

Test script to demonstrate the intelligent music-video matching capabilities.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from music_video_matcher import MusicVideoMatcher

def test_music_video_matching():
    """Test the music-video matching system"""
    print("🎭 Testing Music-Video Matching System")
    print("=" * 50)
    
    # Initialize the matcher
    try:
        matcher = MusicVideoMatcher()
        print("✅ MusicVideoMatcher initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing matcher: {e}")
        return False
    
    # Find test videos
    video_dir = Path("C:/Users/Isaia/Documents/Coding/N8N/shared/videos")
    if not video_dir.exists():
        print("⚠️ Video directory not found, creating sample test")
        return test_sample_matching(matcher)
    
    # Get a few small videos for testing
    video_files = [f for f in video_dir.glob("*.mp4") if f.stat().st_size < 100 * 1024 * 1024]  # Under 100MB
    
    if not video_files:
        print("⚠️ No suitable test videos found")
        return test_sample_matching(matcher)
    
    # Test with first video
    test_video = video_files[0]
    print(f"\n🎬 Testing with: {test_video.name} ({test_video.stat().st_size / 1024 / 1024:.1f} MB)")
    
    try:
        # Step 1: Analyze video context
        print("\n📋 Step 1: Analyzing video context...")
        video_context = matcher.analyze_video_context(str(test_video))
        print(f"   ✅ Content Type: {video_context.content_type}")
        print(f"   ✅ Visual Mood: {video_context.visual_mood}")
        print(f"   ✅ Energy Level: {video_context.energy_level}")
        print(f"   ✅ Themes: {video_context.themes}")
        print(f"   ✅ Duration: {video_context.duration:.1f}s")
        
        # Step 2: Test music analysis
        print("\n🎵 Step 2: Analyzing music library...")
        if matcher.music_selector.music_index:
            sample_music = matcher.music_selector.music_index[0]
            music_context = matcher.analyze_music_context(
                sample_music['file'],
                sample_music['name'], 
                sample_music['genre']
            )
            print(f"   ✅ Sample Music: {music_context.name}")
            print(f"   ✅ Mood: {music_context.mood}")
            print(f"   ✅ Energy: {music_context.energy_level}")
            print(f"   ✅ Themes: {music_context.themes}")
        else:
            print("   ⚠️ No music tracks available")
            return False
        
        # Step 3: Create match index (this will take some time)
        print(f"\n🔄 Step 3: Creating music match index for {test_video.name}...")
        print("   (This may take a few minutes as we analyze each music track...)")
        
        matches = matcher.create_match_index_for_video(str(test_video))
        
        if matches:
            print(f"   ✅ Created {len(matches)} music matches")
            
            # Show top 3 matches
            print(f"\n🏆 Top 3 Music Matches:")
            for i, match in enumerate(matches[:3]):
                print(f"   #{i+1}: {Path(match.music_path).name}")
                print(f"        Score: {match.compatibility_score:.2f}/1.0")
                print(f"        Mood: {match.mood_match} | Energy: {match.energy_match}")
                print(f"        Reason: {match.reasoning[:60]}...")
        else:
            print("   ❌ No matches created")
            return False
        
        # Step 4: Test best music selection
        print(f"\n🎯 Step 4: Getting best music recommendation...")
        best_music = matcher.get_best_music_for_video(str(test_video), min_score=0.6)
        
        if best_music:
            print(f"   ✅ Best Match: {Path(best_music).name}")
        else:
            print("   ⚠️ No music meets minimum compatibility score")
        
        # Step 5: Generate detailed report
        print(f"\n📊 Step 5: Generating detailed match report...")
        matcher.print_match_report(str(test_video))
        
        print(f"\n🎉 Music-Video matching test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def test_sample_matching(matcher):
    """Test with sample data when no videos available"""
    print("\n📝 Running sample matching test...")
    
    try:
        # Test music analysis only
        if matcher.music_selector.music_index:
            music_track = matcher.music_selector.music_index[0]
            print(f"\n🎵 Analyzing sample music: {music_track['name']}")
            
            music_context = matcher.analyze_music_context(
                music_track['file'],
                music_track['name'],
                music_track['genre']
            )
            
            print(f"   ✅ Genre: {music_context.genre}")
            print(f"   ✅ Mood: {music_context.mood}")
            print(f"   ✅ Energy: {music_context.energy_level}")
            print(f"   ✅ Tempo: {music_context.tempo}")
            print(f"   ✅ Themes: {music_context.themes}")
            
            print("\n✅ Sample music analysis completed")
            return True
        else:
            print("❌ No music tracks available for testing")
            return False
            
    except Exception as e:
        print(f"❌ Error in sample test: {e}")
        return False

def demonstrate_integration():
    """Demonstrate how to integrate with enhanced video processor"""
    print("\n🔗 Integration with Enhanced Video Processor")
    print("=" * 50)
    
    integration_code = '''
# Example integration code:

from music_video_matcher import MusicVideoMatcher
from enhanced_video_processor import EnhancedVideoProcessor

# Initialize systems
matcher = MusicVideoMatcher()
processor = EnhancedVideoProcessor()

# Process video with intelligent music selection
def process_video_with_smart_music(video_path, output_path):
    # Get best music match
    best_music = matcher.get_best_music_for_video(video_path, min_score=0.7)
    
    if best_music:
        print(f"Using AI-selected music: {best_music}")
        
        # Process with selected music
        result = processor.process_video(
            video_path=video_path,
            output_path=output_path,
            music_path=best_music,
            use_ai_music_selection=True
        )
    else:
        print("No suitable music found, using random selection")
        result = processor.process_video(video_path, output_path)
    
    return result
'''
    
    print(integration_code)
    print("💡 This shows how the intelligent matching integrates with video processing")

if __name__ == "__main__":
    print("🎭🎵 Music-Video Matching Test Suite")
    print("===================================")
    
    # Test the matching system
    success = test_music_video_matching()
    
    # Show integration example
    demonstrate_integration()
    
    # Summary
    print(f"\n📊 Test Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        print("\n🚀 The intelligent music-video matching system is ready!")
        print("Key features:")
        print("  • GPT-4o powered video context analysis")
        print("  • Intelligent music mood/energy analysis") 
        print("  • Compatibility scoring and ranking")
        print("  • Cached analysis for performance")
        print("  • Integration ready for video processing")
    else:
        print("\n⚠️ Some issues detected. Check the error messages above.")
