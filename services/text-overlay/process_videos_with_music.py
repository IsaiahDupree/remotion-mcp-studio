#!/usr/bin/env python3
"""
Video Processing with SoundCloud Music
-------------------------------------
Integrates SoundCloud track downloading and video processing.
Downloads tracks from SoundCloud using URLs from an Excel sheet,
then adds the downloaded music to videos at -40dB volume.
"""

import os
import sys
import argparse
import logging
import random
from pathlib import Path
from typing import List, Optional, Dict

# Set up rich console for better logging
try:
    from rich.console import Console
    from rich.logging import RichHandler
    
    console = Console()
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console)]
    )
except ImportError:
    # Fallback to standard logging if rich is not available
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

log = logging.getLogger("video_processor")

# Import our utility modules
from utils.soundcloud_downloader import SoundCloudDownloader
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

def download_soundcloud_tracks(excel_path: str, output_dir: str, api_key: Optional[str] = None) -> List[str]:
    """
    Download SoundCloud tracks from URLs in an Excel file.
    
    Args:
        excel_path: Path to Excel file containing SoundCloud URLs
        output_dir: Directory to save downloaded tracks
        api_key: Optional RapidAPI key
        
    Returns:
        List of paths to downloaded music files
    """
    log.info(f"Downloading SoundCloud tracks from {excel_path}")
    
    # Initialize the SoundCloud downloader
    downloader = SoundCloudDownloader(api_key=api_key, output_dir=output_dir)
    
    # Download tracks
    music_files = downloader.download_tracks_from_excel(excel_path)
    
    if music_files:
        log.info(f"Successfully downloaded {len(music_files)} tracks")
    else:
        log.warning("No tracks were downloaded")
    
    return music_files

def process_video_with_music(video_path: str, music_path: str, output_path: str, volume_db: float = -40) -> bool:
    """
    Process a video by adding background music at the specified volume.
    
    Args:
        video_path: Path to input video file
        music_path: Path to music file
        output_path: Path to save the processed video
        volume_db: Volume level in dB (negative means quieter)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        log.info(f"Processing video: {os.path.basename(video_path)}")
        log.info(f"Adding music: {os.path.basename(music_path)}")
        
        # Load video and music
        video = VideoFileClip(video_path)
        music = AudioFileClip(music_path)
        
        # Prepare the music: loop or trim as needed
        if music.duration < video.duration:
            # If music is shorter than video, loop it
            log.info(f"Looping music to match video duration ({video.duration:.2f}s)")
            music = music.loop(duration=video.duration)
        else:
            # If music is longer than video, trim it
            log.info(f"Trimming music to match video duration ({video.duration:.2f}s)")
            music = music.subclip(0, video.duration)
        
        # Set volume level (convert dB to amplitude ratio)
        # Formula: amplitude ratio = 10^(dB/20)
        volume_factor = 10 ** (volume_db / 20)
        log.info(f"Setting music volume to {volume_db} dB (factor: {volume_factor:.4f})")
        music = music.volumex(volume_factor)
        
        # Combine with original audio if present
        if video.audio is not None:
            log.info("Mixing music with original audio")
            final_audio = CompositeAudioClip([video.audio, music])
            video = video.set_audio(final_audio)
        else:
            log.info("No original audio present, using music only")
            video = video.set_audio(music)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Write output file with high quality settings
        log.info(f"Rendering video to {output_path}")
        video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            audio_bitrate="192k",
            preset="medium",
            threads=4
        )
        
        # Close clips to free resources
        video.close()
        music.close()
        
        log.info(f"Successfully processed video: {os.path.basename(output_path)}")
        return True
        
    except Exception as e:
        log.error(f"Error processing video with music: {e}")
        return False

def process_videos_batch(
    video_dir: str,
    music_files: List[str],
    output_dir: str,
    volume_db: float = -40,
    limit: Optional[int] = None
) -> int:
    """
    Process a batch of videos with downloaded music.
    
    Args:
        video_dir: Directory containing input videos
        music_files: List of music files to use
        output_dir: Directory to save processed videos
        volume_db: Volume level in dB for the music
        limit: Maximum number of videos to process (None for all)
        
    Returns:
        Number of successfully processed videos
    """
    if not music_files:
        log.error("No music files available. Cannot process videos.")
        return 0
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all video files in the input directory
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.wmv']
    video_files = []
    
    for root, _, files in os.walk(video_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_files.append(os.path.join(root, file))
    
    if not video_files:
        log.error(f"No video files found in {video_dir}")
        return 0
    
    # Limit the number of videos to process if specified
    if limit and limit > 0:
        video_files = video_files[:limit]
    
    log.info(f"Found {len(video_files)} videos to process")
    log.info(f"Using {len(music_files)} music tracks")
    
    # Process each video with a random music track
    success_count = 0
    for i, video_path in enumerate(video_files):
        # Select a music file (rotating or random)
        music_path = music_files[i % len(music_files)]  # Rotate through available music
        
        # Define output path
        video_name = os.path.basename(video_path)
        output_name = f"music_{Path(video_name).stem}.mp4"
        output_path = os.path.join(output_dir, output_name)
        
        log.info(f"Processing video {i+1}/{len(video_files)}: {video_name}")
        
        # Process the video
        if process_video_with_music(video_path, music_path, output_path, volume_db):
            success_count += 1
    
    log.info(f"Successfully processed {success_count} out of {len(video_files)} videos")
    return success_count

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Download SoundCloud tracks and add them to videos"
    )
    parser.add_argument(
        "--excel",
        default="C:\\Users\\Isaia\\Downloads\\SoundCloud to X Reposter.xlsx",
        help="Path to Excel file with SoundCloud URLs"
    )
    parser.add_argument(
        "--video-dir",
        default="C:\\Users\\Isaia\\Documents\\Coding\\N8N\\shared\\videos",
        help="Directory containing input videos"
    )
    parser.add_argument(
        "--output-dir",
        default="C:\\Users\\Isaia\\Documents\\WordsOnText\\output_videos",
        help="Directory for output videos"
    )
    parser.add_argument(
        "--music-dir",
        default="C:\\Users\\Isaia\\Documents\\WordsOnText\\downloaded_songs",
        help="Directory to save downloaded music"
    )
    parser.add_argument(
        "--volume",
        type=float,
        default=-40,
        help="Volume level in dB (negative means quieter)"
    )
    parser.add_argument(
        "--api-key",
        help="RapidAPI key for SoundCloud Downloader"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of videos to process"
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading tracks and use existing ones in music directory"
    )
    
    args = parser.parse_args()
    
    # Step 1: Get music files (download or use existing)
    music_files = []
    
    if args.skip_download:
        # Use existing music files
        music_dir = args.music_dir
        if os.path.exists(music_dir):
            music_files = [
                os.path.join(music_dir, f) for f in os.listdir(music_dir)
                if f.lower().endswith('.mp3')
            ]
            log.info(f"Using {len(music_files)} existing music files from {music_dir}")
    
    if not music_files:
        # Download from SoundCloud
        music_files = download_soundcloud_tracks(args.excel, args.music_dir, args.api_key)
    
    if not music_files:
        log.error("No music files available. Cannot continue.")
        return 1
    
    # Step 2: Process videos with the music
    success_count = process_videos_batch(
        args.video_dir,
        music_files,
        args.output_dir,
        args.volume,
        args.limit
    )
    
    if success_count > 0:
        log.info(f"✅ Processing complete! {success_count} videos processed successfully.")
        log.info(f"Output videos saved to: {args.output_dir}")
        return 0
    else:
        log.error("❌ Processing failed. No videos were processed successfully.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
