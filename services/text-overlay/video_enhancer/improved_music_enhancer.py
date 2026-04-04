#!/usr/bin/env python3
"""
Improved Music Enhancer Module
==============================

This module provides functionality to enhance videos with background music
using a more efficient multi-step approach. Key features:

1. Speech detection to determine appropriate background music volume
2. Fast processing through multi-step audio extraction and mixing
3. Configurable volume levels and speech emphasis
4. Reliable implementation with proper error handling
"""

import os
import re
import time
import logging
import tempfile
import subprocess
from typing import Optional, Tuple, List, Dict

from utils.soundcloud_ytdlp import SoundCloudYtDlp

# Configure logger
logger = logging.getLogger(__name__)

class ImprovedMusicEnhancer:
    """Enhanced version of MusicEnhancer with faster processing and better speech detection."""
    
    def __init__(self, output_dir: str = "enhanced_videos", music_dir: str = "enhanced_videos/music"):
        """
        Initialize the Music Enhancer.
        
        Args:
            output_dir: Directory to save enhanced videos
            music_dir: Directory to save downloaded music
        """
        self.output_dir = output_dir
        self.music_dir = music_dir
        
        # Create output directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.music_dir, exist_ok=True)
        
        # Initialize SoundCloud downloader
        self.sc_downloader = SoundCloudYtDlp(output_dir=self.music_dir)
        logger.info("SoundCloud downloader initialized")
        
    def download_music_from_excel(self, excel_path: str, sheet_name: str = "Sheet1", url_column: str = "Url") -> Optional[str]:
        """
        Download music from the first SoundCloud URL in an Excel file.
        
        Args:
            excel_path: Path to Excel file
            sheet_name: Name of sheet containing URLs
            url_column: Column name with URLs
            
        Returns:
            Path to downloaded music file or None if failed
        """
        try:
            import pandas as pd
            
            # Read Excel file
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            # Find SoundCloud URLs
            for _, row in df.iterrows():
                if url_column in row and isinstance(row[url_column], str):
                    url = row[url_column].strip()
                    if "soundcloud.com" in url.lower():
                        # Try to download from SoundCloud
                        result = self.sc_downloader.download_track(url)
                        if result:
                            logger.info(f"Successfully downloaded: {result}")
                            return result
            
            logger.warning("No valid SoundCloud URLs found in Excel file")
            return None
            
        except Exception as e:
            logger.error(f"Error downloading music from Excel: {e}")
            return None
            
    def detect_speech(self, video_path: str) -> bool:
        """
        Detect speech in video using silence detection.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Boolean indicating if speech was detected
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
            
    def add_background_music(self, video_path: str, music_path: str,
                           output_path: str = None,
                           volume_factor: float = 0.06,  # Approximately -24dB
                           speech_emphasis_factor: float = 1.5) -> Optional[str]:
        """
        Add background music to a video using the faster multi-step approach.
        
        Args:
            video_path: Path to input video
            music_path: Path to music file
            output_path: Path to save enhanced video (if None, will generate one)
            volume_factor: Base volume factor for background music (0.0-1.0)
            speech_emphasis_factor: Factor to reduce music volume if speech detected
            
        Returns:
            Path to enhanced video or None if failed
        """
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return None
            
        if not os.path.exists(music_path):
            logger.error(f"Music file not found: {music_path}")
            return None
            
        # Generate output path if not provided
        if output_path is None:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(self.output_dir, f"{video_name}_enhanced.mp4")
            
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Detect if the video has speech
        has_speech = self.detect_speech(video_path)
        
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
        
        # Create temporary directory for intermediate files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_video_audio = os.path.join(temp_dir, "temp_video_audio.wav")
            temp_music_audio = os.path.join(temp_dir, "temp_music_audio.wav")
            temp_mixed_audio = os.path.join(temp_dir, "temp_mixed_audio.wav")
            
            try:
                # Step 1: Extract audio from video
                logger.info("Extracting audio from video")
                extract_video_audio_cmd = [
                    'ffmpeg', '-y',
                    '-i', video_path,
                    '-vn', '-acodec', 'pcm_s16le',
                    temp_video_audio
                ]
                subprocess.run(extract_video_audio_cmd, check=True, capture_output=True)
                
                # Step 2: Extract audio from music file
                logger.info("Extracting audio from music")
                extract_music_audio_cmd = [
                    'ffmpeg', '-y',
                    '-i', music_path,
                    '-vn', '-acodec', 'pcm_s16le',
                    temp_music_audio
                ]
                subprocess.run(extract_music_audio_cmd, check=True, capture_output=True)
                
                # Step 3: Mix the audio files
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
                
                # Step 4: Create final video with original video and mixed audio
                logger.info("Creating final video with mixed audio")
                final_cmd = [
                    'ffmpeg', '-y',
                    '-i', video_path,
                    '-i', temp_mixed_audio,
                    '-c:v', 'copy',           # Copy video stream without re-encoding
                    '-map', '0:v',            # Use video from first input
                    '-map', '1:a',            # Use audio from second input
                    '-c:a', 'aac',            # Convert audio to AAC
                    '-b:a', '128k',           # Audio bitrate
                    '-shortest',              # End when shortest input ends
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
                
                # Check for errors in stderr
                for line in process.stderr.split('\n'):
                    if 'Error' in line or 'error' in line:
                        logger.error(f"FFmpeg error: {line}")
                
                # Process finished
                total_time = time.time() - start_time
                
                # Verify output file exists and has content
                if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                    logger.info(f"Successfully added background music in {total_time:.2f} seconds")
                    logger.info(f"Enhanced video saved to: {output_path}")
                    return output_path
                else:
                    logger.error("Failed to create enhanced video file")
                    return None
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Process timed out after {max_time} seconds")
                return None
            except Exception as e:
                logger.error(f"Error adding background music: {e}")
                return None
