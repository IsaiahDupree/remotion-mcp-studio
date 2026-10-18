"""
Text Overlay Enhancement Module
==============================

This module provides functionality for adding text overlays to videos.
It supports various styles, positions, and text generation methods.

Classes:
    TextOverlayEnhancer: Main class for adding text overlays to videos
"""

import os
import sys
import logging
import cv2
import numpy as np
import tempfile
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from pathlib import Path

# Import our text styler
from .text_styler import TextStyler, Style, Position

# Try to import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from video_context_analyzer.frame_analysis.frame_analyzer import FrameAnalyzer
    from video_context_analyzer.transcript_analysis.transcript_analyzer import TranscriptAnalyzer
except ImportError as e:
    logging.warning(f"Could not import video_context_analyzer modules: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("text_overlay")


class TextOverlayEnhancer:
    """
    Class for enhancing videos with text overlays.
    
    This class provides functionality to:
    1. Add text overlays to videos with customizable styles and positions
    2. Generate catchy text based on video content using AI or heuristic methods
    3. Process videos with high quality preservation
    
    Attributes:
        style (Style): Text overlay style (e.g., BLACK_BG_WHITE_TEXT)
        position (Position): Text position on frame (e.g., TOP, CENTER)
        font_scale (float): Size of the text font
        high_quality (bool): Whether to preserve high video quality
        openai_api_key (str): OpenAI API key for AI text generation
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
        Initialize the TextOverlayEnhancer.
        
        Args:
            style: Text overlay style
            position: Text position on frame
            font_scale: Size of the text font
            high_quality: Whether to preserve high video quality
            openai_api_key: OpenAI API key for AI text generation
        """
        self.style = style
        self.position = position
        self.font_scale = font_scale
        self.high_quality = high_quality
        
        # Set OpenAI API key if provided
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        elif "OPENAI_API_KEY" in os.environ:
            logger.info("Using OpenAI API key from environment variable")
        else:
            logger.warning("No OpenAI API key provided. AI-powered text generation will be limited.")
        
        # Initialize components if available
        try:
            self.frame_analyzer = FrameAnalyzer()
            self.transcript_analyzer = TranscriptAnalyzer()
            self.text_styler = TextStyler(style=self.style, position=self.position, font_scale=self.font_scale)
            self.dependencies_loaded = True
        except Exception as e:
            logger.error(f"Error initializing dependencies: {e}")
            # Still create the TextStyler since it's our custom implementation that doesn't depend on external modules
            self.text_styler = TextStyler(style=self.style, position=self.position, font_scale=self.font_scale)
            self.dependencies_loaded = False
    
    def generate_text_for_video(self, video_path: str, custom_text: Optional[str] = None) -> str:
        """
        Generate or use text overlay for a video.
        
        Args:
            video_path: Path to the video file
            custom_text: Custom text to use (overrides generated text)
            
        Returns:
            Text to overlay on the video
        """
        if custom_text:
            logger.info(f"Using custom text: '{custom_text}'")
            return custom_text
            
        if not self.dependencies_loaded:
            logger.warning("Dependencies not loaded. Using default text.")
            return "Must-see viral content"
        
        logger.info("Generating text based on video content...")
        
        try:
            # Extract representative frames
            frames = self.frame_analyzer.extract_representative_frames(video_path)
            
            # Analyze video content using frames
            video_context = self.frame_analyzer.analyze_video_content(frames)
            
            # Extract transcript (if available)
            transcript = self.transcript_analyzer.extract_transcript(video_path)
            
            # Generate catchy text based on content
            if transcript:
                text_result = self.transcript_analyzer.generate_catchy_text_with_ai(
                    transcript=transcript,
                    video_context=video_context
                )
                generated_text = text_result.get("catchy_text", "Must-see viral content")
            else:
                # If no transcript, use frame analysis only
                frame_insights = self.frame_analyzer.get_frame_insights(frames)
                generated_text = frame_insights.get("suggested_caption", "Must-see viral content")
            
            logger.info(f"Generated text: '{generated_text}'")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return "Must-see viral content"  # Fallback text
    
    def enhance_video(
        self, 
        video_path: str, 
        output_path: str, 
        custom_text: Optional[str] = None,
        analyze_first: bool = True
    ) -> Dict[str, Any]:
        """
        Add text overlay to a video.
        
        Args:
            video_path: Path to the input video
            output_path: Path for the enhanced output video
            custom_text: Custom text to overlay (None to generate automatically)
            analyze_first: Whether to analyze the video first
            
        Returns:
            Dict with results including success status and metadata
        """
        if not os.path.exists(video_path):
            logger.error(f"Input video not found: {video_path}")
            return {"success": False, "error": "Input video not found"}
            
        if not self.dependencies_loaded:
            logger.error("Required dependencies not loaded")
            return {"success": False, "error": "Required dependencies not loaded"}
        
        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            # Get text for overlay
            if analyze_first or not custom_text:
                text = self.generate_text_for_video(video_path, custom_text)
            else:
                text = custom_text
            
            logger.info(f"Applying text overlay '{text}' to {video_path}")
            
            # Apply text overlay to video
            result = self.text_styler.apply_text_to_video(
                input_video=video_path,
                output_video=output_path,
                text=text,
                high_quality=self.high_quality
            )
            
            if not result or not os.path.exists(output_path):
                logger.error("Failed to apply text overlay")
                return {"success": False, "error": "Failed to apply text overlay"}
                
            logger.info(f"Text overlay successfully applied. Enhanced video saved to {output_path}")
            return {
                "success": True,
                "output_video": output_path,
                "text": text,
                "style": str(self.style),
                "position": str(self.position)
            }
            
        except Exception as e:
            logger.error(f"Error enhancing video with text: {e}")
            return {"success": False, "error": str(e)}
