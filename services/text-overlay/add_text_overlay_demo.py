#!/usr/bin/env python
"""
Demo script to add text overlay to a video using TextOverlayEnhancer
"""
import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the TextOverlayEnhancer and Position enum
from video_enhancer.text_overlay import TextOverlayEnhancer, Position

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Log to console
        logging.FileHandler("text_overlay_demo.log")  # Also log to file
    ]
)
logger = logging.getLogger("text_overlay_demo")

def main():
    print("=== STARTING TEXT OVERLAY DEMO ====")
    """Main function to add text overlay to a video"""
    
    # Set up paths
    input_video = r"C:\Users\Isaia\Documents\N8N\shared_data\IMG_2401.MP4"
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enhanced_videos")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Set output path
    video_basename = os.path.basename(input_video).split('.')[0]
    output_video = os.path.join(output_dir, f"{video_basename}_text_overlay.mp4")
    
    # Initialize the text overlay enhancer with TOP position
    enhancer = TextOverlayEnhancer(position=Position.TOP, font_scale=1.2)
    
    # Run the text overlay enhancement
    logger.info(f"Adding text overlay to video: {input_video}")
    logger.info(f"Output will be saved to: {output_video}")
    
    # AI will analyze the video and generate appropriate text
    result = enhancer.enhance_video(
        video_path=input_video,
        output_path=output_video,
        analyze_first=True  # Analyze the video to generate AI-based text
    )
    
    # Display results
    if result.get("success", False):
        print(f"Success! Text overlay added: '{result.get('text')}'")
        print(f"Enhanced video saved to: {result.get('output_video')}")
    else:
        print(f"Error adding text overlay: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    try:
        main()
        print("=== DEMO COMPLETED ====")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
