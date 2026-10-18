#!/usr/bin/env python3
"""
WordsOnText Main CLI

This script provides a unified command-line interface for all the functionality 
in the audiovideotools package.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger('wordsontext')

def main():
    """Main entry point for the WordsOnText CLI."""
    parser = argparse.ArgumentParser(
        description="WordsOnText - Audio/Video Processing Tools"
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Add SoundCloud music processing command
    add_music_parser = subparsers.add_parser(
        'add-music', 
        help='Add SoundCloud music to videos with optimized volume'
    )
    
    # Video source arguments
    add_music_parser.add_argument(
        "--video-dir",
        type=str,
        default="./videos",
        help="Directory containing video files"
    )
    
    add_music_parser.add_argument(
        "--specific-video",
        type=str,
        help="Process only a specific video file"
    )
    
    add_music_parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of videos to process"
    )
    
    # Music source arguments
    add_music_parser.add_argument(
        "--music-dir",
        type=str,
        default="./downloaded_songs",
        help="Directory containing music files"
    )
    
    add_music_parser.add_argument(
        "--excel-file",
        type=str,
        help="Excel file containing SoundCloud URLs"
    )
    
    add_music_parser.add_argument(
        "--url-column",
        type=str,
        default="Track URL",
        help="Column name containing track URLs in Excel file (default: 'Track URL')"
    )
    
    # Output arguments
    add_music_parser.add_argument(
        "--output-dir",
        type=str,
        default="./output_videos",
        help="Directory to save processed videos"
    )
    
    # Volume control arguments
    add_music_parser.add_argument(
        "--target-ratio",
        type=float,
        default=0.15,
        help="Target ratio of music volume to original audio (default: 0.15)"
    )
    
    add_music_parser.add_argument(
        "--speech-emphasis",
        type=float,
        default=0.7,
        help="Factor to make music even quieter to emphasize speech (default: 0.7)"
    )
    
    # Background music detection control
    add_music_parser.add_argument(
        "--force-add-music",
        action="store_true",
        help="Force adding music even if video already has it"
    )
    
    add_music_parser.add_argument(
        "--disable-music-check",
        action="store_true",
        help="Disable background music detection check"
    )
    
    add_music_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files"
    )
    
    # Add YouTube Engagement Finder command
    youtube_parser = subparsers.add_parser(
        'youtube-find', 
        help='Find YouTube videos with high engagement but low follower count'
    )
    
    youtube_parser.add_argument(
        "--keyword",
        type=str,
        required=True,
        help="Keyword to search for"
    )
    
    youtube_parser.add_argument(
        "--api-key",
        type=str,
        required=True,
        help="YouTube Data API key"
    )
    
    youtube_parser.add_argument(
        "--output-dir",
        type=str,
        default="./youtube_videos",
        help="Directory to save downloaded videos"
    )
    
    youtube_parser.add_argument(
        "--spreadsheet",
        type=str,
        default="./youtube_engagement_data.xlsx",
        help="Path to save/update engagement data spreadsheet"
    )
    
    youtube_parser.add_argument(
        "--min-views",
        type=int,
        default=5000,
        help="Minimum number of views for a video to be considered"
    )
    
    youtube_parser.add_argument(
        "--min-comments",
        type=int,
        default=10,
        help="Minimum number of comments"
    )
    
    youtube_parser.add_argument(
        "--min-likes",
        type=int,
        default=100,
        help="Minimum number of likes"
    )
    
    youtube_parser.add_argument(
        "--max-subscribers",
        type=int,
        default=100000,
        help="Maximum number of subscribers for channel"
    )
    
    youtube_parser.add_argument(
        "--min-engagement-ratio",
        type=float,
        default=0.05,
        help="Minimum ratio of views to subscribers"
    )
    
    youtube_parser.add_argument(
        "--max-search-results",
        type=int,
        default=100,
        help="Maximum number of search results to analyze"
    )
    
    youtube_parser.add_argument(
        "--download-limit",
        type=int,
        help="Maximum number of videos to download"
    )
    
    youtube_parser.add_argument(
        "--search-only",
        action="store_true",
        help="Only search and analyze videos, don't download"
    )
    
    # Add downloader command for only downloading tracks
    downloader_parser = subparsers.add_parser(
        'download', 
        help='Download tracks from SoundCloud'
    )
    
    downloader_parser.add_argument(
        "--excel-file",
        type=str,
        required=True,
        help="Excel file containing SoundCloud URLs"
    )
    
    downloader_parser.add_argument(
        "--url-column",
        type=str,
        default="Track URL",
        help="Column name containing track URLs in Excel file (default: 'Track URL')"
    )
    
    downloader_parser.add_argument(
        "--output-dir",
        type=str,
        default="./downloaded_songs",
        help="Directory to save downloaded tracks"
    )
    
    downloader_parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of tracks to download"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    if args.command == 'add-music':
        return handle_add_music_command(args)
    elif args.command == 'youtube-find':
        return handle_youtube_find_command(args)
    elif args.command == 'download':
        return handle_download_command(args)
    else:
        parser.print_help()
        return 0

def handle_add_music_command(args):
    """Handle the add-music command."""
    from audiovideotools.downloaders.soundcloud import SoundCloudDownloader
    from audiovideotools.batch_processor import process_videos_batch
    from audiovideotools.utils.file_utils import ensure_directory
    
    # Create output directory if it doesn't exist
    ensure_directory(args.output_dir)
    
    # Check if Excel file is provided for SoundCloud download
    if args.excel_file:
        log.info(f"Downloading SoundCloud tracks from {args.excel_file}")
        downloader = SoundCloudDownloader(args.music_dir)
        downloader.download_from_excel(args.excel_file, args.url_column, limit=args.limit)
    
    # Find all music files
    music_files = []
    for ext in [".mp3", ".wav", ".m4a"]:
        music_files.extend([str(f) for f in Path(args.music_dir).glob(f"*{ext}")])
    
    log.info(f"Found {len(music_files)} music files in {args.music_dir}")
    
    if not music_files:
        log.error("No music files found. Please download some tracks first.")
        return 1
    
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
    
    return 0 if success_count > 0 or not music_files else 1

def handle_youtube_find_command(args):
    """Handle the youtube-find command."""
    from audiovideotools.downloaders.youtube_engagement import YouTubeEngagementFinder
    
    # Initialize YouTube engagement finder
    finder = YouTubeEngagementFinder(
        api_key=args.api_key,
        output_dir=args.output_dir,
        spreadsheet_path=args.spreadsheet,
        min_views=args.min_views,
        min_comments=args.min_comments,
        min_likes=args.min_likes,
        max_subscribers=args.max_subscribers,
        min_engagement_ratio=args.min_engagement_ratio
    )
    
    # Search for videos
    high_engagement_videos = finder.search_and_analyze(args.keyword, args.max_search_results)
    
    log.info(f"Found {len(high_engagement_videos)} high-engagement videos for '{args.keyword}'")
    
    # Download videos if requested
    if not args.search_only and high_engagement_videos:
        downloaded_videos = finder.download_videos(high_engagement_videos, args.download_limit)
        log.info(f"Downloaded {len(downloaded_videos)} videos")
    
    return 0

def handle_download_command(args):
    """Handle the download command."""
    from audiovideotools.downloaders.soundcloud import SoundCloudDownloader
    
    # Create downloader
    downloader = SoundCloudDownloader(args.output_dir)
    
    # Download tracks
    tracks = downloader.download_from_excel(args.excel_file, args.url_column, limit=args.limit)
    
    log.info(f"Downloaded {len(tracks)} tracks")
    
    return 0 if tracks else 1

if __name__ == "__main__":
    sys.exit(main())
