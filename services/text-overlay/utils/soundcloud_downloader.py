#!/usr/bin/env python3
"""
SoundCloud Track Downloader
--------------------------
Utility for downloading tracks from SoundCloud using the RapidAPI SoundCloud MP3 Downloader.
Reads track URLs from an Excel file and downloads them to a specified directory.
"""

import os
import sys
import time
import json
import pandas as pd
import requests
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger("soundcloud_downloader")

# API constants
API_HOST = "rapidapi.com"
API_ENDPOINT = "Get Stream or download URL"
DEFAULT_API_KEY = __import__('os').environ['DEFAULT_API_KEY']

class SoundCloudDownloader:
    """
    Class for downloading SoundCloud tracks using RapidAPI's SoundCloud MP3 Downloader API.
    """
    
    def __init__(self, api_key: Optional[str] = None, output_dir: str = "./downloaded_songs"):
        """
        Initialize the SoundCloud downloader.
        
        Args:
            api_key: RapidAPI key for SoundCloud API
            output_dir: Directory to save downloaded tracks
        """
        self.api_key = api_key or DEFAULT_API_KEY
        self.output_dir = output_dir
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "content-type": "application/json"
        }
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        log.info(f"SoundCloud downloader initialized. Output directory: {self.output_dir}")
    
    def extract_track_id(self, url: str) -> Optional[str]:
        """
        Extract track ID from SoundCloud URL.
        
        Args:
            url: SoundCloud track URL
            
        Returns:
            Track ID if found, None otherwise
        """
        try:
            # Handle different URL formats
            parsed_url = urlparse(url)
            
            # If there's a specific path pattern for SoundCloud tracks, extract from there
            path_parts = parsed_url.path.split('/')
            if len(path_parts) >= 2:
                # Last part might be the track ID or name
                return path_parts[-1]
            
            # If query parameters contain the track ID
            query_params = parse_qs(parsed_url.query)
            if 'track_id' in query_params:
                return query_params['track_id'][0]
                
            # If we can't parse it directly, just use the URL as is
            return url
                
        except Exception as e:
            log.error(f"Failed to extract track ID from URL {url}: {e}")
            return None
    
    def download_track(self, track_url: str) -> Optional[str]:
        """
        Download a track from SoundCloud using the stream URL API.
        
        Args:
            track_url: URL of the track to download
            
        Returns:
            Path to the downloaded file if successful, None otherwise
        """
        try:
            log.info(f"Downloading track: {track_url}")
            
            # Extract track ID or use the URL as is for the filename
            track_id = self.extract_track_id(track_url) or track_url
            
            # Prepare request based on the API from the screenshot
            # Using the curl structure shown in the screenshot
            url = "https://soundcloud-api3.p.rapidapi.com/api/v1/track/url"
            
            # Headers from the screenshot
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "soundcloud-api3.p.rapidapi.com"
            }
            
            # Payload structure based on the screenshot's curl example
            payload = {"url": track_url}
            
            # Make API request to get the stream URL
            response = requests.post(url, json=payload, headers=headers)
            
            # Check if request was successful
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Extract stream URL from response
                    stream_url = data.get("url")
                    title = data.get("title", track_id)
                    
                    if stream_url:
                        log.info(f"Retrieved stream URL for track: {title}")
                        
                        # Download the actual audio file
                        audio_response = requests.get(stream_url)
                        
                        if audio_response.status_code == 200:
                            # Create safe filename
                            safe_title = ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in title)
                            output_path = os.path.join(self.output_dir, f"{safe_title}.mp3")
                            
                            # Save file
                            with open(output_path, 'wb') as f:
                                f.write(audio_response.content)
                                
                            log.info(f"Track downloaded successfully: {output_path}")
                            return output_path
                        else:
                            log.error(f"Failed to download audio file. Status code: {audio_response.status_code}")
                    else:
                        log.error("Stream URL not found in API response")
                except json.JSONDecodeError:
                    log.error(f"Failed to parse API response as JSON: {response.text}")
            else:
                log.error(f"API request failed. Status code: {response.status_code}")
                log.error(f"Response: {response.text}")
                
        except Exception as e:
            log.error(f"Error downloading track: {e}")
            
        return None
    
    def download_tracks_from_excel(self, excel_path: str, url_column: Optional[str] = None) -> List[str]:
        """
        Download tracks from URLs listed in an Excel file.
        
        Args:
            excel_path: Path to Excel file containing track URLs
            url_column: Name of column containing URLs (if None, will try to auto-detect)
            
        Returns:
            List of paths to downloaded files
        """
        downloaded_files = []
        
        try:
            # Read Excel file
            df = pd.read_excel(excel_path)
            
            # If column not specified, first check for 'Track URL' column which is known to exist in the file
            if not url_column and 'Track URL' in df.columns:
                url_column = 'Track URL'
                log.info("Using 'Track URL' column from Excel file")
            # Otherwise try to find a column with URLs
            elif not url_column:
                for col in df.columns:
                    # Check if column contains URLs (looking for strings containing 'soundcloud.com')
                    if any(isinstance(x, str) and 'soundcloud.com' in x.lower() for x in df[col]):
                        url_column = col
                        log.info(f"Found SoundCloud URLs in column: {col}")
                        break
            
            if not url_column:
                log.error("Could not find column with SoundCloud URLs")
                return downloaded_files
            
            # Get all valid URLs
            urls = [url for url in df[url_column] if isinstance(url, str) and 'soundcloud.com' in url.lower()]
            
            if not urls:
                log.warning(f"No SoundCloud URLs found in column '{url_column}'")
                return downloaded_files
            
            log.info(f"Found {len(urls)} SoundCloud URLs to download")
            
            # Download each track with a small delay between requests to avoid rate limiting
            for i, url in enumerate(urls):
                log.info(f"Processing track {i+1}/{len(urls)}")
                file_path = self.download_track(url)
                
                if file_path:
                    downloaded_files.append(file_path)
                
                # Small delay between requests
                if i < len(urls) - 1:
                    time.sleep(1)
        
        except Exception as e:
            log.error(f"Error processing Excel file: {e}")
        
        log.info(f"Downloaded {len(downloaded_files)} tracks successfully")
        return downloaded_files


# Command-line interface
def main():
    """
    Command-line interface for downloading SoundCloud tracks from an Excel file.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Download SoundCloud tracks from an Excel file")
    parser.add_argument("--excel", required=True, help="Path to Excel file containing SoundCloud URLs")
    parser.add_argument("--output-dir", default="./downloaded_songs", help="Directory to save downloaded tracks")
    parser.add_argument("--api-key", help="RapidAPI key for SoundCloud API3")
    parser.add_argument("--url-column", help="Name of column containing SoundCloud URLs")
    
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = SoundCloudDownloader(api_key=args.api_key, output_dir=args.output_dir)
    
    # Download tracks
    downloaded_files = downloader.download_tracks_from_excel(args.excel, args.url_column)
    
    if downloaded_files:
        print(f"Successfully downloaded {len(downloaded_files)} tracks to {args.output_dir}")
        return 0
    else:
        print("No tracks were downloaded")
        return 1


if __name__ == "__main__":
    sys.exit(main())
