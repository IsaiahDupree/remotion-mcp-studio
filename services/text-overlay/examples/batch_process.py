#!/usr/bin/env python3
"""
Batch Processing Example for Smart Text-on-Video Overlay Tool

This script demonstrates how to use the smart text-on-video overlay tool
in a production workflow, processing multiple videos with different prompts
and configurations.
"""

import os
import sys
import csv
import json
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_overlay import process_batch, load_config, setup_openai_client, setup_models
from utils.webhook import WebhookNotifier

# Font presets from smart_overlay.py
FONT_PRESETS = {
    "TechMeStuff": {
        "font": "./fonts/Inter-Bold.ttf",
        "color": "white",
        "stroke_width": 2,
        "stroke_color": "black",
    },
    "Minimalist": {
        "font": "./fonts/Roboto-Light.ttf",
        "color": "white",
        "stroke_width": 1,
        "stroke_color": "black",
    },
    "Dramatic": {
        "font": "./fonts/Montserrat-ExtraBold.ttf",
        "color": "white",
        "stroke_width": 3,
        "stroke_color": "black",
    },
    "Professional": {
        "font": "./fonts/OpenSans-SemiBold.ttf",
        "color": "white",
        "stroke_width": 2,
        "stroke_color": "black",
    },
}

def load_prompts_from_csv(csv_path: str) -> List[Dict[str, str]]:
    """Load prompts and video mappings from a CSV file.
    
    Expected CSV format:
    video_file,prompt
    video1.mp4,Prompt for video 1
    video2.mp4,Prompt for video 2
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        List of dictionaries with video_file and prompt keys
    """
    prompts = []
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompts.append({
                'video_file': row.get('video_file', ''),
                'prompt': row.get('prompt', '')
            })
    return prompts

def process_videos_with_mapping(
    input_dir: str,
    output_dir: str,
    mapping_file: str,
    config_path: str,
    openai_key: str,
    preset: str = "TechMeStuff",
    webhook_url: Optional[str] = None
) -> None:
    """Process videos using a CSV mapping file.
    
    Args:
        input_dir: Directory containing input videos
        output_dir: Directory to save output videos
        mapping_file: CSV file mapping videos to prompts
        config_path: Path to configuration file
        openai_key: OpenAI API key
        preset: Font preset to use
        webhook_url: URL to send webhook notifications to
    """
    # Load configuration
    config = load_config(config_path)
    
    # Initialize OpenAI client
    client = setup_openai_client(openai_key)
    
    # Load models
    setup_models()
    
    # Load prompts from CSV
    prompts = load_prompts_from_csv(mapping_file)
    
    # Get font preset
    font_preset = FONT_PRESETS[preset].copy()
    
    # Create timestamp for the run
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    run_dir = os.path.join(output_dir, f"{timestamp}_batch_run")
    
    # Process each video with its corresponding prompt
    for item in prompts:
        video_file = item['video_file']
        prompt = item['prompt']
        
        # Skip if video file or prompt is empty
        if not video_file or not prompt:
            print(f"Skipping entry with missing video file or prompt: {item}")
            continue
        
        # Get full path to video file
        video_path = os.path.join(input_dir, video_file)
        
        # Skip if video file doesn't exist
        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            continue
        
        # Create output directory for this video
        video_output_dir = os.path.join(run_dir, os.path.splitext(video_file)[0])
        os.makedirs(video_output_dir, exist_ok=True)
        
        print(f"Processing {video_file} with prompt: {prompt}")
        
        # Process the video
        process_batch(
            input_dir=os.path.dirname(video_path),
            output_base_dir=video_output_dir,
            prompt=prompt,
            font_preset=font_preset,
            batch_prompts=None,
            webhook_url=webhook_url,
            single_video=os.path.basename(video_path)
        )
    
    print(f"Batch processing complete. Results saved to {run_dir}")

def main():
    """Parse command-line arguments and process videos."""
    parser = argparse.ArgumentParser(
        description="Batch process videos with Smart Text-on-Video Overlay Tool"
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing input videos"
    )
    parser.add_argument(
        "--output-dir",
        default="./outputs",
        help="Directory to save output videos"
    )
    parser.add_argument(
        "--mapping-file",
        required=True,
        help="CSV file mapping videos to prompts"
    )
    parser.add_argument(
        "--config",
        default="./config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--preset",
        default="TechMeStuff",
        choices=list(FONT_PRESETS.keys()),
        help="Font preset to use"
    )
    parser.add_argument(
        "--webhook-url",
        help="URL to send webhook notifications to"
    )
    parser.add_argument(
        "--openai-key",
        required=True,
        help="OpenAI API key"
    )
    
    args = parser.parse_args()
    
    # Process videos
    process_videos_with_mapping(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        mapping_file=args.mapping_file,
        config_path=args.config,
        openai_key=args.openai_key,
        preset=args.preset,
        webhook_url=args.webhook_url
    )
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
