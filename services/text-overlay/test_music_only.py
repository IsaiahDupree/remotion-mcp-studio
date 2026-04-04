#!/usr/bin/env python3
"""
Quick Music Enhancement Test - Direct FFmpeg Implementation
=========================

This script directly uses ffmpeg to:
1. Add background music to a video using a simplified efficient approach
2. Optimizes for speed and reliability
3. Preserves video quality while ensuring playable output

Usage:
    python test_music_only.py
"""

import os
import sys
import logging
import subprocess
import time
import re
from pathlib import Path

# Target video and music paths
TARGET_VIDEO_PATH = r"C:\Users\Isaia\Documents\N8N\shared_data\copy_E69DC408-5335-401B-8FE1-BB017EECFCFB.MP4"
MUSIC_FILE = r"C:\Users\Isaia\Documents\WordsOnText\downloaded_music\Flux Pavilion - Bass Cannon (Shanghai Doom Flip) - Shanghai Doom.mp3"
OUTPUT_DIR = r"C:\Users\Isaia\Documents\WordsOnText\enhanced_videos"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "direct_enhanced_with_music.mp4")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("music_direct")

def detect_speech(video_path):
    """
    Detect speech in a video to determine appropriate background music volume.
    
    Args:
        video_path: Path to video file
        
    Returns:
        has_speech: Boolean indicating if speech was detected
    """
    logger.info("Detecting speech in video...")
    
    # Use ffprobe silencedetect to identify silence segments
    cmd = [
        'ffprobe',
        '-i', video_path,
        '-af', 'silencedetect=noise=-30dB:d=0.5',  # Detect silence below -30dB lasting at least 0.5 seconds
        '-f', 'null',
        '-'
    ]
    
    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        # Count silence segments
        silence_count = 0
        total_silence_duration = 0
        for line in process.stderr.splitlines():
            if 'silence_end' in line:
                silence_count += 1
                # Extract duration from pattern like: silence_end: 2.94538 | silence_duration: 0.825397
                duration_match = re.search(r'silence_duration:\s+([\d\.]+)', line)
                if duration_match:
                    total_silence_duration += float(duration_match.group(1))
        
        # Analyze silence pattern to determine speech presence
        logger.info(f"Detected {silence_count} silence segments with total duration: {total_silence_duration:.2f} seconds")
        
        # Determine if there's likely speech based on silence pattern
        # If many short silences, likely speech with pauses
        # If few long silences, likely no speech or sparse speech
        has_speech = silence_count >= 3 and total_silence_duration < 30
        logger.info(f"Speech detected: {has_speech}")
        return has_speech
    
    except Exception as e:
        logger.warning(f"Failed to detect speech: {e}")
        # Default to assuming there is speech if detection fails
        return True


def add_music_to_video(video_path, music_path, output_path, volume_factor=0.3, speech_emphasis_factor=1.5):
    """
    Add background music to video using direct ffmpeg command.
    
    Args:
        video_path: Path to input video
        music_path: Path to music file
        output_path: Path to save enhanced video
        volume_factor: Volume level for background music (0.0-1.0)
    
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return False
        
    if not os.path.exists(music_path):
        logger.error(f"Music file not found: {music_path}")
        return False
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Detect if the video has speech
    has_speech = detect_speech(video_path)
    
    # Adjust volume based on speech detection
    if has_speech:
        # If speech detected, lower the background music volume more
        adjusted_volume = volume_factor / speech_emphasis_factor
        logger.info(f"Speech detected, reducing background music volume: {volume_factor} → {adjusted_volume:.3f}")
    else:
        # If no speech detected, use standard volume
        adjusted_volume = volume_factor
        logger.info(f"No speech detected, using standard volume: {adjusted_volume}")
        
    # Get video duration for progress reporting
    video_duration = 0
    duration_cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    
    try:
        duration_result = subprocess.run(
            duration_cmd, 
            capture_output=True,
            text=True,
            check=False
        )
        video_duration = float(duration_result.stdout.strip())
        logger.info(f"Video duration: {video_duration:.2f} seconds")
    except Exception as e:
        logger.warning(f"Could not get video duration: {e}")
    
    # Try much simpler approach - just extract audio from video and music, then merge after
    temp_video_audio = os.path.join(os.path.dirname(output_path), "temp_video_audio.wav")
    temp_music_audio = os.path.join(os.path.dirname(output_path), "temp_music_audio.wav")
    temp_mixed_audio = os.path.join(os.path.dirname(output_path), "temp_mixed_audio.wav")
    
    try:
        # Extract audio from video
        logger.info("Extracting audio from video")
        extract_video_audio_cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            temp_video_audio
        ]
        subprocess.run(extract_video_audio_cmd, check=True, capture_output=True)
        
        # Extract audio from music file
        logger.info("Extracting audio from music")
        extract_music_audio_cmd = [
            'ffmpeg', '-y',
            '-i', music_path,
            '-vn', '-acodec', 'pcm_s16le',
            temp_music_audio
        ]
        subprocess.run(extract_music_audio_cmd, check=True, capture_output=True)
        
        # Mix the two audio files
        logger.info("Mixing audio files")
        mix_audio_cmd = [
            'ffmpeg', '-y',
            '-i', temp_video_audio,
            '-i', temp_music_audio,
            '-filter_complex', f'[1:a]volume={adjusted_volume}[music];[0:a][music]amix=inputs=2:duration=first[out]',
            '-map', '[out]',
            temp_mixed_audio
        ]
        subprocess.run(mix_audio_cmd, check=True, capture_output=True)
        
        # Now create output video with original video and mixed audio
        logger.info("Creating final video with mixed audio")
        final_cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', temp_mixed_audio,
            '-c:v', 'copy',           # Copy video stream without re-encoding
            '-map', '0:v',            # Use video from first input
            '-map', '1:a',            # Use audio from second input
            '-c:a', 'aac',            # Convert audio to AAC
            '-b:a', '128k',           # Lower audio bitrate
            '-shortest',               # End when shortest input ends
            output_path
        ]
        
        logger.info("Starting final ffmpeg process...")
        start_time = time.time()
        max_time = 300  # 5 minutes maximum
        
        process = subprocess.run(
            final_cmd,
            capture_output=True,
            text=True,
            timeout=max_time
        )
        
        logger.info(f"FFmpeg process completed with exit code: {process.returncode}")
        
        # Check stderr for issues
        for line in process.stderr.split('\n'):
            if 'Error' in line or 'error' in line:
                logger.error(f"FFmpeg error: {line}")
        
        # Process finished
        total_time = time.time() - start_time
        
        # Check if output file was created
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            logger.info(f"Successfully added music to video in {total_time:.2f} seconds")
            logger.info(f"Enhanced video saved to: {output_path}")
            return True
        else:
            logger.error("Failed to create enhanced video file")
            return False
            
    except Exception as e:
        logger.error(f"Error adding music to video: {e}")
        return False

def main():
    """Main function to run the test."""
    logger.info("=== Starting Direct Music Enhancement Test ===")
    
    if not os.path.exists(TARGET_VIDEO_PATH):
        logger.error(f"Target video not found: {TARGET_VIDEO_PATH}")
        return 1
        
    if not os.path.exists(MUSIC_FILE):
        logger.error(f"Music file not found: {MUSIC_FILE}")
        return 1
        
    # Add background music to video
    success = add_music_to_video(
        video_path=TARGET_VIDEO_PATH,
        music_path=MUSIC_FILE,
        output_path=OUTPUT_PATH,
        volume_factor=0.06,      # Base volume for background music (6%, approximately -24dB)
        speech_emphasis_factor=1.5  # Further reduce volume if speech detected
    )
    
    if success:
        logger.info("=== Music Enhancement Successful ===")
        return 0
    else:
        logger.error("=== Music Enhancement Failed ===")
        return 1

if __name__ == "__main__":
    sys.exit(main())
