#!/usr/bin/env python
"""
Test script for the music enhancer module
"""
import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the MusicEnhancer
from video_enhancer.music_enhancer import MusicEnhancer

# Configure logging - ensure console output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Explicitly log to stdout
        logging.FileHandler("enhancer_test.log")  # Also log to file
    ]
)
logger = logging.getLogger("test_enhancer")

def main():
    print("=== STARTING VIDEO ENHANCER TEST ====")
    """Main test function"""
    # Set up paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "enhanced_videos", "test_output")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize the music enhancer
    enhancer = MusicEnhancer(output_dir=output_dir)
    
    # Select an input video
    # Using one of the existing videos for testing
    input_video = os.path.join(base_dir, "output_videos", "autovolume_0024d0ff50d04b2eba719fec130a0b74.mp4")
    
    # Alternative video path if the first one doesn't exist
    if not os.path.exists(input_video):
        input_video = os.path.join(base_dir, "autovolume_0024d0ff50d04b2eba719fec130a0b74.mp4")
    
    # If neither exists, scan for any MP4 file
    if not os.path.exists(input_video):
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.mp4'):
                    input_video = os.path.join(root, file)
                    break
            if os.path.exists(input_video):
                break
    
    if not os.path.exists(input_video):
        logger.error("Could not find any input video files for testing")
        return
    
    # Set output path
    video_basename = os.path.basename(input_video).split('.')[0]
    output_video = os.path.join(output_dir, f"{video_basename}_enhanced_test.mp4")
    
    # Run the enhancement test
    logger.info(f"Testing music enhancement on video: {input_video}")
    logger.info(f"Output will be saved to: {output_video}")
    
    # Test speech detection
    logger.info("Testing speech detection...")
    has_speech = enhancer.audio_processor.detect_speech_in_video(input_video)
    logger.info(f"Speech detection result: {has_speech}")
    
    # Test background music detection
    logger.info("Testing background music detection...")
    has_bg_music = enhancer.detect_background_music(input_video)
    logger.info(f"Background music detection result: {has_bg_music}")
    
    # Test music enhancement
    logger.info("Testing music enhancement...")
    result = enhancer.enhance_video_with_music(
        video_path=input_video,
        output_path=output_video,
        auto_detect_existing_music=True
    )
    
    # Display results
    logger.info(f"Enhancement result: {result}")
    
    if result.get("success", False):
        logger.info(f"Successfully enhanced video! Output saved to: {result.get('output_video', output_video)}")
    else:
        logger.error(f"Enhancement failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    try:
        print("Starting test script at", __file__)
        main()
        print("=== TEST COMPLETED ====")
    except Exception as e:
        print(f"ERROR IN TEST: {str(e)}")
        import traceback
        traceback.print_exc()
