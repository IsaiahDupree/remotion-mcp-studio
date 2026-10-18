#!/usr/bin/env python
"""
Fast Combined Video Enhancer
==========================
This script integrates efficient MoviePy-based text overlay with audio transcript analysis
and background music enhancement for high-performance video processing.
"""

import os
import sys
import time
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path if needed
if not os.path.exists(os.path.join(os.path.dirname(__file__), "video_enhancer")):
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our custom modules
from video_enhancer.composite_overlay import CompositeTextOverlayEnhancer
from video_enhancer.text_styler import Position, Style
from video_enhancer.transcript_processor import TranscriptProcessor
from video_enhancer.music_enhancer import MusicEnhancer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("enhancer.log")
    ]
)
logger = logging.getLogger("enhance_video_fast")

def read_env_file(env_path):
    """Read key=value pairs from .env file"""
    env_vars = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                key_value = line.split('=', 1)
                if len(key_value) == 2:
                    key, value = key_value
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        logger.error(f"Error reading .env file: {str(e)}")
    return env_vars

def get_api_key():
    """Get API key from .env file or environment variables"""
    # First try .env file
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        env_vars = read_env_file(env_path)
        api_key = env_vars.get('OPENAI_API_KEY')
        if api_key:
            return api_key
    
    # Then try environment variable
    return os.environ.get('OPENAI_API_KEY')

def enhance_video(
    video_path: str,
    output_path: Optional[str] = None,
    add_music: bool = False,
    music_path: Optional[str] = None,
    position: str = "TOP",
    font_scale: float = 1.2,
    style: str = "BLACK_BG_WHITE_TEXT",
    custom_text: Optional[str] = None,
    api_key: Optional[str] = None,
    auto_detect_music: bool = True,
    speech_emphasis_factor: Optional[float] = None,
    soundcloud_excel: Optional[str] = None,
    track_column: str = "URL"
) -> Dict[str, Any]:
    """
    Enhance video with text overlay and optionally background music using optimized processing.
    
    Args:
        video_path: Path to input video
        output_path: Path for output video (optional)
        add_music: Whether to add background music
        music_path: Path to music file (optional)
        position: Text overlay position
        font_scale: Text size
        style: Text overlay style
        custom_text: Custom text to use (bypasses analysis)
        api_key: OpenAI API key
        auto_detect_music: Whether to detect existing background music
        speech_emphasis_factor: Factor to adjust background music volume during speech
        
    Returns:
        Dictionary with enhancement results
    """
    start_time = time.time()
    
    # Validate input
    if not os.path.exists(video_path):
        return {"success": False, "error": f"Video not found: {video_path}"}
    
    # Determine output path if not specified
    if not output_path:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enhanced_videos")
        os.makedirs(output_dir, exist_ok=True)
        video_basename = os.path.basename(video_path).split('.')[0]
        timestamp = int(time.time())
        output_path = os.path.join(output_dir, f"{video_basename}_enhanced_{timestamp}.mp4")
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Set up enhancement components
    position_enum = getattr(Position, position)
    style_enum = getattr(Style, style)
    
    logger.info(f"Starting fast enhancement for: {video_path}")
    logger.info(f"Output will be saved to: {output_path}")
    
    # Step 1: Process transcript if no custom text is provided
    generated_text = None
    if not custom_text and api_key:
        try:
            logger.info("Analyzing video transcript...")
            transcript_processor = TranscriptProcessor(api_key)
            transcript_result = transcript_processor.process_video_transcript(video_path)
            
            if transcript_result["success"]:
                logger.info(f"Transcript analysis successful")
                transcript_excerpt = transcript_result['transcript'][:100].replace('\n', ' ').strip()
                logger.info(f"Transcript excerpt: {transcript_excerpt}...")
                logger.info(f"Suggested text from transcript: {transcript_result['suggested_text']}")
                generated_text = transcript_result["suggested_text"]
                
                # Save transcript analysis to file for reference
                transcript_json_path = output_path.replace('.mp4', '_transcript.json')
                with open(transcript_json_path, 'w') as f:
                    json.dump(transcript_result, f, indent=2)
                logger.info(f"Full transcript analysis saved to: {transcript_json_path}")
            else:
                logger.warning(f"Transcript analysis failed: {transcript_result.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error processing transcript: {str(e)}")
    
    # Step 2: Apply text overlay
    try:
        logger.info("Applying text overlay with dependency-light processor...")
        text_overlay = CompositeTextOverlayEnhancer(
            position=position_enum, 
            font_scale=font_scale,
            style=style_enum,
            openai_api_key=api_key
        )
        
        # Use AI-generated or custom text
        text = custom_text or generated_text
        
        # Intermediate file for text overlay
        text_only_output = output_path.replace('.mp4', '_text_only.mp4')
        
        # Apply text overlay
        text_result = text_overlay.enhance_video(
            video_path=video_path,
            output_path=text_only_output,
            custom_text=text,
            analyze_first=(text is None)  # Only analyze if no text provided
        )
        
        # Check if text overlay operation actually created the output file
        if not text_result or not os.path.exists(text_only_output):
            logger.error("Text overlay failed or output file was not created")
            return {"success": False, "error": "Text overlay failed"}
            
        # Get the text that was actually used (may be different if AI-generated)
        used_text = text if text else "AI-generated text overlay"
        if hasattr(text_overlay, 'text') and text_overlay.text:
            used_text = text_overlay.text
        logger.info(f"Text overlay applied: '{used_text}'")
        
        # If no music is requested, copy the text-only video to the final output path
        if not add_music:
            logger.info("No background music requested, using text-only enhanced video as final output")
            if os.path.exists(text_only_output):
                try:
                    import shutil
                    shutil.copy2(text_only_output, output_path)
                    logger.info(f"Copied text-only video to final output: {output_path}")
                except Exception as copy_err:
                    logger.error(f"Error copying text-only video: {str(copy_err)}")
            elapsed_time = time.time() - start_time
            logger.info(f"Video enhancement completed in {elapsed_time:.1f} seconds")
            return {
                "success": True,
                "output_video": output_path,
                "text_overlay": used_text,
                "processing_time_seconds": elapsed_time
            }
    except Exception as e:
        logger.error(f"Error in text overlay: {str(e)}")
        return {"success": False, "error": f"Text overlay failed: {str(e)}"}
    
    # Step 3: Add background music if requested
    if add_music:
        try:
            # Use the text overlay result as input for music enhancement
            music_input_video = text_only_output
            
            # SoundCloud Excel integration for music tracks
            # These are passed directly as parameters, no need for kwargs
            
            if soundcloud_excel and os.path.exists(soundcloud_excel):
                logger.info(f"Using SoundCloud tracks from Excel file: {soundcloud_excel}")
                try:
                    import pandas as pd
                    # Load the Excel file
                    df = pd.read_excel(soundcloud_excel)
                    if track_column in df.columns and len(df) > 0:
                        # Select a random track URL
                        import random
                        track_url = random.choice(df[track_column].dropna().tolist())
                        logger.info(f"Selected SoundCloud track: {track_url}")
                        
                        # Use the track URL as the music source
                        music_path = track_url
                    else:
                        logger.warning(f"Column '{track_column}' not found or empty in Excel file")
                except Exception as excel_err:
                    logger.error(f"Error reading SoundCloud Excel file: {str(excel_err)}")
            
            logger.info(f"Adding background music from {music_path if music_path else 'default path'}...")
            
            music_enhancer = MusicEnhancer()
            music_result = music_enhancer.enhance_video_with_music(
                video_path=music_input_video, 
                output_path=output_path, 
                music_path=music_path,
                auto_detect_existing_music=auto_detect_music,
                speech_emphasis=speech_emphasis_factor
            )
            
            if not music_result or not music_result.get("success", False):
                logger.error("Failed to add background music")
                # Continue with the text-only video if music fails
                logger.info("Using text-only enhanced video as final output")
                if os.path.exists(text_only_output):
                    try:
                        import shutil
                        shutil.copy2(text_only_output, output_path)
                        logger.info(f"Copied text-only video to final output: {output_path}")
                    except Exception as copy_err:
                        logger.error(f"Error copying text-only video: {str(copy_err)}")
                        
                elapsed_time = time.time() - start_time
                return {
                    "success": True,
                    "partial": True,
                    "music_error": music_result.get("error", "Unknown music error") if music_result else "Music enhancement failed",
                    "output_video": output_path,
                    "text_overlay": used_text,
                    "music_added": False,
                    "transcript_analysis": transcript_analysis_path if 'transcript_analysis_path' in locals() and transcript_result else None,
                    "processing_time_seconds": elapsed_time
                }
            else:                
                logger.info("Background music added successfully")
                music_added = music_result.get("music_added", True)
                
                # Clean up intermediate file
                try:
                    if os.path.exists(text_only_output) and os.path.exists(output_path):
                        os.remove(text_only_output)
                        logger.info(f"Cleaned up intermediate file: {text_only_output}")
                except Exception as e:
                    logger.warning(f"Error cleaning up intermediate file: {str(e)}")
                    
                elapsed_time = time.time() - start_time
                logger.info(f"Video enhancement completed in {elapsed_time:.1f} seconds")
                return {
                    "success": True,
                    "output_video": output_path,
                    "text_overlay": used_text,
                    "music_added": music_added,
                    "has_existing_music": music_result.get("has_existing_music", False),
                    "transcript_analysis": transcript_analysis_path if transcript_result else None,
                    "processing_time_seconds": elapsed_time
                }
        except Exception as e:
            logger.error(f"Error adding background music: {str(e)}")
            # Continue with text-only video if music enhancement fails
            logger.info("Using text-only enhanced video as final output due to music error")
            if os.path.exists(text_only_output):
                try:
                    import shutil
                    shutil.copy2(text_only_output, output_path)
                    logger.info(f"Copied text-only video to final output: {output_path}")
                except Exception as copy_err:
                    logger.error(f"Error copying text-only video: {str(copy_err)}")
                    
            elapsed_time = time.time() - start_time
            return {
                "success": True,
                "partial": True,
                "music_added": False,
                "music_error": str(e),
                "output_video": output_path,
                "text_overlay": used_text,
                "transcript_analysis": transcript_analysis_path if 'transcript_analysis_path' in locals() and transcript_result else None,
                "processing_time_seconds": elapsed_time
            }

def process_batch(
    video_list: List[str], 
    output_dir: str,
    add_music: bool = False,
    position: str = "TOP",
    api_key: Optional[str] = None,
    music_path: Optional[str] = None,
    soundcloud_excel: Optional[str] = None,
    track_column: str = "URL",
    **kwargs
) -> Dict[str, Any]:
    """
    Process a batch of videos with the same settings.
    
    Args:
        video_list: List of video paths to process
        output_dir: Directory for output videos
        add_music: Whether to add background music
        position: Text position
        api_key: OpenAI API key
        **kwargs: Additional parameters for enhance_video
        
    Returns:
        Dictionary with batch processing results
    """
    os.makedirs(output_dir, exist_ok=True)
    
    results = {
        "total": len(video_list),
        "successful": 0,
        "failed": 0,
        "videos": []
    }
    
    for i, video_path in enumerate(video_list):
        logger.info(f"Processing video {i+1}/{len(video_list)}: {video_path}")
        
        # Set output path
        video_basename = os.path.basename(video_path).split('.')[0]
        output_path = os.path.join(output_dir, f"{video_basename}_enhanced.mp4")
        
        # Process the video
        result = enhance_video(
            video_path=video_path,
            output_path=output_path,
            add_music=add_music,
            position=position,
            api_key=api_key,
            music_path=music_path,
            soundcloud_excel=soundcloud_excel,
            track_column=track_column,
            **kwargs
        )      
        
        # Track results
        if result.get("success", False):
            results["successful"] += 1
        else:
            results["failed"] += 1
            
        results["videos"].append({
            "input": video_path,
            "output": result.get("output_video", ""),
            "success": result.get("success", False),
            "error": result.get("error", None),
            "text": result.get("text_overlay", ""),
            "music_added": result.get("music_added", False)
        })
        
    return results

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fast Video Enhancer - Text Overlay and Background Music")
    parser.add_argument("--input", "-i", required=True, help="Input video file or directory")
    parser.add_argument("--output", "-o", help="Output video file or directory")
    parser.add_argument("--batch", "-b", action="store_true", help="Process directory of videos in batch mode")
    parser.add_argument("--music", "-m", action="store_true", help="Add background music")
    parser.add_argument("--music-path", help="Path to music file (optional)")
    parser.add_argument("--soundcloud-excel", help="Path to Excel file with SoundCloud tracks")
    parser.add_argument("--track-column", default="URL", help="Column name in Excel file containing track URLs")
    parser.add_argument("--position", "-p", default="TOP", 
                        choices=[p.name for p in Position], 
                        help="Position of text overlay")
    parser.add_argument("--font-scale", "-f", type=float, default=1.2, help="Font scale (size)")
    parser.add_argument("--style", "-s", default="BLACK_BG_WHITE_TEXT", 
                        choices=[s.name for s in Style],
                        help="Text style")
    parser.add_argument("--text", "-t", help="Custom text (optional, bypasses analysis)")
    parser.add_argument("--api-key", "-k", help="OpenAI API key (optional)")
    parser.add_argument("--skip-music-detection", action="store_true", help="Skip background music detection")
    parser.add_argument("--speech-emphasis", type=float, help="Factor to adjust music volume during speech (e.g. 0.5)")
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or get_api_key()
    if not api_key:
        print("Warning: No OpenAI API key provided. Some features may be limited.")
    
    print(f"=== STARTING FAST VIDEO ENHANCEMENT ===")
    
    # Handle batch processing vs. single video
    if args.batch:
        # Batch processing mode
        if os.path.isdir(args.input):
            videos = []
            for ext in [".mp4", ".avi", ".mov", ".mkv"]:
                videos.extend([os.path.join(args.input, f) for f in os.listdir(args.input) if f.lower().endswith(ext)])
            
            if not videos:
                print(f"No video files found in directory: {args.input}")
                return
                
            output_dir = args.output or os.path.join(os.path.dirname(os.path.abspath(__file__)), "enhanced_videos", "batch")
            print(f"Processing {len(videos)} videos in batch mode")
            
            results = process_batch(
                video_list=videos,
                output_dir=output_dir,
                add_music=args.music,
                position=args.position,
                font_scale=args.font_scale,
                style=args.style,
                custom_text=args.text,
                api_key=api_key,
                auto_detect_music=(not args.skip_music_detection),
                speech_emphasis_factor=args.speech_emphasis,
                soundcloud_excel=args.soundcloud_excel,
                track_column=args.track_column
            )
            
            print(f"Batch processing complete:")
            print(f"- Total videos: {results['total']}")
            print(f"- Successful: {results['successful']}")
            print(f"- Failed: {results['failed']}")
            print(f"- Output directory: {output_dir}")
            
        else:
            print(f"Error: Batch mode requires a directory path, but got: {args.input}")
            return
            
    else:
        # Single video processing mode
        if not os.path.isfile(args.input):
            print(f"Error: Input file not found: {args.input}")
            return
            
        # Enhance the video
        result = enhance_video(
            video_path=args.input,
            output_path=args.output,
            add_music=args.music,
            music_path=args.music_path,
            position=args.position,
            font_scale=args.font_scale,
            style=args.style,
            custom_text=args.text,
            api_key=api_key,
            auto_detect_music=(not args.skip_music_detection),
            speech_emphasis_factor=args.speech_emphasis
        )
        
        # Display results
        if result.get("success", False):
            print(f"Success! Enhanced video saved to: {result['output_video']}")
            print(f"Text overlay: '{result.get('text_overlay', 'N/A')}'")
            print(f"Processing time: {result.get('processing_time_seconds', 0):.1f} seconds")
            
            if args.music:
                if result.get("music_added", False):
                    print("Background music was added successfully")
                else:
                    print("No background music was added (may already have music)")
                    
            if result.get("partial", False):
                print(f"Note: {result.get('music_error', 'Music enhancement had issues')}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    print("=== ENHANCEMENT COMPLETE ===")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
