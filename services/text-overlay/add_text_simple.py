#!/usr/bin/env python3
"""
Add Text Overlay to Videos - Simple Version

This script adds catchy text overlays to videos for social media optimization
using OpenCV instead of MoviePy's text rendering (avoiding ImageMagick dependency).
"""

import os
import sys
import argparse
import cv2
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Optional, Dict, Any, List, Tuple
from moviepy.editor import VideoFileClip

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger('text_overlay_simple')

class SimpleVideoTextOverlay:
    """Class to add text overlays to videos using OpenCV."""
    
    def __init__(
        self,
        output_dir: str = "./videos_with_text",
        font: int = cv2.FONT_HERSHEY_DUPLEX,  # OpenCV font
        font_scale: float = 1.5,
        color: Tuple[int, int, int] = (255, 255, 255),  # White in BGR
        thickness: int = 2,
        outline_color: Tuple[int, int, int] = (0, 0, 0),  # Black in BGR
        position: str = 'top'
    ):
        """
        Initialize the Simple Video Text Overlay processor.
        
        Args:
            output_dir: Directory to save processed videos
            font: OpenCV font type
            font_scale: Font size scale
            color: Text color (BGR format)
            thickness: Text thickness
            outline_color: Text outline color (BGR format)
            position: Position of text ('top', 'middle', 'bottom')
        """
        self.output_dir = Path(output_dir)
        self.font = font
        self.font_scale = font_scale
        self.color = color
        self.thickness = thickness
        self.outline_color = outline_color
        self.position = position
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def put_text_with_outline(
        self, 
        frame: np.ndarray,
        text: str,
        position: Tuple[int, int]
    ) -> np.ndarray:
        """
        Add text to frame with outline for better visibility.
        
        Args:
            frame: Video frame
            text: Text to add
            position: Position (x, y) to place text
            
        Returns:
            Frame with text added
        """
        # Draw black outline
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            cv2.putText(
                frame, 
                text,
                (position[0] + dx, position[1] + dy),
                self.font,
                self.font_scale,
                self.outline_color,
                self.thickness + 1,
                cv2.LINE_AA
            )
        
        # Draw text in main color
        cv2.putText(
            frame, 
            text,
            position,
            self.font,
            self.font_scale,
            self.color,
            self.thickness,
            cv2.LINE_AA
        )
        
        return frame
    
    def add_text_to_video(
        self, 
        video_path: str, 
        text: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Add text overlay to a video.
        
        Args:
            video_path: Path to input video
            text: Text to overlay
            output_path: Path for output video (optional)
            
        Returns:
            Path to the processed video
        """
        try:
            video_filename = os.path.basename(video_path)
            log.info(f"Processing video: {video_filename}")
            log.info(f"Adding text: '{text}'")
            
            # Determine output path
            if not output_path:
                video_name = os.path.splitext(video_filename)[0]
                output_path = str(self.output_dir / f"{video_name}_with_text.mp4")
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            
            # Check if video opened successfully
            if not cap.isOpened():
                log.error(f"Error opening video: {video_path}")
                return ""
            
            # Get video properties
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Calculate text position
            if self.position == 'top':
                # Top with some padding (10% from top)
                position_y = int(frame_height * 0.1)
            elif self.position == 'middle':
                # Middle of the frame
                position_y = int(frame_height * 0.5)
            else:  # bottom
                # Bottom with some padding (10% from bottom)
                position_y = int(frame_height * 0.9)
            
            # Calculate text width and center it
            (text_width, text_height), _ = cv2.getTextSize(
                text, self.font, self.font_scale, self.thickness
            )
            position_x = (frame_width - text_width) // 2
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(
                output_path, fourcc, fps, (frame_width, frame_height)
            )
            
            # Preserve audio using temporary files
            temp_video_path = str(self.output_dir / f"temp_{video_name}.mp4")
            
            # Process video frames
            frame_count = 0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            last_progress = -1
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                progress = int((frame_count / total_frames) * 100)
                
                # Show progress every 10%
                if progress % 10 == 0 and progress != last_progress:
                    log.info(f"Processing: {progress}% complete")
                    last_progress = progress
                
                # Add text overlay to frame
                self.put_text_with_outline(frame, text, (position_x, position_y))
                
                # Write frame to output video
                out.write(frame)
            
            # Release resources
            cap.release()
            out.release()
            
            # Copy audio from original video
            try:
                log.info("Copying audio from original video...")
                with VideoFileClip(video_path) as orig_clip:
                    if orig_clip.audio:
                        # Rename current output to temp
                        if os.path.exists(output_path):
                            os.rename(output_path, temp_video_path)
                            
                            # Add audio to the temp video
                            with VideoFileClip(temp_video_path) as video_clip:
                                final_clip = video_clip.set_audio(orig_clip.audio)
                                final_clip.write_videofile(
                                    output_path,
                                    codec='libx264',
                                    audio_codec='aac',
                                    temp_audiofile='temp-audio.m4a',
                                    remove_temp=True,
                                    preset='ultrafast',
                                    logger=None
                                )
                            
                            # Remove temp file
                            if os.path.exists(temp_video_path):
                                os.remove(temp_video_path)
                    else:
                        log.info("Original video has no audio track")
            except Exception as e:
                log.error(f"Error copying audio: {e}")
                # If error occurs, keep the video without audio
                if not os.path.exists(output_path) and os.path.exists(temp_video_path):
                    os.rename(temp_video_path, output_path)
            
            log.info(f"Video saved to {output_path}")
            return output_path
                
        except Exception as e:
            log.error(f"Error processing video: {e}")
            return ""

def process_from_report(
    report_path: str,
    video_dir: str,
    output_dir: str,
    video_filename: Optional[str] = None
) -> List[str]:
    """
    Process videos based on the content report.
    
    Args:
        report_path: Path to video content report Excel file
        video_dir: Directory containing videos
        output_dir: Directory to save processed videos
        video_filename: Optional specific video to process
        
    Returns:
        List of processed video paths
    """
    try:
        # Load the report
        df = pd.read_excel(report_path)
        log.info(f"Loaded report with {len(df)} videos")
        
        # Initialize text overlay processor
        overlay = SimpleVideoTextOverlay(output_dir=output_dir)
        
        processed_videos = []
        
        # Filter for specific video if requested
        if video_filename:
            df = df[df['filename'] == video_filename]
            if len(df) == 0:
                log.error(f"Video {video_filename} not found in report")
                return []
        
        # Process each video that needs text overlay
        for _, row in df.iterrows():
            # Video path
            video_path = os.path.join(video_dir, row['filename'])
            
            # Use catchy description from report
            text = row['catchy_description']
            
            if os.path.exists(video_path):
                output_path = overlay.add_text_to_video(video_path, text)
                if output_path:
                    processed_videos.append(output_path)
            else:
                log.warning(f"Video not found: {video_path}")
        
        return processed_videos
        
    except Exception as e:
        log.error(f"Error processing from report: {e}")
        return []

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Add text overlays to videos")
    
    parser.add_argument("--video", type=str, help="Path to video file")
    parser.add_argument("--text", type=str, help="Text to overlay")
    parser.add_argument("--output", type=str, help="Output directory")
    parser.add_argument("--report", type=str, help="Path to video content report")
    parser.add_argument("--video_dir", type=str, help="Directory containing videos")
    parser.add_argument("--font_scale", type=float, default=1.5, help="Font size scale")
    parser.add_argument("--position", type=str, default="top", 
                       choices=["top", "middle", "bottom"], help="Text position")
    
    args = parser.parse_args()
    
    # Default output directory
    output_dir = args.output or "./videos_with_text"
    
    # Process from report
    if args.report:
        video_dir = args.video_dir or os.path.dirname(args.report)
        process_from_report(
            args.report, 
            video_dir, 
            output_dir,
            args.video
        )
    # Process single video
    elif args.video and args.text:
        overlay = SimpleVideoTextOverlay(
            output_dir=output_dir,
            font_scale=args.font_scale,
            position=args.position
        )
        overlay.add_text_to_video(args.video, args.text)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
