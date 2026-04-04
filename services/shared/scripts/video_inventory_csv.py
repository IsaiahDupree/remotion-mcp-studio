#!/usr/bin/env python3
"""
Video Inventory CSV Generator

This script:
1. Scans a directory for video files
2. Extracts metadata from each video
3. Creates a CSV file with the specified headers
4. Includes tracking information from the processed_videos.json file if available
"""

import os
import sys
import json
import csv
import datetime
import subprocess
from pathlib import Path

# Configuration
CONFIG = {
    "videos_dir": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "videos"),
    "tracking_dir": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tracking"),
    "tracking_file": "processed_videos.json",
    "output_csv": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "videos", "video-inventory.csv"),
    "video_extensions": ['.mp4', '.avi', '.mov', '.mkv', '.webm']
}

# CSV Headers
HEADERS = [
    "File Name", 
    "Folder Name", 
    "Date Created", 
    "Duration", 
    "Working Title", 
    "Posted?", 
    "Posting Date", 
    "Status", 
    "Notes"
]

def is_video_file(filename):
    """Check if a file is a video based on extension"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in CONFIG["video_extensions"] or ext.upper() in CONFIG["video_extensions"]

def get_video_duration(video_path):
    """Get video duration using ffprobe (if available)"""
    try:
        # Try to get duration using ffprobe (part of ffmpeg)
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_path}"'
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode('utf-8').strip()
        duration = float(output)
        
        if not math.isnan(duration):
            # Format duration as MM:SS
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            return f"{minutes:02d}:{seconds:02d}"
    except (subprocess.SubprocessError, ValueError) as error:
        print(f"Could not get duration for {video_path}: {error}")
    except Exception as e:
        print(f"Unexpected error getting duration: {e}")
    
    return 'Unknown'

def load_tracking_data():
    """Load the tracking data if available"""
    tracking_file_path = os.path.join(CONFIG["tracking_dir"], CONFIG["tracking_file"])
    
    if os.path.exists(tracking_file_path):
        try:
            with open(tracking_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as err:
            print(f"Error reading tracking file: {err}")
    
    return {"processedVideos": {}}

def get_creation_date(file_path):
    """Get file creation date, falling back to modification date if not available"""
    try:
        # Get file stats
        stats = os.stat(file_path)
        
        # Try to get creation time (ctime on Windows, not reliable on Unix)
        # If not available, fall back to modification time
        if hasattr(stats, 'st_birthtime'):  # macOS
            creation_time = datetime.datetime.fromtimestamp(stats.st_birthtime)
        else:
            # On Windows, st_ctime is creation time; on Unix, it's metadata change time
            # Use modification time as fallback
            creation_time = datetime.datetime.fromtimestamp(stats.st_mtime)
        
        return creation_time
    except Exception as e:
        print(f"Error getting creation date for {file_path}: {e}")
        return datetime.datetime.now()

def main():
    """Main execution function"""
    try:
        # Ensure directories exist
        os.makedirs(CONFIG["tracking_dir"], exist_ok=True)
        os.makedirs(os.path.dirname(CONFIG["output_csv"]), exist_ok=True)
        
        # Load tracking data
        tracking_data = load_tracking_data()
        processed_videos = tracking_data.get("processedVideos", {})
        print(f"Loaded tracking data with {len(processed_videos)} processed videos")
        
        # Scan the directory for video files
        video_files = []
        for root, _, files in os.walk(CONFIG["videos_dir"]):
            for file in files:
                if is_video_file(file) and not file.startswith('.'):
                    video_files.append(os.path.join(root, file))
        
        print(f"Found {len(video_files)} video files in directory")
        
        # Create a list of video objects with CSV-ready data
        videos = []
        for video_path in video_files:
            file = os.path.basename(video_path)
            video_name = os.path.splitext(file)[0]
            
            # Get creation date
            creation_date = get_creation_date(video_path)
            formatted_date = creation_date.strftime('%Y-%m-%d')
            
            # Get folder name (parent directory)
            folder_name = os.path.basename(os.path.dirname(video_path))
            
            # Get duration
            duration = get_video_duration(video_path)
            
            # Check if the video has been processed
            is_processed = video_name in processed_videos
            processing_info = processed_videos.get(video_name, None)
            
            # Create a dictionary with all the required CSV headers
            video_data = {
                "File Name": file,
                "Folder Name": folder_name,
                "Date Created": formatted_date,
                "Duration": duration,
                "Working Title": video_name.replace('_', ' ').replace('-', ' '),
                "Posted?": "Yes" if is_processed else "No",
                "Posting Date": processing_info["processedAt"].split('T')[0] if processing_info and "processedAt" in processing_info else "",
                "Status": processing_info["status"] if processing_info and "status" in processing_info else "pending" if not is_processed else "processed",
                "Notes": ""
            }
            
            videos.append(video_data)
        
        # Sort videos by creation date (newest first)
        videos.sort(key=lambda x: x["Date Created"], reverse=True)
        
        # Write to CSV
        with open(CONFIG["output_csv"], 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=HEADERS)
            writer.writeheader()
            writer.writerows(videos)
        
        print(f"Successfully wrote {len(videos)} videos to {CONFIG['output_csv']}")
        return 0
    
    except Exception as error:
        print(f"Error generating CSV data: {error}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # Import math here to avoid potential issues with circular imports
    import math
    sys.exit(main())
