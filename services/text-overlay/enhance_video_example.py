#!/usr/bin/env python3
"""
Video Enhancement Example

This script demonstrates how to use the modular video context analyzer system
to analyze videos and apply text overlays with the black background style.
"""

import os
import argparse
import logging
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our video enhancer components
from video_context_analyzer.video_enhancer import VideoEnhancer
from video_context_analyzer.styling import Style, Position

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhance_example')

def enhance_single_video(
    video_path, 
    output_path=None, 
    custom_text=None, 
    position="top",
    analyze=True,
    high_quality=True
):
    """
    Enhance a single video with smart text overlay.
    
    Args:
        video_path: Path to video file
        output_path: Path for enhanced output video
        custom_text: Optional custom text (otherwise AI-generated)
        position: Text position ("top", "middle", "bottom")
        analyze: Whether to analyze video content
        high_quality: Whether to use high quality settings
    """
    # Map string position to enum
    position_map = {
        "top": Position.TOP,
        "middle": Position.MIDDLE,
        "bottom": Position.BOTTOM
    }
    position_enum = position_map.get(position, Position.TOP)
    
    # Create enhancer with black background style matching the example
    enhancer = VideoEnhancer(
        style=Style.BLACK_BG_WHITE_TEXT,
        position=position_enum,
        font_scale=1.0,
        high_quality=high_quality
    )
    
    # Default output path if not specified
    if not output_path:
        video_file = Path(video_path)
        output_dir = Path("enhanced_videos")
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"{video_file.stem}_enhanced.mp4")
    
    logger.info(f"Enhancing video: {video_path}")
    logger.info(f"Output will be saved to: {output_path}")
    
    # Enhance the video
    if analyze:
        # Full pipeline: analyze first, then enhance
        result = enhancer.enhance_video(
            video_path,
            output_path=output_path,
            custom_text=custom_text,
            analyze_first=True
        )
        
        # Show analysis results
        if "analysis" in result and "catchy_text" in result["analysis"]:
            logger.info(f"Generated text: {result['analysis']['catchy_text']}")
            
        # Show whether video has background music
        if "analysis" in result and "audio_analysis" in result["analysis"]:
            has_music = result["analysis"]["audio_analysis"].get("has_background_music", False)
            logger.info(f"Video has background music: {has_music}")
    else:
        # Just apply the overlay without analysis
        overlay_text = custom_text or "Must see this content"
        output_path = enhancer.apply_text_overlay(
            video_path,
            text=overlay_text,
            output_path=output_path
        )
    
    logger.info(f"Enhancement complete: {output_path}")
    return output_path

def process_video_list(list_file, output_dir=None):
    """
    Process a list of videos from a text file.
    
    Args:
        list_file: Path to text file with video paths (one per line)
        output_dir: Directory to save enhanced videos
    """
    # Read video paths from file
    with open(list_file, 'r') as f:
        video_paths = [line.strip() for line in f if line.strip()]
    
    if not video_paths:
        logger.error(f"No video paths found in {list_file}")
        return
    
    # Create output directory
    if not output_dir:
        output_dir = "enhanced_videos"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create enhancer
    enhancer = VideoEnhancer(
        style=Style.BLACK_BG_WHITE_TEXT,
        position=Position.TOP,
        output_dir=output_dir,
        high_quality=True
    )
    
    # Process batch
    results = enhancer.process_batch(video_paths, output_dir)
    
    logger.info(f"Batch processing complete. Enhanced {len(results)} videos.")
    logger.info(f"Results saved to {os.path.join(output_dir, 'batch_results.json')}")

def main():
    parser = argparse.ArgumentParser(description='Video Enhancement Example')
    
    parser.add_argument('--video', type=str, help='Path to input video file')
    parser.add_argument('--output', type=str, help='Path for output enhanced video')
    parser.add_argument('--text', type=str, help='Custom text overlay')
    parser.add_argument('--position', type=str, choices=['top', 'middle', 'bottom'],
                        default='top', help='Text position')
    parser.add_argument('--list', type=str, help='Process a list of videos from a file')
    parser.add_argument('--output-dir', type=str, help='Output directory for batch processing')
    parser.add_argument('--no-analyze', action='store_true', 
                        help='Skip content analysis (use custom text or default)')
    parser.add_argument('--standard-quality', action='store_true',
                        help='Use standard quality instead of high quality')
                        
    args = parser.parse_args()
    
    if args.list:
        process_video_list(args.list, args.output_dir)
    elif args.video:
        enhance_single_video(
            args.video,
            output_path=args.output,
            custom_text=args.text,
            position=args.position,
            analyze=not args.no_analyze,
            high_quality=not args.standard_quality
        )
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
