#!/usr/bin/env python3
"""
SoundCloud Music Video Processor
-------------------------------
Comprehensive solution for:
1. Downloading music from SoundCloud using the SoundCloud API3
2. Adding downloaded tracks as background music to videos at -40dB
3. Organizing processed content in a structured output directory

This script is designed to be both robust and user-friendly, with
proper error handling and informative logging throughout.
"""

import os
import sys
import argparse
import logging
import time
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

# Set up rich console for better logging if available
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
    RICH_LOGGING = True
except ImportError:
    # Fallback to standard logging if rich is not available
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    RICH_LOGGING = False

# Set up logger
log = logging.getLogger("soundcloud_video_processor")

# Import our utility modules
from utils.soundcloud_downloader import SoundCloudDownloader
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip


class SoundCloudVideoProcessor:
    """
    Main class for processing videos with SoundCloud music.
    Handles downloading tracks and adding them to videos.
    """
    
    def __init__(
        self,
        api_key: str,
        excel_path: str,
        video_dir: str,
        output_dir: str,
        music_dir: str,
        volume_db: float = -40.0
    ):
        """
        Initialize the SoundCloud video processor.
        
        Args:
            api_key: RapidAPI key for SoundCloud API3
            excel_path: Path to Excel file with SoundCloud track URLs
            video_dir: Directory containing videos to process
            output_dir: Base directory for processed outputs
            music_dir: Directory to store downloaded music
            volume_db: Volume level for background music in dB
        """
        self.api_key = api_key
        self.excel_path = excel_path
        self.video_dir = video_dir
        self.output_dir = output_dir
        self.music_dir = music_dir
        self.volume_db = volume_db
        
        # Create necessary directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.music_dir, exist_ok=True)
        
        # Create a run-specific output directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = os.path.join(self.output_dir, f"run_{timestamp}")
        os.makedirs(self.run_dir, exist_ok=True)
        
        # Setup logging to file as well
        self.log_file = os.path.join(self.run_dir, "processing_log.txt")
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        log.addHandler(file_handler)
        
        # Initialize the SoundCloud downloader
        self.downloader = SoundCloudDownloader(api_key=self.api_key, output_dir=self.music_dir)
        
        log.info(f"SoundCloud Video Processor initialized")
        log.info(f"  Excel Path: {self.excel_path}")
        log.info(f"  Video Directory: {self.video_dir}")
        log.info(f"  Output Directory: {self.run_dir}")
        log.info(f"  Music Directory: {self.music_dir}")
        log.info(f"  Music Volume: {self.volume_db} dB")
    
    def download_music_tracks(self) -> List[str]:
        """
        Download music tracks from SoundCloud using the Excel file.
        
        Returns:
            List of paths to downloaded music files
        """
        log.info("Step 1: Downloading music tracks from SoundCloud")
        
        # Check if Excel file exists
        if not os.path.exists(self.excel_path):
            log.error(f"Excel file not found: {self.excel_path}")
            return []
        
        # Check if existing music files are available
        existing_tracks = [
            os.path.join(self.music_dir, f) for f in os.listdir(self.music_dir)
            if f.lower().endswith('.mp3')
        ]
        
        if existing_tracks:
            log.info(f"Found {len(existing_tracks)} existing music files")
            use_existing = input("Use existing music files? (y/n): ").strip().lower()
            
            if use_existing == 'y':
                log.info("Using existing music files")
                return existing_tracks
        
        # Download tracks from SoundCloud
        log.info(f"Downloading tracks from Excel file: {self.excel_path}")
        downloaded_files = self.downloader.download_tracks_from_excel(self.excel_path)
        
        # Log results
        if downloaded_files:
            log.info(f"Successfully downloaded {len(downloaded_files)} tracks:")
            for file in downloaded_files:
                log.info(f"  - {os.path.basename(file)}")
        else:
            log.warning("No tracks were downloaded")
        
        return downloaded_files
    
    def find_video_files(self, limit: Optional[int] = None) -> List[str]:
        """
        Find video files in the specified directory.
        
        Args:
            limit: Maximum number of videos to return
            
        Returns:
            List of paths to video files
        """
        log.info(f"Finding video files in: {self.video_dir}")
        
        # Check if directory exists
        if not os.path.exists(self.video_dir):
            log.error(f"Video directory not found: {self.video_dir}")
            return []
        
        # Find all video files
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.wmv']
        video_files = []
        
        for root, _, files in os.walk(self.video_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in video_extensions):
                    video_files.append(os.path.join(root, file))
        
        # Sort by name for consistent ordering
        video_files.sort()
        
        # Apply limit if specified
        if limit and limit > 0:
            video_files = video_files[:limit]
        
        if video_files:
            log.info(f"Found {len(video_files)} video files")
        else:
            log.warning("No video files found")
        
        return video_files
    
    def process_video(
        self, 
        video_path: str, 
        music_path: str,
        output_filename: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Process a single video by adding background music at the specified volume.
        
        Args:
            video_path: Path to input video file
            music_path: Path to music file
            output_filename: Optional custom filename for the output
            
        Returns:
            Tuple of (success, output_path)
        """
        try:
            video_filename = os.path.basename(video_path)
            if not output_filename:
                output_filename = f"music_{Path(video_filename).stem}.mp4"
            
            output_path = os.path.join(self.run_dir, output_filename)
            
            log.info(f"Processing video: {video_filename}")
            log.info(f"Adding music: {os.path.basename(music_path)}")
            
            # Load video
            video = VideoFileClip(video_path)
            
            # Load music
            music = AudioFileClip(music_path)
            
            # Prepare music: loop or trim as needed
            if music.duration < video.duration:
                log.info(f"Looping music to match video duration ({video.duration:.2f}s)")
                music = music.loop(duration=video.duration)
            else:
                log.info(f"Trimming music to match video duration ({video.duration:.2f}s)")
                music = music.subclip(0, video.duration)
            
            # Set volume level (convert dB to amplitude ratio)
            # Formula: amplitude ratio = 10^(dB/20)
            volume_factor = 10 ** (self.volume_db / 20)
            log.info(f"Setting music volume to {self.volume_db} dB (factor: {volume_factor:.4f})")
            music = music.volumex(volume_factor)
            
            # Combine with original audio if present
            if video.audio is not None:
                log.info("Mixing music with original audio")
                final_audio = CompositeAudioClip([video.audio, music])
                video = video.set_audio(final_audio)
            else:
                log.info("No original audio present, using music only")
                video = video.set_audio(music)
            
            # Write output file
            log.info(f"Rendering video to: {output_path}")
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
            return True, output_path
            
        except Exception as e:
            log.error(f"Error processing video: {e}")
            return False, None
    
    def process_batch(
        self, 
        video_files: List[str], 
        music_files: List[str],
        random_music: bool = False
    ) -> Tuple[int, List[str]]:
        """
        Process a batch of videos with the downloaded music.
        
        Args:
            video_files: List of video files to process
            music_files: List of music files to use
            random_music: Whether to assign music randomly
            
        Returns:
            Tuple of (success_count, processed_file_paths)
        """
        if not video_files:
            log.error("No video files provided for processing")
            return 0, []
            
        if not music_files:
            log.error("No music files available for processing")
            return 0, []
        
        log.info(f"Processing {len(video_files)} videos with {len(music_files)} music tracks")
        
        # Create CSV file to track processing results
        results_csv = os.path.join(self.run_dir, "processing_results.csv")
        with open(results_csv, 'w') as f:
            f.write("original_video,music_track,output_video,success,duration,volume_db\n")
        
        success_count = 0
        processed_files = []
        
        # Process each video
        for i, video_path in enumerate(video_files):
            # Select music file
            if random_music:
                music_path = random.choice(music_files)
                log.info(f"Randomly selected music track: {os.path.basename(music_path)}")
            else:
                # Rotate through available music
                music_path = music_files[i % len(music_files)]
            
            # Process video
            log.info(f"Processing video {i+1}/{len(video_files)}: {os.path.basename(video_path)}")
            success, output_path = self.process_video(video_path, music_path)
            
            # Update results
            if success:
                success_count += 1
                processed_files.append(output_path)
                
                # Get duration
                try:
                    duration = VideoFileClip(output_path).duration
                except:
                    duration = 0
                
                # Update CSV
                with open(results_csv, 'a') as f:
                    f.write(f"{os.path.basename(video_path)},{os.path.basename(music_path)},"
                            f"{os.path.basename(output_path)},true,{duration:.2f},{self.volume_db}\n")
            else:
                # Update CSV with failure
                with open(results_csv, 'a') as f:
                    f.write(f"{os.path.basename(video_path)},{os.path.basename(music_path)},,false,0,0\n")
            
            # Small delay between processing to avoid overloading system
            if i < len(video_files) - 1:
                time.sleep(1)
        
        return success_count, processed_files
    
    def run(self, limit: Optional[int] = None, random_music: bool = False) -> int:
        """
        Run the full processing pipeline.
        
        Args:
            limit: Maximum number of videos to process
            random_music: Whether to assign music randomly to videos
            
        Returns:
            Success status (0 for success, 1 for failure)
        """
        log.info("Starting SoundCloud Video Processing Pipeline")
        
        # Step 1: Download music tracks
        music_files = self.download_music_tracks()
        if not music_files:
            log.error("No music files available. Cannot continue.")
            return 1
        
        # Step 2: Find video files
        video_files = self.find_video_files(limit)
        if not video_files:
            log.error("No video files found. Cannot continue.")
            return 1
        
        # Step 3: Process videos with music
        success_count, processed_files = self.process_batch(video_files, music_files, random_music)
        
        # Step 4: Report results
        log.info("\nProcessing Complete!")
        log.info(f"Successfully processed {success_count} out of {len(video_files)} videos")
        log.info(f"Output directory: {self.run_dir}")
        log.info(f"Log file: {self.log_file}")
        
        if success_count > 0:
            log.info("✅ Processing successful!")
            return 0
        else:
            log.error("❌ Processing failed: No videos were successfully processed")
            return 1


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Process videos with SoundCloud music"
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
        help="Base directory for output videos"
    )
    parser.add_argument(
        "--music-dir",
        default="C:\\Users\\Isaia\\Documents\\WordsOnText\\downloaded_songs",
        help="Directory to save downloaded music"
    )
    parser.add_argument(
        "--volume",
        type=float,
        default=-40.0,
        help="Volume level in dB (negative means quieter)"
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="RapidAPI key for SoundCloud API3"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of videos to process"
    )
    parser.add_argument(
        "--random-music",
        action="store_true",
        help="Assign music randomly instead of rotating through tracks"
    )
    
    args = parser.parse_args()
    
    # Initialize and run processor
    processor = SoundCloudVideoProcessor(
        api_key=args.api_key,
        excel_path=args.excel,
        video_dir=args.video_dir,
        output_dir=args.output_dir,
        music_dir=args.music_dir,
        volume_db=args.volume
    )
    
    return processor.run(limit=args.limit, random_music=args.random_music)


if __name__ == "__main__":
    sys.exit(main())
