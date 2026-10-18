#!/usr/bin/env python3
"""
Add Text Overlay to Videos

This script adds catchy text overlays to videos for social media optimization.
The text is positioned at the top middle of the video with customizable styling.
"""

import os
import sys
import argparse
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import logging
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger('text_overlay')

# Font options optimized for social media
FONT_OPTIONS = {
    'default': 'Impact',  # Bold font that works well for social media
    'alternative': 'Arial-Bold',
    'modern': 'Verdana-Bold'
}

class VideoTextOverlay:
    """Class to add text overlays to videos."""
    
    def __init__(
        self,
        output_dir: str = "./videos_with_text",
        font: str = FONT_OPTIONS['default'],
        font_size: int = 70,
        color: str = 'white',
        stroke_color: str = 'black',
        stroke_width: float = 2.0,
        position: str = 'top'
    ):
        """
        Initialize the Video Text Overlay processor.
        
        Args:
            output_dir: Directory to save processed videos
            font: Font to use for text
            font_size: Font size
            color: Text color
            stroke_color: Outline color for text
            stroke_width: Width of text outline
            position: Position of text ('top', 'middle', 'bottom')
        """
        self.output_dir = Path(output_dir)
        self.font = font
        self.font_size = font_size
        self.color = color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.position = position
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_text_clip(
        self, 
        text: str, 
        video_width: int, 
        video_height: int,
        duration: float
    ) -> TextClip:
        """
        Create a TextClip with styling optimized for social media visibility.
        
        Args:
            text: Text to display
            video_width: Width of the video
            video_height: Height of the video
            duration: Duration of the text clip
            
        Returns:
            Styled TextClip object
        """
        # Create text clip with styling
        txt_clip = TextClip(
            text, 
            font=self.font, 
            fontsize=self.font_size, 
            color=self.color,
            stroke_color=self.stroke_color,
            stroke_width=self.stroke_width,
            method='caption',
            align='center',
            size=(video_width * 0.9, None)  # 90% of video width, auto height
        )
        
        # Set position
        if self.position == 'top':
            # Position at top with some padding
            position = ('center', video_height * 0.1)
        elif self.position == 'middle':
            position = 'center'
        else:  # bottom
            position = ('center', video_height * 0.9)
        
        # Set duration and position
        txt_clip = txt_clip.set_position(position).set_duration(duration)
        
        # Add fade in/out effect
        fade_duration = min(1.0, duration / 4)
        txt_clip = txt_clip.fadein(fade_duration).fadeout(fade_duration)
        
        return txt_clip
    
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
            log.info(f"Processing video: {os.path.basename(video_path)}")
            log.info(f"Adding text: '{text}'")
            
            # Load the video
            with VideoFileClip(video_path) as video:
                # Create text clip
                txt_clip = self.create_text_clip(
                    text, 
                    video.w, 
                    video.h,
                    video.duration
                )
                
                # Combine video and text
                result = CompositeVideoClip([video, txt_clip])
                
                # Determine output path
                if not output_path:
                    video_name = os.path.splitext(os.path.basename(video_path))[0]
                    output_path = str(self.output_dir / f"{video_name}_with_text.mp4")
                
                # Write output video
                result.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    preset='ultrafast',  # For faster processing, change to 'medium' for final version
                    threads=4,
                    logger=None  # Disable moviepy's verbose logging
                )
                
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
        overlay = VideoTextOverlay(output_dir=output_dir)
        
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
    parser.add_argument("--font", type=str, default=FONT_OPTIONS['default'], 
                       choices=list(FONT_OPTIONS.values()), help="Font to use")
    parser.add_argument("--font_size", type=int, default=70, help="Font size")
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
        overlay = VideoTextOverlay(
            output_dir=output_dir,
            font=args.font,
            font_size=args.font_size,
            position=args.position
        )
        overlay.add_text_to_video(args.video, args.text)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
