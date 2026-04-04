# Modular Music Analysis and Video Integration System

A comprehensive, modular system for intelligent music selection and video processing that integrates with n8n workflows. The system downloads SoundCloud tracks, performs bulk music analysis, and provides intelligent music recommendations based on video content analysis and current music trends.

## 🎯 Key Features

- **Modular Architecture**: Separate modules for music analysis, video analysis, SoundCloud downloads, and trend tracking
- **Intelligent Music Matching**: AI-powered music selection based on video mood, energy, and visual characteristics
- **Bulk Processing**: Analyze entire music libraries and video collections efficiently
- **Trend Integration**: Incorporate current music trends to improve recommendations
- **Cache System**: Persistent caching for fast repeated operations
- **n8n Integration**: Ready-to-use API endpoints for workflow integration

## 📁 System Architecture

```
music_system/
├── config.py                 # Central configuration management
├── music_analyzer.py          # Audio analysis and feature extraction
├── soundcloud_downloader.py   # SoundCloud track downloading
├── video_analyzer.py          # Video content analysis
├── trend_analyzer.py          # Music trend analysis
├── main_system.py            # System orchestrator
├── requirements.txt          # Python dependencies
└── README.md                # This file

cache/                        # Generated cache files
├── music_index.json         # Master music library index
├── music_context_cache.json # Music analysis cache
├── video_context_cache.json # Video analysis cache
├── soundcloud_cache.json    # SoundCloud download tracking
└── trend_cache.json         # Music trend data

soundcloud_music/            # Downloaded SoundCloud tracks
analysis/                    # Analysis results and reports
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd music_system
pip install -r requirements.txt
```

### 2. Install System Requirements

- **FFmpeg**: Required for video analysis
- **yt-dlp**: For SoundCloud downloading (installed via pip)

### 3. Configure Paths

Edit `config.py` to set your specific paths:

```python
PATHS = {
    'videos': Path('/home/node/shared/videos'),
    'wordsontext_music': Path('/srv/music_library'),
    'soundcloud_music': Path('soundcloud_music'),
    # ... other paths
}
```

### 4. Prepare SoundCloud Data

Place your Excel file with SoundCloud URLs at:
`WordsOnText/SoundCloud to X Reposter.xlsx`

Excel should contain columns like:
- `url` or `soundcloud_url` - SoundCloud track URLs
- `title` or `track_title` - Track names
- `artist` or `creator` - Artist names

### 5. Run System Setup

```python
from main_system import MusicSystem

# Initialize system
system = MusicSystem()

# Download and analyze SoundCloud tracks
soundcloud_result = system.setup_soundcloud_music()
print(f"SoundCloud setup: {soundcloud_result}")

# Analyze existing music libraries
analysis_result = system.analyze_existing_music_libraries()
print(f"Music analysis: {analysis_result}")

# Update trend data
system.update_trends()
```

## 🎵 Usage Examples

### Analyze Single Video

```python
result = system.find_music_for_video(
    video_path="/path/to/video.mp4",
    transcript="Children playing energetically in the backyard",
    visual_analysis="Bright outdoor scene with fast movements"
)

print(f"Best match: {result['best_match']['file_name']}")
print(f"Compatibility: {result['best_match']['compatibility_score']:.2f}")
```

### Bulk Video Processing

```python
from pathlib import Path

video_results = system.bulk_process_videos(Path('/home/node/shared/videos'))
system.export_music_recommendations(video_results, Path('recommendations.json'))
```

### Get System Status

```python
status = system.get_system_status()
print(f"Total tracks available: {status['total_tracks']}")
print(f"WordsOnText tracks: {status['music_libraries']['wordsOnText']['tracks']}")
print(f"SoundCloud tracks: {status['music_libraries']['soundcloud']['tracks']}")
```

## 🔧 Module Details

### MusicAnalyzer
- **Audio Feature Extraction**: Tempo, spectral features, MFCCs, energy
- **Mood Classification**: Happy, sad, energetic, calm, neutral
- **Genre Detection**: Electronic, ambient, pop, dance, etc.
- **Compatibility Scoring**: Match music to video characteristics

### VideoAnalyzer
- **Visual Analysis**: Brightness, contrast, color distribution, motion
- **Transcript Analysis**: Keyword detection, sentiment analysis
- **Mood Detection**: Combine visual and audio cues
- **Energy Calculation**: Overall activity and intensity levels

### SoundCloudDownloader
- **Excel Integration**: Parse track data from spreadsheets
- **Batch Downloads**: Efficient bulk downloading with retry logic
- **Metadata Management**: Extract and preserve track information
- **Progress Tracking**: Cache successful/failed downloads

### TrendAnalyzer
- **Multi-Platform Trends**: Spotify, YouTube, SoundCloud data
- **Trend Boosting**: Enhance recommendations with current trends
- **Periodic Updates**: Configurable trend refresh intervals
- **Genre Weighting**: Popularity-weighted genre recommendations

## 🔗 n8n Integration

The system is designed to integrate with your existing n8n video processing workflow:

1. **Video Processing**: Use existing video analysis from n8n
2. **API Calls**: Call `find_music_for_video()` with video data
3. **Music Selection**: Receive intelligent music recommendations
4. **Video Generation**: Use recommended tracks in final video

### Example n8n HTTP Request Node

```json
{
  "method": "POST",
  "url": "http://host.docker.internal:5001/analyze-music-match",
  "body": {
    "video_path": "/home/node/shared/videos/video.mp4",
    "transcript": "{{ $json.transcript }}",
    "visual_analysis": "{{ $json.visual_analysis }}"
  }
}
```

## 📊 Performance Features

- **Caching System**: Avoid re-analyzing files
- **Batch Processing**: Efficient bulk operations
- **Incremental Updates**: Only process new/changed files
- **Memory Management**: Optimized for large music libraries

## 🎛️ Configuration Options

### Music Analysis Settings
```python
MUSIC_ANALYSIS_CONFIG = {
    'supported_formats': ['.mp3', '.wav', '.m4a', '.flac'],
    'features': ['tempo', 'mfcc', 'spectral', 'chroma'],
    'mood_mapping': {
        'happy': ['pop', 'upbeat'],
        'energetic': ['electronic', 'dance'],
        'calm': ['ambient', 'lofi']
    }
}
```

### SoundCloud Settings
```python
SOUNDCLOUD_CONFIG = {
    'batch_size': 10,
    'retry_attempts': 3,
    'quality': '192K',
    'download_dir': Path('soundcloud_music')
}
```

### Trend Analysis Settings
```python
TREND_CONFIG = {
    'sources': ['spotify', 'youtube', 'soundcloud'],
    'update_interval': 86400,  # 24 hours
    'trend_weight': 0.2
}
```

## 🚨 Troubleshooting

### Common Issues

1. **FFmpeg Not Found**
   - Install FFmpeg and ensure it's in your PATH
   - Check with: `ffmpeg -version`

2. **SoundCloud Downloads Failing**
   - Update yt-dlp: `pip install --upgrade yt-dlp`
   - Check SoundCloud URLs are valid and public

3. **Memory Issues with Large Libraries**
   - Process in smaller batches
   - Increase `batch_size` in config
   - Clear cache files if corrupted

4. **Slow Analysis Performance**
   - Enable multiprocessing in config
   - Use SSD storage for cache files
   - Pre-analyze music libraries during setup

### Log Files

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 Updates and Maintenance

### Refresh Music Analysis
```python
# Re-analyze all music (if new tracks added)
system.analyze_existing_music_libraries()
```

### Update Trend Data
```python
# Force trend update
system.update_trends()
```

### Clean Cache
```python
# Clear and rebuild caches
from pathlib import Path
import shutil

cache_dir = Path('cache')
if cache_dir.exists():
    shutil.rmtree(cache_dir)
    
# Re-initialize system
system = MusicSystem()
```

## 🎯 Next Steps

1. **Test Integration**: Import main workflow into n8n
2. **API Development**: Create Flask API endpoints for n8n calls
3. **Performance Tuning**: Optimize for your specific use case
4. **Expand Sources**: Add more trend data sources
5. **Custom Models**: Train custom mood/genre classifiers

## 📈 Monitoring

Track system performance:
- Music library size and analysis completeness
- Trend data freshness
- Cache hit rates
- Recommendation accuracy

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review log files for errors
3. Verify configuration settings
4. Test with smaller datasets first

---

**Ready to revolutionize your music selection workflow!** 🎵✨
