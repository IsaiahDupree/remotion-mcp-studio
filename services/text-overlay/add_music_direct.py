"""
Simple direct script to add background music to a video with proper speech emphasis.
This script focuses on reliability and simplicity by using direct ffmpeg commands.
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

def add_background_music(video_path, music_path, output_path, speech_emphasis=1.5):
    """Add background music to video with appropriate speech emphasis"""
    try:
        # Make sure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Set volume factor based on speech emphasis (higher emphasis = quieter music)
        music_volume = 0.25 / speech_emphasis
        
        # Extract original audio to temporary file
        temp_audio = os.path.join(os.path.dirname(output_path), "temp_audio.aac")
        extract_cmd = [
            'ffmpeg', '-y', 
            '-i', video_path, 
            '-vn', '-acodec', 'copy', 
            temp_audio
        ]
        
        logger.info(f"Extracting original audio: {temp_audio}")
        subprocess.run(extract_cmd, capture_output=True, text=True)
        
        if not os.path.exists(temp_audio):
            logger.error("Failed to extract original audio")
            return None
            
        # Run ffmpeg command to add background music
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', music_path,
            '-i', temp_audio,
            '-filter_complex',
            f'[1:a]aloop=loop=-1:size=2e+09,volume={music_volume}[background];' + 
            '[2:a]volume=1.0[speech];' + 
            '[background][speech]amix=inputs=2:duration=first',
            '-c:v', 'copy',  # Copy video stream without re-encoding
            '-c:a', 'aac',   # AAC audio codec
            '-b:a', '192k',  # Good quality audio
            output_path
        ]
        
        logger.info(f"Adding background music with speech emphasis factor: {speech_emphasis}")
        logger.info(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up temp file
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        
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
    speech_emphasis = 1.5  # Higher value = quieter music, more speech emphasis
    result = add_background_music(
        video_path=input_video,
        music_path=music_path,
        output_path=output_video,
        speech_emphasis=speech_emphasis
    )
    
    if result:
        print(f"\nSuccess! Enhanced video with text overlay and background music saved to:")
        print(f"✓ {output_video}")
        print("\nEnhancements applied:")
        print("✓ Black background with white text overlay at the top")
        print(f"✓ Background music added with speech emphasis factor: {speech_emphasis}")
        return 0
    else:
        print("\nFailed to add background music. Check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
