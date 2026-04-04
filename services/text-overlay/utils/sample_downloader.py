#!/usr/bin/env python3
"""
Sample Video Downloader for Smart Text-on-Video Overlay Tool

Downloads sample public domain videos for testing purposes.
"""

import os
import sys
import requests
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn

# Initialize console
console = Console()

# Sample videos (public domain)
SAMPLE_VIDEOS = [
    {
        "name": "business_meeting.mp4",
        "url": "https://cdn.pixabay.com/vimeo/328240352/business-24924.mp4?width=640&hash=8b5c6c2c9c0e8d0f6e7d4c3b2a1f0e9d8c7b6a5",
        "description": "Business meeting with team discussion",
        "duration": "0:15",
        "size_mb": 2.5,
        "md5": "8b5c6c2c9c0e8d0f6e7d4c3b2a1f0e9d"  # Example hash, will be verified during download
    },
    {
        "name": "technology_typing.mp4",
        "url": "https://cdn.pixabay.com/vimeo/414974537/laptop-40305.mp4?width=640&hash=7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8",
        "description": "Person typing on laptop keyboard",
        "duration": "0:12",
        "size_mb": 1.8,
        "md5": "7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d"  # Example hash, will be verified during download
    },
    {
        "name": "presentation_screen.mp4",
        "url": "https://cdn.pixabay.com/vimeo/330195215/office-25312.mp4?width=640&hash=6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7",
        "description": "Business presentation with charts",
        "duration": "0:20",
        "size_mb": 3.2,
        "md5": "6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f"  # Example hash, will be verified during download
    },
    {
        "name": "creative_workspace.mp4",
        "url": "https://cdn.pixabay.com/vimeo/417410895/office-41031.mp4?width=640&hash=5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6",
        "description": "Creative office workspace",
        "duration": "0:18",
        "size_mb": 2.9,
        "md5": "5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a"  # Example hash, will be verified during download
    },
    {
        "name": "digital_marketing.mp4",
        "url": "https://cdn.pixabay.com/vimeo/359218956/social-media-29415.mp4?width=640&hash=4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5",
        "description": "Social media marketing on devices",
        "duration": "0:22",
        "size_mb": 3.5,
        "md5": "4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b"  # Example hash, will be verified during download
    }
]

def calculate_md5(file_path: str) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_file(url: str, target_path: str) -> bool:
    """Download a file from URL to target path with progress bar."""
    try:
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
        ) as progress:
            task = progress.add_task(f"Downloading {os.path.basename(target_path)}", total=None)
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Get content length if available
            total_size = int(response.headers.get('content-length', 0))
            if total_size:
                progress.update(task, total=total_size)
            
            # Download the file
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))
            
            return True
    except Exception as e:
        console.print(f"[bold red]Error downloading {url}: {e}[/bold red]")
        return False

def download_samples(target_dir: str = "./input_videos", force: bool = False, count: int = 5) -> List[str]:
    """Download sample videos to the target directory.
    
    Args:
        target_dir: Directory to save videos to
        force: Whether to force download even if files exist
        count: Number of sample videos to download (default: 5)
        
    Returns:
        List of downloaded video paths
    """
    console.print("[bold green]Sample Video Downloader[/bold green]")
    console.print(f"Downloading sample videos to: {target_dir}")
    
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    downloaded_videos = []
    
    # Limit the number of videos to download
    videos_to_download = SAMPLE_VIDEOS[:min(count, len(SAMPLE_VIDEOS))]
    
    # Download each sample video
    for video in videos_to_download:
        video_path = os.path.join(target_dir, video["name"])
        
        # Check if file already exists
        if os.path.exists(video_path) and not force:
            console.print(f"[yellow]Video already exists: {video['name']}[/yellow]")
            console.print(f"  Description: {video['description']}")
            console.print(f"  Duration: {video['duration']}")
            console.print(f"  Size: {video['size_mb']} MB")
            
            # Verify hash
            file_hash = calculate_md5(video_path)
            if file_hash == video["md5"]:
                console.print(f"[green]  Hash verified: {file_hash}[/green]")
                downloaded_videos.append(video_path)
            else:
                console.print(f"[yellow]  Hash mismatch. Expected: {video['md5']}, Got: {file_hash}[/yellow]")
                console.print(f"  Re-downloading video...")
                if download_file(video["url"], video_path):
                    console.print(f"[green]  Downloaded: {video['name']}[/green]")
                    downloaded_videos.append(video_path)
        else:
            console.print(f"\nDownloading: {video['name']}")
            console.print(f"  Description: {video['description']}")
            console.print(f"  Duration: {video['duration']}")
            console.print(f"  Size: {video['size_mb']} MB")
            
            if download_file(video["url"], video_path):
                # Verify hash
                file_hash = calculate_md5(video_path)
                if file_hash == video["md5"]:
                    console.print(f"[green]  Hash verified: {file_hash}[/green]")
                else:
                    console.print(f"[yellow]  Hash mismatch. Expected: {video['md5']}, Got: {file_hash}[/yellow]")
                    console.print(f"  File may be corrupted or different from expected.")
                
                downloaded_videos.append(video_path)
    
    console.print(f"\n[bold green]Downloaded {len(downloaded_videos)} sample videos to {target_dir}[/bold green]")
    return downloaded_videos

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download sample videos for testing")
    parser.add_argument(
        "--target-dir", 
        default="./input_videos", 
        help="Directory to save videos to (default: ./input_videos)"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force download even if files exist"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of sample videos to download (default: 5)"
    )
    
    args = parser.parse_args()
    
    download_samples(args.target_dir, args.force, args.count)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
