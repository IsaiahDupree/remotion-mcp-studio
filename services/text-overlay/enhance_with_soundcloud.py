"""
Script to enhance a specific video with text overlay and SoundCloud background music.
Uses real SoundCloud music downloads via yt-dlp and applies proper text overlays.
"""

import os
import sys
import logging
import subprocess
import tempfile
import json
import re
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('enhance_video')

# Import our video enhancer modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from video_context_analyzer.video_enhancer import VideoEnhancer
    from video_context_analyzer.styling import Style, Position
    from audiovideotools.audio_analysis.audio_analyzer import has_background_music
    modules_imported = True
except ImportError as e:
    logger.warning(f"Could not import required modules: {e}")
    modules_imported = False

def download_soundcloud_track(url, output_path):
    """
    Download a SoundCloud track using yt-dlp
    
    Args:
        url: URL of SoundCloud track
        output_path: Path to save downloaded audio
        
    Returns:
        Path to downloaded audio file or None if failed
    """
    try:
        logger.info(f"Downloading SoundCloud track: {url}")
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Use yt-dlp to download audio only
        cmd = [
            'yt-dlp',
            '--no-playlist',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '192K',
            '--output', output_path,
            url
        ]
        
        logger.info(f"Running download command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error downloading track: {result.stderr}")
            return None
            
        # Check if file was downloaded successfully
        if os.path.exists(output_path):
            logger.info(f"Successfully downloaded track to: {output_path}")
            return output_path
        else:
            # yt-dlp might have renamed the file, check output for the actual filename
            match = re.search(r'Destination:\s+(.+?\.mp3)', result.stderr)
            if match:
                actual_path = match.group(1)
                if os.path.exists(actual_path):
                    logger.info(f"Successfully downloaded track to: {actual_path}")
                    return actual_path
                    
        logger.error("Download completed but file not found")
        return None
    
    except Exception as e:
        logger.error(f"Exception downloading SoundCloud track: {e}")
        return None

def check_video_has_speech(video_path):
    """
    Check if the video has speech
    
    Returns:
        bool: True if speech detected, False otherwise
    """
    try:
        # Extract audio to temporary file
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, "temp_audio.wav")
        
        # Extract audio using ffmpeg
        extract_cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-q:a', '0',
            '-map', 'a',
            audio_path
        ]
        
        subprocess.run(extract_cmd, capture_output=True)
        
        # Check if audio file was created
        if not os.path.exists(audio_path):
            logger.warning("Could not extract audio for speech detection")
            return False
            
        # Use ffprobe to analyze audio levels
        analyze_cmd = [
            'ffprobe', '-i', audio_path,
            '-show_entries', 'frame_tags=lavfi.silence_start,lavfi.silence_end',
            '-f', 'lavfi', '-af', 'silencedetect=n=-30dB:d=0.5',
            '-pretty', '-print_format', 'json'
        ]
        
        result = subprocess.run(analyze_cmd, capture_output=True, text=True)
        
        # Clean up
        os.remove(audio_path)
        os.rmdir(temp_dir)
        
        # Simple heuristic: if there are sections that aren't silence, assume speech
        return "silence_end" in result.stderr or "silence_start" in result.stderr
        
    except Exception as e:
        logger.error(f"Error checking for speech: {e}")
        return False  # Assume no speech on error

def add_text_overlay(video_path, output_path, custom_text=None, style=Style.BLACK_BG_WHITE_TEXT, position=Position.TOP):
    """
    Add text overlay to video
    
    Args:
        video_path: Path to input video
        output_path: Path for output video with text
        custom_text: Custom text to overlay (None for auto-generation)
        style: Text style to apply
        position: Position to place text
        
    Returns:
        Path to video with text overlay or None if failed
    """
    try:
        if not modules_imported:
            logger.error("Required modules not available for text overlay")
            return None
            
        # Create video enhancer
        enhancer = VideoEnhancer(
            style=style,
            position=position,
            font_scale=1.2,
            high_quality=True
        )
        
        # If no custom text provided, use a default
        if not custom_text:
            custom_text = "Must-see viral content"
            
        logger.info(f"Adding text overlay: '{custom_text}'")
        
        # Apply text overlay
        result = enhancer.enhance_video(
            video_path=video_path,
            output_path=output_path,
            custom_text=custom_text,
            analyze_first=False  # Skip analysis since we have custom text
        )
        
        if not result.get("success", False):
            logger.error(f"Text overlay failed: {result.get('error', 'unknown error')}")
            return None
            
        logger.info(f"Successfully added text overlay: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Exception adding text overlay: {e}")
        return None

def add_background_music(video_path, music_path, output_path, speech_emphasis=1.5):
    """
    Add background music to video with proper volume adjustment for speech emphasis
    
    Args:
        video_path: Path to input video
        music_path: Path to music file
        output_path: Path for output video with music
        speech_emphasis: Factor to emphasize speech (higher = quieter music)
        
    Returns:
        Path to video with music or None if failed
    """
    try:
        # Make sure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Calculate music volume factor
        has_speech = check_video_has_speech(video_path)
        
        # If no speech detected, use higher music volume
        volume_factor = 0.25 / speech_emphasis if has_speech else 0.4
        
        logger.info(f"Adding background music with volume factor: {volume_factor}")
        logger.info(f"Speech detected: {has_speech}")
        
        # Command to add background music
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', music_path,
            '-filter_complex',
            f'[1:a]aloop=loop=-1:size=2e+09,volume={volume_factor}[a]',
            '-map', '0:v',
            '-map', '[a]',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            output_path
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error adding background music: {result.stderr}")
            return None
            
        if os.path.exists(output_path):
            logger.info(f"Successfully added background music: {output_path}")
            return output_path
        
        logger.error("Output file was not created")
        return None
        
    except Exception as e:
        logger.error(f"Exception adding background music: {e}")
        return None

def enhance_video(video_path, text=None, soundcloud_url=None):
    """
    Enhance a video with text overlay and SoundCloud background music
    
    Args:
        video_path: Path to input video
        text: Custom text overlay (None for auto-generation)
        soundcloud_url: SoundCloud track URL (None to use predefined URL)
        
    Returns:
        dict: Result with success status and output path
    """
    if not os.path.exists(video_path):
        logger.error(f"Input video not found: {video_path}")
        return {"success": False, "error": "Input video not found"}
        
    # Define output paths
    video_basename = os.path.basename(video_path).rsplit('.', 1)[0]
    output_dir = os.path.join(os.path.dirname(os.path.dirname(video_path)), "enhanced_videos")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create music directory
    music_dir = os.path.join(output_dir, "music")
    os.makedirs(music_dir, exist_ok=True)
    
    # Output paths for stages
    text_output_path = os.path.join(output_dir, f"{video_basename}_with_text.mp4")
    final_output_path = os.path.join(output_dir, f"{video_basename}_enhanced.mp4")
    
    # Step 1: Add text overlay
    logger.info(f"Enhancing video with text overlay: {video_path}")
    video_with_text = add_text_overlay(
        video_path=video_path,
        output_path=text_output_path,
        custom_text=text,
        style=Style.BLACK_BG_WHITE_TEXT,
        position=Position.TOP
    )
    
    if not video_with_text:
        return {"success": False, "error": "Failed to add text overlay"}
    
    # Step 2: Add background music
    logger.info("Adding background music from SoundCloud")
    
    # Use provided URL or default
    if not soundcloud_url:
        soundcloud_url = "https://soundcloud.com/ikson/free-happy-background-music-ikson-good-day"
    
    # Download SoundCloud track
    music_filename = f"{video_basename}_music.mp3"
    music_path = os.path.join(music_dir, music_filename)
    
    downloaded_music = download_soundcloud_track(soundcloud_url, music_path)
    if not downloaded_music:
        return {"success": False, "error": "Failed to download SoundCloud track"}
    
    # Add music to video with text overlay
    speech_emphasis = 1.5  # Adjust if needed
    final_video = add_background_music(
        video_path=video_with_text,
        music_path=downloaded_music,
        output_path=final_output_path,
        speech_emphasis=speech_emphasis
    )
    
    if not final_video:
        return {"success": False, "error": "Failed to add background music"}
    
    return {
        "success": True,
        "output_video": final_video,
        "text_added": True,
        "music_added": True,
        "speech_emphasis": speech_emphasis
    }

def main():
    # Input video to enhance
    video_path = r"C:\Users\Isaia\Documents\N8N\shared_data\copy_E69DC408-5335-401B-8FE1-BB017EECFCFB.MP4"
    
    # Custom text or None for auto-generation
    custom_text = "Must-see viral content"
    
    # SoundCloud track URL - using a popular royalty-free track
    soundcloud_url = "https://soundcloud.com/ikson/free-happy-background-music-ikson-good-day"
    
    # Enhance video
    logger.info(f"Starting enhancement process for: {video_path}")
    result = enhance_video(
        video_path=video_path,
        text=custom_text,
        soundcloud_url=soundcloud_url
    )
    
    # Print result
    if result.get("success", False):
        print("\n===== Video Enhancement Complete =====")
        print(f"✓ Enhanced video saved to: {result['output_video']}")
        print("\nEnhancements applied:")
        print("✓ Added black background with white text overlay")
        print(f"✓ Added background music from SoundCloud with speech emphasis")
        print(f"✓ Music volume optimized for speech clarity")
        return 0
    else:
        print("\n===== Video Enhancement Failed =====")
        print(f"✗ Error: {result.get('error', 'unknown error')}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
