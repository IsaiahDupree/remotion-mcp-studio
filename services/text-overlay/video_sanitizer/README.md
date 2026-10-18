# Video Sanitizer

A module for detecting and removing sensitive information from videos, such as API keys, credentials, and other confidential data.

## Features

- Automated detection of text in video frames using OCR
- Recognition of sensitive information patterns (API keys, access tokens, credentials, passwords)
- Blurring or redaction of detected sensitive content
- Customizable pattern detection for specific sensitive data formats
- Performance optimization for efficient processing of large video files

## Requirements

- Python 3.7+
- OpenCV
- NumPy
- pytesseract (and Tesseract OCR installed on your system)

## Installation

Ensure Tesseract OCR is installed on your system:

- Windows: Download and install from [Tesseract at UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
- Linux: `sudo apt install tesseract-ocr`
- macOS: `brew install tesseract`

Add the path to Tesseract executable to your system PATH or specify it in your code.

## Usage

### Basic Usage

```python
from video_sanitizer.sanitizer import VideoSanitizer

# Initialize the sanitizer
sanitizer = VideoSanitizer()

# Sanitize a video file
sanitizer.sanitize_video(
    input_path="path/to/video.mp4",
    output_path="path/to/sanitized_video.mp4"
)
```

### Advanced Usage

```python
from video_sanitizer.sanitizer import VideoSanitizer

# Define custom patterns for sensitive information
custom_patterns = {
    "company_id": r"(?i)company[-_]?id[=:]\s*['\"]([\w-]+)['\"]",
    "internal_key": r"(?i)internal[-_]?key[=:]\s*['\"]([\w-]+)['\"]"
}

# Initialize with custom settings
sanitizer = VideoSanitizer(
    custom_patterns=custom_patterns,
    blur_strength=35,
    detection_confidence=0.7
)

# Process only a segment of the video
sanitizer.sanitize_video(
    input_path="path/to/video.mp4",
    output_path="path/to/sanitized_video.mp4",
    start_time=30.5,  # Start at 30.5 seconds
    end_time=120.0,   # End at 120 seconds
    frame_skip=3      # Process every 3rd frame for speed
)

# Add another custom pattern after initialization
sanitizer.add_custom_pattern(
    name="database_url",
    pattern=r"(?i)mongodb://[^\s]+"
)
```

## Integration with WordsOnText

The Video Sanitizer module can be integrated with other WordsOnText components to create a complete workflow:

1. Preprocess videos to remove sensitive information
2. Use the sanitized videos as input for the text overlay functionality
3. Publish the processed videos with added captions/overlays

## Performance Considerations

- Processing speed depends on video resolution and frame rate
- Use the `frame_skip` parameter for faster processing with minimal quality impact
- Consider batch processing for multiple videos

## Extending the Module

To add new sensitive data detection patterns, you can:

1. Add patterns to the `SENSITIVE_PATTERNS` dictionary in the module
2. Pass custom patterns during initialization
3. Use the `add_custom_pattern()` method at runtime
