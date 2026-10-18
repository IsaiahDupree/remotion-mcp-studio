"""
Example script demonstrating video sanitization functionality.
"""
import os
import argparse
from sanitizer import VideoSanitizer

def main():
    """
    Run video sanitization with command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Sanitize videos to remove sensitive information')
    parser.add_argument('--input', '-i', required=True, help='Input video file path')
    parser.add_argument('--output', '-o', required=False, help='Output video file path')
    parser.add_argument('--blur', '-b', type=int, default=25, help='Blur strength (odd number)')
    parser.add_argument('--confidence', '-c', type=float, default=0.6, help='Text detection confidence threshold')
    parser.add_argument('--skip', '-s', type=int, default=3, help='Process every Nth frame')
    parser.add_argument('--start', type=float, default=0, help='Start time in seconds')
    parser.add_argument('--end', type=float, default=None, help='End time in seconds')
    
    args = parser.parse_args()
    
    # If output is not specified, create one based on input filename
    if not args.output:
        input_base = os.path.basename(args.input)
        input_name = os.path.splitext(input_base)[0]
        input_dir = os.path.dirname(args.input)
        args.output = os.path.join(input_dir, f"{input_name}_sanitized.mp4")
    
    # Initialize sanitizer with custom settings
    sanitizer = VideoSanitizer(
        blur_strength=args.blur,
        detection_confidence=args.confidence
    )
    
    # Add some additional patterns that might be common in development videos
    sanitizer.add_custom_pattern("github_token", r"(?i)gh[ps]_[a-zA-Z0-9_]{36,255}")
    sanitizer.add_custom_pattern("aws_key", r"(?i)AKIA[0-9A-Z]{16}")
    
    # Process the video
    print(f"Sanitizing video: {args.input}")
    print(f"Output will be saved to: {args.output}")
    print(f"Processing with frame skip: {args.skip}, blur strength: {args.blur}")
    
    success = sanitizer.sanitize_video(
        input_path=args.input,
        output_path=args.output,
        start_time=args.start,
        end_time=args.end,
        frame_skip=args.skip
    )
    
    if success:
        print(f"Video sanitization complete: {args.output}")
    else:
        print("Video sanitization failed")

if __name__ == "__main__":
    main()
