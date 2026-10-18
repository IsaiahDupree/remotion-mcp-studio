"""
Simple direct script to add background music to a video.
This version uses a very basic approach to ensure compatibility.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("add_music")

def create_sample_music(output_path, duration=30):
    """Create a simple sample audio file for testing"""
    try:
        # Generate a simple sine wave audio file
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'sine=frequency=440:duration={duration}',
            '-c:a', 'mp3',
            '-b:a', '192k',
            output_path
        ]
        
        logger.info(f"Creating sample music file: {output_path}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error creating sample music: {result.stderr}")
            return None
            
        if os.path.exists(output_path):
            logger.info(f"Created sample music: {output_path}")
            return output_path
        return None
    except Exception as e:
        logger.error(f"Exception creating sample music: {e}")
        return None

def add_background_music_basic(video_path, music_path, output_path, volume_factor=0.2):
    """Add background music to video using the simplest possible approach"""
    try:
        # Make sure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Simply add the music as a quieter background track
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,      # Input video
            '-i', music_path,      # Input music
            '-filter_complex',
            f'[1:0]aloop=loop=-1:size=2e+09,volume={volume_factor}[a]',  # Loop music and set volume
            '-map', '0:v',         # Map video from first input
            '-map', '[a]',         # Map processed audio
            '-c:v', 'copy',        # Copy video stream
            '-c:a', 'aac',         # AAC audio codec
            '-shortest',           # End when shortest input ends
            output_path
        ]
        
        logger.info(f"Adding background music with volume factor: {volume_factor}")
        logger.info(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check result
        if result.returncode != 0:
            logger.error(f"Error adding background music: {result.stderr}")
            return None
            
        if os.path.exists(output_path):
            logger.info(f"Successfully created enhanced video: {output_path}")
            return output_path
        else:
            logger.error("Output file was not created")
            return None
    
    except Exception as e:
        logger.error(f"Exception adding background music: {e}")
        return None

def main():
    # Input video with text overlay
    input_video = r"C:\Users\Isaia\Documents\WordsOnText\enhanced_videos\enhanced_demo_with_text.mp4"
    
    if not os.path.exists(input_video):
        logger.error(f"Input video not found: {input_video}")
        return 1
        
    # Output path
    output_dir = r"C:\Users\Isaia\Documents\WordsOnText\enhanced_videos"
    os.makedirs(output_dir, exist_ok=True)
    output_video = os.path.join(output_dir, "final_enhanced_video.mp4")
    
    # Create music directory
    music_dir = os.path.join(output_dir, "music")
    os.makedirs(music_dir, exist_ok=True)
    
    # Create or use sample music
    sample_music = os.path.join(music_dir, "sample_music.mp3")
    if not os.path.exists(sample_music):
        music_path = create_sample_music(sample_music)
        if not music_path:
            logger.error("Failed to create sample music")
            return 1
    else:
        music_path = sample_music
    
    # Add background music
    volume_factor = 0.15  # Lower value = quieter music
    result = add_background_music_basic(
        video_path=input_video,
        music_path=music_path,
        output_path=output_video,
        volume_factor=volume_factor
    )
    
    if result:
        print(f"\nSuccess! Enhanced video with text overlay and background music saved to:")
        print(f"✓ {output_video}")
        print("\nEnhancements applied:")
        print("✓ Black background with white text overlay at the top")
        print(f"✓ Background music added with volume factor: {volume_factor} (lower is quieter)")
        return 0
    else:
        print("\nFailed to add background music. Check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
