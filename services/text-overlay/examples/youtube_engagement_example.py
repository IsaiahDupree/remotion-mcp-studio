#!/usr/bin/env python3
"""
YouTube Engagement Finder - Integration Example

This example demonstrates how to integrate the YouTube engagement finder
into other applications and software stacks.
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add parent directory to path so we can import the module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the YouTube engagement finder
from audiovideotools.downloaders.youtube_engagement import YouTubeEngagementFinder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("youtube_integration_example")

def basic_usage_example(api_key):
    """Basic usage example."""
    log.info("Running basic usage example...")
    
    # Initialize with your API key and custom parameters
    finder = YouTubeEngagementFinder(
        api_key=api_key,
        min_views=10000,
        min_likes=50,
        min_comments=5,
        max_subscribers=200000,
        min_engagement_ratio=0.01
    )
    
    # Search for videos with high engagement
    videos = finder.search_and_analyze("cooking tutorial", max_results=10)
    
    # Show results
    log.info(f"Found {len(videos)} high engagement videos")
    
    for video in videos[:3]:
        log.info(f"\nTitle: {video['title']}")
        log.info(f"Channel: {video['channel_title']} ({video['subscribers']:,} subscribers)")
        log.info(f"Views: {video['views']:,}")
        log.info(f"Engagement ratio: {video['engagement_ratio']:.2f}")

def integration_with_pandas(api_key):
    """Example of integrating with pandas for data analysis."""
    log.info("\nRunning pandas integration example...")
    
    # Initialize
    finder = YouTubeEngagementFinder(api_key=api_key)
    
    # Search for videos
    finder.search_and_analyze("healthy recipes", max_results=10)
    
    # Export as pandas DataFrame
    df = finder.export_data(format='df')
    
    if df is not None and not df.empty:
        # Example data analysis
        log.info("\nData analysis with pandas:")
        log.info(f"Average views: {df['views'].mean():,.0f}")
        log.info(f"Average engagement ratio: {df['engagement_ratio'].mean():.2f}")
        
        # Find channels with highest engagement
        top_channels = df.sort_values('engagement_ratio', ascending=False).head(3)
        log.info("\nTop engaging channels:")
        for _, row in top_channels.iterrows():
            log.info(f"Channel: {row['channel_title']} - Ratio: {row['engagement_ratio']:.2f}")

def batch_processing_example(api_key):
    """Example of batch processing multiple keywords."""
    log.info("\nRunning batch processing example...")
    
    # Initialize
    finder = YouTubeEngagementFinder(api_key=api_key)
    
    # List of keywords to search
    keywords = ["quick meals", "easy recipes", "cooking hacks"]
    
    # Process each keyword
    all_videos = []
    
    for keyword in keywords:
        log.info(f"Processing keyword: {keyword}")
        videos = finder.search_and_analyze(keyword, max_results=5)
        
        if videos:
            log.info(f"  Found {len(videos)} videos for '{keyword}'")
            all_videos.extend(videos)
    
    # Combine results and sort by engagement ratio
    if all_videos:
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(all_videos)
        
        # Remove duplicates if any
        df = df.drop_duplicates(subset=['video_id'])
        
        # Sort by engagement ratio
        df = df.sort_values('engagement_ratio', ascending=False)
        
        log.info(f"\nFound {len(df)} unique high-engagement videos across all keywords")
        log.info(f"Top video: {df.iloc[0]['title']} - Engagement ratio: {df.iloc[0]['engagement_ratio']:.2f}")
        
        # Export to Excel
        output_path = Path("./batch_search_results.xlsx")
        df.to_excel(output_path, index=False)
        log.info(f"Results exported to {output_path.absolute()}")

def dynamic_configuration_example(api_key):
    """Example of dynamically configuring parameters."""
    log.info("\nRunning dynamic configuration example...")
    
    # Initialize with default parameters
    finder = YouTubeEngagementFinder(api_key=api_key)
    
    # Configure for finding viral content from small channels
    finder.configure(
        min_views=100000,      # High view count
        max_subscribers=10000, # Very small channels
        min_engagement_ratio=1.0  # At least as many views as subscribers
    )
    
    # Search with these parameters
    viral_videos = finder.search_and_analyze("DIY projects", max_results=10)
    log.info(f"Found {len(viral_videos)} viral videos from small channels")
    
    # Reconfigure for broader search
    finder.configure(
        min_views=5000,
        max_subscribers=500000,
        min_engagement_ratio=0.01
    )
    
    # Search with new parameters
    broad_results = finder.search_and_analyze("DIY projects", max_results=10)
    log.info(f"Found {len(broad_results)} videos with broader parameters")

def main():
    """Main function to run examples."""
    # You need to provide a valid YouTube API key to run these examples
    api_key = os.environ.get("YOUTUBE_API_KEY")
    
    if not api_key:
        log.error("YouTube API key not found. Please set YOUTUBE_API_KEY environment variable.")
        log.error("Example: export YOUTUBE_API_KEY='your_api_key'")
        return 1
    
    # Run examples
    try:
        basic_usage_example(api_key)
        integration_with_pandas(api_key)
        batch_processing_example(api_key)
        dynamic_configuration_example(api_key)
        
        log.info("\nAll examples completed successfully!")
        return 0
    except Exception as e:
        log.error(f"Error running examples: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
