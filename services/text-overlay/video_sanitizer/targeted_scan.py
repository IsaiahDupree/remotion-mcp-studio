"""
Targeted script to scan for specific OpenAI API key pattern in a video.
"""
import cv2
import re
import argparse
import os
from datetime import timedelta

def format_timestamp(seconds):
    """Convert seconds to human-readable timestamp."""
    td = timedelta(seconds=seconds)
    minutes, seconds = divmod(td.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def save_frame(frame, output_dir, timestamp_str, frame_num):
    """Save frame as an image file."""
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"frame_{frame_num}_{timestamp_str.replace(':', '-')}.jpg")
    cv2.imwrite(filename, frame)
    return filename

def scan_video_for_openai_key(video_path, save_frames=True, frame_skip=30, output_dir="detected_frames"):
    """
    Scan video for OpenAI API key patterns and save frames where detected.
    
    Args:
        video_path: Path to video file
        save_frames: Whether to save detected frames
        frame_skip: Process every Nth frame
        output_dir: Directory to save detected frames
        
    Returns:
        List of detections with timestamps
    """
    # Define the patterns (project API key format and standard format)
    patterns = {
        'openai_proj_key': r'sk-proj-[a-zA-Z0-9\-_]{70,120}',
        'openai_key': r'sk-[a-zA-Z0-9]{48}'
    }
    
    detections = []
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return detections
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    print(f"Video info: {total_frames} frames, {fps} FPS, duration: {format_timestamp(duration)}")
    print(f"Scanning for API keys every {frame_skip} frames...")
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_skip == 0:
            timestamp = frame_count / fps
            timestamp_str = format_timestamp(timestamp)
            
            print(f"\rScanning frame {frame_count}/{total_frames} at {timestamp_str}", end="")
            
            # Convert frame to text using a simple OCR-like approach
            # Without Tesseract, this is very limited, but we can try to detect 
            # binary patterns that might match our target API key
            
            # For demonstration, we'll check if parts of the API key pattern appear in the binary data
            frame_bytes = frame.tobytes()
            frame_str = str(frame_bytes)
            
            for pattern_name, pattern in patterns.items():
                matches = re.findall(pattern, frame_str)
                if matches:
                    print(f"\nFound potential {pattern_name} at {timestamp_str} (frame {frame_count})")
                    
                    detection = {
                        'pattern': pattern_name,
                        'timestamp': timestamp,
                        'timestamp_str': timestamp_str,
                        'frame_number': frame_count,
                        'matches': matches
                    }
                    
                    if save_frames:
                        filename = save_frame(frame, output_dir, timestamp_str, frame_count)
                        detection['saved_frame'] = filename
                        print(f"Saved frame to {filename}")
                    
                    detections.append(detection)
        
        frame_count += 1
        if frame_count > total_frames:
            break
    
    cap.release()
    print("\nVideo scan complete")
    
    return detections

def main():
    parser = argparse.ArgumentParser(description="Targeted scan for OpenAI API keys in videos")
    parser.add_argument("--input", "-i", required=True, help="Path to video file")
    parser.add_argument("--skip", "-s", type=int, default=30, help="Process every Nth frame")
    parser.add_argument("--no-save", action="store_true", help="Don't save detected frames")
    parser.add_argument("--output-dir", "-o", default="detected_frames", help="Directory to save detected frames")
    
    args = parser.parse_args()
    
    detections = scan_video_for_openai_key(
        args.input, 
        save_frames=not args.no_save, 
        frame_skip=args.skip,
        output_dir=args.output_dir
    )
    
    if not detections:
        print("No API keys detected in the video.")
        return
    
    print("\n===== API KEY DETECTION REPORT =====")
    print(f"Found {len(detections)} potential instances of API keys")
    
    for detection in sorted(detections, key=lambda d: d['timestamp']):
        print(f"\nAt {detection['timestamp_str']} (frame {detection['frame_number']}):")
        print(f"  - Pattern: {detection['pattern']}")
        print(f"  - Matches: {len(detection['matches'])}")
        if 'saved_frame' in detection:
            print(f"  - Saved frame: {detection['saved_frame']}")

if __name__ == "__main__":
    main()
