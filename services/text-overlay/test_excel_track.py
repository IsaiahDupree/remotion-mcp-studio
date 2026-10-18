#!/usr/bin/env python3
"""
Test Downloading First SoundCloud Track from Excel
-------------------------------------------------
This script extracts the first SoundCloud track URL from the Excel file
and attempts to download it using the SoundCloud API3 endpoint.
"""

import os
import sys
import pandas as pd
import argparse
from utils.soundcloud_downloader import SoundCloudDownloader

def main():
    """Extract first track URL from Excel and test download."""
    parser = argparse.ArgumentParser(description="Test SoundCloud download from Excel")
    parser.add_argument(
        "--excel", 
        default="C:\\Users\\Isaia\\Downloads\\SoundCloud to X Reposter.xlsx",
        help="Path to Excel file with SoundCloud URLs"
    )
    parser.add_argument(
        "--api-key", 
        required=True, 
        help="RapidAPI key for SoundCloud API3"
    )
    parser.add_argument(
        "--output-dir", 
        default="./downloaded_songs",
        help="Directory to save downloaded tracks"
    )
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        # Read Excel file
        print(f"Reading Excel file: {args.excel}")
        df = pd.read_excel(args.excel)
        
        # Check if 'Track URL' column exists
        if 'Track URL' in df.columns:
            # Get first valid URL
            for i, row in df.iterrows():
                track_url = row['Track URL']
                if isinstance(track_url, str) and 'soundcloud.com' in track_url:
                    print(f"Found track URL: {track_url}")
                    
                    # Initialize downloader
                    downloader = SoundCloudDownloader(
                        api_key=args.api_key,
                        output_dir=args.output_dir
                    )
                    
                    # Attempt to download
                    print(f"Attempting to download track...")
                    track_path = downloader.download_track(track_url)
                    
                    if track_path:
                        print(f"SUCCESS! Track downloaded to: {track_path}")
                        return 0
                    else:
                        print("FAILED to download track.")
                        return 1
                    
                    # Only test the first URL
                    break
            
            print("No valid SoundCloud URLs found in the Excel file.")
            return 1
        else:
            print("'Track URL' column not found in Excel file.")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
