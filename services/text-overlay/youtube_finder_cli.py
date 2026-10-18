#!/usr/bin/env python3
"""
YouTube Engagement Finder CLI

This script provides a command-line interface for finding, analyzing and downloading
YouTube videos with high engagement metrics (views, likes, comments) but relatively
low follower/subscriber count.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger('youtube_finder_cli')

# Import the YouTube engagement finder
from audiovideotools.downloaders.youtube_engagement import YouTubeEngagementFinder

def main():
    """Main entry point for the CLI script."""
    parser = argparse.ArgumentParser(
        description="Find and download YouTube videos with high engagement but low follower count"
    )
    
    parser.add_argument(
        "--keyword",
        type=str,
        required=True,
        help="Keyword to search for"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        required=True,
        help="YouTube Data API key"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./youtube_videos",
        help="Directory to save downloaded videos"
    )
    
    parser.add_argument(
        "--spreadsheet",
        type=str,
        default="./youtube_engagement_data.xlsx",
        help="Path to save/update engagement data spreadsheet"
    )
    
    parser.add_argument(
        "--min-views",
        type=int,
        default=5000,
        help="Minimum number of views for a video to be considered"
    )
    
    parser.add_argument(
        "--min-comments",
        type=int,
        default=10,
        help="Minimum number of comments"
    )
    
    parser.add_argument(
        "--min-likes",
        type=int,
        default=100,
        help="Minimum number of likes"
    )
    
    parser.add_argument(
        "--max-subscribers",
        type=int,
        default=100000,
        help="Maximum number of subscribers for channel"
    )
    
    parser.add_argument(
        "--min-engagement-ratio",
        type=float,
        default=0.05,
        help="Minimum ratio of views to subscribers"
    )
    
    parser.add_argument(
        "--max-search-results",
        type=int,
        default=100,
        help="Maximum number of search results to analyze"
    )
    
    parser.add_argument(
        "--download-limit",
        type=int,
        help="Maximum number of videos to download"
    )
    
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Only search and analyze videos, don't download"
    )
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
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

if __name__ == "__main__":
    sys.exit(main())
