#!/usr/bin/env python3
"""
Download Top SoundCloud Tracks
==============================
Automatically download a curated selection of top tracks from the reposter file
"""

import pandas as pd
import os
import sys
import time
import json
from pathlib import Path
import yt_dlp
from datetime import datetime

def download_top_tracks(num_tracks: int = 25):
    """Download top tracks automatically"""
    
    excel_path = "SoundCloud to X Reposter.xlsx"
    
    print("🎵 DOWNLOADING TOP SOUNDCLOUD TRACKS")
    print("=" * 60)
    print(f"🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Target: {num_tracks} tracks")
    
    if not os.path.exists(excel_path):
        print(f"❌ Excel file not found: {excel_path}")
        return False
    
    try:
        # Setup music directory
        music_dir = Path("music_library")
        music_dir.mkdir(exist_ok=True)
        
        # Create genre directories
        genres = ["electronic", "hiphop", "lofi", "house", "ambient", "general"]
        for genre in genres:
            (music_dir / genre).mkdir(exist_ok=True)
        
        print(f"📁 Music directory: {music_dir.absolute()}")
        
        # Read and filter Excel file
        df = pd.read_excel(excel_path)
        
        # Clean data
        df = df.dropna(subset=['Track URL'])
        df = df[df['Track URL'].str.contains('soundcloud.com', na=False)]
        
        # Remove duplicates based on URL
        df = df.drop_duplicates(subset=['Track URL'])
        
        # Try to get diverse selection
        diverse_df = []
        
        # Get tracks from different genres/artists
        unique_artists = df['Author'].unique()[:15]  # Top 15 artists
        for artist in unique_artists:
            artist_tracks = df[df['Author'] == artist].head(2)  # Max 2 per artist
            diverse_df.append(artist_tracks)
        
        if diverse_df:
            df_selected = pd.concat(diverse_df).drop_duplicates(subset=['Track URL']).head(num_tracks)
        else:
            df_selected = df.head(num_tracks)
        
        print(f"📊 Selected {len(df_selected)} diverse tracks from {len(df)} total")
        
        # Configure yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '192',
            'writeinfojson': False,
            'quiet': True,
            'no_warnings': True,
        }
        
        # Download tracks
        successful_downloads = []
        failed_downloads = []
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for index, row in df_selected.iterrows():
                print(f"\n{'='*50}")
                print(f"📀 Track {len(successful_downloads) + len(failed_downloads) + 1}/{len(df_selected)}")
                
                title = str(row['Track Title'])[:50]  # Limit title length
                artist = str(row['Author'])[:30]     # Limit artist length
                url = str(row['Track URL'])
                genre = str(row.get('Genre', 'general')).lower()
                
                print(f"🎵 {title} by {artist}")
                print(f"🔗 {url[:60]}...")
                
                # Determine genre directory
                genre_dir = music_dir / "general"
                for g in genres:
                    if g in genre.lower() or g in title.lower() or g in artist.lower():
                        genre_dir = music_dir / g
                        break
                
                # Create safe filename
                safe_name = f"{artist} - {title}".replace('/', '_').replace('\\', '_').replace(':', '_')
                safe_name = ''.join(c for c in safe_name if c.isalnum() or c in (' ', '-', '_')).strip()[:80]
                
                # Set output template
                ydl_opts['outtmpl'] = str(genre_dir / f"{safe_name}.%(ext)s")
                
                try:
                    # Check if already exists
                    existing_files = list(genre_dir.glob(f"{safe_name}.*"))
                    if existing_files:
                        print(f"⚠️  Already exists: {existing_files[0].name}")
                        successful_downloads.append({
                            'title': title,
                            'artist': artist,
                            'file': str(existing_files[0]),
                            'status': 'already_exists'
                        })
                        continue
                    
                    # Download
                    with yt_dlp.YoutubeDL(ydl_opts) as current_ydl:
                        current_ydl.download([url])
                    
                    # Verify download
                    new_files = list(genre_dir.glob(f"{safe_name}.*"))
                    if new_files:
                        print(f"✅ Downloaded: {new_files[0].name}")
                        successful_downloads.append({
                            'title': title,
                            'artist': artist,
                            'file': str(new_files[0]),
                            'genre': genre_dir.name,
                            'status': 'downloaded'
                        })
                    else:
                        print(f"❌ Download failed: File not found")
                        failed_downloads.append({'title': title, 'artist': artist, 'url': url})
                
                except Exception as e:
                    print(f"❌ Download failed: {str(e)[:100]}")
                    failed_downloads.append({'title': title, 'artist': artist, 'url': url, 'error': str(e)})
                
                # Small delay
                time.sleep(1)
        
        # Create results
        results = {
            'successful': successful_downloads,
            'failed': failed_downloads,
            'total_attempted': len(df_selected),
            'download_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save results
        results_file = music_dir / "download_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Create music index
        create_music_index()
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 DOWNLOAD SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successful: {len(successful_downloads)}")
        print(f"❌ Failed: {len(failed_downloads)}")
        print(f"📁 Music library: {music_dir.absolute()}")
        
        if successful_downloads:
            print(f"\n🎵 Downloaded tracks:")
            for track in successful_downloads[:10]:  # Show first 10
                print(f"   ✅ {track['artist']} - {track['title']}")
            if len(successful_downloads) > 10:
                print(f"   ... and {len(successful_downloads) - 10} more")
        
        return len(successful_downloads) > 0
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_music_index():
    """Create music index for easy access"""
    
    music_dir = Path("music_library")
    music_files = []
    
    for genre_dir in music_dir.iterdir():
        if genre_dir.is_dir():
            for music_file in genre_dir.glob("*.mp3"):
                music_files.append({
                    'file': str(music_file),
                    'name': music_file.stem,
                    'genre': genre_dir.name,
                    'size_mb': round(music_file.stat().st_size / (1024 * 1024), 2)
                })
    
    index_file = music_dir / "music_index.json"
    with open(index_file, 'w') as f:
        json.dump(music_files, f, indent=2)
    
    print(f"📋 Created music index: {len(music_files)} tracks")
    return True

def main():
    """Main function"""
    
    print("🎵 TOP SOUNDCLOUD TRACKS DOWNLOADER")
    print("=" * 50)
    
    if download_top_tracks(25):  # Download 25 diverse tracks
        print("\n🎉 Download completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Test local music selector")
        print("   2. Update video processor to use local tracks")
        print("   3. Process videos with local background music")
    else:
        print("\n❌ Download failed")

if __name__ == "__main__":
    main()
