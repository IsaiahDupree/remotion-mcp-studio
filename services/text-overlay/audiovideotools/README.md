# AudioVideoTools Package

A modular Python package for audio/video processing, background music addition, and content discovery.

## Features

- **Audio Analysis**: Detect background music in videos and calculate optimal volume levels
- **Video Processing**: Add background music with optimized volume for speech clarity
- **SoundCloud Integration**: Download tracks from Excel files of SoundCloud URLs
- **YouTube Engagement Finder**: Search for high-engagement videos with low subscriber counts
- **Batch Processing**: Process multiple videos with a single command
- **Configurable Options**: Extensive CLI options for all tools

## Package Structure

```
audiovideotools/
├── __init__.py                  # Package initialization
├── audio_analysis/              # Audio analysis modules
│   ├── __init__.py
│   └── audio_analyzer.py        # Background music detection & volume analysis
├── video_processing/            # Video processing modules
│   ├── __init__.py
│   └── music_mixer.py           # Music addition with volume optimization
├── downloaders/                 # Content downloaders
│   ├── __init__.py
│   ├── soundcloud.py            # SoundCloud track downloader
│   └── youtube_engagement.py    # YouTube engagement finder
├── utils/                       # Utility functions
│   ├── __init__.py
│   └── file_utils.py            # File operations helpers
└── batch_processor.py           # Batch processing module
```

## Installation

1. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. For YouTube functionality, obtain a YouTube Data API v3 key:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the YouTube Data API v3
   - Create API credentials
   - Save your API key for later use

## Usage

### Add Background Music to Videos

Process videos with auto-optimized background music from SoundCloud:

```bash
python main.py add-music --excel-file "SoundCloud_Tracks.xlsx" --video-dir "./videos" --speech-emphasis 0.5
```

#### Key Options:

- `--video-dir`: Directory containing videos to process
- `--music-dir`: Directory containing music files (default: ./downloaded_songs)
- `--excel-file`: Excel file with SoundCloud track URLs
- `--output-dir`: Directory for processed videos (default: ./output_videos)
- `--target-ratio`: Target ratio of music to original audio volume (default: 0.15)
- `--speech-emphasis`: Factor to prioritize speech clarity (default: 0.7)
- `--force-add-music`: Force adding music even if video already has it
- `--disable-music-check`: Disable background music detection
- `--specific-video`: Process only a specific video
- `--limit`: Maximum number of videos to process

### Find High-Engagement YouTube Videos

Search for videos with high engagement metrics but low subscriber counts:

```bash
python main.py youtube-find --keyword "your search term" --api-key "YOUR_API_KEY"
```

#### Key Options:

- `--keyword`: Search query (required)
- `--api-key`: YouTube Data API key (required)
- `--output-dir`: Directory to save videos (default: ./youtube_videos)
- `--spreadsheet`: Path to save data (default: ./youtube_engagement_data.xlsx)
- `--min-views`: Minimum view count (default: 5000)
- `--min-comments`: Minimum comment count (default: 10)
- `--min-likes`: Minimum like count (default: 100)
- `--max-subscribers`: Maximum subscriber count (default: 100000)
- `--min-engagement-ratio`: Minimum views/subscribers ratio (default: 0.05)
- `--max-search-results`: Maximum videos to analyze (default: 100)
- `--download-limit`: Maximum videos to download
- `--search-only`: Only search, don't download videos

### Download SoundCloud Tracks

Download tracks from SoundCloud using an Excel file:

```bash
python main.py download --excel-file "SoundCloud_Tracks.xlsx"
```

#### Key Options:

- `--excel-file`: Excel file with SoundCloud track URLs (required)
- `--url-column`: Column name with URLs (default: "Track URL")
- `--output-dir`: Directory to save tracks (default: ./downloaded_songs)
- `--limit`: Maximum number of tracks to download

## Advanced Usage

### Background Music Detection

The package includes sophisticated audio analysis to detect if videos already have background music:

- Spectral flatness analysis
- Low frequency content ratio
- Volume variation measurement
- Spectral centroid calculation
- Sustained volume ratio

### Audio Volume Optimization

Automatically calculates optimal background music volume based on:

- Original audio RMS levels
- Speech emphasis factor
- Target volume ratio

This ensures that speech remains clear while background music enhances the video.
