"""
Text Styling Module for Video Enhancement
=======================================

This module provides text styling functionality for video overlay.
"""

import os
import sys
import logging
import cv2
import numpy as np
from pathlib import Path
import subprocess
import tempfile
from enum import Enum
from typing import Dict, Any, Tuple, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("text_styler")

# Define style and position enums if not already imported
class Style(Enum):
    BLACK_BG_WHITE_TEXT = 1
    WHITE_BG_BLACK_TEXT = 2
    TRANSPARENT_BG_WHITE_TEXT = 3

class Position(Enum):
    TOP = 1
    CENTER = 2
    BOTTOM = 3


class TextStyler:
    """
    Class for styling and applying text overlays to videos.
    """
    
    def __init__(
        self,
        style: Style = Style.BLACK_BG_WHITE_TEXT,
        position: Position = Position.TOP,
        font_scale: float = 1.0,
        thickness: int = 2,
        font_face: int = cv2.FONT_HERSHEY_SIMPLEX,
        margin: int = 20
    ):
        """
        Initialize the TextStyler.
        
        Args:
            style: Text overlay style
            position: Text position on frame
            font_scale: Size of the text font
            thickness: Thickness of the text
            font_face: Font face to use
            margin: Margin from edges
        """
        self.style = style
        self.position = position
        self.font_scale = font_scale
        self.thickness = thickness
        self.font_face = font_face
        self.margin = margin
        
    def get_text_size(self, text: str) -> Tuple[int, int]:
        """Get width and height of text with current settings."""
        (text_width, text_height), _ = cv2.getTextSize(
            text, self.font_face, self.font_scale, self.thickness
        )
        return text_width, text_height
    
    def calculate_text_position(self, frame_size: Tuple[int, int], text: str) -> Tuple[int, int]:
        """Calculate the position to place text based on frame size and position setting."""
        frame_width, frame_height = frame_size
        text_width, text_height = self.get_text_size(text)
        
        # Calculate x position (centered horizontally)
        x = (frame_width - text_width) // 2
        
        # Calculate y position based on position setting
        if self.position == Position.TOP:
            y = self.margin + text_height
        elif self.position == Position.CENTER:
            y = (frame_height + text_height) // 2
        else:  # BOTTOM
            y = frame_height - self.margin
            
        return x, y
    
    def apply_text_overlay(self, frame: np.ndarray, text: str) -> np.ndarray:
        """
        Apply text overlay to a single frame.
        
        Args:
            frame: Input video frame
            text: Text to overlay
            
        Returns:
            Frame with text overlay
        """
        frame_height, frame_width = frame.shape[:2]
        text_width, text_height = self.get_text_size(text)
        x, y = self.calculate_text_position((frame_width, frame_height), text)
        
        # Create a copy of the frame
        result = frame.copy()
        
        # Apply styling based on style setting
        if self.style == Style.BLACK_BG_WHITE_TEXT:
            # Create black background rectangle
            bg_margin = 10
            cv2.rectangle(
                result,
                (x - bg_margin, y - text_height - bg_margin),
                (x + text_width + bg_margin, y + bg_margin),
                (0, 0, 0),
                -1
            )
            # Add white text
            cv2.putText(
                result, text, (x, y),
                self.font_face, self.font_scale, (255, 255, 255),
                self.thickness, cv2.LINE_AA
            )
        elif self.style == Style.WHITE_BG_BLACK_TEXT:
            # Create white background rectangle
            bg_margin = 10
            cv2.rectangle(
                result,
                (x - bg_margin, y - text_height - bg_margin),
                (x + text_width + bg_margin, y + bg_margin),
                (255, 255, 255),
                -1
            )
            # Add black text
            cv2.putText(
                result, text, (x, y),
                self.font_face, self.font_scale, (0, 0, 0),
                self.thickness, cv2.LINE_AA
            )
        else:  # TRANSPARENT_BG_WHITE_TEXT
            # Add white text directly (no background)
            cv2.putText(
                result, text, (x, y),
                self.font_face, self.font_scale, (255, 255, 255),
                self.thickness, cv2.LINE_AA
            )
            
        return result
    
    def apply_text_to_video(
        self,
        input_video: str,
        output_video: str,
        text: str,
        high_quality: bool = True
    ) -> bool:
        """
        Apply text overlay to an entire video.
        
        Args:
            input_video: Path to input video
            output_video: Path to output video
            text: Text to overlay
            high_quality: Whether to preserve high video quality
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Applying text overlay to video: {input_video}")
        
        try:
            # Create temporary directory for frames
            with tempfile.TemporaryDirectory() as temp_dir:
                # Open the video
                cap = cv2.VideoCapture(input_video)
                if not cap.isOpened():
                    logger.error(f"Could not open video: {input_video}")
                    return False
                
                # Get video properties
                frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                # Create video writer with appropriate codec
                if high_quality:
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use mp4v codec for high quality
                else:
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Use XVID for compatibility
                    
                # Create output directory if it doesn't exist
                os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)
                
                # Create video writer
                out = cv2.VideoWriter(
                    output_video,
                    fourcc,
                    fps,
                    (frame_width, frame_height)
                )
                
                frame_count = 0
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                logger.info(f"Processing {total_frames} frames")
                
                # Process each frame
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                        
                    # Apply text overlay
                    frame_with_text = self.apply_text_overlay(frame, text)
                    
                    # Write frame to output video
                    out.write(frame_with_text)
                    
                    frame_count += 1
                    if frame_count % 100 == 0:
                        logger.info(f"Processed {frame_count}/{total_frames} frames")
                
                # Release resources
                cap.release()
                out.release()
                
                logger.info(f"Text overlay complete: {output_video}")
                return True
                
        except Exception as e:
            logger.error(f"Error applying text to video: {e}")
            return False
