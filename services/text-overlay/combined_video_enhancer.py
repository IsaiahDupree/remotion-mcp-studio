#!/usr/bin/env python
"""
Combined Video Enhancer
======================
This script integrates frame analysis and transcript processing to create enhanced videos
with AI-generated text overlays based on both visual and audio content.
"""

import os
import sys
import time
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Import our custom video enhancement modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from video_enhancer.text_overlay import TextOverlayEnhancer, Position, Style
from video_enhancer.transcript_processor import TranscriptProcessor
from video_enhancer.music_enhancer import MusicEnhancer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("combined_enhancer.log")
    ]
)
logger = logging.getLogger("combined_enhancer")

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
        print(f"Error reading .env file: {str(e)}")
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
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enhance video with text overlay and optionally background music.
    
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
        
    Returns:
        Dictionary with enhancement results
    """
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
    
    logger.info(f"Starting combined enhancement for: {video_path}")
    logger.info(f"Output will be saved to: {output_path}")
    
    # Step 1: Process transcript if no custom text is provided
    generated_text = None
    if not custom_text:
        try:
            logger.info("Analyzing video transcript...")
            transcript_processor = TranscriptProcessor(api_key)
            transcript_result = transcript_processor.process_video_transcript(video_path)
            
            if transcript_result["success"]:
                logger.info(f"Transcript analysis successful")
                logger.info(f"Transcript excerpt: {transcript_result['transcript'][:100]}...")
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
        logger.info("Applying text overlay...")
        text_overlay = TextOverlayEnhancer(
            position=position_enum, 
            font_scale=font_scale,
            style=style_enum,
            openai_api_key=api_key
        )
        
        # Use hierarchy: custom_text > transcript-generated text > AI will generate its own
        overlay_text = custom_text or generated_text
        
        # Intermediate file for text overlay
        if add_music:
            # If we're adding music, create an intermediate file for the text overlay
            intermediate_path = output_path.replace('.mp4', '_text_only.mp4')
        else:
            # If no music, write directly to output
            intermediate_path = output_path
        
        overlay_result = text_overlay.enhance_video(
            video_path=video_path,
            output_path=intermediate_path,
            custom_text=overlay_text,
            analyze_first=(overlay_text is None)  # Only analyze if no text provided
        )
        
        if not overlay_result.get("success", False):
            return {"success": False, "error": f"Text overlay failed: {overlay_result.get('error', 'Unknown error')}"}
            
        logger.info(f"Text overlay applied: '{overlay_result.get('text')}'")
        
        # If not adding music, we're done
        if not add_music:
            return {
                "success": True,
                "output_video": output_path,
                "text_overlay": overlay_result.get("text"),
                "music_added": False
            }
    
    except Exception as e:
        logger.error(f"Error applying text overlay: {str(e)}")
        return {"success": False, "error": str(e)}
    
    # Step 3: Add background music if requested
    if add_music:
        try:
            logger.info("Adding background music...")
            music_enhancer = MusicEnhancer()
            
            music_result = music_enhancer.enhance_video_with_music(
                video_path=intermediate_path,  # Use the video with text overlay
                output_path=output_path,
                music_path=music_path,
                auto_detect_existing_music=True
            )
            
            # Clean up intermediate file
            try:
                if os.path.exists(intermediate_path) and intermediate_path != output_path:
                    os.remove(intermediate_path)
                    logger.debug(f"Cleaned up intermediate file: {intermediate_path}")
            except Exception as e:
                logger.warning(f"Error cleaning up intermediate file: {str(e)}")
            
            if not music_result.get("success", False):
                return {"success": False, "error": f"Music enhancement failed: {music_result.get('error', 'Unknown error')}"}
                
            logger.info(f"Background music added: {music_result.get('music_added', False)}")
            
            return {
                "success": True,
                "output_video": output_path,
                "text_overlay": overlay_result.get("text"),
                "music_added": music_result.get("music_added", False)
            }
        
        except Exception as e:
            logger.error(f"Error adding background music: {str(e)}")
            # If music fails but we have text overlay, return partial success
            return {
                "success": True,
                "partial": True,
                "output_video": intermediate_path,
                "text_overlay": overlay_result.get("text"),
                "music_added": False,
                "music_error": str(e)
            }

def main():
    parser = argparse.ArgumentParser(description="Enhance videos with AI-generated text overlays and background music")
    parser.add_argument("--input", "-i", required=True, help="Path to input video")
    parser.add_argument("--output", "-o", help="Path to output video (optional)")
    parser.add_argument("--music", "-m", action="store_true", help="Add background music")
    parser.add_argument("--music-path", help="Path to music file (optional)")
    parser.add_argument("--position", "-p", default="TOP", 
                        choices=[p.name for p in Position], 
                        help="Position of text overlay")
    parser.add_argument("--font-scale", "-f", type=float, default=1.2, help="Font scale (size)")
    parser.add_argument("--style", "-s", default="BLACK_BG_WHITE_TEXT", 
                        choices=[s.name for s in Style],
                        help="Text style")
    parser.add_argument("--text", "-t", help="Custom text (optional, bypasses analysis)")
    parser.add_argument("--api-key", "-k", help="OpenAI API key (optional)")
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or get_api_key()
    if not api_key:
        print("Warning: No OpenAI API key provided. Some features may be limited.")
    
    print(f"=== STARTING COMBINED VIDEO ENHANCEMENT ===")
    
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
        api_key=api_key
    )
    
    # Display results
    if result.get("success", False):
        print(f"Success! Enhanced video saved to: {result['output_video']}")
        print(f"Text overlay: '{result.get('text_overlay', 'N/A')}'")
        
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
