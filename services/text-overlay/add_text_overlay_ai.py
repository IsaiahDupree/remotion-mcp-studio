#!/usr/bin/env python
"""
Script to add AI-generated text overlay to a video using TextOverlayEnhancer
"""
import os
import sys
import logging
from pathlib import Path
import argparse

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the TextOverlayEnhancer and Position enum
from video_enhancer.text_overlay import TextOverlayEnhancer, Position, Style

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Log to console
        logging.FileHandler("text_overlay_ai.log")  # Also log to file
    ]
)
logger = logging.getLogger("text_overlay_ai")

def main():
    print("=== STARTING AI TEXT OVERLAY ENHANCER ====")
    
    parser = argparse.ArgumentParser(description="Add AI-generated text overlay to a video")
    parser.add_argument("--input", "-i", required=True, help="Path to input video")
    parser.add_argument("--output", "-o", help="Path to output video (optional)")
    parser.add_argument("--position", "-p", default="TOP", choices=["TOP", "BOTTOM", "CENTER", "TOP_LEFT", "TOP_RIGHT", "BOTTOM_LEFT", "BOTTOM_RIGHT"], 
                        help="Position of text overlay")
    parser.add_argument("--font-scale", "-f", type=float, default=1.2, help="Font scale (size)")
    parser.add_argument("--custom-text", "-t", help="Custom text (optional, overrides AI generation)")
    parser.add_argument("--style", "-s", default="BLACK_BG_WHITE_TEXT", 
                        choices=["BLACK_BG_WHITE_TEXT", "WHITE_BG_BLACK_TEXT", "TRANSPARENT_WHITE_TEXT", "TRANSPARENT_BLACK_TEXT"],
                        help="Text style")
    
    args = parser.parse_args()
    
    # Set up paths
    input_video = args.input
    if not os.path.exists(input_video):
        print(f"Error: Input video not found: {input_video}")
        return
        
    # Determine output path
    if args.output:
        output_video = args.output
    else:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enhanced_videos")
        os.makedirs(output_dir, exist_ok=True)
        video_basename = os.path.basename(input_video).split('.')[0]
        output_video = os.path.join(output_dir, f"{video_basename}_ai_text.mp4")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)
    
    # Map string arguments to enum values
    position = getattr(Position, args.position)
    style = getattr(Style, args.style)
    
    # Initialize the text overlay enhancer
    enhancer = TextOverlayEnhancer(
        position=position, 
        font_scale=args.font_scale,
        style=style,
        # OpenAI API key is read from environment variable
    )
    
    # Run the text overlay enhancement
    logger.info(f"Adding AI-generated text overlay to video: {input_video}")
    logger.info(f"Output will be saved to: {output_video}")
    
    # Analyze the video and generate appropriate text, or use custom text
    result = enhancer.enhance_video(
        video_path=input_video,
        output_path=output_video,
        custom_text=args.custom_text,
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
        print("=== ENHANCEMENT COMPLETED ====")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
