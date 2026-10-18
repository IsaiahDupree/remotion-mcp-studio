"""
Batch video processor for adding background music to videos.

This module integrates all components of the audiovideotools package to provide a complete
solution for adding background music to videos with optimized volume levels and
intelligent background music detection.
"""

import os
import sys
import logging
import argparse
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import our components
from .downloaders.soundcloud import SoundCloudDownloader
from .video_processing.music_mixer import MusicMixer
from .utils.file_utils import find_videos, ensure_directory, choose_random_file

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger('batch_processor')

def process_videos_batch(
    video_dir: str,
    music_files: List[str],
    output_dir: str,
    target_ratio: float = 0.15,
    speech_emphasis: float = 0.7,
    force_add_music: bool = False,
    skip_existing_music: bool = True,
    overwrite: bool = False,
    limit: Optional[int] = None,
    specific_video: Optional[str] = None
) -> int:
    """
    Process a batch of videos with background music.
    
    Args:
        video_dir: Directory containing video files
        music_files: List of music file paths to use
        output_dir: Directory to save processed videos
        target_ratio: Target ratio of music volume to original audio
        speech_emphasis: Factor to make music even quieter to emphasize speech
        force_add_music: Force adding music even if video already has it
        skip_existing_music: Skip videos that already have background music
        overwrite: Overwrite existing output files
        limit: Maximum number of videos to process
        specific_video: Process only a specific video file
        
    Returns:
        Number of successfully processed videos
    """
    if not music_files:
        log.error("No music files available")
        return 0
        
    # Create output directory if it doesn't exist
    ensure_directory(output_dir)
    
    # Find video files to process
    if specific_video:
        video_path = os.path.join(video_dir, specific_video)
        if os.path.exists(video_path):
            video_files = [video_path]
        else:
            log.error(f"Specific video not found: {specific_video}")
            return 0
    else:
        video_files = find_videos(video_dir, limit)
    
    if not video_files:
        log.error(f"No video files found in {video_dir}")
        return 0
    
    log.info(f"Found {len(video_files)} videos to process")
    log.info(f"Using {len(music_files)} music tracks")
    
    # Initialize music mixer
    mixer = MusicMixer(
        target_ratio=target_ratio,
        speech_emphasis=speech_emphasis,
        force_add_music=force_add_music,
        skip_existing_music=skip_existing_music,
        overwrite=overwrite
    )
    
    # Process each video
    success_count = 0
    for i, video_path in enumerate(video_files):
        video_name = os.path.basename(video_path)
        
        # Choose a random music file for each video
        music_path = choose_random_file(music_files)
        if not music_path:
            log.error("No music files available")
            break
        
        # Generate unique output path for each video
        basename, ext = os.path.splitext(video_name)
        timestamp = int(os.path.getmtime(video_path))  # Use file modification time for consistency
        output_path = os.path.join(output_dir, f"autovolume_{basename}_{timestamp}{ext}")
        
        log.info(f"Processing video {i+1}/{len(video_files)}: {video_name}")
        
        # Process the video with auto-calculated volume and speech emphasis
        if mixer.process_video(video_path, music_path, output_path):
            success_count += 1
        else:
            log.info(f"Skipping video {video_name} (likely already has music or permission error)")
    
    if success_count == 0:
        if len(video_files) == 0:
            log.warning("No videos found to process")
        else:
            log.info("ℹ️ All videos were skipped (likely already have music)")
    else:
        log.info(f"✅ Successfully processed {success_count} videos")
        
    return success_count

def main():
    """Main entry point for the batch processor."""
    parser = argparse.ArgumentParser(
        description="Process videos with auto-volume background music"
    )
    
    parser.add_argument(
        "--video-dir",
        type=str,
        default="./videos",
        help="Directory containing video files"
    )
    
    parser.add_argument(
        "--music-dir",
        type=str,
        default="./downloaded_songs",
        help="Directory containing music files"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output_videos",
        help="Directory to save processed videos"
    )
    
    parser.add_argument(
        "--target-ratio",
        type=float,
        default=0.15,
        help="Target ratio of music volume to original audio (default: 0.15)"
    )
    
    parser.add_argument(
        "--speech-emphasis",
        type=float,
        default=0.7,
        help="Factor to make music even quieter to emphasize speech (default: 0.7)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of videos to process"
    )
    
    parser.add_argument(
        "--specific-video",
        type=str,
        help="Process only this specific video file"
    )
    
    parser.add_argument(
        "--excel-file",
        type=str,
        help="Excel file containing SoundCloud URLs"
    )
    
    parser.add_argument(
        "--url-column",
        type=str,
        default="Track URL",
        help="Column name containing track URLs in Excel file (default: 'Track URL')"
    )
    
    parser.add_argument(
        "--force-add-music",
        action="store_true",
        help="Force adding music even if video already has it"
    )
    
    parser.add_argument(
        "--disable-music-check",
        action="store_true",
        help="Disable background music detection check"
    )
    
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files"
    )
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    ensure_directory(args.output_dir)
    
    # Check if Excel file is provided for SoundCloud download
    if args.excel_file:
        log.info(f"Downloading SoundCloud tracks from {args.excel_file}")
        downloader = SoundCloudDownloader(args.music_dir)
        downloader.download_from_excel(args.excel_file, args.url_column)
    
    # Find all music files
    music_files = []
    for ext in [".mp3", ".wav", ".m4a"]:
        music_files.extend(list(Path(args.music_dir).glob(f"*{ext}")))
    music_files = [str(f) for f in music_files]
    
    log.info(f"Found {len(music_files)} music files in {args.music_dir}")
    
    # Process videos with auto-volume music
    success_count = process_videos_batch(
        args.video_dir,
        music_files,
        args.output_dir,
        args.target_ratio,
        args.speech_emphasis,
        args.force_add_music,
        not args.disable_music_check,  # Skip existing music unless disabled
        args.overwrite,
        args.limit,
        args.specific_video
    )
    
    # Return appropriate exit code
    if success_count > 0:
        return 0
    elif len(music_files) == 0:
        log.error("No music files found")
        return 1
    else:
        # If we skipped videos because they already have music, that's not an error
        return 0

if __name__ == "__main__":
    sys.exit(main())
