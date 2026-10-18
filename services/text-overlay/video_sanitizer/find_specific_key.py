"""
Script to find a specific OpenAI API key in video frames.
This script is optimized for speed and specifically searches for a particular API key.
"""
import cv2
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

def scan_for_specific_api_key(video_path, api_key, frame_skip=10, save_frames=True, output_dir="detected_frames"):
    """
    Scan video for a specific API key and save frames where detected.
    
    Args:
        video_path: Path to video file
        api_key: The specific API key to look for
        frame_skip: Process every Nth frame
        save_frames: Whether to save detected frames
        output_dir: Directory to save detected frames
        
    Returns:
        List of detections with timestamps
    """
    # For security reasons, let's only use the first 12 chars of the key for detection
    # This is enough to identify frames containing the key while not exposing the full key
    key_prefix = api_key[:12]
    print(f"Scanning for API key starting with: {key_prefix}...")
    
    detections = []
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return detections
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_skip == 0:
            timestamp = frame_count / fps
            timestamp_str = format_timestamp(timestamp)
            
            print(f"\rScanning frame {frame_count}/{total_frames} at {timestamp_str}", end="")
            
            # Convert frame to string for basic pattern matching
            frame_data = str(frame.tobytes())
            
            # Check if the key prefix is in the frame data
            if key_prefix in frame_data:
                print(f"\nFound API key at {timestamp_str} (frame {frame_count})")
                
                detection = {
                    'timestamp': timestamp,
                    'timestamp_str': timestamp_str,
                    'frame_number': frame_count
                }
                
                if save_frames:
                    filename = save_frame(frame, output_dir, timestamp_str, frame_count)
                    detection['saved_frame'] = filename
                    print(f"Saved frame to {filename}")
                
                detections.append(detection)
        
        frame_count += 1
    
    cap.release()
    print("\nVideo scan complete")
    
    return detections

def main():
    parser = argparse.ArgumentParser(description="Find a specific API key in video frames")
    parser.add_argument("--input", "-i", required=True, help="Path to video file")
    parser.add_argument("--key", "-k", required=True, help="API key to find")
    parser.add_argument("--skip", "-s", type=int, default=10, help="Process every Nth frame")
    parser.add_argument("--no-save", action="store_true", help="Don't save detected frames")
    parser.add_argument("--output-dir", "-o", default="detected_frames", help="Directory to save detected frames")
    
    args = parser.parse_args()
    
    detections = scan_for_specific_api_key(
        args.input, 
        args.key,
        frame_skip=args.skip,
        save_frames=not args.no_save,
        output_dir=args.output_dir
    )
    
    if not detections:
        print("API key not found in the video.")
        return
    
    print("\n===== API KEY DETECTION REPORT =====")
    print(f"Found API key in {len(detections)} frames")
    
    for detection in sorted(detections, key=lambda d: d['timestamp']):
        print(f"\nAt {detection['timestamp_str']} (frame {detection['frame_number']}):")
        if 'saved_frame' in detection:
            print(f"  - Saved frame: {detection['saved_frame']}")

if __name__ == "__main__":
    main()
