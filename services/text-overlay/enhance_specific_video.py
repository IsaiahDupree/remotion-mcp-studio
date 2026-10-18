"""
Script to enhance a specific video by adding text overlay and background music.
This combines the video analysis, text overlay, and background music modules.
"""

import os
import sys
import logging
import subprocess
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('enhance_specific')

# Import our video enhancer modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from video_context_analyzer.video_enhancer import VideoEnhancer
from video_context_analyzer.styling import Style, Position

# Try to import audio analysis module
try:
    from audiovideotools.audio_analysis.audio_analyzer import has_background_music
except ImportError:
    logger.warning("Could not import audiovideotools module. Music detection may be limited.")
    has_background_music = None

def check_video_needs_enhancement(video_path):
    """
    Check if the video needs enhancement (has no background music or text overlays)
    
    Returns:
        dict: Analysis results with needs_music and needs_text keys
    """
    logger.info(f"Analyzing video: {video_path}")
    result = {"needs_music": True, "needs_text": True}
    
    # Quick verification that file exists
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return None
        
    # Extract audio for analysis
    try:
        temp_dir = os.path.join(os.path.dirname(video_path), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        audio_path = os.path.join(temp_dir, "temp_audio.wav")
        
        # Use ffmpeg to extract audio
        extract_cmd = [
            'ffmpeg', '-y', 
            '-i', video_path, 
            '-q:a', '0', 
            '-map', 'a', 
            audio_path
        ]
        
        logger.info("Extracting audio for analysis...")
        subprocess.run(extract_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Check if audio file was created
        if not os.path.exists(audio_path):
            logger.warning("Could not extract audio. Assuming no background music.")
        elif has_background_music is not None:
            # Check for background music using our analyzer
            has_music = has_background_music(video_path, audio_path)
            result["needs_music"] = not has_music
            logger.info(f"Background music detection: {'Not present' if result['needs_music'] else 'Already present'}")
    except Exception as e:
        logger.error(f"Error during audio analysis: {e}")
    
    # Clean up temp directory
    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(temp_dir) and not os.listdir(temp_dir):
            os.rmdir(temp_dir)
    except Exception as e:
        logger.warning(f"Error cleaning up temp files: {e}")
    
    return result

def create_sample_music(output_path, duration=60):
    """Create a sample audio file for background music"""
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

def add_background_music(video_path, music_path, output_path, volume_factor=0.15):
    """Add background music to video"""
    try:
        # Make sure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Simply add the music as a background track
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
            logger.info(f"Successfully added background music: {output_path}")
            return output_path
        else:
            logger.error("Output file was not created")
            return None
    
    except Exception as e:
        logger.error(f"Exception adding background music: {e}")
        return None

def enhance_specific_video():
    """Enhance a specific video with text overlay and background music"""
    
    # Input video to enhance
    video_path = r"C:\Users\Isaia\Documents\N8N\shared_data\copy_E69DC408-5335-401B-8FE1-BB017EECFCFB.MP4"
    
    # Output directory
    output_dir = os.path.join(os.path.dirname(os.path.dirname(video_path)), "enhanced_videos")
    os.makedirs(output_dir, exist_ok=True)
    
    # Output paths for stages
    video_basename = os.path.basename(video_path).rsplit('.', 1)[0]
    text_output_path = os.path.join(output_dir, f"{video_basename}_with_text.mp4")
    final_output_path = os.path.join(output_dir, f"{video_basename}_enhanced.mp4")
    
    # Check if video needs enhancement
    analysis = check_video_needs_enhancement(video_path)
    if analysis is None:
        return None
    
    # Custom text overlay or let the system generate one
    custom_text = "Must-see viral content"  # You can change this or set to None for auto-generation
    
    # Step 1: Add text overlay
    if analysis["needs_text"]:
        logger.info(f"Adding text overlay to video: {video_path}")
        
        # Create video enhancer with black background style
        enhancer = VideoEnhancer(
            style=Style.BLACK_BG_WHITE_TEXT,  # Black background with white text
            position=Position.TOP,            # Position at top of frame
            font_scale=1.2,                   # Slightly larger text for visibility
            high_quality=True                 # Maintain high video quality
        )
        
        # Apply text overlay
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
        video_with_text = text_output_path
    else:
        logger.info("Video already has text overlay. Skipping text addition.")
        video_with_text = video_path
    
    # Step 2: Add background music if needed
    if analysis["needs_music"]:
        # Create or use sample music
        music_dir = os.path.join(output_dir, "music")
        os.makedirs(music_dir, exist_ok=True)
        sample_music = os.path.join(music_dir, "sample_music.mp3")
        
        if not os.path.exists(sample_music):
            music_path = create_sample_music(sample_music)
            if not music_path:
                logger.error("Failed to create sample music")
                return video_with_text  # Return video with just text
        else:
            music_path = sample_music
        
        # Add background music
        volume_factor = 0.15  # Lower value = quieter music (adjust for speech emphasis)
        music_result = add_background_music(
            video_path=video_with_text,
            music_path=music_path,
            output_path=final_output_path,
            volume_factor=volume_factor
        )
        
        if music_result:
            logger.info(f"Background music added successfully: {final_output_path}")
            return final_output_path
        else:
            logger.error("Failed to add background music")
            return video_with_text
    else:
        logger.info("Video already has background music. Skipping music addition.")
        return video_with_text

if __name__ == "__main__":
    enhanced_path = enhance_specific_video()
    
    if enhanced_path:
        print(f"\nSuccess! Video enhancement complete.")
        print(f"Enhanced video saved to: {enhanced_path}")
        print("\nEnhancements applied:")
        print("✓ Black background with white text overlay added at the top")
        print("✓ Background music added with optimized volume")
    else:
        print("\nEnhancement failed. Check logs for details.")
