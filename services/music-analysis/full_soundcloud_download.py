#!/usr/bin/env python3
"""
Full SoundCloud Download - All 336 tracks
Runs independently with progress logging
"""
import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from soundcloud_downloader import SoundCloudDownloader
from config import SOUNDCLOUD_DIR

# Setup logging to file
log_file = Path(__file__).parent / "soundcloud_download.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_progress_file():
    """Create a progress tracking file"""
    progress_file = Path(__file__).parent / "download_progress.json"
    return progress_file

def save_progress(progress_data, progress_file):
    """Save download progress"""
    try:
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving progress: {e}")

def load_progress(progress_file):
    """Load existing progress"""
    try:
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading progress: {e}")
    
    return {
        'started_at': datetime.now().isoformat(),
        'total_tracks': 0,
        'downloaded': 0,
        'failed': 0,
        'skipped': 0,
        'current_track': 0,
        'completed_urls': [],
        'failed_urls': []
    }

def download_all_soundcloud_tracks():
    """Download all SoundCloud tracks with progress tracking"""
    logger.info("🚀 Starting Full SoundCloud Download Process")
    logger.info("=" * 60)
    
    # Setup progress tracking
    progress_file = create_progress_file()
    progress = load_progress(progress_file)
    
    try:
        # Initialize downloader
        sc = SoundCloudDownloader()
        tracks = sc.load_soundcloud_data()
        
        if not tracks:
            logger.error("❌ No tracks found in Excel file!")
            return
        
        progress['total_tracks'] = len(tracks)
        logger.info(f"📊 Total tracks to download: {len(tracks)}")
        logger.info(f"📁 Download directory: {SOUNDCLOUD_DIR}")
        
        # Check existing downloads
        existing_files = list(SOUNDCLOUD_DIR.glob("*.mp3")) + list(SOUNDCLOUD_DIR.glob("*.m4a"))
        logger.info(f"🎵 Existing downloads: {len(existing_files)}")
        
        # Download each track
        for i, track in enumerate(tracks, 1):
            progress['current_track'] = i
            
            try:
                title = track.get('title', 'Unknown')
                artist = track.get('artist', 'Unknown')
                url = track.get('url', '')
                
                logger.info(f"\n--- Track {i}/{len(tracks)} ({(i/len(tracks)*100):.1f}%) ---")
                logger.info(f"🎵 {title} by {artist}")
                
                # Skip if already processed
                if url in progress['completed_urls']:
                    logger.info("✅ Already completed - skipping")
                    progress['skipped'] += 1
                elif url in progress['failed_urls']:
                    logger.info("⚠️  Previously failed - skipping")
                    progress['skipped'] += 1
                elif track['file_path'].exists():
                    logger.info("✅ File exists - skipping")
                    progress['completed_urls'].append(url)
                    progress['skipped'] += 1
                else:
                    # Download the track
                    logger.info("🔄 Downloading...")
                    success = sc.download_track(track)
                    
                    if success:
                        logger.info("✅ Download successful!")
                        progress['downloaded'] += 1
                        progress['completed_urls'].append(url)
                    else:
                        logger.error("❌ Download failed")
                        progress['failed'] += 1
                        progress['failed_urls'].append(url)
                    
                    # Brief pause between downloads
                    time.sleep(3)
                
                # Save progress every 10 tracks
                if i % 10 == 0:
                    save_progress(progress, progress_file)
                    logger.info(f"💾 Progress saved: {progress['downloaded']} downloaded, {progress['failed']} failed")
                
            except KeyboardInterrupt:
                logger.info("⏹️  Download interrupted by user")
                save_progress(progress, progress_file)
                break
            except Exception as e:
                logger.error(f"❌ Error processing track {i}: {e}")
                progress['failed'] += 1
                continue
        
        # Final progress save
        progress['completed_at'] = datetime.now().isoformat()
        save_progress(progress, progress_file)
        
        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 DOWNLOAD COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"✅ Successfully downloaded: {progress['downloaded']}")
        logger.info(f"⏭️  Skipped (existing): {progress['skipped']}")
        logger.info(f"❌ Failed: {progress['failed']}")
        logger.info(f"📊 Total processed: {progress['current_track']}/{progress['total_tracks']}")
        
        # Check final file count
        final_files = list(SOUNDCLOUD_DIR.glob("*.mp3")) + list(SOUNDCLOUD_DIR.glob("*.m4a"))
        logger.info(f"🎵 Total audio files in library: {len(final_files)}")
        
        if len(final_files) > 0:
            logger.info("🎉 SoundCloud music library is now ready!")
            logger.info("🚀 You can now run the enhanced music analysis API")
        
        return progress
        
    except Exception as e:
        logger.error(f"❌ Critical error in download process: {e}")
        save_progress(progress, progress_file)
        return progress

def check_download_status():
    """Check current download status"""
    progress_file = create_progress_file()
    
    if not progress_file.exists():
        logger.info("📊 No download progress found - starting fresh")
        return None
    
    try:
        with open(progress_file, 'r') as f:
            progress = json.load(f)
        
        logger.info("📊 Current Download Status:")
        logger.info(f"   Started: {progress.get('started_at', 'Unknown')}")
        logger.info(f"   Progress: {progress.get('current_track', 0)}/{progress.get('total_tracks', 0)}")
        logger.info(f"   Downloaded: {progress.get('downloaded', 0)}")
        logger.info(f"   Failed: {progress.get('failed', 0)}")
        logger.info(f"   Skipped: {progress.get('skipped', 0)}")
        
        if 'completed_at' in progress:
            logger.info(f"   Completed: {progress['completed_at']}")
        
        return progress
        
    except Exception as e:
        logger.error(f"Error reading progress: {e}")
        return None

if __name__ == "__main__":
    print("🎧 SoundCloud Full Download Manager")
    print("=" * 50)
    
    # Check if download is already in progress or completed
    existing_progress = check_download_status()
    
    if existing_progress and 'completed_at' in existing_progress:
        print("✅ Download already completed!")
        print(f"📊 Final stats: {existing_progress['downloaded']} downloaded, {existing_progress['failed']} failed")
        
        # Check current files
        existing_files = list(SOUNDCLOUD_DIR.glob("*.mp3")) + list(SOUNDCLOUD_DIR.glob("*.m4a"))
        print(f"🎵 Current library: {len(existing_files)} files")
        
    else:
        print("🚀 Starting full download of all 336 SoundCloud tracks...")
        print("📝 Progress will be logged to soundcloud_download.log")
        print("⏹️  Press Ctrl+C to stop (progress will be saved)")
        print("\n" + "=" * 50)
        
        # Start the download
        final_progress = download_all_soundcloud_tracks()
        
        print("\n🎯 Download process completed!")
        if final_progress:
            print(f"📊 Final results: {final_progress.get('downloaded', 0)} downloaded, {final_progress.get('failed', 0)} failed")
