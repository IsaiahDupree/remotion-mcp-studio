#!/usr/bin/env python3
"""
Create Music Index
==================
Create index of downloaded music files
"""

import json
from pathlib import Path

def create_music_index():
    """Create music index"""
    
    music_dir = Path('music_library')
    music_files = []
    
    print("🎵 Creating Music Index")
    print("=" * 40)
    
    if not music_dir.exists():
        print("❌ Music library not found")
        return False
    
    # Find all music files
    for genre_dir in music_dir.iterdir():
        if genre_dir.is_dir():
            print(f"📁 Checking {genre_dir.name}/")
            
            # Look for various audio formats
            for ext in ['*.mp3', '*.aac', '*.m4a', '*.wav']:
                for music_file in genre_dir.glob(ext):
                    size_mb = round(music_file.stat().st_size / (1024 * 1024), 2)
                    music_files.append({
                        'file': str(music_file),
                        'name': music_file.stem,
                        'genre': genre_dir.name,
                        'size_mb': size_mb
                    })
                    print(f"   🎵 {music_file.name} ({size_mb} MB)")
    
    # Save index
    index_file = music_dir / 'music_index.json'
    with open(index_file, 'w') as f:
        json.dump(music_files, f, indent=2)
    
    print(f"\n✅ Created music index: {len(music_files)} tracks")
    print(f"📁 Saved to: {index_file}")
    
    # Show summary
    if music_files:
        total_size = sum(track['size_mb'] for track in music_files)
        genres = list(set(track['genre'] for track in music_files))
        
        print(f"\n📊 Summary:")
        print(f"   Total tracks: {len(music_files)}")
        print(f"   Total size: {total_size:.1f} MB")
        print(f"   Genres: {genres}")
        
        print(f"\n🎵 Track List:")
        for track in music_files:
            print(f"   - {track['name']} ({track['genre']}, {track['size_mb']} MB)")
    
    return len(music_files) > 0

if __name__ == "__main__":
    create_music_index()
