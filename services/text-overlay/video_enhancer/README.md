# Video Enhancer Module

A modular system for enhancing videos with text overlays and background music from SoundCloud or local sources.

## Overview

The Video Enhancer module provides a comprehensive solution for improving video engagement by adding:

1. **Text Overlays**: Add catchy text captions to videos using AI-powered analysis or custom text
2. **Background Music**: Add background music from SoundCloud tracks or local audio files with speech emphasis

The module is designed with a focus on:
- **Modularity**: Separate components that can be used independently or together
- **Reusability**: Common functionality extracted into reusable components
- **Performance**: Optimized for handling both single videos and batch processing
- **Robustness**: Error handling and fallbacks for all critical operations

## Architecture

The module consists of three main components:

1. **TextOverlayEnhancer**: Handles generating and adding text overlays to videos
2. **MusicEnhancer**: Manages downloading SoundCloud tracks and adding background music
3. **VideoEnhancer**: Orchestrates the complete enhancement process

```
video_enhancer/
├── __init__.py         # Package initialization and exports
├── enhancer.py         # Main VideoEnhancer orchestration class
├── text_overlay.py     # Text overlay functionality
└── music_enhancer.py   # Music enhancement and SoundCloud integration
```

## Features

- **Text Overlay Generation**
  - AI-powered text generation using OpenAI API (when available)
  - Fallback to heuristic methods when API is unavailable
  - Customizable text style, position, and size
  - Black background with white text for optimal readability

- **Background Music Integration**
  - Reliable SoundCloud track downloads using yt-dlp
  - Auto-detection of existing background music
  - Speech emphasis to maintain clarity of original audio
  - Volume optimization based on speech presence
  - Support for local music files

- **Processing Capabilities**
  - Single video enhancement
  - Batch processing of multiple videos
  - Excel-based processing for custom enhancement options
  - High-quality video preservation

## Dependencies

- **Python Packages**:
  - OpenCV: For video processing and text rendering
  - pandas: For Excel file processing
  - yt-dlp: For SoundCloud track downloads
  - ffmpeg-python: For audio processing (optional, ffmpeg command line used as fallback)

- **External Tools**:
  - ffmpeg: Required for audio extraction and processing
  - ffprobe: Used for audio analysis

## Usage Examples

### Basic Enhancement

```python
from video_enhancer import VideoEnhancer

# Initialize the enhancer
enhancer = VideoEnhancer(
    output_dir="./enhanced_videos",
    speech_emphasis=1.5
)

# Enhance a video with text overlay and background music
result = enhancer.enhance_video(
    video_path="path/to/video.mp4",
    add_text=True,
    add_music=True,
    soundcloud_url="https://soundcloud.com/artist/track"
)

if result["success"]:
    print(f"Video enhanced successfully: {result['output_video']}")
```

### Text-Only Enhancement

```python
from video_enhancer import TextOverlayEnhancer
from video_context_analyzer.styling import Style, Position

# Initialize text enhancer
text_enhancer = TextOverlayEnhancer(
    style=Style.BLACK_BG_WHITE_TEXT,
    position=Position.TOP,
    font_scale=1.2
)

# Add text overlay to video
result = text_enhancer.enhance_video(
    video_path="path/to/video.mp4",
    output_path="path/to/output.mp4",
    custom_text="Watch this amazing content!"
)
```

### Music-Only Enhancement

```python
from video_enhancer import MusicEnhancer

# Initialize music enhancer
music_enhancer = MusicEnhancer(
    output_dir="./enhanced_videos",
    speech_emphasis=1.8
)

# Add background music to video
result = music_enhancer.enhance_video_with_music(
    video_path="path/to/video.mp4",
    output_path="path/to/output.mp4",
    soundcloud_url="https://soundcloud.com/artist/track"
)
```

### Batch Processing

```python
from video_enhancer import VideoEnhancer
import os

# Initialize enhancer
enhancer = VideoEnhancer()

# Find all videos in directory
video_paths = [os.path.join("videos", f) for f in os.listdir("videos") 
               if f.endswith(('.mp4', '.mov', '.avi'))]

# Enhance all videos
results = enhancer.batch_enhance_videos(
    video_paths=video_paths,
    add_text=True,
    add_music=True,
    soundcloud_url="https://soundcloud.com/artist/track"
)

print(f"Enhanced {results['successful_videos']} of {results['total_videos']} videos")
```

## Command Line Interface

The module comes with a command-line example script at `examples/enhance_video_example.py` that demonstrates different usage patterns:

```bash
# Enhance a single video
python examples/enhance_video_example.py single --video path/to/video.mp4 --add-text --add-music --soundcloud-url "https://soundcloud.com/artist/track"

# Batch process videos in a directory
python examples/enhance_video_example.py batch --input-dir path/to/videos --add-text --add-music

# Process videos listed in an Excel file
python examples/enhance_video_example.py excel --excel-file video_list.xlsx --video-column "VideoPath" --soundcloud-column "MusicURL" --text-column "CustomText"
```

## Best Practices

1. **Set OpenAI API Key** for better text generation:
   ```
   export OPENAI_API_KEY=your-api-key
   ```

2. **Pre-download music files** for batch processing to avoid repeated downloads

3. **Use SoundCloud yt-dlp downloader** for reliable track downloads

4. **Adjust speech emphasis** based on the importance of the original audio:
   - Higher values (e.g., 2.0) for important speech content 
   - Lower values (e.g., 0.8) to emphasize music over speech

5. **Auto-detect existing features** to avoid redundant processing

## Advanced Usage

### Custom Text Styling

You can customize text styling by modifying the `Style` and `Position` enums or creating your own style handlers in the text styler.

### Custom Music Analysis

For advanced audio analysis, you can extend the music enhancer with custom detection algorithms for different types of audio content.

### Performance Optimization

For batch processing large numbers of videos, consider:
1. Pre-downloading all required music files
2. Enabling parallel processing (requires custom implementation)
3. Setting appropriate quality settings based on output requirements
