#!/usr/bin/env python
"""
Script to analyze video frames with OpenAI GPT-4o and generate text overlay
This script samples frames every 5 seconds and uses AI to generate insightful text
"""

import os
import sys
import cv2
import time
import base64
import tempfile
import logging
import argparse
from pathlib import Path
import requests
from typing import List, Dict, Any, Optional
import json

# Add parent directory to path to allow importing video_enhancer modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from video_enhancer modules
from video_enhancer.text_overlay import TextOverlayEnhancer, Position, Style

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("frame_analysis.log")
    ]
)
logger = logging.getLogger("frame_analysis")

def extract_frames(video_path: str, interval_seconds: int = 5) -> List[Dict[str, Any]]:
    """
    Extract frames from video at specified interval
    
    Args:
        video_path: Path to video file
        interval_seconds: Number of seconds between frames
        
    Returns:
        List of dictionaries with frame data and timestamps
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
        
    try:
        # Open video capture
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
            
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        logger.info(f"Video properties: {fps} fps, {total_frames} frames, {duration:.2f} seconds")
        
        # Calculate frame interval
        frame_interval = int(fps * interval_seconds)
        
        frames = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                # Calculate timestamp
                timestamp = frame_count / fps
                
                # Save frame to a temporary file
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                    frame_path = temp_file.name
                    cv2.imwrite(frame_path, frame)
                    
                logger.info(f"Extracted frame at {timestamp:.2f}s, saved to {frame_path}")
                
                frames.append({
                    "frame_path": frame_path,
                    "timestamp": timestamp,
                    "frame_number": frame_count
                })
            
            frame_count += 1
            
        cap.release()
        return frames
        
    except Exception as e:
        logger.error(f"Error extracting frames: {str(e)}")
        raise

def analyze_frame_with_openai(frame_path: str, api_key: str) -> Dict[str, Any]:
    """
    Analyze a frame using OpenAI GPT-4o
    
    Args:
        frame_path: Path to frame image file
        api_key: OpenAI API key
        
    Returns:
        Dictionary with analysis results
    """
    try:
        # Read the image and encode as base64
        with open(frame_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        # Prepare request to OpenAI API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are an expert video analyzer. Provide a concise, catchy caption (1-2 sentences) for this frame from a video that would make an engaging text overlay. Focus on the main subject and action. Make it attention-grabbing and shareable."},
                {"role": "user", "content": [
                    {"type": "text", "text": "Analyze this video frame and suggest a catchy text overlay that would make this video more engaging on social media."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            "max_tokens": 100
        }
        
        # Make the API request
        logger.info(f"Sending frame to OpenAI for analysis")
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        
        # Parse result
        result = response.json()
        text = result["choices"][0]["message"]["content"].strip()
        logger.info(f"OpenAI suggested text: {text}")
        
        return {
            "text": text,
            "full_response": result
        }
        
    except Exception as e:
        logger.error(f"Error analyzing frame with OpenAI: {str(e)}")
        return {"text": "Captivating moment", "error": str(e)}

def generate_text_from_frames(frames: List[Dict[str, Any]], api_key: str) -> str:
    """
    Generate text overlay from multiple frame analyses
    
    Args:
        frames: List of frame data dictionaries with analysis results
        api_key: OpenAI API key
        
    Returns:
        Final text overlay to use
    """
    if not frames:
        return "Must-see viral content"
        
    # Analyze all frames
    frame_texts = []
    for frame in frames:
        analysis = analyze_frame_with_openai(frame["frame_path"], api_key)
        frame["analysis"] = analysis
        frame_texts.append(analysis["text"])
        
    # Summarize all analyses
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Use OpenAI to synthesize a single text from all frame analyses
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are an expert at creating viral video captions. Synthesize the following frame descriptions into a single, concise, attention-grabbing text overlay (1-2 sentences) for the entire video."},
                {"role": "user", "content": f"Create a catchy text overlay based on these frame descriptions: {json.dumps(frame_texts)}"}
            ],
            "max_tokens": 100
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        final_text = result["choices"][0]["message"]["content"].strip()
        logger.info(f"Final synthesized text: {final_text}")
        
        return final_text
        
    except Exception as e:
        logger.error(f"Error synthesizing text: {str(e)}")
        # If synthesis fails, take the first frame description
        if frame_texts:
            return frame_texts[0]
        return "Must-see viral content"

def cleanup_temp_files(frames: List[Dict[str, Any]]) -> None:
    """Delete temporary frame image files"""
    for frame in frames:
        try:
            if os.path.exists(frame["frame_path"]):
                os.remove(frame["frame_path"])
                logger.debug(f"Deleted temporary file: {frame['frame_path']}")
        except Exception as e:
            logger.warning(f"Error cleaning up file {frame['frame_path']}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Generate AI text overlay from video frames")
    parser.add_argument("--input", "-i", required=True, help="Path to input video")
    parser.add_argument("--output", "-o", help="Path to output video (optional)")
    parser.add_argument("--interval", "-t", type=int, default=5, help="Interval between frames (seconds)")
    parser.add_argument("--position", "-p", default="TOP", choices=["TOP", "BOTTOM", "CENTER", "TOP_LEFT", "TOP_RIGHT", "BOTTOM_LEFT", "BOTTOM_RIGHT"], 
                        help="Position of text overlay")
    parser.add_argument("--font-scale", "-f", type=float, default=1.2, help="Font scale (size)")
    parser.add_argument("--style", "-s", default="BLACK_BG_WHITE_TEXT", 
                        choices=["BLACK_BG_WHITE_TEXT", "WHITE_BG_BLACK_TEXT", "TRANSPARENT_WHITE_TEXT", "TRANSPARENT_BLACK_TEXT"],
                        help="Text style")
    parser.add_argument("--api-key", "-k", help="OpenAI API key (overrides environment variable)")
    
    args = parser.parse_args()
    
    # Get OpenAI API key from command line args or environment
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found. Please provide it with --api-key or set OPENAI_API_KEY environment variable.")
        sys.exit(1)
    
    print(f"=== STARTING FRAME ANALYSIS AND TEXT OVERLAY ({args.interval}-SECOND INTERVALS) ===")
    
    try:
        # Set up paths
        input_video = args.input
        if not os.path.exists(input_video):
            print(f"Error: Input video not found: {input_video}")
            return
            
        # Determine output path
        if args.output:
            output_video = args.output
        else:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enhanced_videos")
            os.makedirs(output_dir, exist_ok=True)
            video_basename = os.path.basename(input_video).split('.')[0]
            output_video = os.path.join(output_dir, f"{video_basename}_ai_overlay_{int(time.time())}.mp4")
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)
        
        # Extract frames at specified interval
        logger.info(f"Extracting frames from {input_video} every {args.interval} seconds")
        frames = extract_frames(input_video, args.interval)
        logger.info(f"Extracted {len(frames)} frames")
        
        # Generate text from frame analyses
        logger.info("Analyzing frames with OpenAI GPT-4o")
        generated_text = generate_text_from_frames(frames, api_key)
        logger.info(f"Generated text: '{generated_text}'")
        
        # Clean up temporary frame files
        cleanup_temp_files(frames)
        
        # Map string arguments to enum values
        position = getattr(Position, args.position)
        style = getattr(Style, args.style)
        
        # Initialize the text overlay enhancer
        logger.info("Initializing text overlay enhancer")
        enhancer = TextOverlayEnhancer(
            position=position, 
            font_scale=args.font_scale,
            style=style,
            openai_api_key=api_key
        )
        
        # Apply generated text overlay
        logger.info(f"Applying text overlay to video: {input_video}")
        logger.info(f"Output will be saved to: {output_video}")
        
        result = enhancer.enhance_video(
            video_path=input_video,
            output_path=output_video,
            custom_text=generated_text,
            analyze_first=False  # Skip analysis since we've already done it
        )
        
        # Display results
        if result.get("success", False):
            print(f"Success! Text overlay added: '{result.get('text')}'")
            print(f"Enhanced video saved to: {result.get('output_video')}")
        else:
            print(f"Error adding text overlay: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("=== ENHANCEMENT COMPLETED ===")

if __name__ == "__main__":
    main()
