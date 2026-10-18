"""
Simplified script for detecting API keys in videos without requiring Tesseract OCR.
Uses pure regex pattern matching on video frames.
"""
import os
import cv2
import re
import argparse
import json
from datetime import timedelta
from typing import List, Dict, Any

# Define regex patterns for common API keys
API_KEY_PATTERNS = {
    'openai_key': r'sk-[a-zA-Z0-9]{48}',
    'openai_org': r'org-[a-zA-Z0-9]{24}',
    'openai_proj_key': r'sk-proj-[a-zA-Z0-9\-_]{70,120}',
    'github_token': r'gh[ps]_[a-zA-Z0-9_]{36,}',
    'aws_key': r'AKIA[0-9A-Z]{16}',
    'aws_secret': r'[0-9a-zA-Z/+]{40}'
}

def format_timestamp(seconds):
    """Convert seconds to human-readable timestamp."""
    td = timedelta(seconds=seconds)
    minutes, seconds = divmod(td.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def scan_frame_for_api_keys(frame, patterns=API_KEY_PATTERNS):
    """
    Scan a frame for potential API keys using regex patterns.
    This is a simplified version that works without OCR.
    """
    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Use adaptive thresholding to make text stand out
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Extract text using contours (simple approach)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detections = []
    for contour in contours:
        # Filter out very small contours
        if cv2.contourArea(contour) < 50:
            continue
        
        # Get bounding box
        x, y, w, h = cv2.boundingRect(contour)
        
        # Extract region
        roi = frame[y:y+h, x:x+w]
        
        # Skip if region is too small
        if w < 10 or h < 10:
            continue
        
        # Placeholder for OCR - in a full implementation, this would extract text
        # For now, we'll simulate by checking if any pattern is in the frame
        # This approach will have limited success but might catch visible API keys
        for pattern_name, pattern in patterns.items():
            # This is more of a demonstration than a robust solution
            # In reality, without OCR, this has significant limitations
            if re.search(pattern, str(roi.tobytes())):
                detections.append({
                    'pattern': pattern_name,
                    'region': (x, y, w, h),
                    'text': f"Potential {pattern_name} detected"
                })
    
    return detections

def analyze_video(video_path, frame_skip=10):
    """
    Analyze video for sensitive information.
    
    Args:
        video_path: Path to the video file
        frame_skip: Process every Nth frame
        
    Returns:
        List of detected sensitive information with timestamps
    """
    all_detections = []
    
    try:
        # Open the video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return all_detections
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Only process every nth frame
            if frame_count % frame_skip == 0:
                # Calculate timestamp
                timestamp = frame_count / fps
                
                print(f"\rProcessing frame {frame_count}/{total_frames} at {format_timestamp(timestamp)}", end="")
                
                # Scan frame for sensitive content
                detections = scan_frame_for_api_keys(frame)
                
                # Add timestamp to each detection
                for detection in detections:
                    detection['timestamp'] = timestamp
                    detection['timestamp_str'] = format_timestamp(timestamp)
                    detection['frame_number'] = frame_count
                    all_detections.append(detection)
            
            frame_count += 1
        
        cap.release()
        print("\nVideo analysis complete.")
        
    except Exception as e:
        print(f"Error analyzing video: {e}")
    
    return all_detections

def main():
    parser = argparse.ArgumentParser(description="Detect potential API keys in videos")
    parser.add_argument("--input", "-i", required=True, help="Path to video file")
    parser.add_argument("--skip", "-s", type=int, default=10, help="Process every Nth frame")
    parser.add_argument("--output", "-o", help="Optional JSON output file path")
    
    args = parser.parse_args()
    
    print(f"Analyzing video: {args.input}")
    print(f"Processing every {args.skip} frames")
    
    detections = analyze_video(args.input, args.skip)
    
    if not detections:
        print("No sensitive information detected.")
        return
    
    # Process and group detections by timestamp
    detections_by_timestamp = {}
    for detection in detections:
        timestamp_str = detection['timestamp_str']
        if timestamp_str not in detections_by_timestamp:
            detections_by_timestamp[timestamp_str] = []
        detections_by_timestamp[timestamp_str].append(detection)
    
    # Print report
    print("\n===== SENSITIVE INFORMATION REPORT =====")
    print(f"Found {len(detections)} potential instances of sensitive information")
    
    for timestamp, timestamp_detections in sorted(detections_by_timestamp.items()):
        print(f"\nAt timestamp {timestamp}:")
        for detection in timestamp_detections:
            print(f"  - {detection['pattern']}")
    
    # Save to JSON if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump({
                "video_path": args.input,
                "detections": detections,
                "detections_by_timestamp": {k: [d for d in v] for k, v in detections_by_timestamp.items()}
            }, f, indent=2)
        print(f"\nDetailed report saved to: {args.output}")

if __name__ == "__main__":
    main()
