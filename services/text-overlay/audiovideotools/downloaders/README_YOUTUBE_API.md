# YouTube Engagement Finder API Documentation

## Overview

The YouTube Engagement Finder is a modular component that helps discover YouTube videos with high engagement metrics (views, likes, comments) but relatively low subscriber counts. This indicates content that performs exceptionally well relative to the channel's size.

## Features

- Search for videos using keywords
- Filter by engagement metrics (views, likes, comments)
- Calculate and filter by engagement ratio (views/subscribers)
- Download high-engagement videos (optional)
- Track all metrics in a spreadsheet
- Exportable results for integration with other systems

## API Reference

### `YouTubeEngagementFinder` Class

```python
from audiovideotools.downloaders.youtube_engagement import YouTubeEngagementFinder

# Initialize
finder = YouTubeEngagementFinder(
    api_key="YOUR_YOUTUBE_API_KEY",
    output_dir="./path/to/save/videos",
    spreadsheet_path="./path/to/save/data.xlsx",
    min_views=5000,
    min_comments=10,
    min_likes=100,
    max_subscribers=100000,
    min_engagement_ratio=0.05
)
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | str | None | YouTube Data API key (required) |
| `output_dir` | str | "./youtube_videos" | Directory to save downloaded videos |
| `spreadsheet_path` | str | "./youtube_engagement_data.xlsx" | Path to save data spreadsheet |
| `min_views` | int | 5000 | Minimum views for a video |
| `min_comments` | int | 10 | Minimum comments for a video |
| `min_likes` | int | 100 | Minimum likes for a video |
| `max_subscribers` | int | 100000 | Maximum channel subscribers |
| `min_engagement_ratio` | float | 0.05 | Minimum views/subscribers ratio |

#### Methods

##### `search_and_analyze(keyword, max_results=50) -> List[Dict]`

Search for videos matching a keyword and analyze their engagement metrics.

```python
# Search and analyze without downloading
high_engagement_videos = finder.search_and_analyze("cooking recipes", max_results=100)
```

**Parameters:**
- `keyword` (str): Search term
- `max_results` (int, optional): Maximum search results to analyze. Default: 50.

**Returns:**
- List of dictionaries containing video data for high engagement videos

##### `download_videos(video_list, limit=None) -> List[str]`

Download videos from a list of video data dictionaries.

```python
# Download the top 5 high-engagement videos
downloaded_paths = finder.download_videos(high_engagement_videos, limit=5)
```

**Parameters:**
- `video_list` (List[Dict]): List of video data dictionaries
- `limit` (int, optional): Maximum videos to download. Default: None (download all).

**Returns:**
- List of paths to downloaded video files

##### `save_to_spreadsheet() -> None`

Save tracked videos to the spreadsheet.

```python
# Save data to spreadsheet
finder.save_to_spreadsheet()
```

##### `export_data(format='json') -> Dict`

Export tracked videos in the specified format.

```python
# Export data as JSON
data = finder.export_data(format='json')
```

**Parameters:**
- `format` (str, optional): Export format ('json', 'dict', 'df'). Default: 'json'.

**Returns:**
- Data in requested format

## Usage Examples

### Basic Search and Download

```python
from audiovideotools.downloaders.youtube_engagement import YouTubeEngagementFinder

# Initialize with API key
finder = YouTubeEngagementFinder(api_key="YOUR_API_KEY")

# Search for videos
videos = finder.search_and_analyze("cooking tutorials", max_results=50)
print(f"Found {len(videos)} high-engagement videos")

# Download videos (optional)
downloaded = finder.download_videos(videos, limit=5)
print(f"Downloaded {len(downloaded)} videos")
```

### Integration with Custom Application

```python
from audiovideotools.downloaders.youtube_engagement import YouTubeEngagementFinder

class MyApplication:
    def __init__(self):
        self.youtube_finder = YouTubeEngagementFinder(
            api_key="YOUR_API_KEY",
            min_views=10000,
            min_engagement_ratio=0.1
        )
    
    def discover_trending_content(self, keywords):
        all_videos = []
        for keyword in keywords:
            videos = self.youtube_finder.search_and_analyze(keyword)
            all_videos.extend(videos)
        
        # Sort by engagement ratio
        all_videos.sort(key=lambda x: x["engagement_ratio"], reverse=True)
        return all_videos[:10]  # Return top 10
```

### Data Processing Pipeline

```python
from audiovideotools.downloaders.youtube_engagement import YouTubeEngagementFinder
import pandas as pd

# Initialize finder
finder = YouTubeEngagementFinder(api_key="YOUR_API_KEY")

# Search for videos
videos = finder.search_and_analyze("python tutorial")

# Export as pandas DataFrame
df = finder.export_data(format='df')

# Perform custom analysis
df['views_to_likes_ratio'] = df['views'] / df['likes']
most_engaging = df[df['views_to_likes_ratio'] < 20]  # Videos with high like ratio
```

## Adjusting Parameters for Different Use Cases

### Finding Viral Content

```python
finder = YouTubeEngagementFinder(
    api_key="YOUR_API_KEY",
    min_views=100000,          # High view threshold
    min_engagement_ratio=1.0,  # At least as many views as subscribers
    max_subscribers=500000     # Allow medium-sized channels
)
```

### Finding Hidden Gems

```python
finder = YouTubeEngagementFinder(
    api_key="YOUR_API_KEY",
    min_views=5000,            # Modest view count
    max_subscribers=10000,     # Very small channels only
    min_engagement_ratio=0.5   # Good engagement relative to size
)
```

## API Key Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Create credentials (API key)
5. Use this key in your application

## Common Issues and Solutions

### Rate Limiting

The YouTube API has daily quota limits. If you encounter rate limiting:

```python
# Use more conservative parameters
finder = YouTubeEngagementFinder(
    api_key="YOUR_API_KEY",
    max_results=10  # Request fewer results per search
)

# Implement rate limiting in your application
import time
keywords = ["keyword1", "keyword2", "keyword3"]
for keyword in keywords:
    videos = finder.search_and_analyze(keyword)
    time.sleep(10)  # Wait between API calls
```

### Improving Result Quality

If you're not finding the expected results:

```python
# Use more specific keywords
videos = finder.search_and_analyze("beginner python projects github")

# Adjust engagement thresholds based on the content niche
finder = YouTubeEngagementFinder(
    api_key="YOUR_API_KEY",
    min_views=1000,            # Lower for niche topics
    min_engagement_ratio=0.01  # Lower for competitive categories
)
```
