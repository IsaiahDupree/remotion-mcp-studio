#!/usr/bin/env python3
"""
Video Inventory CSV Generator for Windows

This script:
1. Scans the videos directory for video files
2. Extracts metadata from each video
3. Creates a CSV file with the specified headers
4. Includes tracking information from the processed_videos.json file if available

Designed specifically for the n8n setup on Windows.
"""

import os
import sys
import json
import csv
import datetime
import subprocess
import math
from pathlib import Path

# Configuration - Using Windows-style paths
CONFIG = {
    # Windows paths
    "videos_dir": r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos",
    "tracking_dir": r"C:\Users\Isaia\Documents\Coding\N8N\shared\.tracking",
    "output_csv": r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\video-inventory.csv",
    
    # Docker paths
    "docker_videos_dir": "/home/node/shared/videos",
    
    # Common settings
    "tracking_file": "processed_videos.json",
    "video_extensions": ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.MP4', '.AVI', '.MOV', '.MKV', '.WEBM']
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
    "Notes",
    "videoPath",         # Windows path
    "dockerPath",        # Docker path
    "videoName",
    "fileSize",
    "detectedAt"
]

def is_video_file(filename):
    """Check if a file is a video based on extension"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in [x.lower() for x in CONFIG["video_extensions"]]

def get_video_duration(video_path):
    """Get video duration using ffprobe (if available)"""
    try:
        # Try to get duration using ffprobe (part of ffmpeg)
        # Use double quotes for Windows paths with spaces
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
    """Get file creation date, which is reliable on Windows"""
    try:
        # Get file stats
        stats = os.stat(file_path)
        
        # On Windows, st_ctime is creation time
        creation_time = datetime.datetime.fromtimestamp(stats.st_ctime)
        return creation_time
    except Exception as e:
        print(f"Error getting creation date for {file_path}: {e}")
        return datetime.datetime.now()

def main():
    """Main execution function"""
    try:
        # Ensure directories exist
        os.makedirs(CONFIG["tracking_dir"], exist_ok=True)
        
        # Load tracking data
        tracking_data = load_tracking_data()
        processed_videos = tracking_data.get("processedVideos", {})
        print(f"Loaded tracking data with {len(processed_videos)} processed videos")
        
        # Scan the directory for video files
        video_files = []
        if os.path.exists(CONFIG["videos_dir"]):
            for root, _, files in os.walk(CONFIG["videos_dir"]):
                for file in files:
                    if is_video_file(file) and not file.startswith('.'):
                        video_files.append(os.path.join(root, file))
        else:
            print(f"Error: Videos directory not found: {CONFIG['videos_dir']}")
            return 1
        
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
            
            # Create Windows and Docker paths
            windows_path = video_path
            docker_path = os.path.join(CONFIG["docker_videos_dir"], file).replace('\\', '/')
            
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
                "Notes": "",
                "videoPath": windows_path,  # Windows path
                "dockerPath": docker_path,   # Docker path
                "videoName": video_name,
                "fileSize": os.path.getsize(video_path),
                "detectedAt": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
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
    sys.exit(main())
