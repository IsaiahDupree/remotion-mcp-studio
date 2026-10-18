#!/usr/bin/env python3
"""
Local Music Selector
===================
Enhanced music selection system that uses locally downloaded tracks
"""

import json
import os
import random
from pathlib import Path
from typing import Dict, List, Optional

class LocalMusicSelector:
    """Select music from locally downloaded tracks"""
    
    def __init__(self, music_library_path: str = "music_library"):
        """Initialize with path to music library"""
        self.music_library = Path(music_library_path)
        self.music_index = self._load_music_index()
        
    def _load_music_index(self) -> List[Dict]:
        """Load the music index"""
        
        index_file = self.music_library / "music_index.json"
        
        if not index_file.exists():
            print(f"⚠️ Music index not found: {index_file}")
            return []
        
        try:
            with open(index_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading music index: {e}")
            return []
    
    def get_available_tracks(self) -> List[Dict]:
        """Get all available tracks"""
        return self.music_index
    
    def get_tracks_by_genre(self, genre: str) -> List[Dict]:
        """Get tracks by genre"""
        return [track for track in self.music_index if track['genre'].lower() == genre.lower()]
    
    def get_tracks_by_mood(self, mood: str) -> List[Dict]:
        """Get tracks by mood (if available in filename)"""
        mood_lower = mood.lower()
        return [track for track in self.music_index 
                if mood_lower in track['name'].lower()]
    
    def get_random_track(self, genre: Optional[str] = None) -> Optional[str]:
        """Get a random track, optionally filtered by genre"""
        
        if not self.music_index:
            print("❌ No music tracks available")
            return None
        
        if genre:
            tracks = self.get_tracks_by_genre(genre)
            if not tracks:
                print(f"⚠️ No tracks found for genre: {genre}")
                tracks = self.music_index
        else:
            tracks = self.music_index
        
        if tracks:
            selected = random.choice(tracks)
            print(f"🎵 Selected: {selected['name']} ({selected['genre']})")
            return selected['file']
        
        return None
    
    def get_track_by_criteria(self, criteria: Dict) -> Optional[str]:
        """Get track by specific criteria"""
        
        if not self.music_index:
            return None
        
        # Filter by criteria
        filtered_tracks = self.music_index
        
        if 'genre' in criteria:
            filtered_tracks = [t for t in filtered_tracks 
                             if t['genre'].lower() == criteria['genre'].lower()]
        
        if 'mood' in criteria:
            mood_lower = criteria['mood'].lower()
            filtered_tracks = [t for t in filtered_tracks 
                             if mood_lower in t['name'].lower()]
        
        if 'name_contains' in criteria:
            name_filter = criteria['name_contains'].lower()
            filtered_tracks = [t for t in filtered_tracks 
                             if name_filter in t['name'].lower()]
        
        if filtered_tracks:
            selected = random.choice(filtered_tracks)
            print(f"🎵 Selected by criteria: {selected['name']} ({selected['genre']})")
            return selected['file']
        
        print(f"⚠️ No tracks found matching criteria: {criteria}")
        return self.get_random_track()
    
    def get_stats(self) -> Dict:
        """Get music library statistics"""
        
        if not self.music_index:
            return {'total': 0, 'genres': [], 'total_size_mb': 0}
        
        genres = list(set(track['genre'] for track in self.music_index))
        total_size = sum(track['size_mb'] for track in self.music_index)
        
        genre_counts = {}
        for genre in genres:
            genre_counts[genre] = len(self.get_tracks_by_genre(genre))
        
        return {
            'total': len(self.music_index),
            'genres': genres,
            'genre_counts': genre_counts,
            'total_size_mb': round(total_size, 2)
        }
    
    def list_all_tracks(self):
        """Print all available tracks"""
        
        if not self.music_index:
            print("❌ No music tracks available")
            return
        
        print(f"🎵 Available Music Tracks ({len(self.music_index)} total)")
        print("=" * 60)
        
        # Group by genre
        genres = list(set(track['genre'] for track in self.music_index))
        
        for genre in sorted(genres):
            genre_tracks = self.get_tracks_by_genre(genre)
            print(f"\n🎼 {genre.upper()} ({len(genre_tracks)} tracks):")
            
            for track in genre_tracks:
                print(f"   🎵 {track['name']}")
                print(f"      📁 {track['file']}")
                print(f"      📊 {track['size_mb']:.1f} MB")


def test_local_music_selector():
    """Test the local music selector"""
    
    print("🧪 Testing Local Music Selector")
    print("=" * 50)
    
    selector = LocalMusicSelector()
    
    # Get stats
    stats = selector.get_stats()
    print(f"📊 Music Library Stats:")
    print(f"   Total tracks: {stats['total']}")
    print(f"   Genres: {stats['genres']}")
    print(f"   Total size: {stats['total_size_mb']} MB")
    
    if stats['total'] > 0:
        # Test random selection
        print(f"\n🎲 Random track selection:")
        random_track = selector.get_random_track()
        if random_track:
            print(f"   Selected: {random_track}")
        
        # Test genre selection
        if stats['genres']:
            test_genre = stats['genres'][0]
            print(f"\n🎼 Genre selection ('{test_genre}'):")
            genre_track = selector.get_random_track(genre=test_genre)
            if genre_track:
                print(f"   Selected: {genre_track}")
        
        # Test criteria selection
        print(f"\n🔍 Criteria selection:")
        criteria_track = selector.get_track_by_criteria({'genre': 'lofi'})
        if criteria_track:
            print(f"   Selected: {criteria_track}")
        
        # List all tracks
        print(f"\n📋 All available tracks:")
        selector.list_all_tracks()
    
    else:
        print("⚠️ No music tracks found. Run bulk_download_music.py first.")


if __name__ == "__main__":
    test_local_music_selector()
