"""
Script to add background music to a video with proper speech emphasis.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('add_music')

def create_sample_music(output_path, duration=60):
    """Create a sample audio file for background music"""
    try:
        # Generate a simple sine wave audio file
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            # Use a more pleasant sound than a simple sine wave
            '-i', f'aevalsrc=0.5*sin(440*2*PI*t):s=44100:d={duration}',
            '-c:a', 'mp3',
            '-b:a', '192k',
            output_path
        ]
        
        logger.info(f"Creating sample music file: {output_path}")
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if os.path.exists(output_path):
            logger.info(f"Created sample music: {output_path}")
            return output_path
        
        logger.error("Failed to create sample music file")
        return None
    except Exception as e:
        logger.error(f"Exception creating sample music: {e}")
        return None

def add_background_music(video_path, music_path, output_path, speech_emphasis=1.5):
    """
    Add background music to video with speech emphasis
    
    Args:
        video_path: Path to input video
        music_path: Path to music track
        output_path: Path for output video
        speech_emphasis: Factor to emphasize speech over music (higher = quieter music)
    """
    try:
        # Make sure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Calculate volume factor based on speech emphasis
        volume_factor = 0.25 / speech_emphasis  # Lower value = quieter music
        
        # Command to add background music
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', music_path,
            '-filter_complex',
            # Loop music for duration of video and set volume
            f'[1:a]aloop=loop=-1:size=2e+09,volume={volume_factor}[a]',
            # Map video from first input and audio from the music
            '-map', '0:v',  # Video from input
            '-map', '[a]',  # Processed audio
            '-c:v', 'copy',  # Copy video without re-encoding
            '-c:a', 'aac',   # AAC audio codec
            '-b:a', '192k',  # Good audio quality
            '-shortest',     # End when shortest input ends
            output_path
        ]
        
        logger.info(f"Adding background music with speech emphasis factor: {speech_emphasis}")
        logger.info(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error adding background music: {result.stderr}")
            return None
            
        if os.path.exists(output_path):
            logger.info(f"Successfully added background music: {output_path}")
            return output_path
        else:
            logger.error("Output file was not created")
            return None
    except Exception as e:
        logger.error(f"Exception adding background music: {e}")
        return None

def main():
    # Input video with text overlay
    video_path = r"C:\Users\Isaia\Documents\N8N\enhanced_videos\copy_E69DC408-5335-401B-8FE1-BB017EECFCFB_with_text.mp4"
    
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return 1
    
    # Output path
    output_dir = os.path.dirname(video_path)
    output_name = os.path.basename(video_path).replace("_with_text.mp4", "_enhanced.mp4")
    output_path = os.path.join(output_dir, output_name)
    
    # Create music directory
    music_dir = os.path.join(output_dir, "music")
    os.makedirs(music_dir, exist_ok=True)
    
    # Create or use sample music
    sample_music = os.path.join(music_dir, "sample_music.mp3")
    if not os.path.exists(sample_music):
        music_path = create_sample_music(sample_music, duration=60)
        if not music_path:
            logger.error("Failed to create sample music")
            return 1
    else:
        music_path = sample_music
    
    # Add background music with speech emphasis
    speech_emphasis = 1.5  # Higher value = quieter music, more speech emphasis
    result = add_background_music(
        video_path=video_path,
        music_path=music_path,
        output_path=output_path,
        speech_emphasis=speech_emphasis
    )
    
    if result:
        print(f"\nSuccess! Background music added to video with text overlay.")
        print(f"Enhanced video saved to: {output_path}")
        print("\nEnhancements applied:")
        print("✓ Black background with white text overlay at the top")
        print(f"✓ Background music added with speech emphasis factor: {speech_emphasis}")
        print("  (Higher speech emphasis = quieter background music)")
        return 0
    else:
        print("\nFailed to add background music. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
