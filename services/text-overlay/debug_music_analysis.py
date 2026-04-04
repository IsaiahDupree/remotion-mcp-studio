#!/usr/bin/env python3
"""
Debug script to test music analysis endpoint directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from music_video_matcher import MusicVideoMatcher
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_music_analysis():
    """Test the music analysis logic directly"""
    
    try:
        # Initialize the matcher
        logger.info("🔧 Initializing MusicVideoMatcher...")
        matcher = MusicVideoMatcher()
        
        # Test video file
        video_filename = "v12044gd0000cu2t04nog65p7djql4g0.MP4"
        video_path = os.path.join(r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos", video_filename)
        
        logger.info(f"📹 Testing video: {video_path}")
        logger.info(f"📁 Video exists: {os.path.exists(video_path)}")
        
        # Test the analysis
        logger.info("🎵 Running music compatibility analysis...")
        result = matcher.analyze_music_compatibility(video_path)
        
        logger.info(f"✅ Analysis completed successfully!")
        logger.info(f"📊 Result type: {type(result)}")
        logger.info(f"📊 Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in music analysis: {str(e)}")
        logger.error(f"❌ Error type: {type(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    result = test_music_analysis()
    print(f"\n🎯 Final result: {result}")
