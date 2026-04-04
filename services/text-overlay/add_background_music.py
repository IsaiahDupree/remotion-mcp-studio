#!/usr/bin/env python3
"""
Background Music Integration Test
--------------------------------
Test script for adding background music from Excel list to videos.
The music will be added at -40dB volume level.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
import pandas as pd
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

# Set up rich console and logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console)]
)
log = logging.getLogger("music_integration")

def get_music_links_from_excel(excel_path):
    """Extract music links from Excel file."""
    try:
        df = pd.read_excel(excel_path)
        # Try to find a column containing URLs
        url_columns = []
        for col in df.columns:
            if any(str(x).startswith(('http://', 'https://')) for x in df[col] if isinstance(x, str)):
                url_columns.append(col)
        
        if url_columns:
            music_links = []
            for col in url_columns:
                links = [x for x in df[col] if isinstance(x, str) and (str(x).startswith(('http://', 'https://')))]
                music_links.extend(links)
            
            log.info(f"Found {len(music_links)} music links in Excel file")
            return music_links
        else:
            # If no URL columns found, try to find file paths
            file_columns = []
            for col in df.columns:
                if any(isinstance(x, str) and os.path.exists(str(x)) for x in df[col]):
                    file_columns.append(col)
            
            if file_columns:
                music_files = []
                for col in file_columns:
                    files = [x for x in df[col] if isinstance(x, str) and os.path.exists(str(x))]
                    music_files.extend(files)
                
                log.info(f"Found {len(music_files)} music files in Excel file")
                return music_files
            else:
                log.warning("No music URLs or valid file paths found in Excel file")
                return []
                
    except Exception as e:
        log.error(f"Error reading Excel file: {e}")
        return []

def add_music_to_video(video_path, music_path, output_path, volume_db=-40):
    """Add background music to video at specified volume level."""
    try:
        log.info(f"Processing video: {os.path.basename(video_path)}")
        
        # Load video
        video = VideoFileClip(video_path)
        
        # Load music if it exists
        if os.path.exists(music_path):
            music = AudioFileClip(music_path)
            
            # Loop music if needed
            if music.duration < video.duration:
                music = music.loop(duration=video.duration)
            else:
                # Trim music if longer than video
                music = music.subclip(0, video.duration)
            
            # Set volume level (convert dB to amplitude ratio)
            volume_factor = 10 ** (volume_db / 20)
            music = music.volumex(volume_factor)
            
            # Combine with original audio if present
            if video.audio is not None:
                final_audio = CompositeAudioClip([video.audio, music])
                video = video.set_audio(final_audio)
            else:
                video = video.set_audio(music)
        else:
            log.warning(f"Music file not found: {music_path}, skipping audio addition")
        
        # Write output file
        video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        
        # Close clips
        video.close()
        if 'music' in locals():
            music.close()
            
        log.info(f"Video processed successfully: {os.path.basename(output_path)}")
        return True
    except Exception as e:
        log.error(f"Error adding music to video: {e}")
        return False

def process_videos(input_dir, output_dir, excel_path, volume_db=-40):
    """Process all videos in input directory and add background music."""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Get list of video files
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.wmv']
    video_files = []
    for ext in video_extensions:
        video_files.extend([os.path.join(input_dir, f) for f in os.listdir(input_dir) 
                           if f.lower().endswith(ext)])
    
    if not video_files:
        log.error(f"No video files found in {input_dir}")
        return False
    
    log.info(f"Found {len(video_files)} videos to process")
    
    # Get music information from Excel
    music_files = get_music_links_from_excel(excel_path)
    
    if not music_files:
        log.error("No music files found in Excel")
        return False
    
    # Process each video
    success_count = 0
    for i, video_path in enumerate(video_files):
        # Select music file (cycle through available music)
        music_idx = i % len(music_files)
        music_path = music_files[music_idx]
        
        # Get output path
        video_name = os.path.basename(video_path)
        output_path = os.path.join(output_dir, f"bgmusic_{video_name}")
        
        # Add music to video
        if add_music_to_video(video_path, music_path, output_path, volume_db):
            success_count += 1
    
    log.info(f"Processed {success_count} out of {len(video_files)} videos successfully")
    return success_count > 0

def main():
    """Main entry point for the music integration tool."""
    parser = argparse.ArgumentParser(description="Add background music to videos")
    parser.add_argument("--input_dir", default="C:\\Users\\Isaia\\Documents\\Coding\\N8N\\shared\\videos",
                        help="Directory containing input videos")
    parser.add_argument("--output_dir", default="C:\\Users\\Isaia\\Documents\\WordsOnText\\output_videos",
                        help="Directory for output videos")
    parser.add_argument("--excel_path", default="C:\\Users\\Isaia\\Downloads\\SoundCloud to X Reposter.xlsx",
                        help="Path to Excel file with music information")
    parser.add_argument("--volume", type=float, default=-40,
                        help="Volume level in dB (negative means quieter)")
    
    args = parser.parse_args()
    
    # Process videos
    if process_videos(args.input_dir, args.output_dir, args.excel_path, args.volume):
        log.info("Processing complete. Check output directory for results.")
        return 0
    else:
        log.error("Processing failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
