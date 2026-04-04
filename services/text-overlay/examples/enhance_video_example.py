#!/usr/bin/env python3
"""
Video Enhancement Example Script
===============================

This example demonstrates how to use the modular video enhancer system
to add text overlays and SoundCloud background music to videos.

It provides examples for:
1. Single video enhancement
2. Batch video enhancement
3. Enhancement with Excel file input
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path to import video_enhancer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video_enhancer import VideoEnhancer
from video_context_analyzer.styling import Style, Position

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("enhance_example")


def enhance_specific_video(args):
    """Enhance a specific video with text and/or music."""
    # Create output directory if needed
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Set up enhancer
    enhancer = VideoEnhancer(
        output_dir=args.output_dir,
        style=Style.BLACK_BG_WHITE_TEXT,
        position=Position.TOP if args.position == "top" else Position.CENTER,
        font_scale=args.font_scale,
        speech_emphasis=args.speech_emphasis,
        high_quality=args.high_quality,
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
    
    # Generate output path
    video_basename = os.path.basename(args.video).split('.')[0]
    output_path = os.path.join(args.output_dir, f"{video_basename}_enhanced.mp4")
    
    # Enhance the video
    result = enhancer.enhance_video(
        video_path=args.video,
        output_path=output_path,
        add_text=args.add_text,
        add_music=args.add_music,
        custom_text=args.text,
        soundcloud_url=args.soundcloud_url,
        music_path=args.music_path,
        speech_emphasis=args.speech_emphasis,
        analyze_first=not args.skip_analysis,
        auto_detect_features=not args.skip_auto_detect
    )
    
    # Show result
    if result.get("success", False):
        logger.info(f"Video enhancement successful: {result.get('output_video')}")
        
        # Show details about what was done
        if result.get("text_overlay_added", False):
            logger.info(f"Added text overlay: '{result.get('text', 'Unknown text')}'")
        
        if result.get("music_added", False):
            logger.info(f"Added background music with speech emphasis factor: {result.get('speech_emphasis', 'unknown')}")
        elif "music_error" in result:
            logger.warning(f"Music not added due to error: {result.get('music_error')}")
    else:
        logger.error(f"Video enhancement failed: {result.get('error', 'Unknown error')}")
    
    return result.get("success", False)


def enhance_batch_videos(args):
    """Enhance multiple videos from a directory."""
    # Create output directory if needed
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Find videos in input directory
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.m4v']
    video_paths = []
    
    for root, _, files in os.walk(args.input_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_paths.append(os.path.join(root, file))
    
    if not video_paths:
        logger.error(f"No video files found in {args.input_dir}")
        return False
    
    logger.info(f"Found {len(video_paths)} videos to process")
    
    # Set up enhancer
    enhancer = VideoEnhancer(
        output_dir=args.output_dir,
        style=Style.BLACK_BG_WHITE_TEXT,
        position=Position.TOP if args.position == "top" else Position.CENTER,
        font_scale=args.font_scale,
        speech_emphasis=args.speech_emphasis,
        high_quality=args.high_quality,
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
    
    # Enhance videos in batch
    results = enhancer.batch_enhance_videos(
        video_paths=video_paths,
        add_text=args.add_text,
        add_music=args.add_music,
        custom_text=args.text,
        soundcloud_url=args.soundcloud_url,
        speech_emphasis=args.speech_emphasis,
        analyze_first=not args.skip_analysis,
        auto_detect_features=not args.skip_auto_detect
    )
    
    # Show summary of results
    success_count = results.get("successful_videos", 0)
    fail_count = results.get("failed_videos", 0)
    total = len(video_paths)
    
    logger.info(f"Batch processing complete: {success_count}/{total} videos enhanced successfully")
    if fail_count > 0:
        logger.warning(f"{fail_count}/{total} videos failed processing")
    
    return success_count > 0


def enhance_from_excel(args):
    """Enhance videos listed in an Excel file."""
    # Check Excel file exists
    if not os.path.exists(args.excel_file):
        logger.error(f"Excel file not found: {args.excel_file}")
        return False
    
    # Create output directory if needed
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Set up enhancer
    enhancer = VideoEnhancer(
        output_dir=args.output_dir,
        style=Style.BLACK_BG_WHITE_TEXT,
        position=Position.TOP if args.position == "top" else Position.CENTER,
        font_scale=args.font_scale,
        speech_emphasis=args.speech_emphasis,
        high_quality=args.high_quality,
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
    
    # Enhance videos from Excel
    results = enhancer.enhance_from_excel(
        excel_path=args.excel_file,
        video_column=args.video_column,
        soundcloud_column=args.soundcloud_column,
        text_column=args.text_column,
        add_text=args.add_text,
        add_music=args.add_music,
        default_text=args.text,
        default_soundcloud_url=args.soundcloud_url,
        speech_emphasis=args.speech_emphasis,
        analyze_first=not args.skip_analysis,
        auto_detect_features=not args.skip_auto_detect
    )
    
    # Show summary of results
    success_count = results.get("successful_videos", 0)
    fail_count = results.get("failed_videos", 0)
    total = results.get("total_videos", 0)
    
    logger.info(f"Excel processing complete: {success_count}/{total} videos enhanced successfully")
    if fail_count > 0:
        logger.warning(f"{fail_count}/{total} videos failed processing")
    
    return success_count > 0


def main():
    """Main function for the example script."""
    parser = argparse.ArgumentParser(description="Enhance videos with text overlays and background music")
    
    # Create subparsers for different modes
    subparsers = parser.add_subparsers(dest="mode", help="Processing mode")
    
    # Single video mode
    single_parser = subparsers.add_parser("single", help="Enhance a single video")
    single_parser.add_argument("--video", required=True, help="Path to input video file")
    
    # Batch mode
    batch_parser = subparsers.add_parser("batch", help="Enhance multiple videos from a directory")
    batch_parser.add_argument("--input-dir", required=True, help="Input directory containing videos")
    
    # Excel mode
    excel_parser = subparsers.add_parser("excel", help="Enhance videos listed in an Excel file")
    excel_parser.add_argument("--excel-file", required=True, help="Path to Excel file with video paths")
    excel_parser.add_argument("--video-column", required=True, help="Column name with video paths")
    excel_parser.add_argument("--soundcloud-column", help="Column name with SoundCloud URLs")
    excel_parser.add_argument("--text-column", help="Column name with custom text overlays")
    
    # Common options for all modes
    for subparser in [single_parser, batch_parser, excel_parser]:
        subparser.add_argument("--output-dir", default="./enhanced_videos", help="Output directory")
        subparser.add_argument("--add-text", action="store_true", help="Add text overlay")
        subparser.add_argument("--add-music", action="store_true", help="Add background music")
        subparser.add_argument("--text", help="Custom text overlay (overrides auto-generation)")
        subparser.add_argument("--soundcloud-url", help="SoundCloud track URL")
        subparser.add_argument("--music-path", help="Path to local music file")
        subparser.add_argument("--speech-emphasis", type=float, default=1.5, help="Speech emphasis factor")
        subparser.add_argument("--font-scale", type=float, default=1.2, help="Font size scale")
        subparser.add_argument("--position", choices=["top", "center"], default="top", help="Text position")
        subparser.add_argument("--high-quality", action="store_true", help="Preserve high video quality")
        subparser.add_argument("--skip-analysis", action="store_true", help="Skip content analysis")
        subparser.add_argument("--skip-auto-detect", action="store_true", help="Skip auto-detection of features")
    
    args = parser.parse_args()
    
    # Check if any enhancement is requested
    if not args.add_text and not args.add_music:
        logger.error("Please specify at least one enhancement: --add-text and/or --add-music")
        return 1
    
    # Process according to selected mode
    if args.mode == "single":
        success = enhance_specific_video(args)
    elif args.mode == "batch":
        success = enhance_batch_videos(args)
    elif args.mode == "excel":
        success = enhance_from_excel(args)
    else:
        parser.print_help()
        return 1
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
