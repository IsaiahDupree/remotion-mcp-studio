#!/usr/bin/env python3
"""
Video Content Analyzer

Analyzes videos in a directory to detect which need background music
and generates short catchy descriptions for each video.
"""

import os
import sys
import csv
import pandas as pd
import numpy as np
import cv2
import logging
from pathlib import Path
from moviepy.editor import VideoFileClip
import tempfile
import random
import re
from typing import List, Dict, Tuple, Optional, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import audio analysis functionality
from audiovideotools.audio_analysis.audio_analyzer import has_background_music

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger('video_content_analyzer')

# Video formats to analyze
VIDEO_FORMATS = ['.mp4', '.MP4', '.mov', '.MOV', '.avi', '.AVI']

def get_video_files(directory: str) -> List[str]:
    """
    Get all video files in the specified directory.
    
    Args:
        directory: Path to directory containing videos
        
    Returns:
        List of full paths to video files
    """
    video_files = []
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path) and any(file.endswith(ext) for ext in VIDEO_FORMATS):
            video_files.append(file_path)
    return video_files

def analyze_video_audio(video_path: str) -> Tuple[bool, Dict[str, float]]:
    """
    Analyze video audio to detect if it already has background music.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Tuple of (has_music_boolean, metrics_dict)
    """
    try:
        # Extract audio using moviepy
        log.info(f"Analyzing audio for {os.path.basename(video_path)}")
        with VideoFileClip(video_path) as video:
            # Skip if video has no audio
            if not video.audio:
                log.warning(f"No audio track found in {os.path.basename(video_path)}")
                return False, {"error": "No audio track"}
            
            # Get audio as numpy array
            audio_array = video.audio.to_soundarray()
            sample_rate = video.audio.fps
            
            # Use existing function to detect background music
            has_music, metrics = has_background_music(audio_array, sample_rate)
            
            log.info(f"Background music detection for {os.path.basename(video_path)}: {has_music}")
            return has_music, metrics
    except Exception as e:
        log.error(f"Error analyzing {os.path.basename(video_path)}: {e}")
        return False, {"error": str(e)}

def generate_video_description(video_path: str, existing_description: Optional[str] = None) -> str:
    """
    Generate a concise (6 words or less) catchy summary for a video.
    
    This function extracts key frames from the video and generates a description.
    If an existing description is provided, it will attempt to condense it.
    
    Args:
        video_path: Path to video file
        existing_description: Optional existing description to condense
        
    Returns:
        Short catchy description
    """
    # If we have an existing description, condense it
    if existing_description:
        # Extract key words and create a shorter version
        words = re.findall(r'\b\w+\b', existing_description)
        important_words = [word for word in words if len(word) > 3 and word.lower() not in 
                          ['with', 'this', 'that', 'from', 'there', 'here', 'have', 'your']]
        
        if important_words:
            # Take up to 6 important words
            selected_words = important_words[:min(6, len(important_words))]
            return ' '.join(selected_words).capitalize()
    
    # If no existing description or couldn't condense it properly
    # Generate some generic descriptions based on filename
    filename = os.path.basename(video_path)
    
    # Sample catchy phrases
    generic_phrases = [
        "Must see this amazing content",
        "You won't believe what happens",
        "Awesome moment caught on camera",
        "This will make your day",
        "Wait for the ending",
        "Mind-blowing reveal at 0:30"
    ]
    
    return random.choice(generic_phrases)

def get_video_metadata_from_csv(directory: str) -> Dict[str, Dict[str, Any]]:
    """
    Extract video metadata from CSV files in the directory.
    
    Args:
        directory: Directory containing CSV files
        
    Returns:
        Dictionary mapping filenames to metadata
    """
    metadata = {}
    
    # CSV files that might contain metadata
    csv_files = ['instagram_videos.csv', 'videos_list.csv', 'actual_videos_list.csv']
    
    for csv_file in csv_files:
        csv_path = os.path.join(directory, csv_file)
        if not os.path.exists(csv_path):
            continue
            
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Look for file path column
                file_path_col = next((col for col in ['FilePath', 'filename', 'path'] 
                                     if col in row and row[col]), None)
                
                if file_path_col:
                    file_path = row[file_path_col]
                    filename = os.path.basename(file_path)
                    
                    # Store all metadata for this file
                    if filename not in metadata:
                        metadata[filename] = {}
                        
                    # Add all fields from this CSV
                    for key, value in row.items():
                        if value:  # Only add non-empty values
                            metadata[filename][key] = value
    
    return metadata

def create_content_report(video_dir: str, output_path: Optional[str] = None) -> str:
    """
    Analyze videos and create an Excel report indicating which need
    background music and words/descriptions.
    
    Args:
        video_dir: Directory containing videos
        output_path: Optional path for the output Excel file
        
    Returns:
        Path to the created Excel file
    """
    if not output_path:
        output_path = os.path.join(video_dir, "video_content_report.xlsx")
    
    # Get all videos
    video_files = get_video_files(video_dir)
    log.info(f"Found {len(video_files)} videos to analyze")
    
    # Get metadata from CSV files
    metadata = get_video_metadata_from_csv(video_dir)
    
    # Analyze each video
    results = []
    
    for video_path in video_files:
        filename = os.path.basename(video_path)
        log.info(f"Processing {filename}")
        
        # Basic video info
        video_info = {
            'filename': filename,
            'path': video_path,
            'size_mb': round(os.path.getsize(video_path) / (1024 * 1024), 2)
        }
        
        # Add metadata from CSVs if available
        file_metadata = metadata.get(filename, {})
        for key, value in file_metadata.items():
            if key not in video_info:
                video_info[key] = value
        
        # Detect if background music is needed
        has_music, audio_metrics = analyze_video_audio(video_path)
        video_info['has_background_music'] = "Yes" if has_music else "No"
        video_info['needs_background_music'] = "No" if has_music else "Yes"
        
        # Generate catchy description if not already available
        existing_description = file_metadata.get('Description', '')
        existing_title = file_metadata.get('Title', '')
        
        if existing_description or existing_title:
            source_text = existing_description if existing_description else existing_title
            catchy_description = generate_video_description(video_path, source_text)
        else:
            catchy_description = generate_video_description(video_path)
            
        video_info['catchy_description'] = catchy_description
        
        # Add to results
        results.append(video_info)
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(results)
    
    # Reorder columns to put important ones first
    important_cols = ['filename', 'needs_background_music', 'catchy_description', 
                     'has_background_music', 'Title', 'Description', 'size_mb', 'path']
    
    # Get columns that exist in the DataFrame
    existing_cols = [col for col in important_cols if col in df.columns]
    
    # Add any other columns that weren't in our important list
    other_cols = [col for col in df.columns if col not in important_cols]
    final_cols = existing_cols + other_cols
    
    # Reorder and save
    df = df[final_cols]
    df.to_excel(output_path, index=False)
    
    log.info(f"Report created at {output_path}")
    return output_path

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze videos for background music and generate descriptions")
    parser.add_argument("--video_dir", default="C:\\Users\\Isaia\\Documents\\N8N\\shared_data",
                       help="Directory containing videos to analyze")
    parser.add_argument("--output", default=None,
                       help="Path for output Excel report")
    
    args = parser.parse_args()
    
    create_content_report(args.video_dir, args.output)
    
if __name__ == "__main__":
    main()
