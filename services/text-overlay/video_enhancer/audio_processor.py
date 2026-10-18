"""
Audio Processor Module
=====================

This module provides audio processing functionality for video enhancement:
- Speech detection
- Audio extraction
- Audio mixing
- Volume adjustment

Used by the music enhancement module for intelligent audio processing.
"""

import os
import re
import time
import logging
import tempfile
import subprocess
from typing import Dict, Any, Optional, Tuple, List, Union
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("audio_processor")


class AudioProcessor:
    """
    Class for audio processing operations used in video enhancement.
    
    This class provides functionality to:
    1. Detect speech in videos
    2. Extract audio from videos
    3. Mix audio streams with dynamic volume adjustment
    4. Preprocess audio files for optimal mixing
    """
    
    def __init__(self, speech_emphasis: float = 1.5):
        """
        Initialize the AudioProcessor.
        
        Args:
            speech_emphasis: Factor to emphasize speech over music (higher = quieter music)
        """
        self.speech_emphasis = speech_emphasis
    
    def detect_speech_in_video(self, video_path: str) -> bool:
        """
        Detect if a video contains speech.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            True if speech detected, False otherwise
        """
        return self.has_speech(video_path)
        
    def has_speech(self, video_path: str) -> bool:
        """
        Check if a video has speech audio.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            True if speech detected, False otherwise
        """
        try:
            # Extract audio to temporary file
            with tempfile.TemporaryDirectory() as temp_dir:
                audio_path = os.path.join(temp_dir, "temp_audio.wav")
                
                # Extract audio using ffmpeg with improved settings
                extract_cmd = [
                    'ffmpeg', '-y',
                    '-i', video_path,
                    '-vn',  # No video
                    '-ar', '16000',  # Lower sampling rate for faster processing
                    '-ac', '1',  # Convert to mono
                    '-acodec', 'pcm_s16le',  # PCM format for better analysis
                    audio_path
                ]
                
                subprocess.run(extract_cmd, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                
                if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
                    logger.warning("Could not extract audio for speech detection or audio file is too small")
                    return False
                    
                # Use ffprobe to analyze audio levels with silencedetect filter
                speech_cmd = [
                    'ffprobe', '-i', audio_path,
                    '-af', 'silencedetect=n=-30dB:d=0.5',
                    '-f', 'null', '-'
                ]
                
                result = subprocess.run(
                    speech_cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Analyze silence detection output
                if result.stderr:
                    # Count silence periods
                    silence_count = result.stderr.count("silence_end")
                    total_silence = 0
                    
                    # Extract silence durations
                    silence_matches = re.finditer(r'silence_duration: ([\d\.]+)', result.stderr)
                    for match in silence_matches:
                        try:
                            silence_duration = float(match.group(1))
                            total_silence += silence_duration
                        except (ValueError, IndexError):
                            continue
                    
                    # Get total duration of the audio
                    duration_cmd = ['ffprobe', '-i', audio_path, '-show_entries', 'format=duration', 
                                  '-v', 'quiet', '-of', 'csv=p=0']
                    duration_result = subprocess.run(duration_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    
                    try:
                        total_duration = float(duration_result.stdout.strip())
                    except (ValueError, IndexError):
                        total_duration = 0
                    
                    # Determine if speech exists based on silence analysis
                    if total_duration > 0:
                        silence_ratio = total_silence / total_duration
                        
                        # If less than 70% is silence and we have some silence breaks, likely speech
                        if silence_ratio < 0.7 and silence_count > 2:
                            logger.info("Speech detected in video")
                            return True
                
                logger.info("No speech detected in video")
                return False
            
        except Exception as e:
            logger.error(f"Error checking for speech: {e}")
            return False  # Assume no speech on error
    
    def extract_audio(self, video_path: str, output_path: str) -> bool:
        """
        Extract audio from a video file.
        
        Args:
            video_path: Path to the video file
            output_path: Path to save extracted audio
            
        Returns:
            True if successful, False otherwise
        """
        try:
            extract_cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM format for better quality
                '-ar', '44100',  # Standard audio rate
                '-ac', '2',  # Stereo
                output_path
            ]
            
            subprocess.run(extract_cmd, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                logger.info(f"Successfully extracted audio to {output_path}")
                return True
            else:
                logger.error("Failed to extract audio or file is too small")
                return False
                
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return False
    
    def get_audio_duration(self, audio_path: str) -> float:
        """
        Get the duration of an audio file.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Duration in seconds (0 if error)
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                audio_path
            ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.stdout.strip():
                duration = float(result.stdout.strip())
                return duration
            else:
                return 0
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return 0
    
    def preprocess_music_file(self, music_path: str) -> str:
        """
        Preprocess music file to optimize for faster addition to video.
        
        Args:
            music_path: Path to the original music file
            
        Returns:
            Path to the processed music file (or original if processing fails)
        """
        try:
            # Create a processed version in the same directory
            basename = os.path.basename(music_path)
            dirname = os.path.dirname(music_path)
            processed_path = os.path.join(dirname, f"processed_{basename}")
            
            # Preprocess to mono, lower bitrate for faster processing
            preprocess_cmd = [
                'ffmpeg', '-y',
                '-i', music_path,
                '-ac', '1',  # Convert to mono
                '-ar', '22050',  # Lower sample rate
                '-b:a', '96k',  # Lower bitrate
                processed_path
            ]
            
            result = subprocess.run(preprocess_cmd, check=True, capture_output=True, text=True)
            
            if os.path.exists(processed_path) and os.path.getsize(processed_path) > 1000:
                logger.info(f"Successfully preprocessed music: {processed_path}")
                return processed_path
            else:
                logger.warning("Failed to preprocess music, using original file")
                return music_path
                
        except Exception as e:
            logger.error(f"Error preprocessing music: {e}")
            return music_path
    
    def mix_audio(self, 
                  video_audio_path: str, 
                  music_audio_path: str, 
                  output_audio_path: str, 
                  volume_factor: float = 0.06,
                  has_speech: bool = True) -> bool:
        """
        Mix video audio and music audio with dynamic volume adjustment.
        
        Args:
            video_audio_path: Path to the video audio file
            music_audio_path: Path to the music audio file
            output_audio_path: Path to save the mixed audio
            volume_factor: Base volume factor for music (0.0 to 1.0)
            has_speech: Whether video has speech to apply dynamic adjustment
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Adjust volume based on speech detection
            if has_speech:
                # Lower volume for speech emphasis
                actual_volume = volume_factor / self.speech_emphasis
                logger.info(f"Speech detected, reducing music volume to {actual_volume:.3f}")
            else:
                # Use standard volume factor
                actual_volume = volume_factor
                logger.info(f"No speech detected, using standard music volume {actual_volume:.3f}")
                
            # Get video audio duration
            video_duration = self.get_audio_duration(video_audio_path)
            
            if video_duration == 0:
                logger.error("Could not determine video duration")
                return False
            
            # Create ffmpeg filter for audio mixing with looping if music is shorter
            mix_audio_cmd = [
                'ffmpeg', '-y',
                '-i', video_audio_path,
                '-i', music_audio_path,
                '-filter_complex', 
                f'[1:a]aloop=loop=-1:size=2e+09,volume={actual_volume}[music];[0:a][music]amix=duration=first:dropout_transition=2',
                '-c:a', 'pcm_s16le',  # Use PCM for high quality
                output_audio_path
            ]
            
            subprocess.run(mix_audio_cmd, check=True, capture_output=True)
            
            if os.path.exists(output_audio_path) and os.path.getsize(output_audio_path) > 1000:
                logger.info(f"Successfully mixed audio tracks to {output_audio_path}")
                return True
            else:
                logger.error("Failed to mix audio streams or file is too small")
                return False
                
        except Exception as e:
            logger.error(f"Error mixing audio streams: {e}")
            return False
    
    def add_background_music_with_speech_emphasis(self, video_path: str, music_path: str, output_path: str, base_volume: float = 0.06, speech_emphasis_factor: float = 1.5) -> Optional[str]:
        """
        Add background music to a video with dynamic volume adjustment based on speech.
        
        Args:
            video_path: Path to the input video
            music_path: Path to the music file
            output_path: Path for the output video
            base_volume: Base volume factor for music (lower = quieter music)
            speech_emphasis_factor: Factor to emphasize speech (higher = quieter music during speech)
            
        Returns:
            Path to the output video or None if failed
        """
        try:
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract audio from video
                video_audio_path = os.path.join(temp_dir, "video_audio.wav")
                if not self.extract_audio(video_path, video_audio_path):
                    logger.error("Failed to extract audio from video")
                    return None
                
                # Mix audio with dynamic volume adjustment
                mixed_audio_path = os.path.join(temp_dir, "mixed_audio.wav")
                if not self.mix_audio(video_audio_path, music_path, mixed_audio_path, base_volume, True):
                    logger.error("Failed to mix audio")
                    return None
                
                # Create output directory if it doesn't exist
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                
                # Combine video with new mixed audio
                cmd = [
                    'ffmpeg', '-y',
                    '-i', video_path,
                    '-i', mixed_audio_path,
                    '-c:v', 'copy',         # Copy video stream without re-encoding
                    '-c:a', 'aac',          # Use AAC for audio
                    '-b:a', '192k',         # Good quality audio
                    '-map', '0:v',          # Use video from first input
                    '-map', '1:a',          # Use audio from second input
                    '-shortest',            # End when shortest input ends
                    output_path
                ]
                
                logger.info(f"Combining video with mixed audio to {output_path}")
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                if os.path.exists(output_path):
                    logger.info(f"Successfully created enhanced video: {output_path}")
                    return output_path
                else:
                    logger.error("Failed to create enhanced video")
                    return None
                    
        except Exception as e:
            logger.error(f"Error adding background music with speech emphasis: {e}")
            return None
    
    def add_background_music_simple(self, video_path: str, music_path: str, output_path: str, volume_factor: float = 0.06) -> Optional[str]:
        """
        Add background music to a video with a constant volume level (no speech detection).
        
        Args:
            video_path: Path to the input video
            music_path: Path to the music file
            output_path: Path for the output video
            volume_factor: Volume factor for music (lower = quieter music)
            
        Returns:
            Path to the output video or None if failed
        """
        try:
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract audio from video
                video_audio_path = os.path.join(temp_dir, "video_audio.wav")
                if not self.extract_audio(video_path, video_audio_path):
                    logger.error("Failed to extract audio from video")
                    return None
                
                # Mix audio with constant volume (no speech detection)
                mixed_audio_path = os.path.join(temp_dir, "mixed_audio.wav")
                if not self.mix_audio(video_audio_path, music_path, mixed_audio_path, volume_factor, False):
                    logger.error("Failed to mix audio")
                    return None
                
                # Create output directory if it doesn't exist
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                
                # Combine video with new mixed audio
                cmd = [
                    'ffmpeg', '-y',
                    '-i', video_path,
                    '-i', mixed_audio_path,
                    '-c:v', 'copy',         # Copy video stream without re-encoding
                    '-c:a', 'aac',          # Use AAC for audio
                    '-b:a', '192k',         # Good quality audio
                    '-map', '0:v',          # Use video from first input
                    '-map', '1:a',          # Use audio from second input
                    '-shortest',            # End when shortest input ends
                    output_path
                ]
                
                logger.info(f"Combining video with mixed audio to {output_path}")
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                if os.path.exists(output_path):
                    logger.info(f"Successfully created enhanced video: {output_path}")
                    return output_path
                else:
                    logger.error("Failed to create enhanced video")
                    return None
                    
        except Exception as e:
            logger.error(f"Error adding background music with simple mixing: {e}")
            return None
    
    def create_sample_music(self, output_path: Optional[str] = None, duration: int = 60) -> Optional[str]:
        """
        Create a sample music file for testing or when downloads fail.
        
        Args:
            output_path: Path to save the sample music file (None for auto-generated)
            duration: Duration of the sample music in seconds
            
        Returns:
            Path to the created sample music file or None if failed
        """
        try:
            if not output_path:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                    output_path = temp_file.name
                    
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Use ffmpeg to generate a pleasant chord progression with transitions
            # This creates a more natural sounding music compared to pure tones
            sample_music_cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi', 
                '-i', f'aevalsrc='.join([
                    # More complex chord progression with slight variations for a more interesting sound
                    '0.2*sin(2*PI*110*t)+0.2*sin(2*PI*220*t)+0.1*sin(2*PI*330*t)+0.05*sin(2*PI*440*t):',
                    '0.2*sin(2*PI*130*t)+0.2*sin(2*PI*260*t)+0.1*sin(2*PI*390*t)+0.05*sin(2*PI*520*t):',
                    '0.2*sin(2*PI*146*t)+0.2*sin(2*PI*293*t)+0.1*sin(2*PI*440*t)+0.05*sin(2*PI*586*t):',
                    '0.2*sin(2*PI*164*t)+0.2*sin(2*PI*329*t)+0.1*sin(2*PI*493*t)+0.05*sin(2*PI*658*t)'
                ]) + f':c=1:d={duration}:s=44100',
                '-af', 'apad=pad_dur=2,atempo=0.5,aresample=44100,aformat=channel_layouts=stereo',
                output_path
            ]
            
            subprocess.run(sample_music_cmd, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            
            # Verify file was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                logger.info(f"Successfully created sample music file: {output_path}")
                return output_path
                
            logger.error("Failed to create sample music file")
            return None
            
        except Exception as e:
            logger.error(f"Exception creating sample music: {e}")
            return None
