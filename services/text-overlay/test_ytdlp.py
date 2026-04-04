#!/usr/bin/env python3
"""
Test Script for SoundCloud yt-dlp Downloader
-------------------------------------------
Tests downloading SoundCloud tracks using yt-dlp.
"""

import os
import sys
import argparse
from utils.soundcloud_ytdlp import SoundCloudYtDlp

def main():
    """Test the SoundCloud yt-dlp downloader."""
    parser = argparse.ArgumentParser(description="Test SoundCloud yt-dlp downloader")
    parser.add_argument("--url", help="SoundCloud track URL to download")
    parser.add_argument("--excel", default="C:\\Users\\Isaia\\Downloads\\SoundCloud to X Reposter.xlsx", 
                        help="Excel file with SoundCloud URLs")
    parser.add_argument("--output-dir", default="./downloaded_songs", help="Output directory")
    parser.add_argument("--test-mode", choices=["single", "excel", "both"], default="both",
                        help="Test mode: single URL, excel file, or both")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize downloader
    downloader = SoundCloudYtDlp(output_dir=args.output_dir)
    
    success = False
    
    # Test with single URL if specified or if in both mode
    if (args.test_mode in ["single", "both"]) and args.url:
        print(f"Testing download with URL: {args.url}")
        track_path = downloader.download_track(args.url)
        
        if track_path and os.path.exists(track_path):
            print(f"Success! Track downloaded to: {track_path}")
            success = True
        else:
            print("Failed to download single track.")
    
    # Test with Excel file if in excel or both mode
    if args.test_mode in ["excel", "both"]:
        print(f"Testing download with Excel file: {args.excel}")
        tracks = downloader.download_tracks_from_excel(args.excel)
        
        if tracks:
            print(f"Success! Downloaded {len(tracks)} tracks:")
            for track in tracks:
                print(f"  - {os.path.basename(track)}")
            success = True
        else:
            print("Failed to download any tracks from Excel.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
