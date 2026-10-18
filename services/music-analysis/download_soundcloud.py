#!/usr/bin/env python3
"""
Download SoundCloud tracks from Excel file
"""
import time
from soundcloud_downloader import SoundCloudDownloader

def download_soundcloud_batch(count=5):
    """Download a batch of SoundCloud tracks"""
    print(f"🎧 Starting SoundCloud download (first {count} tracks)...")
    
    try:
        sc = SoundCloudDownloader()
        tracks = sc.load_soundcloud_data()
        
        if not tracks:
            print("❌ No tracks found!")
            return
        
        print(f"📊 Total tracks available: {len(tracks)}")
        print(f"🔄 Downloading first {min(count, len(tracks))} tracks...")
        
        success_count = 0
        failed_count = 0
        
        for i, track in enumerate(tracks[:count]):
            print(f"\n--- Track {i+1}/{min(count, len(tracks))} ---")
            print(f"🎵 {track.get('title', 'Unknown')} by {track.get('artist', 'Unknown')}")
            print(f"🔗 {track.get('url', '')}")
            
            try:
                # Check if already downloaded
                if track['file_path'].exists():
                    print("✅ Already downloaded - skipping")
                    success_count += 1
                    continue
                
                # Download the track
                print("🔄 Downloading...")
                success = sc.download_track(track)
                
                if success:
                    print("✅ Download successful!")
                    success_count += 1
                else:
                    print("❌ Download failed")
                    failed_count += 1
                
                # Brief pause between downloads
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error downloading track: {e}")
                failed_count += 1
        
        print(f"\n📊 Download Summary:")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📁 Downloaded to: {sc.download_dir}")
        
        # List current files
        audio_files = list(sc.download_dir.glob("*.mp3")) + list(sc.download_dir.glob("*.m4a"))
        print(f"🎵 Total audio files now: {len(audio_files)}")
        
        return success_count, failed_count
        
    except Exception as e:
        print(f"❌ Error in download process: {e}")
        return 0, 0

def check_current_library():
    """Check current music library status"""
    print("📊 Current Music Library Status:")
    print("=" * 50)
    
    from config import SOUNDCLOUD_DIR, MUSIC_DIR
    
    # SoundCloud downloads
    if SOUNDCLOUD_DIR.exists():
        sc_files = list(SOUNDCLOUD_DIR.glob("*.mp3")) + list(SOUNDCLOUD_DIR.glob("*.m4a"))
        print(f"🎧 SoundCloud tracks: {len(sc_files)}")
    else:
        print("🎧 SoundCloud directory not found")
    
    # WordsOnText library
    if MUSIC_DIR.exists():
        wot_files = list(MUSIC_DIR.rglob("*.mp3")) + list(MUSIC_DIR.rglob("*.wav"))
        print(f"🎵 WordsOnText tracks: {len(wot_files)}")
    else:
        print("🎵 WordsOnText library not found")

if __name__ == "__main__":
    # Check current status
    check_current_library()
    
    print("\n" + "="*50)
    print("Starting SoundCloud Downloads")
    print("="*50)
    
    # Download first 5 tracks as test
    success, failed = download_soundcloud_batch(5)
    
    print(f"\n🎯 Test download complete: {success} successful, {failed} failed")
    
    if success > 0:
        print("\n✅ SoundCloud download system is working!")
        print("💡 To download all tracks, run:")
        print("   python -c \"from main_system import MusicSystem; ms = MusicSystem(); ms.setup_soundcloud_music()\"")
    else:
        print("\n⚠️  SoundCloud download needs troubleshooting")
