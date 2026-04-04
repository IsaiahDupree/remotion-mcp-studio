#!/usr/bin/env python3
"""
Test SoundCloud Download and Video Enhancement
=============================================

This script:
1. Downloads a SoundCloud track using the SoundCloudYtDlp utility
2. Enhances a specific video by adding text overlay and the downloaded music
3. Provides detailed logging of the process

Usage:
    python test_enhance_specific_video.py --soundcloud-url <url>
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import tempfile

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
try:
    from utils.soundcloud_ytdlp import SoundCloudYtDlp
    from video_enhancer import VideoEnhancer
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure the modules are properly installed")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_enhance_video.log")
    ]
)
logger = logging.getLogger("test_enhance")

# Specific video path from the user request
TARGET_VIDEO_PATH = r"C:\Users\Isaia\Documents\N8N\shared_data\copy_E69DC408-5335-401B-8FE1-BB017EECFCFB.MP4"


def download_soundcloud_track(url, output_dir):
    """
    Download a SoundCloud track using SoundCloudYtDlp utility.
    
    Args:
        url: SoundCloud track URL
        output_dir: Directory to save the downloaded track
        
    Returns:
        Path to downloaded track or None if download failed
    """
    logger.info(f"Testing SoundCloud download from URL: {url}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize downloader
    downloader = SoundCloudYtDlp(output_dir=output_dir)
    
    try:
        # Download track
        track_path = downloader.download_track(url)
        
        # Verify download
        if track_path and os.path.exists(track_path):
            logger.info(f"Successfully downloaded track to: {track_path}")
            logger.info(f"File size: {os.path.getsize(track_path)} bytes")
            return track_path
        else:
            logger.error("Failed to download track")
            return None
            
    except Exception as e:
        logger.error(f"Error downloading SoundCloud track: {e}")
        return None


def enhance_video(video_path, music_path, custom_text=None):
    """
    Enhance a video with text overlay and background music.
    
    Args:
        video_path: Path to the video file
        music_path: Path to the music file
        custom_text: Custom text overlay (None for auto-generation)
        
    Returns:
        Path to enhanced video or None if enhancement failed
    """
    logger.info(f"Enhancing video: {video_path}")
    logger.info(f"Using music from: {music_path}")
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), "enhanced_videos")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create output path
    video_basename = os.path.basename(video_path).split('.')[0]
    output_path = os.path.join(output_dir, f"{video_basename}_enhanced.mp4")
    
    # Initialize enhancer
    enhancer = VideoEnhancer(
        output_dir=output_dir,
        speech_emphasis=1.5,
        high_quality=True,
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
    
    try:
        # Enhance video
        result = enhancer.enhance_video(
            video_path=video_path,
            output_path=output_path,
            add_text=True,
            add_music=True,
            custom_text=custom_text,
            music_path=music_path,
            auto_detect_features=True
        )
        
        # Check result
        if result.get("success", False):
            enhanced_path = result.get("output_video")
            logger.info(f"Video enhancement successful")
            logger.info(f"Enhanced video saved to: {enhanced_path}")
            
            # Log details
            if result.get("text_overlay_added", False):
                logger.info(f"Added text overlay: '{result.get('text', 'Unknown')}'")
                
            if result.get("music_added", False):
                logger.info(f"Added background music with speech emphasis: {result.get('speech_emphasis', 1.5)}")
                
            return enhanced_path
        else:
            logger.error(f"Video enhancement failed: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        logger.error(f"Exception during video enhancement: {e}")
        return None


def main():
    """Main function to test SoundCloud download and video enhancement."""
    parser = argparse.ArgumentParser(
        description="Test SoundCloud download and video enhancement"
    )
    parser.add_argument(
        "--soundcloud-url",
        default="https://soundcloud.com/royaltyfreebackgroundmusic/happy-acoustic-guitar-background-music-for-video-royalty-free-music-no-copyright-music",
        help="SoundCloud track URL"
    )
    parser.add_argument(
        "--video",
        default=TARGET_VIDEO_PATH,
        help="Path to the video file"
    )
    parser.add_argument(
        "--text",
        help="Custom text overlay (omit for auto-generation)"
    )
    parser.add_argument(
        "--output-dir",
        default="./downloaded_music",
        help="Directory to save downloaded music"
    )
    
    args = parser.parse_args()
    
    # Check if video exists
    if not os.path.exists(args.video):
        logger.error(f"Video file not found: {args.video}")
        return 1
    
    logger.info("=== Starting SoundCloud Download Test ===")
    
    # Step 1: Download SoundCloud track
    track_path = download_soundcloud_track(args.soundcloud_url, args.output_dir)
    
    if not track_path:
        logger.error("SoundCloud download failed, cannot proceed with video enhancement")
        return 1
        
    logger.info("=== Starting Video Enhancement Test ===")
    
    # Step 2: Enhance video with downloaded music
    enhanced_video = enhance_video(args.video, track_path, args.text)
    
    if not enhanced_video:
        logger.error("Video enhancement failed")
        return 1
        
    logger.info("=== Test Completed Successfully ===")
    logger.info(f"Enhanced video: {enhanced_video}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
