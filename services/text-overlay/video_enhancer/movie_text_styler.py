"""
MoviePy-based Text Styler Module
===============================

This module provides efficient text overlay functionality using MoviePy.
It offers significant performance improvements over frame-by-frame OpenCV processing.
"""

import os
import sys
import logging
from enum import Enum
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
    from moviepy.video.tools.subtitles import SubtitlesClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logging.warning("MoviePy not available. Please install with: pip install moviepy")

# Import enums from original styler for compatibility
from .text_styler import Style, Position

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("movie_text_styler")

class MovieTextStyler:
    """
    Class for applying text overlays to videos efficiently using MoviePy.
    
    This class provides a more efficient alternative to frame-by-frame OpenCV processing.
    
    Attributes:
        style (Style): Text overlay style
        position (Position): Text position on frame
        font_scale (float): Size of the text font
    """
    
    def __init__(
        self,
        style: Style = Style.BLACK_BG_WHITE_TEXT,
        position: Position = Position.TOP,
        font_scale: float = 1.0
    ):
        """
        Initialize the MovieTextStyler.
        
        Args:
            style: Text overlay style
            position: Text position on frame
            font_scale: Size of the text font
        """
        if not MOVIEPY_AVAILABLE:
            raise ImportError("MoviePy is required for this module. Install with: pip install moviepy")
            
        self.style = style
        self.position = position
        self.font_scale = font_scale
    
    def _get_text_color(self) -> str:
        """Get text color based on style"""
        if self.style in [Style.BLACK_BG_WHITE_TEXT, Style.TRANSPARENT_BG_WHITE_TEXT]:
            return 'white'
        return 'black'
    
    def _get_bg_color(self) -> Optional[str]:
        """Get background color based on style or None for transparent"""
        if self.style == Style.BLACK_BG_WHITE_TEXT:
            return 'black'
        elif self.style == Style.WHITE_BG_BLACK_TEXT:
            return 'white'
        elif self.style == Style.TRANSPARENT_BG_WHITE_TEXT:
            return None  # Transparent
        return None  # Default to transparent for any other style
    
    def _get_position(self, video_width: int, video_height: int, text_clip: TextClip) -> tuple:
        """
        Get position coordinates based on Position enum.
        
        Args:
            video_width: Width of the video
            video_height: Height of the video
            text_clip: The text clip to position
            
        Returns:
            Tuple of (x, y) coordinates
        """
        text_width, text_height = text_clip.size
        
        # Calculate positions with some margin
        margin = int(15 * self.font_scale)
        
        if self.position == Position.TOP:
            return ('center', margin)
        elif self.position == Position.BOTTOM:
            return ('center', video_height - text_height - margin)
        elif self.position == Position.CENTER:
            return ('center', 'center')
        elif self.position == Position.TOP_LEFT:
            return (margin, margin)
        elif self.position == Position.TOP_RIGHT:
            return (video_width - text_width - margin, margin)
        elif self.position == Position.BOTTOM_LEFT:
            return (margin, video_height - text_height - margin)
        elif self.position == Position.BOTTOM_RIGHT:
            return (video_width - text_width - margin, video_height - text_height - margin)
        
        # Default to center
        return ('center', 'center')
    
    def apply_text_to_video(
        self,
        input_video: str,
        output_video: str,
        text: str,
        high_quality: bool = True
    ) -> bool:
        """Apply text overlay to video using MoviePy
        
        Args:
            input_video: Path to input video
            output_video: Path to output video
            text: Text to overlay
            high_quality: Whether to use high quality encoding
            
        Returns:
            True if successful, False otherwise
        """
        """
        Apply text overlay to a video using MoviePy.
        
        Args:
            input_video: Path to input video
            output_video: Path to output video
            text: Text to overlay
            high_quality: Whether to use high quality encoding
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(input_video):
            logger.error(f"Input video not found: {input_video}")
            return False
            
        try:
            logger.info(f"Applying text overlay to video: {input_video}")
            
            # Load the video
            video = VideoFileClip(input_video)
            
            # Calculate font size based on video dimensions and font scale
            video_width, video_height = video.size
            fontsize = int(min(video_width, video_height) * 0.05 * self.font_scale)
            
            logger.info(f"Using text style: {self.style.name}")
            
            # Get styling parameters
            text_color = self._get_text_color()
            bg_color = self._get_bg_color()
            
            # Create text clip with appropriate styling
            text_clip = TextClip(
                text,
                fontsize=fontsize,
                color=text_color,
                bg_color=bg_color,
                font="Arial-Bold",
                kerning=-2,
                interline=-1,
                align='center',
                method='label' if bg_color else 'caption'  # Use caption for transparent background
            )
            
            # Set position
            position = self._get_position(video_width, video_height, text_clip)
            text_clip = text_clip.set_position(position).set_duration(video.duration)
            
            # Compose video with text overlay
            final_clip = CompositeVideoClip([video, text_clip])
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)
            
            # Set encoding parameters based on quality
            if high_quality:
                bitrate = "8000k"
                codec = "libx264"
                preset = "medium"  # Balance between speed and quality
            else:
                bitrate = "4000k"
                codec = "libx264"
                preset = "faster"
                
            logger.info(f"Writing enhanced video to: {output_video}")
            
            # Write the result
            final_clip.write_videofile(
                output_video,
                codec=codec,
                preset=preset,
                bitrate=bitrate,
                audio_codec="aac",
                threads=4,  # Use multiple threads for faster processing
                logger=None  # Suppress MoviePy's progress bar
            )
            
            # Close the clips to release resources
            text_clip.close()
            video.close()
            final_clip.close()
            
            logger.info("Text overlay complete")
            return True
            
        except Exception as e:
            logger.error(f"Error applying text overlay: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
