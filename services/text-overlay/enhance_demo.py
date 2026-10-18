"""
Demo script to enhance a specific video with text overlay and optional background music.
Integrates with SoundCloud music download and volume optimization.
"""

import os
import sys
import logging
import subprocess
import json
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('enhance_demo')

# Import our video enhancer
from video_context_analyzer.video_enhancer import VideoEnhancer
from video_context_analyzer.styling import Style, Position

# For background music download and processing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from audiovideotools.audio_analysis.audio_analyzer import has_background_music
except ImportError:
    logger.warning("Could not import audiovideotools module. Music optimization may be limited.")
    has_background_music = None

def download_soundcloud_track(url, output_dir):
    """
    Download a SoundCloud track using yt-dlp
    
    Args:
        url: SoundCloud track URL
        output_dir: Directory to save the downloaded track
        
    Returns:
        Path to the downloaded audio file
    """
    try:
        # Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Use yt-dlp to download the track
        logger.info(f"Downloading SoundCloud track: {url}")
        
        # Set up command
        cmd = [
            'yt-dlp',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',  # Best quality
            '--output', f"{output_dir}/%(title)s.%(ext)s",
            url
        ]
        
        # Execute command
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error downloading track: {result.stderr}")
            return None
        
        # Parse output to find downloaded file path
        output_lines = result.stdout.split('\n')
        downloaded_file = None
        
        for line in output_lines:
            if '[download] Destination:' in line:
                downloaded_file = line.split('[download] Destination: ')[1].strip()
            if '[ExtractAudio] Destination:' in line:
                downloaded_file = line.split('[ExtractAudio] Destination: ')[1].strip()
        
        if not downloaded_file or not os.path.exists(downloaded_file):
            # Look for any mp3 file in the output directory
            mp3_files = list(Path(output_dir).glob('*.mp3'))
            if mp3_files:
                downloaded_file = str(mp3_files[0])
            else:
                logger.error("Could not find downloaded file")
                return None
                
        logger.info(f"SoundCloud track downloaded to: {downloaded_file}")
        return downloaded_file
    
    except Exception as e:
        logger.error(f"Error downloading SoundCloud track: {e}")
        return None

def add_background_music(video_path, music_path, output_path, speech_emphasis=1.5):
    """
    Add background music to a video with volume optimization
    
    Args:
        video_path: Path to input video
        music_path: Path to music track
        output_path: Path for output video
        speech_emphasis: Factor to emphasize speech over music
        
    Returns:
        Path to output video
    """
    try:
        # Volume optimization parameters
        audio_volume_factor = 0.25 * speech_emphasis  # Lower value = quieter music
        
        # Command to extract original audio
        temp_audio = os.path.join(os.path.dirname(output_path), "temp_original_audio.aac")
        extract_audio_cmd = [
            'ffmpeg', '-y', '-i', video_path, '-vn', '-acodec', 'copy', temp_audio
        ]
        
        # Run extraction
        subprocess.run(extract_audio_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Command to add background music with volume control
        add_music_cmd = [
            'ffmpeg', '-y',
            '-i', video_path,  # Original video
            '-i', music_path,  # Background music
            '-i', temp_audio,  # Original audio
            '-filter_complex',
            f'[1:a]aloop=loop=-1:size=2e+09,volume={audio_volume_factor}[background];' +
            '[2:a]volume=1.0[speech];' +
            '[background][speech]amix=inputs=2:duration=first',
            '-c:v', 'copy',  # Copy video stream
            '-c:a', 'aac', '-b:a', '192k',  # Good quality audio
            output_path
        ]
        
        # Run command to add music
        logger.info("Adding background music with optimized volume...")
        subprocess.run(add_music_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Clean up temp files
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
            
        if os.path.exists(output_path):
            logger.info(f"Background music added successfully: {output_path}")
            return output_path
        else:
            logger.error("Failed to add background music")
            return None
            
    except Exception as e:
        logger.error(f"Error adding background music: {e}")
        return None

def enhance_video(add_music=True):
    """
    Enhance a specific video with text overlay and optional background music
    
    Args:
        add_music: Whether to add background music
        
    Returns:
        Path to the enhanced video
    """
    # Input video to enhance
    video_path = r"C:\Users\Isaia\Documents\WordsOnText\output_videos\music_0024d0ff50d04b2eba719fec130a0b74.mp4"
    
    # Output directory
    output_dir = r"C:\Users\Isaia\Documents\WordsOnText\enhanced_videos"
    os.makedirs(output_dir, exist_ok=True)
    
    # Output paths
    text_output_path = os.path.join(output_dir, "enhanced_demo_with_text.mp4")
    final_output_path = os.path.join(output_dir, "enhanced_demo_complete.mp4")
    
    # Custom text overlay (or set to None to use AI-generated text)
    custom_text = "Must-see viral content"
    
    # Create video enhancer with black background style
    enhancer = VideoEnhancer(
        style=Style.BLACK_BG_WHITE_TEXT,  # Black background with white text
        position=Position.TOP,            # Position at top of frame
        font_scale=1.2,                   # Slightly larger text for visibility
        high_quality=True                 # Maintain high video quality
    )
    
    # Step 1: Add text overlay
    logger.info(f"Enhancing video with text overlay: {video_path}")
    logger.info(f"Initial output will be saved to: {text_output_path}")
    
    result = enhancer.enhance_video(
        video_path=video_path,
        output_path=text_output_path,
        custom_text=custom_text,
        analyze_first=True  # Analyze content first
    )
    
    if not result.get("success", False):
        logger.error(f"Text overlay enhancement failed: {result.get('error', 'unknown error')}")
        return None
    
    logger.info(f"Text overlay added successfully: {text_output_path}")
    
    # Step 2: Add background music if requested
    if add_music:
        # Check if input video already has background music
        has_music = False
        if has_background_music is not None:
            try:
                has_music = has_background_music(video_path)
                logger.info(f"Background music detection result: {has_music}")
            except Exception as e:
                logger.warning(f"Could not detect background music: {e}")
        
        if has_music:
            logger.info("Video already has background music. Skipping music addition.")
            return text_output_path
        
        # Download a sample SoundCloud track
        soundcloud_url = "https://soundcloud.com/royalty-free-music-soundcloud/cheerful-gaming-loop-pluck-dubstep-music"  # Sample track
        music_dir = os.path.join(output_dir, "music")
        music_path = download_soundcloud_track(soundcloud_url, music_dir)
        
        if not music_path:
            logger.error("Failed to download music. Using text overlay version only.")
            return text_output_path
        
        # Add background music with optimized volume
        music_result = add_background_music(
            video_path=text_output_path,
            music_path=music_path,
            output_path=final_output_path,
            speech_emphasis=1.5  # Emphasize original speech
        )
        
        if music_result:
            logger.info(f"Background music added successfully: {final_output_path}")
            return final_output_path
        else:
            logger.error("Failed to add background music. Using text overlay version.")
            return text_output_path
    
    # Return path to enhanced video
    return text_output_path

if __name__ == "__main__":
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Enhance a video with text overlay and background music")
    parser.add_argument("--no-music", action="store_true", help="Skip adding background music")
    parser.add_argument("--speech-emphasis", type=float, default=1.5, 
                      help="Factor to emphasize speech over music (higher = quieter music)")
    args = parser.parse_args()
    
    # Enhance the video
    enhanced_path = enhance_video(add_music=not args.no_music)
    
    if enhanced_path:
        print(f"\nSuccessfully enhanced video! Output saved to: {enhanced_path}")
        print("✓ Black background with white text overlay added at top of the video")
        if not args.no_music:
            print("✓ Background music added with speech emphasis")
    else:
        print("\nEnhancement failed. Check logs for details.")
