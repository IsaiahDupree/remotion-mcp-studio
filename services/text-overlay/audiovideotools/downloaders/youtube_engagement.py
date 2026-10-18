"""
YouTube Engagement Finder

This module helps find YouTube videos with high engagement metrics
but relatively low subscriber counts. It can be used as a standalone tool
or integrated into other software stacks.
"""

import os
import sys
import logging
import time
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path

import pandas as pd
import googleapiclient.discovery

log = logging.getLogger("youtube_engagement_finder")

class YouTubeEngagementFinder:
    """Class to find and download YouTube videos with high engagement but low subscriber count.
    
    This class provides a modular API for discovering, analyzing, and downloading YouTube videos 
    with high engagement metrics (views, likes, comments) relative to subscriber count.
    
    Attributes:
        api_key: YouTube Data API key
        output_dir: Directory to save downloaded videos
        spreadsheet_path: Path to save/update engagement data spreadsheet
        min_views: Minimum number of views for a video to be considered
        min_comments: Minimum number of comments
        min_likes: Minimum number of likes
        max_subscribers: Maximum number of subscribers for channel
        min_engagement_ratio: Minimum ratio of views to subscribers
        data: Pandas DataFrame containing tracked video data
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        output_dir: str = "./youtube_videos",
        spreadsheet_path: str = "./youtube_engagement_data.xlsx",
        min_views: int = 5000,
        min_comments: int = 10,
        min_likes: int = 100,
        max_subscribers: int = 100000,
        min_engagement_ratio: float = 0.05  # views/subscribers ratio
    ):
        """
        Initialize the YouTube Engagement Finder.
        
        Args:
            api_key: YouTube Data API key
            output_dir: Directory to save downloaded videos
            spreadsheet_path: Path to save/update engagement data spreadsheet
            min_views: Minimum number of views for a video to be considered
            min_comments: Minimum number of comments
            min_likes: Minimum number of likes
            max_subscribers: Maximum number of subscribers for channel
            min_engagement_ratio: Minimum ratio of views to subscribers
        """
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.spreadsheet_path = spreadsheet_path
        self.min_views = min_views
        self.min_comments = min_comments
        self.min_likes = min_likes
        self.max_subscribers = max_subscribers
        self.min_engagement_ratio = min_engagement_ratio
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data tracking
        self._initialize_data_tracking()
        
    def _initialize_data_tracking(self):
        """Initialize data tracking spreadsheet."""
        if os.path.exists(self.spreadsheet_path):
            try:
                self.data = pd.read_excel(self.spreadsheet_path)
                log.info(f"Loaded existing data from {self.spreadsheet_path} with {len(self.data)} records")
            except Exception as e:
                log.error(f"Error loading data: {e}")
                self._create_new_dataframe()
        else:
            self._create_new_dataframe()
    
    def _create_new_dataframe(self):
        """Create a new dataframe for tracking videos."""
        self.data = pd.DataFrame({
            "video_id": [], 
            "title": [], 
            "channel_id": [],
            "channel_title": [],
            "subscribers": [],
            "views": [],
            "comments": [],
            "likes": [],
            "engagement_ratio": [],
            "published_at": [],
            "search_keyword": [],
            "download_path": [],
            "download_date": []
        })
        log.info("Created new data tracking spreadsheet")
    
    def search_and_analyze(self, keyword: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search for videos by keyword and analyze their engagement metrics.
        
        Args:
            keyword: The search keyword
            max_results: Maximum number of results to analyze
            
        Returns:
            List of high-engagement video data dictionaries
        """
        if not self.api_key:
            log.error("YouTube API key is required for search")
            return []
            
        log.info(f"Searching YouTube for '{keyword}'...")
        
        try:
            # Check if required packages are installed
            import googleapiclient.discovery
            import googleapiclient.errors
        except ImportError:
            log.error("Google API client not installed. Run: pip install google-api-python-client")
            return []
        
        # Initialize YouTube API client
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=self.api_key
        )
        
        # Initial search request
        search_request = youtube.search().list(
            q=keyword,
            part="snippet",
            maxResults=min(50, max_results),
            type="video",
            order="viewCount"  # Sort by view count to get high-engagement videos first
        )
        
        high_engagement_videos = []
        total_fetched = 0
        
        # Fetch search results, potentially with pagination
        while search_request and total_fetched < max_results:
            search_response = search_request.execute()
            
            video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
            if not video_ids:
                break
                
            # Get detailed video information (including metrics)
            videos_response = youtube.videos().list(
                part="snippet,statistics",
                id=",".join(video_ids)
            ).execute()
            
            # Get channel details for subscriber counts
            channel_ids = list(set(item["snippet"]["channelId"] for item in search_response.get("items", [])))
            channels_response = youtube.channels().list(
                part="statistics",
                id=",".join(channel_ids)
            ).execute()
            
            # Create channel ID to subscriber count mapping
            channel_subscribers = {}
            for channel in channels_response.get("items", []):
                channel_id = channel["id"]
                if "statistics" in channel and "subscriberCount" in channel["statistics"]:
                    channel_subscribers[channel_id] = int(channel["statistics"]["subscriberCount"])
                else:
                    channel_subscribers[channel_id] = 0
            
            # Process each video and check engagement criteria
            for video in videos_response.get("items", []):
                video_id = video["id"]
                
                # Skip if we've already processed this video before
                if self.data is not None and (self.data["video_id"] == video_id).any():
                    log.info(f"Skipping already tracked video: {video_id}")
                    continue
                
                # Get video metrics
                stats = video.get("statistics", {})
                views = int(stats.get("viewCount", 0))
                likes = int(stats.get("likeCount", 0))
                comments = int(stats.get("commentCount", 0))
                
                # Get channel info
                channel_id = video["snippet"]["channelId"]
                subscribers = channel_subscribers.get(channel_id, 0)
                
                # Calculate engagement ratio
                engagement_ratio = views / max(subscribers, 1)
                
                # Check if video meets criteria
                meets_criteria = (
                    views >= self.min_views
                    and comments >= self.min_comments
                    and likes >= self.min_likes
                    and subscribers <= self.max_subscribers
                    and engagement_ratio >= self.min_engagement_ratio
                )
                
                if meets_criteria:
                    video_data = {
                        "video_id": video_id,
                        "title": video["snippet"]["title"],
                        "channel_id": channel_id,
                        "channel_title": video["snippet"]["channelTitle"],
                        "subscribers": subscribers,
                        "views": views,
                        "comments": comments,
                        "likes": likes,
                        "engagement_ratio": engagement_ratio,
                        "published_at": video["snippet"]["publishedAt"],
                        "search_keyword": keyword,
                        "download_path": "",
                        "download_date": ""
                    }
                    
                    high_engagement_videos.append(video_data)
                    log.info(f"Found high engagement video: {video_data['title']}")
                    log.info(f"  Views: {views:,}, Subs: {subscribers:,}, Ratio: {engagement_ratio:.4f}")
            
            # Get next page if available
            total_fetched += len(search_response.get("items", []))
            search_request = youtube.search().list_next(search_request, search_response) if total_fetched < max_results else None
        
        log.info(f"Found {len(high_engagement_videos)} videos matching engagement criteria")
        return high_engagement_videos
    
    def download_videos(self, videos: List[Dict[str, Any]], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Download high-engagement videos and update tracking information.
        
        Args:
            videos: List of video data dictionaries
            limit: Maximum number of videos to download
            
        Returns:
            Updated list of video data with download paths
        """
        if limit is not None:
            videos = videos[:limit]
        
        if not videos:
            log.info("No videos to download")
            return []
        
        log.info(f"Downloading {len(videos)} videos...")
        
        # Check if yt-dlp is installed
        try:
            subprocess.run(["yt-dlp", "--version"], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            log.error("yt-dlp not found. Please install it with: pip install yt-dlp")
            return videos
        
        downloaded_videos = []
        for i, video in enumerate(videos):
            video_id = video["video_id"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            log.info(f"Downloading video {i+1}/{len(videos)}: {video['title']}")
            
            # Create safe filename
            safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in video["title"])
            safe_title = safe_title[:100]  # Limit length
            output_path = self.output_dir / f"{safe_title}-{video_id}.%(ext)s"
            
            # Download video with yt-dlp
            cmd = [
                "yt-dlp",
                "--format", "best[height<=720]",  # Limit to 720p
                "--output", str(output_path),
                video_url
            ]
            
            try:
                process = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
                
                if process.returncode == 0:
                    # Find the downloaded file (actual extension may vary)
                    for ext in [".mp4", ".webm", ".mkv"]:
                        potential_path = str(output_path).replace("%(ext)s", ext[1:])
                        if os.path.exists(potential_path):
                            video["download_path"] = potential_path
                            video["download_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            downloaded_videos.append(video)
                            log.info(f"Successfully downloaded to {potential_path}")
                            break
                    
                    if not video.get("download_path"):
                        log.warning(f"Downloaded file not found for video ID: {video_id}")
                else:
                    log.error(f"Error downloading video {video_id}: {process.stderr}")
            
            except Exception as e:
                log.error(f"Error during download of {video_id}: {e}")
        
        # Update tracking data
        self._update_tracking_data(downloaded_videos)
        
        return downloaded_videos
    
    def _update_tracking_data(self, videos: List[Dict[str, Any]]):
        """Update tracking data and save to spreadsheet."""
        if not videos:
            return
            
        # Convert videos to DataFrame
        new_data = pd.DataFrame(videos)
        
        # Append to existing data
        self.data = pd.concat([self.data, new_data], ignore_index=True)
        
        # Save to Excel file
        self.save_to_spreadsheet()
    
    def save_to_spreadsheet(self):
        """Save collected data to spreadsheet.
        
        Returns:
            str: Path to the saved spreadsheet or None if no data was saved
        """
        if self.data is not None and not self.data.empty:
            self.data.to_excel(self.spreadsheet_path, index=False)
            log.info(f"Saved {len(self.data)} videos to {self.spreadsheet_path}")
            return str(self.spreadsheet_path)
        else:
            log.warning("No data to save to spreadsheet")
            return None
            
    def export_data(self, format='json'):
        """Export the tracked videos data in various formats.
        
        Args:
            format (str): Format to export data in - 'json', 'dict', 'df' (DataFrame)
            
        Returns:
            Various: Data in requested format, or None if no data available
        """
        if self.data is None or self.data.empty:
            log.warning("No data to export")
            return None
            
        if format.lower() == 'json':
            return self.data.to_json(orient='records')
        elif format.lower() == 'dict':
            return self.data.to_dict('records')
        elif format.lower() == 'df':
            return self.data
        else:
            log.warning(f"Unsupported export format: {format}. Using 'dict' instead.")
            return self.data.to_dict('records')
            
    def configure(self, **kwargs):
        """Update configuration parameters for the finder.
        
        Args:
            **kwargs: Configuration parameters to update, such as min_views,
                    min_likes, min_comments, max_subscribers, min_engagement_ratio
                    
        Returns:
            Self for method chaining
        """
        valid_params = [
            'min_views', 'min_likes', 'min_comments', 
            'max_subscribers', 'min_engagement_ratio'
        ]
        
        for param, value in kwargs.items():
            if param in valid_params and hasattr(self, param):
                setattr(self, param, value)
                log.debug(f"Updated {param} = {value}")
            else:
                log.warning(f"Invalid parameter: {param}")
                
        return self  # Allow method chaining
    
    def run_search_and_download(
        self, 
        keyword: str, 
        max_search_results: int = 100, 
        download_limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Complete workflow to search and download high-engagement videos.
        
        Args:
            keyword: Search keyword
            max_search_results: Maximum results to analyze
            download_limit: Maximum videos to download
            
        Returns:
            List of downloaded video data
        """
        # Search for videos and analyze metrics
        high_engagement_videos = self.search_and_analyze(keyword, max_search_results)
        
        # Download videos that meet criteria
        downloaded_videos = self.download_videos(high_engagement_videos, download_limit)
        
        return downloaded_videos
