#!/usr/bin/env python3
"""
Test SoundCloud download functionality
"""
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from soundcloud_downloader import SoundCloudDownloader
from config import SOUNDCLOUD_CONFIG

def test_soundcloud_setup():
    """Test SoundCloud download setup"""
    print("🎧 Testing SoundCloud Download Setup...")
    
    # Check Excel file
    excel_file = SOUNDCLOUD_CONFIG['excel_file']
    print(f"📁 Excel file path: {excel_file}")
    print(f"📁 Excel file exists: {excel_file.exists()}")
    
    if excel_file.exists():
        print(f"📁 Excel file size: {excel_file.stat().st_size} bytes")
    
    # Check download directory
    download_dir = SOUNDCLOUD_CONFIG['download_dir']
    print(f"📁 Download directory: {download_dir}")
    print(f"📁 Download directory exists: {download_dir.exists()}")
    
    if download_dir.exists():
        audio_files = list(download_dir.glob("*.mp3")) + list(download_dir.glob("*.wav")) + list(download_dir.glob("*.m4a"))
        print(f"🎵 Current audio files: {len(audio_files)}")
        
        for file in audio_files[:5]:  # Show first 5 files
            print(f"   - {file.name}")
    
    # Initialize downloader
    try:
        downloader = SoundCloudDownloader()
        print("✅ SoundCloud downloader initialized successfully")
        
        # Check if Excel file can be read
        if excel_file.exists():
            try:
                tracks = downloader.load_tracks_from_excel()
                print(f"📊 Tracks found in Excel: {len(tracks)}")
                
                # Show first few tracks
                for i, track in enumerate(tracks[:3]):
                    print(f"   Track {i+1}: {track.get('title', 'Unknown')} - {track.get('url', 'No URL')}")
                
                return tracks
                
            except Exception as e:
                print(f"❌ Error reading Excel file: {e}")
                return []
        else:
            print("⚠️  Excel file not found - cannot load tracks")
            return []
            
    except Exception as e:
        print(f"❌ Error initializing SoundCloud downloader: {e}")
        return []

def test_single_download():
    """Test downloading a single track"""
    print("\n🎵 Testing Single Track Download...")
    
    # Sample SoundCloud URL for testing
    test_url = "https://soundcloud.com/example-track"  # This would need to be a real URL
    
    try:
        downloader = SoundCloudDownloader()
        print(f"🔄 Would attempt to download: {test_url}")
        print("⚠️  Skipping actual download to avoid errors with invalid URL")
        
        # Check yt-dlp availability
        import subprocess
        result = subprocess.run(['yt-dlp', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ yt-dlp available: {result.stdout.strip()}")
        else:
            print("❌ yt-dlp not available")
            
    except Exception as e:
        print(f"❌ Error in download test: {e}")

def main():
    """Main test function"""
    print("🚀 SoundCloud Download Test")
    print("=" * 50)
    
    # Test setup
    tracks = test_soundcloud_setup()
    
    # Test download capability
    test_single_download()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    excel_file = SOUNDCLOUD_CONFIG['excel_file']
    download_dir = SOUNDCLOUD_CONFIG['download_dir']
    
    status = {
        'excel_exists': excel_file.exists(),
        'download_dir_exists': download_dir.exists(),
        'tracks_in_excel': len(tracks) if tracks else 0,
        'current_downloads': len(list(download_dir.glob("*.mp3"))) if download_dir.exists() else 0
    }
    
    print(f"📁 Excel file: {'✅ Found' if status['excel_exists'] else '❌ Missing'}")
    print(f"📁 Download directory: {'✅ Ready' if status['download_dir_exists'] else '❌ Missing'}")
    print(f"📊 Tracks in Excel: {status['tracks_in_excel']}")
    print(f"🎵 Current downloads: {status['current_downloads']}")
    
    if status['excel_exists'] and status['tracks_in_excel'] > 0 and status['current_downloads'] == 0:
        print("\n🎯 RECOMMENDATION: Run SoundCloud download to populate music library")
        print("   Use: python -c \"from main_system import MusicSystem; ms = MusicSystem(); ms.setup_soundcloud_music()\"")
    elif status['current_downloads'] > 0:
        print(f"\n✅ SoundCloud library ready with {status['current_downloads']} tracks")
    else:
        print("\n⚠️  SoundCloud setup incomplete - check Excel file and configuration")
    
    return status

if __name__ == "__main__":
    main()
