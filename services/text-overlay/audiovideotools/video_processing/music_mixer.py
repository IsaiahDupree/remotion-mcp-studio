"""
Video-audio mixer module for adding background music to videos.

This module provides functionality to:
1. Add background music to videos at optimized volume levels
2. Trim and adjust music to match video duration
3. Process videos with audio considerations
"""

import os
import logging
from typing import Optional, Dict, Any, Tuple, Union
from pathlib import Path
import numpy as np
import tempfile

# Import necessary modules - these would be installed via requirements.txt
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
except ImportError:
    logging.error("moviepy not installed. Install with: pip install moviepy")
    raise

# Import our own modules
from ..audio_analysis.audio_analyzer import has_background_music, calculate_optimal_volume_db

# Set up logging
log = logging.getLogger('music_mixer')

class MusicMixer:
    """Music mixer class for adding background music to videos."""
    
    def __init__(
        self,
        target_ratio: float = 0.15,
        speech_emphasis: float = 0.7,
        force_add_music: bool = False,
        skip_existing_music: bool = True,
        overwrite: bool = False
    ):
        """
        Initialize the MusicMixer.
        
        Args:
            target_ratio: Target ratio of music volume to original audio volume
            speech_emphasis: Factor to make music even quieter to emphasize speech
            force_add_music: Force adding music even if video already has it
            skip_existing_music: Skip videos that already have background music
            overwrite: Overwrite existing output files
        """
        self.target_ratio = target_ratio
        self.speech_emphasis = speech_emphasis
        self.force_add_music = force_add_music
        self.skip_existing_music = skip_existing_music
        self.overwrite = overwrite
    
    def process_video(
        self,
        video_path: str,
        music_path: str,
        output_path: str
    ) -> bool:
        """
        Process a video by adding background music with automatically calculated volume.
        
        Args:
            video_path: Path to the input video file
            music_path: Path to the music file to add as background
            output_path: Path where the output video will be saved
        
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            log.info(f"Processing video: {os.path.basename(video_path)}")
            
            # Check if output file already exists and handle accordingly
            if os.path.exists(output_path) and not self.overwrite:
                log.warning(f"Output file already exists: {output_path}")
                
                # Generate new unique filename with timestamp
                dirname = os.path.dirname(output_path)
                basename = os.path.basename(output_path)
                name, ext = os.path.splitext(basename)
                
                # Import only when needed to avoid circular imports
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(dirname, f"{name}_{timestamp}{ext}")
                log.info(f"New output path: {output_path}")
                
            # Load video
            video = VideoFileClip(video_path)
            
            # Check if video already has background music if configured to do so
            if self.skip_existing_music and not self.force_add_music:
                log.info("Checking if video already has background music...")
                
                # Extract audio array from video for analysis
                audio_array = video.audio.to_soundarray()
                sample_rate = video.audio.fps
                
                has_music, metrics = has_background_music(audio_array, sample_rate)
                
                # Log metrics for debugging
                log.info(f"Music detection metrics: {metrics}")
                
                if has_music:
                    log.info("Background music detected in original video. Skipping.")
                    video.close()
                    return False
                else:
                    log.info("No background music detected in original video.")
            
            # Add background music at optimized volume
            output_path = self._add_background_music(video, music_path, output_path)
            video.close()
            
            return True
            
        except Exception as e:
            log.error(f"Error processing video: {e}")
            # Ensure resources are cleaned up
            try:
                if 'video' in locals():
                    video.close()
            except:
                pass
            return False
    
    def _add_background_music(self, video: VideoFileClip, music_path: str, output_path: str) -> str:
        """
        Add background music to a video at an optimized volume level.
        
        Args:
            video: VideoFileClip object of the input video
            music_path: Path to the music file
            output_path: Path where the output video will be saved
        
        Returns:
            Path to the output video (may change if file exists and overwrite is False)
        """
        try:
            log.info(f"Adding music: {os.path.basename(music_path)}")
            
            # Analyze original audio volume
            log.info(f"Analyzing audio volume for: {os.path.basename(video.filename)}")
            audio_array = video.audio.to_soundarray()
            
            # Calculate optimal volume level based on original audio
            volume_db = calculate_optimal_volume_db(
                audio_array, 
                self.target_ratio,
                self.speech_emphasis
            )
            log.info(f"Using calculated volume level: {volume_db:.2f} dB")
            
            # Convert from dB to volume factor
            # volume_factor = 10**(volume_db/20.0)
            # equivalent to 10^(db/20) since dB = 20*log10(ratio)
            volume_factor = np.power(10, volume_db / 20.0)
            
            # Load music file
            music = AudioFileClip(music_path)
            
            # Adjust music duration to match video
            video_duration = video.duration
            log.info(f"Trimming music to match video duration ({video_duration:.2f}s)")
            
            # If music is shorter than video, loop it
            if music.duration < video_duration:
                # Calculate how many repeats we need
                repeats = int(np.ceil(video_duration / music.duration))
                music = music.loop(repeats)
            
            # Trim music to video duration
            music = music.subclip(0, video_duration)
            
            # Set music volume
            log.info(f"Setting music volume to {volume_db:.2f} dB (factor: {volume_factor:.4f})")
            music = music.volumex(volume_factor)
            
            # Mix with original audio
            log.info("Mixing music with original audio")
            final_audio = CompositeAudioClip([video.audio, music])
            
            # Create output video with new audio
            final_video = video.set_audio(final_audio)
            
            # Write the output file
            log.info(f"Writing output video to: {output_path}")
            
            # Attempt to use optimal encoding settings
            codec = "libx264"
            audio_codec = "aac"
            preset = "medium"
            threads = 4  # Use multiple threads for encoding
            temp_audiofile = tempfile.NamedTemporaryFile(suffix='.m4a').name
            
            # Write video with optimized settings
            final_video.write_videofile(
                output_path,
                codec=codec,
                audio_codec=audio_codec,
                preset=preset,
                threads=threads,
                temp_audiofile=temp_audiofile,
                remove_temp=True
            )
            
            # Clean up resources
            music.close()
            final_video.close()
            
            return output_path
            
        except Exception as e:
            log.error(f"Error adding background music: {e}")
            # Try to clean up resources even if there was an error
            try:
                if 'music' in locals():
                    music.close()
                if 'final_video' in locals():
                    final_video.close()
            except:
                pass
            raise
