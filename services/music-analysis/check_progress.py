#!/usr/bin/env python3
"""
Quick progress checker for SoundCloud downloads
"""
import json
from pathlib import Path
from datetime import datetime

def check_progress():
    """Check current download progress"""
    progress_file = Path("download_progress.json")
    download_dir = Path("../soundcloud_music")
    
    print("🎧 SoundCloud Download Progress Check")
    print("=" * 40)
    
    # Check progress file
    if progress_file.exists():
        try:
            with open(progress_file, 'r') as f:
                progress = json.load(f)
            
            current = progress.get('current_track', 0)
            total = progress.get('total_tracks', 336)
            downloaded = progress.get('downloaded', 0)
            failed = progress.get('failed', 0)
            skipped = progress.get('skipped', 0)
            
            percentage = (current / total * 100) if total > 0 else 0
            
            print(f"📊 Progress: {current}/{total} tracks ({percentage:.1f}%)")
            print(f"✅ Downloaded: {downloaded}")
            print(f"⏭️  Skipped: {skipped}")
            print(f"❌ Failed: {failed}")
            
            if 'started_at' in progress:
                started = datetime.fromisoformat(progress['started_at'])
                elapsed = datetime.now() - started
                print(f"⏱️  Running for: {elapsed}")
                
                if current > 0:
                    avg_time_per_track = elapsed.total_seconds() / current
                    remaining_tracks = total - current
                    eta_seconds = remaining_tracks * avg_time_per_track
                    eta_hours = eta_seconds / 3600
                    print(f"🕐 ETA: ~{eta_hours:.1f} hours")
            
        except Exception as e:
            print(f"❌ Error reading progress: {e}")
    else:
        print("📊 No progress file found")
    
    # Check actual files
    if download_dir.exists():
        audio_files = list(download_dir.glob("*.mp3")) + list(download_dir.glob("*.m4a"))
        print(f"🎵 Audio files on disk: {len(audio_files)}")
        
        if audio_files:
            print("📁 Recent downloads:")
            sorted_files = sorted(audio_files, key=lambda f: f.stat().st_mtime, reverse=True)
            for file in sorted_files[:5]:
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"   - {file.name} ({size_mb:.1f}MB)")
    else:
        print("📁 Download directory not found")

if __name__ == "__main__":
    check_progress()
