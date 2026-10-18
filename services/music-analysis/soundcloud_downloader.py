"""
SoundCloud Music Downloader Module - Downloads tracks from SoundCloud URLs
"""
import pandas as pd
import json
import subprocess
import requests
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse
import time
import logging
from config import SOUNDCLOUD_CONFIG, DATABASE_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SoundCloudDownloader:
    def __init__(self):
        self.config = SOUNDCLOUD_CONFIG
        self.excel_file = self.config['excel_file']
        self.download_dir = self.config['download_dir']
        self.cache_file = DATABASE_CONFIG['soundcloud_cache']
        self.batch_size = self.config['batch_size']
        self.retry_attempts = self.config['retry_attempts']
        
        # Ensure download directory exists
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing cache
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load existing download cache"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
        return {'downloaded': [], 'failed': [], 'metadata': {}}
    
    def _save_cache(self):
        """Save download cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def load_soundcloud_data(self) -> List[Dict]:
        """Load SoundCloud data from Excel file"""
        try:
            if not self.excel_file.exists():
                logger.error(f"Excel file not found: {self.excel_file}")
                return []
            
            # Try reading different sheet names
            sheet_names = ['Sheet1', 'SoundCloud', 'Tracks', 'Data']
            df = None
            
            for sheet_name in sheet_names:
                try:
                    df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
                    logger.info(f"Successfully loaded sheet: {sheet_name}")
                    break
                except:
                    continue
            
            if df is None:
                # Try reading first sheet
                df = pd.read_excel(self.excel_file)
            
            # Clean and process data
            tracks = []
            for _, row in df.iterrows():
                track_data = self._extract_track_info(row)
                if track_data:
                    tracks.append(track_data)
            
            logger.info(f"Loaded {len(tracks)} tracks from Excel")
            return tracks
            
        except Exception as e:
            logger.error(f"Error loading Excel data: {e}")
            return []
    
    def _extract_track_info(self, row: pd.Series) -> Optional[Dict]:
        """Extract track information from Excel row"""
        try:
            track = {}
            
            # Specific column names for this Excel format
            url_columns = ['Track URL', 'url', 'link', 'soundcloud_url', 'track_url']
            title_columns = ['Track Title', 'title', 'track_title', 'name', 'song_name']
            artist_columns = ['Author', 'artist', 'creator', 'author', 'uploader']
            genre_columns = ['Genre', 'genre', 'style']
            
            # Extract URL
            for col in url_columns:
                if col in row.index and pd.notna(row[col]):
                    url = str(row[col]).strip()
                    if 'soundcloud.com' in url:
                        track['url'] = url
                        break
            
            if 'url' not in track:
                return None
            
            # Extract title
            for col in title_columns:
                if col in row.index and pd.notna(row[col]):
                    track['title'] = str(row[col]).strip()
                    break
            
            # Extract artist
            for col in artist_columns:
                if col in row.index and pd.notna(row[col]):
                    track['artist'] = str(row[col]).strip()
                    break
            
            # Extract genre
            for col in genre_columns:
                if col in row.index and pd.notna(row[col]):
                    track['genre'] = str(row[col]).strip()
                    break
            
            # Generate safe filename
            safe_title = self._make_safe_filename(
                track.get('title', 'Unknown Track')
            )
            safe_artist = self._make_safe_filename(
                track.get('artist', 'Unknown Artist')
            )
            
            track['filename'] = f"{safe_artist} - {safe_title}.mp3"
            track['file_path'] = self.download_dir / track['filename']
            
            return track
            
        except Exception as e:
            logger.error(f"Error extracting track info: {e}")
            return None
    
    def _make_safe_filename(self, name: str) -> str:
        """Create safe filename from track/artist name"""
        # Remove/replace problematic characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.() "
        safe_name = ''.join(c for c in name if c in safe_chars)
        
        # Remove extra spaces and limit length
        safe_name = ' '.join(safe_name.split())[:50]
        
        return safe_name if safe_name else "Unknown"
    
    def download_track(self, track: Dict) -> bool:
        """Download a single SoundCloud track"""
        url = track['url']
        file_path = track['file_path']
        
        # Check if already downloaded
        if str(url) in self.cache['downloaded']:
            logger.info(f"Already downloaded: {track.get('title', url)}")
            return True
        
        if file_path.exists():
            logger.info(f"File exists: {file_path.name}")
            self.cache['downloaded'].append(str(url))
            self._save_cache()
            return True
        
        # Download using yt-dlp (best tool for SoundCloud)
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Downloading: {track.get('title', url)} (attempt {attempt + 1})")
                
                cmd = [
                    'yt-dlp',
                    '--extract-audio',
                    '--audio-format', 'mp3',
                    '--audio-quality', '192K',
                    '--output', str(file_path.with_suffix('.%(ext)s')),
                    '--no-playlist',
                    url
                ]
                
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=300
                )
                
                if result.returncode == 0 and file_path.exists():
                    logger.info(f"Successfully downloaded: {file_path.name}")
                    self.cache['downloaded'].append(str(url))
                    self.cache['metadata'][str(url)] = track
                    self._save_cache()
                    return True
                else:
                    logger.warning(f"Download failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.warning(f"Download timeout for: {url}")
            except Exception as e:
                logger.error(f"Download error: {e}")
            
            time.sleep(2)  # Wait before retry
        
        # Mark as failed
        self.cache['failed'].append(str(url))
        self._save_cache()
        return False
    
    def bulk_download(self, tracks: List[Dict]) -> Dict:
        """Download multiple tracks with progress tracking"""
        results = {
            'successful': [],
            'failed': [],
            'skipped': []
        }
        
        logger.info(f"Starting bulk download of {len(tracks)} tracks")
        
        for i, track in enumerate(tracks, 1):
            logger.info(f"Processing track {i}/{len(tracks)}")
            
            try:
                if self.download_track(track):
                    results['successful'].append(track)
                else:
                    results['failed'].append(track)
                    
            except Exception as e:
                logger.error(f"Error processing track {i}: {e}")
                results['failed'].append(track)
            
            # Brief pause between downloads
            time.sleep(1)
        
        logger.info(f"Download complete: {len(results['successful'])} successful, "
                   f"{len(results['failed'])} failed")
        
        return results
    
    def get_downloaded_tracks(self) -> List[Path]:
        """Get list of successfully downloaded track files"""
        downloaded_files = []
        
        for file_path in self.download_dir.rglob("*.mp3"):
            if file_path.is_file():
                downloaded_files.append(file_path)
        
        return downloaded_files
    
    def update_metadata(self, file_path: Path, metadata: Dict):
        """Update metadata for a downloaded track"""
        try:
            # Use mutagen to update MP3 metadata
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC
            
            audio = MP3(str(file_path))
            
            if audio.tags is None:
                audio.add_tags()
            
            # Update tags
            if 'title' in metadata:
                audio.tags.add(TIT2(encoding=3, text=metadata['title']))
            if 'artist' in metadata:
                audio.tags.add(TPE1(encoding=3, text=metadata['artist']))
            
            audio.save()
            logger.info(f"Updated metadata for: {file_path.name}")
            
        except Exception as e:
            logger.error(f"Error updating metadata: {e}")
    
    def cleanup_failed_downloads(self):
        """Remove partial/corrupted download files"""
        cleaned = 0
        
        for file_path in self.download_dir.rglob("*.part"):
            try:
                file_path.unlink()
                cleaned += 1
            except Exception:
                pass
        
        logger.info(f"Cleaned up {cleaned} partial download files")
        return cleaned
