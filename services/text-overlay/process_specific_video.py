#!/usr/bin/env python3
"""
Process Specific Video with Intelligent Music Matching
=====================================================

Process the user's specific video with AI-powered music selection and enhanced features.
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from smart_video_processor import SmartVideoProcessor

def process_user_video():
    """Process the specific video with intelligent music matching"""
    
    # Video path
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\v12044gd0000cu2t04nog65p7djql4g0.MP4"
    
    # Output path
    output_path = r"C:\Users\Isaia\Documents\WordsOnText\enhanced_videos\v12044gd0000cu2t04nog65p7djql4g0_smart_enhanced.mp4"
    
    print("🎬 Processing Specific Video with Intelligent Music Matching")
    print("=" * 65)
    print(f"📹 Input Video: {Path(video_path).name}")
    print(f"💾 Output Path: {Path(output_path).name}")
    
    # Check if video exists
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    # Get video file info
    video_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
    print(f"📊 Video Size: {video_size:.1f} MB")
    
    try:
        # Initialize smart processor
        print(f"\n🚀 Initializing Smart Video Processor...")
        processor = SmartVideoProcessor(
            use_intelligent_matching=True,
            fallback_to_random=True,
            min_compatibility_score=0.6,  # Lower threshold for better chance of matching
            cache_analyses=True
        )
        
        # Step 1: Generate music compatibility report
        print(f"\n📊 Step 1: Generating Music Compatibility Report...")
        print("   (This will analyze the video content and all available music tracks)")
        
        report = processor.get_music_compatibility_report(video_path)
        
        if report.get('error'):
            print(f"   ❌ Error generating report: {report['error']}")
        else:
            print(f"   ✅ Analysis Complete!")
            print(f"   📋 Video Content Type: {report['video_context']['content_type']}")
            print(f"   🎭 Visual Mood: {report['video_context']['visual_mood']}")
            print(f"   ⚡ Energy Level: {report['video_context']['energy_level']}")
            print(f"   🏷️ Themes: {', '.join(report['video_context']['themes'])}")
            print(f"   ⏱️ Duration: {report['video_context']['duration']:.1f}s")
            
            print(f"\n🎵 Music Analysis Results:")
            print(f"   📚 Total Music Options: {report['total_music_options']}")
            print(f"   🏆 Recommendation: {report['recommendation']}")
            
            if report['top_matches']:
                print(f"\n🥇 Top 3 Music Matches:")
                for i, match in enumerate(report['top_matches'][:3]):
                    print(f"   #{i+1}: {match['music_name']}")
                    print(f"        Score: {match['compatibility_score']:.2f}/1.0")
                    print(f"        Mood: {match['mood_match']} | Energy: {match['energy_match']}")
                    print(f"        Reason: {match['reasoning'][:80]}...")
        
        # Step 2: Process with intelligent music selection
        print(f"\n🎬 Step 2: Processing Video with Smart Music Selection...")
        print("   (This will enhance the video with AI-selected music and features)")
        
        # Configure processing options
        config = {
            'use_smart_music': True,
            'text_style': 'modern',
            'text_position': 'bottom',
            'music_volume': 0.04,  # -28dB optimized volume
            'frame_analysis_interval': 30.0,
            'preserve_resolution': True,
            'detect_existing_music': True
        }
        
        # Process the video
        result = processor.process_video_with_smart_music(
            video_path=video_path,
            output_path=output_path,
            config=config
        )
        
        # Display results
        print(f"\n📊 Processing Results:")
        if result.get('success', False):
            print(f"   ✅ Processing Status: SUCCESS")
            print(f"   🎵 Music Used: {Path(result.get('selected_music', 'None')).name if result.get('selected_music') else 'None'}")
            print(f"   🎯 Selection Method: {result.get('music_selection_method', 'Unknown')}")
            print(f"   ⏱️ Processing Time: {result.get('processing_time_seconds', 0):.1f}s")
            
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / (1024 * 1024)
                print(f"   📁 Output Size: {output_size:.1f} MB")
                print(f"   📄 Output File: {output_path}")
            
            print(f"\n🎉 Video successfully processed with intelligent music matching!")
            return True
        else:
            print(f"   ❌ Processing Status: FAILED")
            print(f"   🚨 Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing video: {e}")
        return False

def quick_music_preview():
    """Show a quick preview of what music tracks are available"""
    print(f"\n🎵 Available Music Preview")
    print("=" * 30)
    
    try:
        from local_music_selector import LocalMusicSelector
        
        selector = LocalMusicSelector()
        stats = selector.get_stats()
        
        print(f"📚 Music Library Stats:")
        print(f"   Total Tracks: {stats['total_tracks']}")
        print(f"   Total Size: {stats['total_size_mb']:.1f} MB")
        print(f"   Genres: {len(stats['genres'])} different genres")
        
        # Show some sample tracks
        if selector.music_index:
            print(f"\n🎼 Sample Tracks:")
            for i, track in enumerate(selector.music_index[:5]):
                print(f"   {i+1}. {track['name']} ({track['genre']})")
                
    except Exception as e:
        print(f"⚠️ Could not load music library: {e}")

if __name__ == "__main__":
    print("🎭🎵 Intelligent Video Processing Demo")
    print("=====================================")
    
    # Show music preview
    quick_music_preview()
    
    # Process the specific video
    success = process_user_video()
    
    # Final summary
    print(f"\n📊 Final Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        print(f"\n🚀 Your video has been enhanced with:")
        print(f"   • AI-analyzed video content for optimal music matching")
        print(f"   • Context-aware background music selection")
        print(f"   • Enhanced text overlays with frame analysis")
        print(f"   • Optimized audio levels (-25 to -30dB background music)")
        print(f"   • Resolution preservation throughout processing")
    else:
        print(f"\n⚠️ Processing failed. Check the error messages above.")
        print(f"💡 You may need to:")
        print(f"   • Ensure the video file is accessible")
        print(f"   • Check that your music library is properly indexed")
        print(f"   • Verify your OpenAI API key is working")
