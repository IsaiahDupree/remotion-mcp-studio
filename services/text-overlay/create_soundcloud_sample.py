#!/usr/bin/env python3
"""
Create a sample SoundCloud tracks Excel file for testing the Flask API
"""

import pandas as pd
import os

# Sample SoundCloud tracks data
sample_tracks = [
    {
        'Title': 'Chill Background Music',
        'Artist': 'LoFi Producer',
        'URL': 'https://soundcloud.com/example/chill-background-music',
        'Duration': '3:45',
        'Genre': 'Lofi',
        'BPM': 85,
        'Mood': 'Relaxed'
    },
    {
        'Title': 'Upbeat Tech Vibes',
        'Artist': 'TechBeats',
        'URL': 'https://soundcloud.com/example/upbeat-tech-vibes',
        'Duration': '4:12',
        'Genre': 'Electronic',
        'BPM': 128,
        'Mood': 'Energetic'
    },
    {
        'Title': 'Acoustic Motivation',
        'Artist': 'Indie Acoustic',
        'URL': 'https://soundcloud.com/example/acoustic-motivation',
        'Duration': '2:58',
        'Genre': 'Acoustic',
        'BPM': 95,
        'Mood': 'Inspiring'
    },
    {
        'Title': 'Corporate Success',
        'Artist': 'Business Sounds',
        'URL': 'https://soundcloud.com/example/corporate-success',
        'Duration': '3:20',
        'Genre': 'Corporate',
        'BPM': 110,
        'Mood': 'Professional'
    },
    {
        'Title': 'Ambient Focus',
        'Artist': 'Ambient Works',
        'URL': 'https://soundcloud.com/example/ambient-focus',
        'Duration': '5:15',
        'Genre': 'Ambient',
        'BPM': 72,
        'Mood': 'Focused'
    }
]

def create_sample_excel():
    """Create sample SoundCloud tracks Excel file"""
    
    # Create DataFrame
    df = pd.DataFrame(sample_tracks)
    
    # Save to Excel
    output_path = 'soundcloud_tracks.xlsx'
    df.to_excel(output_path, index=False, sheet_name='SoundCloud_Tracks')
    
    print(f"Created sample SoundCloud tracks file: {output_path}")
    print(f"Contains {len(sample_tracks)} sample tracks")
    
    # Display the data
    print("\nSample tracks:")
    print(df.to_string(index=False))
    
    return output_path

if __name__ == '__main__':
    create_sample_excel()
