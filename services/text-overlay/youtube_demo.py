#!/usr/bin/env python3
"""
YouTube Engagement Finder Demo

This script demonstrates the YouTube engagement finder functionality
without requiring an actual API key, using simulated data.
"""

import os
import sys
import logging
import argparse
import random
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger('youtube_demo')

def simulate_search_results(keyword, max_results=100):
    """Generate simulated search results for demonstration purposes."""
    log.info(f"Simulating search for: {keyword}")
    
    # Create random video data
    videos = []
    for i in range(max_results):
        # Generate random metrics that simulate real engagement patterns
        views = random.randint(1000, 5000000)
        subscribers = random.randint(100, 2000000)
        likes = int(views * random.uniform(0.01, 0.2))  # 1-20% like ratio
        comments = int(views * random.uniform(0.001, 0.03))  # 0.1-3% comment ratio
        
        # Calculate engagement ratio - key metric
        engagement_ratio = views / max(subscribers, 1)
        
        # Generate random date within last year
        published_date = (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")
        
        # Create video entry
        video = {
            "video_id": f"vid_{random.randint(10000, 99999)}",
            "title": f"{keyword.title()} - Example Video {i+1}",
            "channel_id": f"channel_{random.randint(10000, 99999)}",
            "channel_title": f"Creator {random.randint(1, 1000)}",
            "subscribers": subscribers,
            "views": views,
            "comments": comments,
            "likes": likes,
            "engagement_ratio": engagement_ratio,
            "published_at": published_date,
            "search_keyword": keyword
        }
        videos.append(video)
    
    return videos

def filter_high_engagement_videos(videos, min_views=5000, min_comments=10, 
                                 min_likes=100, max_subscribers=100000, 
                                 min_engagement_ratio=0.05):
    """Filter videos based on engagement criteria."""
    high_engagement_videos = []
    
    for video in videos:
        # Check if video meets engagement criteria
        if (video["views"] >= min_views and 
            video["comments"] >= min_comments and
            video["likes"] >= min_likes and
            video["subscribers"] <= max_subscribers and
            video["engagement_ratio"] >= min_engagement_ratio):
            
            high_engagement_videos.append(video)
    
    return high_engagement_videos

def main():
    """Main entry point for the demo script."""
    parser = argparse.ArgumentParser(
        description="Demo for YouTube Engagement Finder without API key"
    )
    
    parser.add_argument(
        "--keyword",
        type=str,
        default="python tutorial",
        help="Keyword to search for"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./youtube_videos",
        help="Directory to save simulated spreadsheet"
    )
    
    parser.add_argument(
        "--min-views",
        type=int,
        default=5000,
        help="Minimum number of views for a video to be considered"
    )
    
    parser.add_argument(
        "--min-comments",
        type=int,
        default=10,
        help="Minimum number of comments"
    )
    
    parser.add_argument(
        "--min-likes",
        type=int,
        default=100,
        help="Minimum number of likes"
    )
    
    parser.add_argument(
        "--max-subscribers",
        type=int,
        default=100000,
        help="Maximum number of subscribers for channel"
    )
    
    parser.add_argument(
        "--min-engagement-ratio",
        type=float,
        default=0.05,
        help="Minimum ratio of views to subscribers"
    )
    
    parser.add_argument(
        "--max-search-results",
        type=int,
        default=100,
        help="Maximum number of search results to simulate"
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Simulate search results
    all_videos = simulate_search_results(args.keyword, args.max_search_results)
    
    # Filter for high engagement
    high_engagement_videos = filter_high_engagement_videos(
        all_videos,
        args.min_views,
        args.min_comments,
        args.min_likes,
        args.max_subscribers,
        args.min_engagement_ratio
    )
    
    # Display results
    log.info(f"Found {len(all_videos)} total videos in search results")
    log.info(f"Filtered to {len(high_engagement_videos)} high engagement videos")
    
    # Show the top 5 videos by engagement ratio
    if high_engagement_videos:
        sorted_videos = sorted(high_engagement_videos, 
                              key=lambda x: x["engagement_ratio"], 
                              reverse=True)
        
        log.info("\nTop 5 High Engagement Videos:")
        for i, video in enumerate(sorted_videos[:5]):
            log.info(f"\n{i+1}. {video['title']}")
            log.info(f"   Channel: {video['channel_title']} ({video['subscribers']:,} subscribers)")
            log.info(f"   Views: {video['views']:,} | Likes: {video['likes']:,} | Comments: {video['comments']:,}")
            log.info(f"   Engagement ratio: {video['engagement_ratio']:.2f}")
        
        # Save results to Excel
        df = pd.DataFrame(high_engagement_videos)
        excel_path = output_dir / f"youtube_engagement_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(excel_path, index=False)
        log.info(f"\nResults saved to: {excel_path}")
    else:
        log.info("No videos met the engagement criteria. Try adjusting your filters.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
