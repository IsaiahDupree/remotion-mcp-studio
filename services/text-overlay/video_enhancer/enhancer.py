"""
Video Enhancement Orchestrator
============================

This module provides a unified interface for enhancing videos with both text overlays 
and background music. It orchestrates the text overlay and music enhancement modules.

Classes:
    VideoEnhancer: Main class for enhancing videos with both text and music
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

# Import module components
from .text_overlay import TextOverlayEnhancer
from .music_enhancer import MusicEnhancer

# Try to import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from video_context_analyzer.styling import Style, Position
except ImportError:
    # Define fallback enums if imports fail
    from enum import Enum, auto
    class Style(Enum):
        BLACK_BG_WHITE_TEXT = auto()
        
    class Position(Enum):
        TOP = auto()
        CENTER = auto()
        BOTTOM = auto()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("video_enhancer")


class VideoEnhancer:
    """
    Class for enhancing videos with text overlays and background music.
    
    This class orchestrates the entire video enhancement process including:
    1. Text overlay enhancement (adding catchy text with customizable style)
    2. Music enhancement (adding background music with speech emphasis)
    3. Auto-detection of existing features to prevent redundant processing
    4. Batch processing capabilities
    
    Attributes:
        output_dir (str): Directory for output files
        text_enhancer (TextOverlayEnhancer): Text overlay component
        music_enhancer (MusicEnhancer): Music enhancement component
        openai_api_key (str): OpenAI API key for AI-powered features
    """
    
    def __init__(
        self,
        output_dir: str = "./enhanced_videos",
        style: Style = Style.BLACK_BG_WHITE_TEXT,
        position: Position = Position.TOP,
        font_scale: float = 1.2,
        speech_emphasis: float = 1.5,
        high_quality: bool = True,
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize the VideoEnhancer.
        
        Args:
            output_dir: Directory for output files
            style: Text overlay style
            position: Text position on frame
            font_scale: Size of the text font
            speech_emphasis: Factor to emphasize speech (higher = quieter music)
            high_quality: Whether to preserve high video quality
            openai_api_key: OpenAI API key for AI-powered features
        """
        self.output_dir = output_dir
        
        # Set OpenAI API key if provided
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        elif "OPENAI_API_KEY" in os.environ:
            logger.info("Using OpenAI API key from environment variable")
        else:
            logger.warning("No OpenAI API key provided. AI-powered features will be limited.")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize components
        self.text_enhancer = TextOverlayEnhancer(
            style=style,
            position=position,
            font_scale=font_scale,
            high_quality=high_quality,
            openai_api_key=openai_api_key
        )
        
        self.music_enhancer = MusicEnhancer(
            output_dir=output_dir,
            speech_emphasis=speech_emphasis
        )
        
        logger.info("VideoEnhancer initialized successfully")
    
    def enhance_video(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        add_text: bool = True,
        add_music: bool = True,
        custom_text: Optional[str] = None,
        soundcloud_url: Optional[str] = None,
        music_path: Optional[str] = None,
        speech_emphasis: Optional[float] = None,
        analyze_first: bool = True,
        auto_detect_features: bool = True
    ) -> Dict[str, Any]:
        """
        Enhance a video with text overlay and/or background music.
        
        Args:
            video_path: Path to the input video
            output_path: Path for the final enhanced video (None for auto-generated)
            add_text: Whether to add text overlay
            add_music: Whether to add background music
            custom_text: Custom text overlay (None for auto-generation)
            soundcloud_url: URL to SoundCloud track (None to use music_path or sample)
            music_path: Path to existing music file (None to download or generate)
            speech_emphasis: Factor to emphasize speech (higher = quieter music)
            analyze_first: Whether to analyze the video before enhancement
            auto_detect_features: Whether to check for existing features
            
        Returns:
            Dict with results including success status and metadata
        """
        if not os.path.exists(video_path):
            logger.error(f"Input video not found: {video_path}")
            return {"success": False, "error": "Input video not found"}
        
        try:
            # Create auto-generated output path if not provided
            if not output_path:
                video_basename = os.path.basename(video_path).split('.')[0]
                output_path = os.path.join(self.output_dir, f"{video_basename}_enhanced.mp4")
            
            # Create intermediate paths for multi-step enhancement
            text_output_path = output_path
            if add_text and add_music:
                # If doing both enhancements, create an intermediate path for text overlay
                dirname, filename = os.path.split(output_path)
                text_output_path = os.path.join(dirname, f"{os.path.splitext(filename)[0]}_with_text.mp4")
            
            result = {"success": True}
            current_video = video_path
            
            # Step 1: Add text overlay if requested
            if add_text:
                logger.info(f"Adding text overlay to video: {video_path}")
                text_result = self.text_enhancer.enhance_video(
                    video_path=current_video,
                    output_path=text_output_path,
                    custom_text=custom_text,
                    analyze_first=analyze_first
                )
                
                if not text_result.get("success", False):
                    logger.error(f"Text overlay failed: {text_result.get('error', 'unknown error')}")
                    return text_result
                
                result.update({
                    "text_overlay_added": True,
                    "text": text_result.get("text", custom_text),
                    "text_output_path": text_output_path
                })
                
                # Update current video for next step
                current_video = text_output_path
            
            # Step 2: Add background music if requested
            if add_music:
                logger.info(f"Adding background music to video: {current_video}")
                music_result = self.music_enhancer.enhance_video_with_music(
                    video_path=current_video,
                    output_path=output_path,
                    soundcloud_url=soundcloud_url,
                    music_path=music_path,
                    speech_emphasis=speech_emphasis,
                    auto_detect_existing_music=auto_detect_features
                )
                
                if not music_result.get("success", False):
                    logger.error(f"Music enhancement failed: {music_result.get('error', 'unknown error')}")
                    # If text was added but music failed, still return the text-enhanced video
                    if add_text:
                        result["output_video"] = current_video
                        result["music_added"] = False
                        result["music_error"] = music_result.get("error", "unknown error")
                        return result
                    return music_result
                
                result.update({
                    "music_added": music_result.get("music_added", True),
                    "speech_emphasis": music_result.get("speech_emphasis", speech_emphasis),
                    "output_video": music_result.get("output_video", output_path)
                })
            elif add_text:
                # If only adding text, set output video to the text result
                result["output_video"] = current_video
            
            return result
            
        except Exception as e:
            logger.error(f"Error enhancing video: {e}")
            return {"success": False, "error": str(e)}
    
    def batch_enhance_videos(
        self,
        video_paths: List[str],
        add_text: bool = True,
        add_music: bool = True,
        custom_text: Optional[str] = None,
        soundcloud_url: Optional[str] = None,
        speech_emphasis: Optional[float] = None,
        output_dir: Optional[str] = None,
        analyze_first: bool = True,
        auto_detect_features: bool = True
    ) -> Dict[str, Any]:
        """
        Enhance multiple videos in batch mode.
        
        Args:
            video_paths: List of paths to input videos
            add_text: Whether to add text overlay
            add_music: Whether to add background music
            custom_text: Custom text overlay (None for auto-generation)
            soundcloud_url: URL to SoundCloud track (None to use sample music)
            speech_emphasis: Factor to emphasize speech (higher = quieter music)
            output_dir: Directory for output files (None to use instance output_dir)
            analyze_first: Whether to analyze videos before enhancement
            auto_detect_features: Whether to check for existing features
            
        Returns:
            Dict with results for each video
        """
        results = {"success": True, "videos": {}}
        success_count = 0
        
        # Use provided output directory or instance default
        output_directory = output_dir or self.output_dir
        
        # Download SoundCloud track once for all videos if URL provided
        shared_music_path = None
        if add_music and soundcloud_url:
            logger.info(f"Downloading shared music for batch processing: {soundcloud_url}")
            music_filename = "batch_music.mp3"
            shared_music_path = self.music_enhancer.download_music_from_soundcloud(soundcloud_url, music_filename)
            
            if not shared_music_path:
                logger.warning("Failed to download SoundCloud track. Will use individual music for each video.")
        
        # Process each video
        for i, video_path in enumerate(video_paths):
            if not os.path.exists(video_path):
                logger.warning(f"Video not found, skipping: {video_path}")
                results["videos"][video_path] = {"success": False, "error": "Video not found"}
                continue
                
            try:
                logger.info(f"Processing video {i+1}/{len(video_paths)}: {video_path}")
                
                # Create output path
                video_basename = os.path.basename(video_path).split('.')[0]
                output_path = os.path.join(output_directory, f"{video_basename}_enhanced.mp4")
                
                # Enhance video
                result = self.enhance_video(
                    video_path=video_path,
                    output_path=output_path,
                    add_text=add_text,
                    add_music=add_music,
                    custom_text=custom_text,
                    # Use shared music path if available, otherwise use URL
                    music_path=shared_music_path,
                    soundcloud_url=None if shared_music_path else soundcloud_url,
                    speech_emphasis=speech_emphasis,
                    analyze_first=analyze_first,
                    auto_detect_features=auto_detect_features
                )
                
                results["videos"][video_path] = result
                
                if result.get("success", False):
                    success_count += 1
                    logger.info(f"Successfully enhanced video: {output_path}")
                else:
                    logger.error(f"Failed to enhance video: {result.get('error', 'unknown error')}")
                
            except Exception as e:
                logger.error(f"Error processing video {video_path}: {e}")
                results["videos"][video_path] = {"success": False, "error": str(e)}
        
        # Update overall success stats
        results["total_videos"] = len(video_paths)
        results["successful_videos"] = success_count
        results["failed_videos"] = len(video_paths) - success_count
        
        return results
    
    def enhance_from_excel(
        self,
        excel_path: str,
        video_column: str,
        soundcloud_column: Optional[str] = None,
        text_column: Optional[str] = None,
        add_text: bool = True,
        add_music: bool = True,
        default_text: Optional[str] = None,
        default_soundcloud_url: Optional[str] = None,
        speech_emphasis: Optional[float] = None,
        analyze_first: bool = True,
        auto_detect_features: bool = True
    ) -> Dict[str, Any]:
        """
        Enhance videos listed in an Excel file.
        
        Args:
            excel_path: Path to Excel file containing video paths and options
            video_column: Name of column containing video paths
            soundcloud_column: Name of column with SoundCloud URLs (None to use default)
            text_column: Name of column with custom text (None to use default or auto-generate)
            add_text: Whether to add text overlay
            add_music: Whether to add background music
            default_text: Default text to use if text_column is None or empty
            default_soundcloud_url: Default SoundCloud URL if soundcloud_column is None or empty
            speech_emphasis: Factor to emphasize speech (higher = quieter music)
            analyze_first: Whether to analyze videos before enhancement
            auto_detect_features: Whether to check for existing features
            
        Returns:
            Dict with results for each video
        """
        try:
            # Import pandas here to avoid requiring it when not using this feature
            import pandas as pd
            
            if not os.path.exists(excel_path):
                logger.error(f"Excel file not found: {excel_path}")
                return {"success": False, "error": "Excel file not found"}
                
            # Read Excel file
            logger.info(f"Reading Excel file: {excel_path}")
            df = pd.read_excel(excel_path)
            
            if video_column not in df.columns:
                logger.error(f"Video column '{video_column}' not found in Excel file")
                return {"success": False, "error": f"Video column '{video_column}' not found"}
                
            # Prepare list of videos and options
            videos = []
            custom_texts = []
            soundcloud_urls = []
            
            for i, row in df.iterrows():
                video_path = row[video_column]
                
                # Skip invalid video paths
                if not isinstance(video_path, str) or not os.path.exists(video_path):
                    logger.warning(f"Invalid video path in row {i+1}, skipping: {video_path}")
                    continue
                
                videos.append(video_path)
                
                # Get custom text if column exists
                if text_column and text_column in df.columns and pd.notna(row[text_column]):
                    custom_texts.append(str(row[text_column]))
                else:
                    custom_texts.append(default_text)
                
                # Get SoundCloud URL if column exists
                if soundcloud_column and soundcloud_column in df.columns and pd.notna(row[soundcloud_column]):
                    url = row[soundcloud_column]
                    if isinstance(url, str) and 'soundcloud.com' in url.lower():
                        soundcloud_urls.append(url)
                    else:
                        soundcloud_urls.append(default_soundcloud_url)
                else:
                    soundcloud_urls.append(default_soundcloud_url)
            
            logger.info(f"Found {len(videos)} valid videos in Excel file")
            
            # Process each video with its specific options
            results = {"success": True, "videos": {}}
            success_count = 0
            
            for i, (video_path, custom_text, soundcloud_url) in enumerate(zip(videos, custom_texts, soundcloud_urls)):
                logger.info(f"Processing video {i+1}/{len(videos)}: {video_path}")
                
                # Create output path
                video_basename = os.path.basename(video_path).split('.')[0]
                output_path = os.path.join(self.output_dir, f"{video_basename}_enhanced.mp4")
                
                # Enhance video
                result = self.enhance_video(
                    video_path=video_path,
                    output_path=output_path,
                    add_text=add_text,
                    add_music=add_music,
                    custom_text=custom_text,
                    soundcloud_url=soundcloud_url,
                    speech_emphasis=speech_emphasis,
                    analyze_first=analyze_first,
                    auto_detect_features=auto_detect_features
                )
                
                results["videos"][video_path] = result
                
                if result.get("success", False):
                    success_count += 1
                    logger.info(f"Successfully enhanced video: {output_path}")
                else:
                    logger.error(f"Failed to enhance video: {result.get('error', 'unknown error')}")
            
            # Update overall success stats
            results["total_videos"] = len(videos)
            results["successful_videos"] = success_count
            results["failed_videos"] = len(videos) - success_count
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing Excel file: {e}")
            return {"success": False, "error": str(e)}
