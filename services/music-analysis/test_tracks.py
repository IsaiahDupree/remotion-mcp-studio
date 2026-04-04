#!/usr/bin/env python3
"""
Test SoundCloud track loading
"""
from soundcloud_downloader import SoundCloudDownloader

def test_track_loading():
    """Test loading tracks from Excel"""
    print("🎧 Testing SoundCloud track loading...")
    
    try:
        sc = SoundCloudDownloader()
        tracks = sc.load_soundcloud_data()
        
        print(f"✅ Found {len(tracks)} valid tracks")
        
        if tracks:
            print("\n🎵 First 5 tracks:")
            for i, track in enumerate(tracks[:5]):
                title = track.get('title', 'Unknown')
                artist = track.get('artist', 'Unknown')
                genre = track.get('genre', 'Unknown')
                url = track.get('url', '')[:50] + '...' if len(track.get('url', '')) > 50 else track.get('url', '')
                print(f"  {i+1}. {title} by {artist} [{genre}]")
                print(f"     URL: {url}")
        
        return tracks
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    tracks = test_track_loading()
    print(f"\n📊 Total tracks ready for download: {len(tracks)}")
