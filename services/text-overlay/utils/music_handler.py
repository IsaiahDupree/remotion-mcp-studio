#!/usr/bin/env python3
"""
Music Handler Utility
---------------------
Utility functions for handling background music in videos.
Provides functionality to read music tracks from Excel files and
apply background music to videos at specified volume levels.
"""

import os
import random
import pandas as pd
from typing import List, Dict, Optional, Union, Tuple
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
import logging

# Set up logging
log = logging.getLogger("music_handler")

def read_music_tracks_from_excel(excel_path: str) -> List[Dict[str, str]]:
    """
    Read music track information from Excel file.
    
    Args:
        excel_path: Path to Excel file containing music track information
        
    Returns:
        List of dictionaries containing music track information
    """
    try:
        # Read Excel file
        df = pd.read_excel(excel_path)
        
        # Convert dataframe to list of dictionaries
        tracks = df.to_dict(orient="records")
        
        log.info(f"Successfully read {len(tracks)} music tracks from {excel_path}")
        return tracks
    except Exception as e:
        log.error(f"Failed to read music tracks from Excel file: {e}")
        return []

def get_random_track(tracks: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    Get a random music track from the list of tracks.
    
    Args:
        tracks: List of track dictionaries
        
    Returns:
        Dictionary containing track information or None if no tracks are available
    """
    if not tracks:
        return None
    
    return random.choice(tracks)

def apply_background_music(video_path: str, music_path: str, output_path: str, 
                          volume_level: float = -40) -> bool:
    """
    Apply background music to a video at the specified volume level.
    
    Args:
        video_path: Path to input video file
        music_path: Path to music file to use as background
        output_path: Path where the output video will be saved
        volume_level: Volume level in dB (negative means quieter)
        
    Returns:
        Boolean indicating success or failure
    """
    try:
        # Load video and audio
        video_clip = VideoFileClip(video_path)
        music_clip = AudioFileClip(music_path)
        
        # Loop music if it's shorter than the video
        if music_clip.duration < video_clip.duration:
            music_clip = music_clip.loop(duration=video_clip.duration)
        else:
            # Trim music if it's longer than the video
            music_clip = music_clip.subclip(0, video_clip.duration)
        
        # Set music volume
        music_clip = music_clip.volumex(volume_level/20)  # Convert dB to amplitude ratio
        
        # Combine original audio with background music
        if video_clip.audio is not None:
            new_audio = CompositeAudioClip([video_clip.audio, music_clip])
        else:
            new_audio = music_clip
        
        # Apply new audio to video
        final_clip = video_clip.set_audio(new_audio)
        
        # Write output file
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        
        # Close clips to free resources
        video_clip.close()
        music_clip.close()
        final_clip.close()
        
        log.info(f"Successfully added background music to {video_path}")
        return True
    except Exception as e:
        log.error(f"Failed to add background music to video: {e}")
        return False
