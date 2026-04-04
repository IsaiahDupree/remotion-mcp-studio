"""
MoviePy-Based Text Overlay Enhancement Module
===========================================

This module provides an enhanced version of the text overlay functionality
using MoviePy for significantly faster processing compared to frame-by-frame OpenCV.
"""

import os
import sys
import logging
import tempfile
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# Import original text overlay enhancer and style enums for compatibility
from .text_overlay import TextOverlayEnhancer as BaseTextOverlayEnhancer
from .text_styler import Style, Position
from .movie_text_styler import MovieTextStyler

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("moviepy_overlay")

class FastTextOverlayEnhancer(BaseTextOverlayEnhancer):
    """
    Extended class for enhancing videos with text overlays using MoviePy.
    
    This class extends the original TextOverlayEnhancer but replaces the
    frame-by-frame processing with more efficient MoviePy-based processing.
    """
    
    def __init__(
        self,
        style: Style = Style.BLACK_BG_WHITE_TEXT,
        position: Position = Position.TOP,
        font_scale: float = 1.0,
        high_quality: bool = True,
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize the FastTextOverlayEnhancer.
        
        Args:
            style: Text overlay style
            position: Text position on frame
            font_scale: Size of the text font
            high_quality: Whether to preserve high video quality
            openai_api_key: OpenAI API key for AI text generation
        """
        # Initialize the base class
        super().__init__(
            style=style,
            position=position, 
            font_scale=font_scale,
            high_quality=high_quality,
            openai_api_key=openai_api_key
        )
        
        # Replace the text styler with MoviePy-based implementation
        self.text_styler = MovieTextStyler(
            style=self.style, 
            position=self.position, 
            font_scale=self.font_scale
        )
        
        logger.info("Using high-performance MoviePy text styler")

if __name__ == "__main__":
    # Simple example to demonstrate usage
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        output_path = video_path.replace(".mp4", "_enhanced.mp4")
        enhancer = FastTextOverlayEnhancer(position=Position.TOP)
        result = enhancer.enhance_video(video_path, output_path)
        print(f"Enhancement result: {result}")
    else:
        print("Usage: python moviepy_overlay.py <video_path>")
