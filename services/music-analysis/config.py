"""
Configuration settings for the Enhanced Music Analysis System
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
SHARED_DIR = BASE_DIR / "shared"
VIDEOS_DIR = SHARED_DIR / "videos"
MUSIC_DIR = BASE_DIR / "music_library"
SOUNDCLOUD_DIR = BASE_DIR / "soundcloud_music"
CACHE_DIR = BASE_DIR / "cache"
ANALYSIS_DIR = BASE_DIR / "analysis"

# Paths configuration
PATHS = {
    'base': BASE_DIR,
    'videos': VIDEOS_DIR,
    'wordsontext_music': MUSIC_DIR,
    'soundcloud_music': SOUNDCLOUD_DIR,
    'cache': CACHE_DIR,
    'analysis': ANALYSIS_DIR
}

# Database settings
DATABASE_CONFIG = {
    'music_index': CACHE_DIR / "music_index.json",
    'video_cache': CACHE_DIR / "video_context_cache.json",
    'music_cache': CACHE_DIR / "music_context_cache.json",
    'soundcloud_cache': CACHE_DIR / "soundcloud_cache.json",
    'trend_cache': CACHE_DIR / "trend_cache.json"
}

# API settings
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 5001,
    'debug': True
}

# Music analysis settings
MUSIC_ANALYSIS_CONFIG = {
    'supported_formats': ['.mp3', '.wav', '.flac', '.m4a', '.aac'],
    'analysis_features': [
        'tempo', 'key', 'energy', 'valence', 'danceability', 
        'acousticness', 'instrumentalness', 'speechiness'
    ],
    'mood_mapping': {
        'happy': ['upbeat', 'energetic', 'cheerful', 'positive'],
        'sad': ['melancholic', 'emotional', 'slow', 'minor'],
        'energetic': ['fast', 'electronic', 'dance', 'workout'],
        'calm': ['ambient', 'relaxing', 'peaceful', 'meditative'],
        'dramatic': ['cinematic', 'intense', 'orchestral', 'epic']
    }
}

# Video analysis settings
VIDEO_ANALYSIS_CONFIG = {
    'supported_formats': ['.mp4', '.mov', '.avi', '.mkv'],
    'frame_extraction': {
        'interval': 30,  # seconds
        'max_frames': 10
    },
    'transcript_analysis': {
        'sentiment_threshold': 0.5,
        'energy_keywords': ['energetic', 'fast', 'exciting', 'action'],
        'calm_keywords': ['peaceful', 'slow', 'relaxing', 'quiet']
    }
}

# SoundCloud settings
SOUNDCLOUD_CONFIG = {
    'excel_file': BASE_DIR / "WordsOnText" / "SoundCloud to X Reposter.xlsx",
    'download_dir': SOUNDCLOUD_DIR,
    'batch_size': 10,
    'retry_attempts': 3,
    'quality': 'high'  # high, medium, low
}

# Trend analysis settings
TREND_CONFIG = {
    'sources': ['spotify', 'youtube', 'soundcloud'],
    'update_interval': 24 * 60 * 60,  # 24 hours in seconds
    'trend_weight': 0.3,  # influence on music selection
    'genres_trending': []  # populated dynamically
}

# Ensure directories exist
for dir_path in [CACHE_DIR, ANALYSIS_DIR, SOUNDCLOUD_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)
