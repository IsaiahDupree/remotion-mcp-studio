#!/usr/bin/env python3
"""
Test Script for SoundCloud Downloader
------------------------------------
Tests the SoundCloud downloader with the updated API endpoint.
"""

import os
import sys
import logging
import argparse
from utils.soundcloud_downloader import SoundCloudDownloader

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger("test_soundcloud")

def main():
    """Test the SoundCloud downloader with a single URL."""
    parser = argparse.ArgumentParser(description="Test SoundCloud downloader")
    parser.add_argument("--url", help="SoundCloud track URL to download")
    parser.add_argument("--excel", help="Excel file with SoundCloud URLs")
    parser.add_argument("--api-key", required=True, help="RapidAPI key for SoundCloud API3")
    parser.add_argument("--output-dir", default="./downloaded_songs", help="Output directory")
    
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = SoundCloudDownloader(api_key=args.api_key, output_dir=args.output_dir)
    
    if args.url:
        # Test with a single URL
        log.info(f"Testing download with URL: {args.url}")
        track_path = downloader.download_track(args.url)
        
        if track_path:
            log.info(f"Success! Track downloaded to: {track_path}")
            return 0
        else:
            log.error("Failed to download track.")
            return 1
    elif args.excel:
        # Test with Excel file
        log.info(f"Testing download with Excel file: {args.excel}")
        tracks = downloader.download_tracks_from_excel(args.excel)
        
        if tracks:
            log.info(f"Success! Downloaded {len(tracks)} tracks.")
            for track in tracks:
                log.info(f"  - {os.path.basename(track)}")
            return 0
        else:
            log.error("Failed to download any tracks from Excel.")
            return 1
    else:
        log.error("Please provide either --url or --excel argument")
        return 1

if __name__ == "__main__":
    sys.exit(main())
