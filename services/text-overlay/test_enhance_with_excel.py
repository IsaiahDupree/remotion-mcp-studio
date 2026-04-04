#!/usr/bin/env python3
"""
Test Video Enhancement with SoundCloud URLs from Excel
====================================================

This script:
1. Reads SoundCloud URLs from the Excel file
2. Downloads a SoundCloud track using the SoundCloudYtDlp utility
3. Enhances a specific video by adding text overlay and the downloaded music
4. Provides detailed logging of the process

Usage:
    python test_enhance_with_excel.py
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path
import tempfile
import random

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
EXCEL_FILE_PATH = r"C:\Users\Isaia\Documents\WordsOnText\data\SoundCloud to X Reposter.xlsx"


def get_soundcloud_urls_from_excel(excel_path):
    """
    Extract SoundCloud URLs from the Excel file.
    
    Args:
        excel_path: Path to the Excel file
        
    Returns:
        List of SoundCloud URLs
    """
    logger.info(f"Reading SoundCloud URLs from Excel file: {excel_path}")
    
    try:
        # Read the Excel file
        df = pd.read_excel(excel_path)
        
        # Find columns that might contain SoundCloud URLs
        url_columns = []
        for col in df.columns:
            # Check a sample of values in the column to see if they contain 'soundcloud.com'
            sample = df[col].dropna().astype(str).head(10)
            if any('soundcloud.com' in str(url).lower() for url in sample):
                url_columns.append(col)
        
        if not url_columns:
            logger.warning("No columns containing SoundCloud URLs found in the Excel file")
            return []
        
        # Extract URLs from the identified columns
        urls = []
        for col in url_columns:
            # Filter out non-URL values
            valid_urls = [
                str(url) for url in df[col].dropna() 
                if isinstance(url, str) and 'soundcloud.com' in url.lower()
            ]
            urls.extend(valid_urls)
        
        logger.info(f"Found {len(urls)} SoundCloud URLs in the Excel file")
        
        # Return unique URLs
        unique_urls = list(set(urls))
        return unique_urls
        
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        return []


def download_soundcloud_track(url, output_dir):
    """
    Download a SoundCloud track using SoundCloudYtDlp utility.
    
    Args:
        url: SoundCloud track URL
        output_dir: Directory to save the downloaded track
        
    Returns:
        Path to downloaded track or None if download failed
    """
    logger.info(f"Downloading SoundCloud track from URL: {url}")
    
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
            custom_text=custom_text or "Must-watch content!",
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
    logger.info("=== Starting Video Enhancement Test with Excel SoundCloud URLs ===")
    
    # Check if video exists
    if not os.path.exists(TARGET_VIDEO_PATH):
        logger.error(f"Target video not found: {TARGET_VIDEO_PATH}")
        return 1
    
    # Check if Excel file exists
    if not os.path.exists(EXCEL_FILE_PATH):
        logger.error(f"Excel file not found: {EXCEL_FILE_PATH}")
        return 1
    
    # Step 1: Get SoundCloud URLs from Excel file
    logger.info(f"Reading SoundCloud URLs from: {EXCEL_FILE_PATH}")
    soundcloud_urls = get_soundcloud_urls_from_excel(EXCEL_FILE_PATH)
    
    if not soundcloud_urls:
        logger.error("No SoundCloud URLs found in Excel file")
        return 1
    
    logger.info(f"Found {len(soundcloud_urls)} SoundCloud URLs")
    
    # Step 2: Try downloading tracks until one succeeds
    music_path = None
    download_dir = os.path.join(os.path.dirname(__file__), "downloaded_music")
    
    # Try with a random selection of up to 5 URLs
    test_urls = random.sample(soundcloud_urls, min(5, len(soundcloud_urls)))
    
    for i, url in enumerate(test_urls):
        logger.info(f"Attempt {i+1}/{len(test_urls)}: Downloading SoundCloud track from {url}")
        track_path = download_soundcloud_track(url, download_dir)
        
        if track_path:
            music_path = track_path
            logger.info(f"Successfully downloaded track: {track_path}")
            break
        else:
            logger.warning(f"Failed to download from {url}, trying next URL")
    
    if not music_path:
        logger.error("Failed to download any SoundCloud tracks. Cannot proceed with enhancement.")
        return 1
    
    # Step 3: Enhance video with downloaded music
    logger.info("=== Enhancing Video with Downloaded Music ===")
    
    enhanced_video = enhance_video(
        video_path=TARGET_VIDEO_PATH,
        music_path=music_path,
        custom_text="Must-See Content!"  # You can customize this text
    )
    
    if not enhanced_video:
        logger.error("Video enhancement failed")
        return 1
    
    logger.info("=== Test Completed Successfully ===")
    logger.info(f"Enhanced video saved to: {enhanced_video}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
