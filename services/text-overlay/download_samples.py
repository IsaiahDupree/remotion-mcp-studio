#!/usr/bin/env python3
"""
Command-line interface for downloading sample videos.
"""

import argparse
import sys
from utils.sample_downloader import download_samples

def main():
    """Parse command-line arguments and download sample videos."""
    parser = argparse.ArgumentParser(
        description="Download sample videos for Smart Text-on-Video Overlay Tool"
    )
    parser.add_argument(
        "--target-dir", 
        default="./input_videos", 
        help="Directory to save videos to (default: ./input_videos)"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force download even if files exist"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of sample videos to download (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Download sample videos
    download_samples(args.target_dir, args.force, args.count)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
