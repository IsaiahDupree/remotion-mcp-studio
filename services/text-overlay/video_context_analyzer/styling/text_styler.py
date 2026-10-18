"""
Text Styler Module

Provides simple, modular styling for text overlays on videos.
Focused on creating professional, social-media-optimized text styles.
"""

import os
import cv2
import numpy as np
import logging
from typing import Tuple, Dict, Any, Optional, List
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('text_styler')

class Position(Enum):
    TOP = 'top'
    MIDDLE = 'middle'
    BOTTOM = 'bottom'

class Style(Enum):
    BLACK_BG_WHITE_TEXT = 'black_bg_white_text'  # Like the example image
    WHITE_BG_BLACK_TEXT = 'white_bg_black_text'
    TRANSPARENT_OUTLINE = 'transparent_outline'

class TextStyler:
    """
    Simple, modular text styling for video overlays.
    """
    
    def __init__(
        self,
        style: Style = Style.BLACK_BG_WHITE_TEXT,
        position: Position = Position.TOP,
        font_scale: float = 1.0,
        padding: int = 10,
        bg_opacity: float = 0.8,
        animation: bool = False
    ):
        """
        Initialize the Text Styler.
        
        Args:
            style: Text style to use
            position: Vertical position on frame
            font_scale: Font size scaling
            padding: Padding around text in pixels
            bg_opacity: Background opacity (0-1)
            animation: Whether to animate text entrance
        """
        self.style = style
        self.position = position
        self.font_scale = font_scale
        self.padding = padding
        self.bg_opacity = bg_opacity
        self.animation = animation
        
        # Default font settings
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Style-specific settings
        if self.style == Style.BLACK_BG_WHITE_TEXT:
            self.text_color = (255, 255, 255)  # White (BGR)
            self.bg_color = (0, 0, 0)          # Black (BGR)
            self.thickness = 2
        elif self.style == Style.WHITE_BG_BLACK_TEXT:
            self.text_color = (0, 0, 0)         # Black (BGR)
            self.bg_color = (255, 255, 255)     # White (BGR)
            self.thickness = 2
        elif self.style == Style.TRANSPARENT_OUTLINE:
            self.text_color = (255, 255, 255)   # White (BGR)
            self.bg_color = None                # No background
            self.thickness = 2
    
    def get_text_size(self, text: str) -> Tuple[int, int]:
        """
        Get the size of text using cv2.
        
        Args:
            text: Text to measure
            
        Returns:
            (width, height) of text
        """
        (text_width, text_height), baseline = cv2.getTextSize(
            text, 
            self.font, 
            self.font_scale, 
            self.thickness
        )
        return text_width, text_height
    
    def calculate_position(
        self, 
        text_width: int, 
        text_height: int, 
        frame_width: int, 
        frame_height: int
    ) -> Tuple[int, int, int, int]:
        """
        Calculate text and background position.
        
        Args:
            text_width: Width of text
            text_height: Height of text
            frame_width: Width of video frame
            frame_height: Height of video frame
            
        Returns:
            (bg_x, bg_y, text_x, text_y) coordinates
        """
        # Calculate background dimensions (with padding)
        bg_width = text_width + (self.padding * 2)
        bg_height = text_height + (self.padding * 2)
        
        # Calculate horizontal center (always centered horizontally)
        bg_x = (frame_width - bg_width) // 2
        text_x = (frame_width - text_width) // 2
        
        # Calculate vertical position based on position enum
        if self.position == Position.TOP:
            # 10% from top
            bg_y = int(frame_height * 0.1)
            text_y = bg_y + text_height + self.padding
        elif self.position == Position.MIDDLE:
            # Middle of frame
            bg_y = (frame_height - bg_height) // 2
            text_y = bg_y + text_height + self.padding
        else:  # Position.BOTTOM
            # 10% from bottom
            bg_y = int(frame_height * 0.9) - bg_height
            text_y = bg_y + text_height + self.padding
            
        return bg_x, bg_y, text_x, text_y
    
    def apply_text_overlay(
        self, 
        frame: np.ndarray, 
        text: str,
        frame_number: int = 0,
        total_frames: int = 0
    ) -> np.ndarray:
        """
        Apply text overlay to a single frame.
        
        Args:
            frame: Input video frame
            text: Text to overlay
            frame_number: Current frame number (for animation)
            total_frames: Total frames in video (for animation)
            
        Returns:
            Frame with text overlay applied
        """
        frame_height, frame_width = frame.shape[:2]
        
        # Get text dimensions
        text_width, text_height = self.get_text_size(text)
        
        # Calculate positions
        bg_x, bg_y, text_x, text_y = self.calculate_position(
            text_width, text_height, frame_width, frame_height
        )
        
        # Apply animation if enabled
        opacity = self.bg_opacity
        if self.animation and total_frames > 0:
            # Simple fade-in animation for first 1 second (assuming 30 fps)
            if frame_number < 30:
                fade_factor = frame_number / 30
                opacity *= fade_factor
            # And fade-out for last 1 second
            elif frame_number > (total_frames - 30) and total_frames > 60:
                fade_factor = (total_frames - frame_number) / 30
                opacity *= fade_factor
        
        # Create a copy of the frame
        result = frame.copy()
        
        # Draw background rectangle if style needs it
        if self.bg_color is not None:
            # Create background rectangle
            bg_width = text_width + (self.padding * 2)
            bg_height = text_height + (self.padding * 2)
            
            # Create overlay for semi-transparent background
            overlay = frame.copy()
            cv2.rectangle(
                overlay,
                (bg_x, bg_y),
                (bg_x + bg_width, bg_y + bg_height),
                self.bg_color,
                -1  # Filled rectangle
            )
            
            # Apply overlay with transparency
            cv2.addWeighted(overlay, opacity, result, 1 - opacity, 0, result)
            
        # Draw text
        if self.style == Style.TRANSPARENT_OUTLINE:
            # Add black outline for better visibility
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                cv2.putText(
                    result,
                    text,
                    (text_x + dx, text_y + dy),
                    self.font,
                    self.font_scale,
                    (0, 0, 0),  # Black outline
                    self.thickness + 1,
                    cv2.LINE_AA
                )
        
        # Draw main text
        cv2.putText(
            result,
            text,
            (text_x, text_y),
            self.font,
            self.font_scale,
            self.text_color,
            self.thickness,
            cv2.LINE_AA
        )
            
        return result
    
    def create_style_preview(self, text: str, width: int = 1280, height: int = 720) -> np.ndarray:
        """
        Create a preview image of how text will look with current style.
        
        Args:
            text: Sample text to display
            width: Preview image width
            height: Preview image height
            
        Returns:
            Preview image
        """
        # Create blank frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Fill with a gray background to simulate video content
        frame.fill(128)
        
        # Apply text overlay
        result = self.apply_text_overlay(frame, text)
        
        return result
