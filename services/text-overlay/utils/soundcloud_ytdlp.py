#!/usr/bin/env python3
"""
SoundCloud Downloader using yt-dlp
---------------------------------
A utility module for downloading SoundCloud tracks using yt-dlp.
This provides a reliable fallback when API methods are unavailable.
"""

import os
import sys
import logging
import subprocess
import pandas as pd
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

class SoundCloudYtDlp:
    """Class for downloading SoundCloud tracks using yt-dlp."""
    
    def __init__(self, output_dir: str = "./downloaded_songs"):
        """
        Initialize the SoundCloud downloader.
        
        Args:
            output_dir: Directory to save downloaded tracks
        """
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        log.info(f"SoundCloud yt-dlp downloader initialized. Output directory: {self.output_dir}")
        
        # Check if yt-dlp is installed
        try:
            result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                log.info(f"yt-dlp version: {result.stdout.strip()}")
            else:
                log.warning("yt-dlp check returned non-zero exit code. It may not be installed correctly.")
        except FileNotFoundError:
            log.error("yt-dlp not found. Please install it with: pip install yt-dlp")
            log.info("Attempting to install yt-dlp automatically...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp"], check=True)
                log.info("yt-dlp installed successfully")
            except subprocess.CalledProcessError:
                log.error("Failed to install yt-dlp. Please install it manually.")
    
    def download_track(self, url: str, output_template: Optional[str] = None) -> Optional[str]:
        """
        Download a track from SoundCloud.
        
        Args:
            url: URL of SoundCloud track
            output_template: Optional yt-dlp output template
            
        Returns:
            Path to downloaded file, or None if download failed
        """
        log.info(f"Downloading track: {url}")
        
        if not url or "soundcloud.com" not in url:
            log.error("Invalid SoundCloud URL")
            return None
        
        # Default output template: Title - Artist.mp3
        if not output_template:
            output_template = os.path.join(self.output_dir, "%(title)s - %(uploader)s.%(ext)s")
        
        try:
            # Prepare yt-dlp command
            cmd = [
                "yt-dlp",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "0",  # Best quality
                "--embed-thumbnail",
                "--add-metadata",
                "--output", output_template,
                "--no-progress",
                url
            ]
            
            log.info("Running yt-dlp command...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Extract the filename from yt-dlp output
                for line in result.stdout.splitlines():
                    if "[ExtractAudio] Destination:" in line:
                        file_path = line.split("[ExtractAudio] Destination: ")[1]
                        log.info(f"Successfully downloaded to: {file_path}")
                        return file_path
                    elif "[download] Destination:" in line:
                        file_path = line.split("[download] Destination: ")[1]
                        if os.path.exists(file_path):
                            log.info(f"Successfully downloaded to: {file_path}")
                            return file_path
                
                # If we couldn't find the exact file path in output, try to guess
                log.info("Could not determine exact output file, looking in output directory...")
                newest_file = self._get_newest_file(self.output_dir)
                if newest_file:
                    log.info(f"Using newest file in directory: {newest_file}")
                    return newest_file
                return None
            else:
                log.error(f"yt-dlp failed: {result.stderr}")
                return None
                
        except Exception as e:
            log.error(f"Error downloading track: {e}")
            return None
    
    def _get_newest_file(self, directory: str) -> Optional[str]:
        """Get the newest file in a directory."""
        try:
            files = [os.path.join(directory, f) for f in os.listdir(directory) 
                     if os.path.isfile(os.path.join(directory, f)) and f.endswith('.mp3')]
            if not files:
                return None
            return max(files, key=os.path.getctime)
        except Exception as e:
            log.error(f"Error finding newest file: {e}")
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
                log.error("Could not find a column with SoundCloud URLs")
                return []
            
            log.info(f"Found {len(df)} rows in Excel file")
            
            # Download each track
            for i, row in df.iterrows():
                url = row[url_column]
                
                # Skip invalid/empty URLs
                if not isinstance(url, str) or 'soundcloud.com' not in url.lower():
                    continue
                
                log.info(f"Processing track {i+1}/{len(df)}: {url}")
                
                # Download track
                track_path = self.download_track(url)
                
                if track_path:
                    downloaded_files.append(track_path)
                    log.info(f"Successfully downloaded track {i+1}/{len(df)}")
                else:
                    log.error(f"Failed to download track {i+1}/{len(df)}")
                
        except Exception as e:
            log.error(f"Error processing Excel file: {e}")
            
        log.info(f"Downloaded {len(downloaded_files)} out of {len(df)} tracks")
        return downloaded_files
