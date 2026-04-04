"""
SoundCloud downloader module for fetching music tracks.

This module provides functionality to:
1. Download SoundCloud tracks from URLs
2. Extract track information from Excel spreadsheets
3. Manage downloaded files
"""

import os
import sys
import logging
import pandas as pd
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import shutil
import json

# Set up logging
log = logging.getLogger('soundcloud_downloader')

class SoundCloudDownloader:
    """SoundCloud track downloader using yt-dlp."""
    
    def __init__(self, output_dir: str = "./downloaded_songs"):
        """
        Initialize SoundCloud downloader.
        
        Args:
            output_dir: Directory to save downloaded tracks
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def download_from_excel(
        self,
        excel_path: str,
        url_column: str = "Track URL",
        sheet_name: int = 0,
        limit: Optional[int] = None
    ) -> List[str]:
        """
        Download SoundCloud tracks from URLs in an Excel file.
        
        Args:
            excel_path: Path to Excel file containing SoundCloud URLs
            url_column: Column name containing track URLs
            sheet_name: Sheet name or index in Excel file
            limit: Maximum number of tracks to download (None for all)
        
        Returns:
            List of paths to downloaded audio files
        """
        try:
            log.info(f"Reading track URLs from Excel file: {excel_path}")
            
            # Read Excel file
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            if url_column not in df.columns:
                log.error(f"URL column '{url_column}' not found in Excel file")
                return []
            
            # Get URLs and optional filter by limit
            urls = df[url_column].dropna().tolist()
            
            if limit:
                urls = urls[:limit]
                
            log.info(f"Found {len(urls)} track URLs to download")
            
            # Download each track
            downloaded_files = []
            for i, url in enumerate(urls):
                log.info(f"Downloading track {i+1}/{len(urls)}: {url}")
                
                try:
                    file_path = self.download_track(url)
                    if file_path:
                        downloaded_files.append(file_path)
                except Exception as e:
                    log.error(f"Error downloading track {url}: {e}")
            
            log.info(f"Downloaded {len(downloaded_files)} tracks successfully")
            return downloaded_files
            
        except Exception as e:
            log.error(f"Error processing Excel file: {e}")
            return []
    
    def download_track(self, url: str) -> Optional[str]:
        """
        Download a single SoundCloud track.
        
        Args:
            url: SoundCloud track URL
            
        Returns:
            Path to downloaded file or None if download failed
        """
        try:
            log.info(f"Downloading track: {url}")
            
            # Ensure yt-dlp is installed
            try:
                subprocess.run(["yt-dlp", "--version"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                log.error("yt-dlp not found. Please install it with: pip install yt-dlp")
                return None
            
            # Set output template for yt-dlp
            output_template = str(self.output_dir / "%(artist)s - %(title)s - %(uploader)s.%(ext)s")
            
            # Download using yt-dlp
            cmd = [
                "yt-dlp",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "0",  # Best quality
                "--embed-thumbnail",
                "--add-metadata",
                "--output", output_template,
                url
            ]
            
            # Run download command
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if process.returncode != 0:
                log.error(f"Download failed: {process.stderr}")
                return None
            
            # Extract filename from output
            for line in process.stdout.split('\n'):
                if "Destination" in line and ".mp3" in line:
                    file_path = line.split("Destination: ")[1].strip()
                    if os.path.exists(file_path):
                        return file_path
            
            # Try to find the downloaded file in the output directory
            # This is a fallback if we couldn't extract the filename from output
            latest_file = self._get_latest_file()
            if latest_file:
                return latest_file
                
            log.warning("Downloaded file not found in output")
            return None
            
        except Exception as e:
            log.error(f"Error downloading track: {e}")
            return None
    
    def _get_latest_file(self) -> Optional[str]:
        """Get the most recently modified file in the output directory."""
        try:
            files = list(self.output_dir.glob("*.*"))
            if not files:
                return None
                
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return str(files[0])
            
        except Exception as e:
            log.error(f"Error getting latest file: {e}")
            return None
    
    def get_all_tracks(self) -> List[str]:
        """
        Get all downloaded tracks.
        
        Returns:
            List of paths to all downloaded tracks
        """
        try:
            # Find all audio files in the output directory
            extensions = [".mp3", ".wav", ".m4a", ".ogg"]
            files = []
            
            for ext in extensions:
                files.extend(list(self.output_dir.glob(f"*{ext}")))
                
            return [str(f) for f in files]
            
        except Exception as e:
            log.error(f"Error getting tracks: {e}")
            return []
