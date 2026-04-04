"""
File utility functions for handling files and directories.

This module provides utility functions for:
1. Finding and filtering video files
2. Generating unique filenames
3. Managing file paths and creation
"""

import os
import logging
import random
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Set up logging
log = logging.getLogger('file_utils')

# Common video file extensions
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm']

def find_videos(directory: str, limit: Optional[int] = None) -> List[str]:
    """
    Find all video files in a directory.
    
    Args:
        directory: Directory to search for video files
        limit: Maximum number of files to return (None for all)
        
    Returns:
        List of video file paths
    """
    try:
        video_files = []
        dir_path = Path(directory)
        
        # Check if directory exists
        if not dir_path.exists() or not dir_path.is_dir():
            log.error(f"Directory not found: {directory}")
            return []
        
        # Find all video files
        for ext in VIDEO_EXTENSIONS:
            video_files.extend(list(dir_path.glob(f"*{ext}")))
        
        # Convert to string paths and sort alphabetically
        video_paths = [str(f) for f in video_files]
        video_paths.sort()
        
        # Apply limit if specified
        if limit is not None:
            video_paths = video_paths[:limit]
            
        log.info(f"Found {len(video_paths)} video files in {directory}")
        return video_paths
        
    except Exception as e:
        log.error(f"Error finding videos: {e}")
        return []

def ensure_directory(directory_path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Directory path to create
        
    Returns:
        True if directory exists or was created, False otherwise
    """
    try:
        dir_path = Path(directory_path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        log.error(f"Error creating directory {directory_path}: {e}")
        return False

def generate_unique_filename(base_path: str, suffix: Optional[str] = None) -> str:
    """
    Generate a unique filename based on the original path.
    
    Args:
        base_path: Original file path
        suffix: Optional suffix to add before extension
        
    Returns:
        Unique file path
    """
    try:
        path = Path(base_path)
        directory = path.parent
        filename = path.stem
        extension = path.suffix
        
        # Generate timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Add random component to ensure uniqueness
        random_suffix = str(random.randint(1000, 9999))
        
        # Build new filename
        if suffix:
            new_filename = f"{filename}_{suffix}_{timestamp}_{random_suffix}{extension}"
        else:
            new_filename = f"{filename}_{timestamp}_{random_suffix}{extension}"
            
        # Return full path
        return str(directory / new_filename)
        
    except Exception as e:
        log.error(f"Error generating unique filename: {e}")
        # Fall back to timestamp only
        return f"{base_path}.{datetime.datetime.now().timestamp()}"

def choose_random_file(file_list: List[str]) -> Optional[str]:
    """
    Choose a random file from a list of files.
    
    Args:
        file_list: List of file paths
        
    Returns:
        Random file path or None if list is empty
    """
    if not file_list:
        return None
    
    return random.choice(file_list)
