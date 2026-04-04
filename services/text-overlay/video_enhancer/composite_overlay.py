"""
Composite Text Overlay Enhancement Module
=======================================

This module provides an enhanced version of the text overlay functionality
using a combination of MoviePy and Pillow, without requiring ImageMagick.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# Import original text overlay enhancer and style enums for compatibility
from .text_overlay import TextOverlayEnhancer as BaseTextOverlayEnhancer
from .text_styler import Style, Position
from .composite_text_styler import CompositeTextStyler

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("composite_overlay")

class CompositeTextOverlayEnhancer(BaseTextOverlayEnhancer):
    """
    Enhanced class for adding text overlays to videos using a dependency-light approach.
    
    This class uses a combination of MoviePy and Pillow for efficient text overlay
    processing without requiring ImageMagick.
    """
    
    def __init__(
        self,
        style: Style = Style.BLACK_BG_WHITE_TEXT,
        position: Position = Position.TOP,
        font_scale: float = 1.0,
        high_quality: bool = True,
        openai_api_key: Optional[str] = None,
        font_file: Optional[str] = None
    ):
        """
        Initialize the CompositeTextOverlayEnhancer.
        
        Args:
            style: Text overlay style
            position: Text position on frame
            font_scale: Size of the text font
            high_quality: Whether to preserve high video quality
            openai_api_key: OpenAI API key for AI text generation
            font_file: Path to TTF font file (optional)
        """
        # Initialize the base class
        super().__init__(
            style=style,
            position=position, 
            font_scale=font_scale,
            high_quality=high_quality,
            openai_api_key=openai_api_key
        )
        
        # Replace the text styler with composite implementation
        self.text_styler = CompositeTextStyler(
            style=self.style, 
            position=self.position, 
            font_scale=self.font_scale,
            font_file=font_file
        )
        
        logger.info("Using dependency-light composite text styler (no ImageMagick required)")

if __name__ == "__main__":
    # Simple example to demonstrate usage
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        output_path = video_path.replace(".mp4", "_enhanced.mp4")
        enhancer = CompositeTextOverlayEnhancer(position=Position.TOP)
        result = enhancer.enhance_video(video_path, output_path)
        print(f"Enhancement result: {result}")
    else:
        print("Usage: python composite_overlay.py <video_path>")
