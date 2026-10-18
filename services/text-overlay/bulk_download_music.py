#!/usr/bin/env python3
"""
Bulk Download SoundCloud Music Tracks
=====================================
Download all tracks from the Excel file and organize them locally
"""

import pandas as pd
import os
import sys
import time
import json
from pathlib import Path
import yt_dlp
from datetime import datetime

def setup_download_directory():
    """Create and setup the music download directory"""
    
    music_dir = Path("music_library")
    music_dir.mkdir(exist_ok=True)
    
    # Create subdirectories by genre/mood
    genres = ["lofi", "electronic", "acoustic", "corporate", "ambient", "general"]
    for genre in genres:
        (music_dir / genre).mkdir(exist_ok=True)
    
    return music_dir

def get_safe_filename(title, artist):
    """Create a safe filename from title and artist"""
    
    # Combine title and artist
    filename = f"{artist} - {title}"
    
    # Remove/replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename

def download_track(url, output_path, title, artist):
    """Download a single track using yt-dlp"""
    
    try:
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(output_path / f"{get_safe_filename(title, artist)}.%(ext)s"),
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '192',
            'writeinfojson': False,
            'quiet': False,
            'no_warnings': False,
            'extractsubtitles': False,
            'writesubtitles': False,
        }
        
        print(f"🎵 Downloading: {title} by {artist}")
        print(f"   URL: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        print(f"✅ Downloaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def bulk_download_music(max_tracks: int = 50):
    """Download music tracks from Excel file"""
    
    excel_path = "SoundCloud to X Reposter.xlsx"
    
    print("🎵 BULK MUSIC DOWNLOAD STARTED")
    print("=" * 60)
    print(f"🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not os.path.exists(excel_path):
        print(f"❌ Excel file not found: {excel_path}")
        return False
    
    try:
        # Setup download directory
        music_dir = setup_download_directory()
        print(f"📁 Music directory: {music_dir.absolute()}")
        
        # Read Excel file
        df = pd.read_excel(excel_path)
        
        # Clean and filter the data
        df = df.dropna(subset=['Track URL'])  # Remove rows without URLs
        df = df[df['Track URL'].str.contains('soundcloud.com', na=False)]  # Only SoundCloud URLs
        
        # Limit number of tracks to download
        if len(df) > max_tracks:
            print(f"📊 Found {len(df)} tracks, limiting to top {max_tracks} for this download")
            df = df.head(max_tracks)
        
        print(f"📊 Total tracks to download: {len(df)}")
        
        # Track download results
        download_results = {
            'successful': [],
            'failed': [],
            'total': len(df)
        }
        
        # Download each track
        for index, row in df.iterrows():
            print(f"\n{'='*60}")
            print(f"📀 Track {index + 1}/{len(df)}")
            
            title = str(row['Track Title'])
            artist = str(row['Author'])
            url = str(row['Track URL'])
            genre = str(row.get('Genre', 'general')).lower()
            tags = str(row.get('Tags', ''))
            
            print(f"🎵 Title: {title}")
            print(f"🎤 Artist: {artist}")
            print(f"🎼 Genre: {genre}")
            print(f"🏷️ Tags: {tags[:50]}..." if len(tags) > 50 else f"🏷️ Tags: {tags}")
            
            # Determine output directory based on genre
            genre_dir = music_dir / genre.lower()
            if not genre_dir.exists():
                genre_dir = music_dir / "general"
            
            # Check if already downloaded
            safe_filename = get_safe_filename(title, artist)
            existing_files = list(genre_dir.glob(f"{safe_filename}.*"))
            
            if existing_files:
                print(f"⚠️  Already exists: {existing_files[0].name}")
                download_results['successful'].append({
                    'title': title,
                    'artist': artist,
                    'file': str(existing_files[0]),
                    'status': 'already_exists'
                })
                continue
            
            # Download the track
            if download_track(url, genre_dir, title, artist):
                # Find the downloaded file
                downloaded_files = list(genre_dir.glob(f"{safe_filename}.*"))
                if downloaded_files:
                    download_results['successful'].append({
                        'title': title,
                        'artist': artist,
                        'file': str(downloaded_files[0]),
                        'genre': genre,
                        'tags': tags,
                        'status': 'downloaded'
                    })
                else:
                    download_results['failed'].append({
                        'title': title,
                        'artist': artist,
                        'url': url,
                        'error': 'File not found after download'
                    })
            else:
                download_results['failed'].append({
                    'title': title,
                    'artist': artist,
                    'url': url,
                    'error': 'Download failed'
                })
            
            # Small delay between downloads
            time.sleep(2)
        
        # Save download results
        results_file = music_dir / "download_results.json"
        with open(results_file, 'w') as f:
            json.dump(download_results, f, indent=2)
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 DOWNLOAD SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successful: {len(download_results['successful'])}")
        print(f"❌ Failed: {len(download_results['failed'])}")
        print(f"📁 Total files: {len(download_results['successful'])}")
        
        if download_results['successful']:
            print(f"\n🎵 Successfully downloaded tracks:")
            for track in download_results['successful']:
                print(f"   ✅ {track['artist']} - {track['title']}")
                print(f"      📁 {track['file']}")
        
        if download_results['failed']:
            print(f"\n❌ Failed downloads:")
            for track in download_results['failed']:
                print(f"   ❌ {track['artist']} - {track['title']}")
                print(f"      Error: {track['error']}")
        
        print(f"\n📁 Music library created at: {music_dir.absolute()}")
        print(f"📝 Results saved to: {results_file}")
        
        return len(download_results['successful']) > 0
        
    except Exception as e:
        print(f"❌ Bulk download failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_music_index():
    """Create an index of downloaded music for easy access"""
    
    music_dir = Path("music_library")
    if not music_dir.exists():
        print("❌ Music library not found")
        return False
    
    try:
        # Find all music files
        music_files = []
        for genre_dir in music_dir.iterdir():
            if genre_dir.is_dir():
                for music_file in genre_dir.glob("*.mp3"):
                    music_files.append({
                        'file': str(music_file),
                        'name': music_file.stem,
                        'genre': genre_dir.name,
                        'size_mb': music_file.stat().st_size / (1024 * 1024)
                    })
        
        # Create index
        index_file = music_dir / "music_index.json"
        with open(index_file, 'w') as f:
            json.dump(music_files, f, indent=2)
        
        print(f"📋 Music index created: {index_file}")
        print(f"🎵 Total tracks indexed: {len(music_files)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Index creation failed: {e}")
        return False

def main():
    """Main function"""
    
    print("🎵 SOUNDCLOUD MUSIC BULK DOWNLOADER")
    print("=" * 50)
    
    # Ask user how many tracks to download
    try:
        max_tracks = int(input("How many tracks would you like to download? (default: 20): ") or "20")
    except:
        max_tracks = 20
    
    print(f"📊 Downloading up to {max_tracks} tracks...")
    
    # Download music
    if bulk_download_music(max_tracks):
        print("\n🎉 Bulk download completed successfully!")
        
        # Create index
        if create_music_index():
            print("✅ Music index created successfully!")
        
        print("\n📝 Next steps:")
        print("   1. Music files are organized by genre")
        print("   2. Update music enhancer to use local files")
        print("   3. Test video processing with local music")
        
        return True
    else:
        print("\n❌ Bulk download failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
