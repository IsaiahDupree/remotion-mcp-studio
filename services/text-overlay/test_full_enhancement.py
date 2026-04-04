#!/usr/bin/env python3
"""
Full Video Enhancement Test
=========================

This script:
1. Sets the OpenAI API key in the environment
2. Reads SoundCloud URLs from the Excel file
3. Downloads a SoundCloud track using the SoundCloudYtDlp utility
4. Enhances a specific video by adding text overlay and the downloaded music
5. Provides detailed logging of the process

Usage:
    python test_full_enhancement.py
"""

import os
import sys
import logging
import pandas as pd
import random
import tempfile
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# OpenAI API key should be set via environment variable
# os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

# Import required modules
try:
    from utils.soundcloud_ytdlp import SoundCloudYtDlp
    from video_enhancer import VideoEnhancer
    from video_enhancer.text_styler import Style, Position
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
        logging.FileHandler("test_full_enhancement.log")
    ]
)
logger = logging.getLogger("test_enhance")

# Specific video path from the user request
TARGET_VIDEO_PATH = r"C:\Users\Isaia\Documents\N8N\shared_data\copy_E69DC408-5335-401B-8FE1-BB017EECFCFB.MP4"
EXCEL_FILE_PATH = r"C:\Users\Isaia\Documents\WordsOnText\data\SoundCloud to X Reposter.xlsx"


def get_soundcloud_url_from_excel(excel_path):
    """Get a random SoundCloud URL from the Excel file."""
    try:
        # Read the Excel file
        df = pd.read_excel(excel_path)
        
        # Find columns that might contain SoundCloud URLs
        soundcloud_urls = []
        
        # Search through all columns for SoundCloud URLs
        for column in df.columns:
            column_values = df[column].astype(str)
            soundcloud_links = [
                url for url in column_values 
                if isinstance(url, str) and 'soundcloud.com' in url.lower()
            ]
            soundcloud_urls.extend(soundcloud_links)
        
        # Filter out invalid URLs
        valid_urls = [url for url in soundcloud_urls if url and isinstance(url, str) and url.startswith('http')]
        
        if not valid_urls:
            logger.warning("No valid SoundCloud URLs found in Excel file.")
            return None
        
        # Return a random URL
        random_url = random.choice(valid_urls)
        logger.info(f"Selected random SoundCloud URL: {random_url}")
        return random_url
        
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        return None


def download_music(soundcloud_url=None):
    """Download music from SoundCloud or use a previously downloaded track."""
    # Create output directory for downloaded music
    download_dir = os.path.join(os.path.dirname(__file__), "downloaded_music")
    os.makedirs(download_dir, exist_ok=True)
    
    # Check for existing music files
    existing_music = [
        os.path.join(download_dir, f) for f in os.listdir(download_dir)
        if f.endswith(('.mp3', '.m4a', '.wav'))
    ]
    
    # Use an existing file if available and no URL specified
    if existing_music and not soundcloud_url:
        track_path = random.choice(existing_music)
        logger.info(f"Using existing music file: {track_path}")
        return track_path
    
    # If no URL was provided, get one from the Excel file
    if not soundcloud_url:
        soundcloud_url = get_soundcloud_url_from_excel(EXCEL_FILE_PATH)
        if not soundcloud_url:
            logger.error("No SoundCloud URL available.")
            return None
    
    # Download the track
    try:
        logger.info(f"Downloading SoundCloud track: {soundcloud_url}")
        downloader = SoundCloudYtDlp(output_dir=download_dir)
        track_path = downloader.download_track(soundcloud_url)
        
        if track_path and os.path.exists(track_path):
            logger.info(f"Successfully downloaded track to: {track_path}")
            return track_path
        else:
            logger.error("Failed to download track")
            return None
    except Exception as e:
        logger.error(f"Error downloading track: {e}")
        return None


def enhance_video(video_path, music_path, text=None):
    """Enhance a video with text overlay and background music."""
    if not os.path.exists(video_path):
        logger.error(f"Video not found: {video_path}")
        return None
        
    if not os.path.exists(music_path):
        logger.error(f"Music not found: {music_path}")
        return None
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), "enhanced_videos")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename
    video_basename = os.path.basename(video_path).split('.')[0]
    output_path = os.path.join(output_dir, f"{video_basename}_enhanced.mp4")
    
    # Initialize the video enhancer with our custom settings
    enhancer = VideoEnhancer(
        output_dir=output_dir,
        style=Style.BLACK_BG_WHITE_TEXT,
        position=Position.TOP,
        font_scale=1.2,
        speech_emphasis=1.5,
        high_quality=True,
        # The API key is already set in the environment
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
    
    try:
        logger.info(f"Enhancing video: {video_path}")
        logger.info(f"Using music: {music_path}")
        if text:
            logger.info(f"Using custom text: {text}")
        
        # Perform the enhancement
        result = enhancer.enhance_video(
            video_path=video_path,
            output_path=output_path,
            add_text=True,
            add_music=True,
            custom_text=text or "Must-watch content!",
            music_path=music_path,
            auto_detect_features=True
        )
        
        # Check the result
        if result.get("success", False):
            enhanced_path = result.get("output_video")
            logger.info(f"Video enhancement successful: {enhanced_path}")
            return enhanced_path
        else:
            logger.error(f"Video enhancement failed: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        logger.error(f"Exception during video enhancement: {e}")
        return None


def main():
    """Main function to test the full enhancement pipeline."""
    logger.info("=== Starting Full Video Enhancement Test ===")
    logger.info(f"Target video: {TARGET_VIDEO_PATH}")
    logger.info(f"Using OpenAI API key: {os.environ.get('OPENAI_API_KEY') is not None}")
    
    if not os.path.exists(TARGET_VIDEO_PATH):
        logger.error(f"Target video not found: {TARGET_VIDEO_PATH}")
        return 1
    
    # Step 1: Download music from SoundCloud
    logger.info("Step 1: Downloading music from SoundCloud")
    music_path = download_music()
    
    if not music_path:
        logger.error("Failed to obtain music. Cannot proceed.")
        return 1
    
    # Step 2: Enhance the video
    logger.info("Step 2: Enhancing video with text and music")
    enhanced_video = enhance_video(
        video_path=TARGET_VIDEO_PATH,
        music_path=music_path,
        text="Must-See Content!"
    )
    
    if not enhanced_video:
        logger.error("Video enhancement failed")
        return 1
    
    logger.info("=== Test Completed Successfully ===")
    logger.info(f"Enhanced video saved to: {enhanced_video}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
