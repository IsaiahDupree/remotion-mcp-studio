"""
Script for detecting and reporting sensitive information in videos.
"""
import os
import argparse
import json
from datetime import timedelta
from sanitizer import VideoSanitizer

def format_timestamp(seconds):
    """Convert seconds to human-readable timestamp."""
    td = timedelta(seconds=seconds)
    minutes, seconds = divmod(td.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def main():
    """Detect and report sensitive information in videos."""
    parser = argparse.ArgumentParser(description='Detect and report sensitive information in videos')
    parser.add_argument('--input', '-i', required=True, help='Input video file path')
    parser.add_argument('--confidence', '-c', type=float, default=0.5, help='Text detection confidence threshold')
    parser.add_argument('--skip', '-s', type=int, default=5, help='Process every Nth frame')
    parser.add_argument('--output-json', '-o', help='Optional JSON output file for the report')
    
    args = parser.parse_args()
    
    # Initialize sanitizer with common API key patterns
    sanitizer = VideoSanitizer(
        detection_confidence=args.confidence
    )
    
    # Add patterns specifically for common API keys
    sanitizer.add_custom_pattern("openai_key", r"sk-[a-zA-Z0-9]{48}")
    sanitizer.add_custom_pattern("openai_org", r"org-[a-zA-Z0-9]{24}")
    sanitizer.add_custom_pattern("openai_proj_key", r"sk-proj-[a-zA-Z0-9\-_]{70,120}")
    sanitizer.add_custom_pattern("github_token", r"gh[ps]_[a-zA-Z0-9_]{36,}")
    sanitizer.add_custom_pattern("aws_key", r"AKIA[0-9A-Z]{16}")
    sanitizer.add_custom_pattern("aws_secret", r"[0-9a-zA-Z/+]{40}")
    
    print(f"Analyzing video for sensitive information: {args.input}")
    print(f"Processing with frame skip: {args.skip}")
    
    # Run detection in report-only mode
    detections = sanitizer.sanitize_video(
        input_path=args.input,
        output_path="",  # Not creating output in report mode
        frame_skip=args.skip,
        report_only=True
    )
    
    if not detections:
        print("No sensitive information detected in the video.")
        return
    
    # Process and group detections by timestamp
    detections_by_timestamp = {}
    for detection in detections:
        timestamp_str = format_timestamp(detection['timestamp'])
        if timestamp_str not in detections_by_timestamp:
            detections_by_timestamp[timestamp_str] = []
        
        # Clean up detection for display (remove large objects)
        display_detection = {
            'timestamp': timestamp_str,
            'timestamp_seconds': detection['timestamp'],
            'frame_number': detection['frame_number'],
            'pattern': detection['pattern'],
            'text': detection['text'].strip(),
        }
        detections_by_timestamp[timestamp_str].append(display_detection)
    
    # Print report to console
    print("\n===== SENSITIVE INFORMATION REPORT =====")
    print(f"Found {len(detections)} instances of sensitive information in the video")
    
    for timestamp, timestamp_detections in sorted(detections_by_timestamp.items()):
        print(f"\nAt timestamp {timestamp}:")
        for detection in timestamp_detections:
            # Truncate long text for display
            text = detection['text']
            if len(text) > 50:
                text = text[:25] + "..." + text[-22:]
            print(f"  - {detection['pattern']}: {text}")
    
    # Save to JSON if requested
    if args.output_json:
        with open(args.output_json, 'w') as f:
            json.dump({
                'video_path': args.input,
                'detections': list(detections),
                'detections_by_timestamp': detections_by_timestamp
            }, f, indent=2)
        print(f"\nDetailed report saved to: {args.output_json}")

if __name__ == "__main__":
    main()
