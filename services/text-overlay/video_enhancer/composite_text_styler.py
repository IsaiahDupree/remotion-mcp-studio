"""
Composite Text Styler Module
============================

This module provides an efficient text overlay solution that combines
the best of MoviePy and Pillow for text overlays without requiring ImageMagick.
"""

import os
import sys
import time
import logging
import tempfile
from enum import Enum
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

try:
    from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    logging.warning("Required dependencies not available. Please install: pip install moviepy pillow numpy")

# Import enums from original styler for compatibility
from .text_styler import Style, Position

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("composite_text_styler")

class CompositeTextStyler:
    """
    Class for applying text overlays to videos efficiently using MoviePy and Pillow.
    
    This implementation avoids the need for ImageMagick.
    """
    
    def __init__(
        self,
        style: Style = Style.BLACK_BG_WHITE_TEXT,
        position: Position = Position.TOP,
        font_scale: float = 1.0,
        font_file: Optional[str] = None  # Path to a .ttf font file
    ):
        """
        Initialize the CompositeTextStyler.
        
        Args:
            style: Text overlay style
            position: Text position on frame
            font_scale: Size of the text font
            font_file: Path to a .ttf font file (optional)
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("Required dependencies not available. Please install: pip install moviepy pillow numpy")
            
        self.style = style
        self.position = position
        self.font_scale = font_scale
        
        # Try to locate a default font if none provided
        self.font_file = font_file
        if not font_file:
            # Use Arial if available (Windows), otherwise fall back to a system font
            windows_font = "C:\\Windows\\Fonts\\Arial.ttf"
            if os.path.exists(windows_font):
                self.font_file = windows_font
            else:
                # For other systems, use default
                self.font_file = None
    
    def _get_text_color(self) -> Tuple[int, int, int]:
        """Get text color based on style"""
        if self.style in [Style.BLACK_BG_WHITE_TEXT, Style.TRANSPARENT_BG_WHITE_TEXT]:
            return (255, 255, 255)  # White
        return (0, 0, 0)  # Black
    
    def _get_bg_color(self) -> Optional[Tuple[int, int, int]]:
        """Get background color based on style or None for transparent"""
        if self.style == Style.BLACK_BG_WHITE_TEXT:
            return (0, 0, 0)  # Black
        elif self.style == Style.WHITE_BG_BLACK_TEXT:
            return (255, 255, 255)  # White
        # Transparent for all other styles
        return None
    
    def _create_text_image(self, text: str, video_size: Tuple[int, int]) -> np.ndarray:
        """
        Create a transparent image with text rendered using PIL
        
        Args:
            text: Text to render
            video_size: Size of the video (width, height)
            
        Returns:
            Numpy array with the text rendered on transparent background
        """
        # Ensure we use the exact dimensions from the original video
        width, height = int(video_size[0]), int(video_size[1])
        logger.info(f"Original video resolution: {width}x{height}")
        
        # Calculate font size based on video dimensions and font scale
        font_size = int(min(width, height) * 0.05 * self.font_scale)
        
        # Create a PIL Image for the text with exact dimensions
        img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Try to use the specified font, or fall back to default
        try:
            if self.font_file:
                font = ImageFont.truetype(self.font_file, font_size)
            else:
                # Use default PIL font
                font = ImageFont.load_default()
                # Scale default font
                font_size = max(12, int(font_size / 3))  # Default font is small, scale appropriately
        except Exception as e:
            logger.warning(f"Error loading font, using default: {str(e)}")
            font = ImageFont.load_default()
        
        # Get text dimensions
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Calculate text position
        margin = int(20 * self.font_scale)
        
        # Center horizontally
        x = (width - text_width) // 2
        
        # Position vertically based on setting
        if self.position == Position.TOP:
            y = margin
        elif self.position == Position.CENTER:
            y = (height - text_height) // 2
        else:  # BOTTOM
            y = height - text_height - margin
        
        # Get colors
        text_color = self._get_text_color()
        bg_color = self._get_bg_color()
        
        # Draw background if needed
        if bg_color:
            padding = int(10 * self.font_scale)
            bg_rect = [
                x - padding, 
                y - padding,
                x + text_width + padding,
                y + text_height + padding
            ]
            draw.rectangle(bg_rect, fill=(*bg_color, 220))  # Slightly transparent background
        
        # Draw text
        draw.text((x, y), text, fill=(*text_color, 255), font=font)
        
        # Convert PIL image to numpy array
        return np.array(img)
    
    def apply_text_to_video(
        self,
        input_video: str,
        output_video: str,
        text: str,
        high_quality: bool = True
    ) -> bool:
        """
        Apply text overlay to a video using MoviePy with PIL text rendering.
        
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
            start_time = time.time()
            logger.info(f"Applying text overlay to video: {input_video}")
            
            # Load the video
            video = VideoFileClip(input_video)
            
            logger.info(f"Using text style: {self.style.name}")
            
            # Create text image with the same dimensions as video
            text_img = self._create_text_image(text, video.size)
            
            # Create a mask for the text (where alpha channel > 0)
            mask = text_img[:,:,3] > 0
            
            # Track progress with frame counter and timestamps
            frame_count = 0
            total_frames = int(video.fps * video.duration)
            last_log_time = time.time()
            log_interval = 1.0  # Log every second
            
            logger.info(f"Processing {total_frames} frames at {video.fps} fps")
            
            # Create a PIL Image for each frame with our text overlay
            def add_text_to_frame(get_frame, t):
                nonlocal frame_count, last_log_time
                
                # Get the original frame
                frame = get_frame(t)
                
                # Update counter and log progress periodically
                frame_count += 1
                current_time = time.time()
                if current_time - last_log_time > log_interval:
                    progress = (frame_count / total_frames) * 100
                    elapsed = current_time - start_time
                    eta = (elapsed / frame_count) * (total_frames - frame_count) if frame_count > 0 else 0
                    logger.info(f"Processed {frame_count}/{total_frames} frames ({progress:.1f}%) - ETA: {eta:.1f}s")
                    last_log_time = current_time
                
                # Convert frame to PIL Image
                frame_img = Image.fromarray(frame)
                
                # Create a PIL RGBA image from our text array
                text_rgba = Image.fromarray(text_img)
                
                # Composite the images
                result = Image.alpha_composite(frame_img.convert('RGBA'), text_rgba)
                
                # Convert back to RGB for video
                return np.array(result.convert('RGB'))
                
            # Create a new clip using our frame processing function
            # Ensure we maintain the exact same dimensions and fps
            final_clip = video.fl(lambda gf, t: add_text_to_frame(gf, t))
            
            # Explicitly preserve original video properties
            final_clip = final_clip.set_fps(video.fps)
            final_clip = final_clip.set_duration(video.duration)
            
            # Log original video properties for debugging
            logger.info(f"Original video properties: {video.w}x{video.h} @ {video.fps} fps, duration: {video.duration}s")
            logger.info(f"Final clip properties: {final_clip.w}x{final_clip.h} @ {final_clip.fps} fps, duration: {final_clip.duration}s")
            
            # Duration is automatically handled by the fl function
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)
            
            # Get original video properties to maintain format
            # Extract codec information and rotation metadata
            try:
                import subprocess
                
                # Get codec and bitrate
                cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 
                       'stream=codec_name,bit_rate', '-of', 'default=noprint_wrappers=1', input_video]
                output = subprocess.check_output(cmd).decode('utf-8').strip().split('\n')
                
                original_codec = None
                original_bitrate = None
                
                for line in output:
                    if line.startswith('codec_name='):
                        original_codec = line.split('=')[1].strip()
                    elif line.startswith('bit_rate='):
                        original_bitrate = line.split('=')[1].strip()
                
                # Get rotation metadata
                rotation_cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', 
                               '-show_entries', 'stream_side_data=rotation', '-of', 'default=noprint_wrappers=1:nokey=1', input_video]
                try:
                    rotation_output = subprocess.check_output(rotation_cmd).decode('utf-8').strip()
                    video_rotation = rotation_output if rotation_output else None
                    if video_rotation:
                        logger.info(f"Video rotation detected: {video_rotation}")
                except:
                    video_rotation = None
                
                # Clean any control characters
                if original_codec:
                    original_codec = original_codec.replace('\r', '').replace('\n', '').strip()
                if original_bitrate:
                    original_bitrate = original_bitrate.replace('\r', '').replace('\n', '').strip()
                    
                logger.info(f"Original video codec: {original_codec}, bitrate: {original_bitrate}, rotation: {video_rotation}")
            except Exception as e:
                logger.warning(f"Could not determine original codec: {str(e)}")
                original_codec = None
                original_bitrate = None
                video_rotation = None
            
            # Set encoding parameters, preferring original when available
            if original_codec and original_codec != 'hevc' and original_codec != 'h265':
                # Use libx264 instead of h264 for compatibility
                if original_codec == 'h264':
                    codec = 'libx264'
                else:
                    codec = original_codec
            else:
                codec = 'libx264'  # Default to h264 (using libx264 which is the encoder name)
                
            if original_bitrate and original_bitrate.isdigit() and int(original_bitrate) > 0:
                bitrate = original_bitrate
            else:
                bitrate = "8000k" if high_quality else "4000k"
                
            preset = "medium" if high_quality else "faster"
                
            logger.info(f"Writing enhanced video to: {output_video}")
            
            # Build FFmpeg parameters
            ffmpeg_params = [
                "-pix_fmt", "yuv420p",  # Standard pixel format for compatibility
                "-movflags", "+faststart",  # Optimize for web streaming
                "-s", f"{video.w}x{video.h}",  # Force exact output resolution
                "-aspect", f"{video.w}:{video.h}"  # Set aspect ratio to match dimensions
            ]
            
            # Write video with proper resolution preservation
            final_clip.write_videofile(
                output_video,
                codec=codec,
                bitrate=bitrate,
                audio_codec='aac',
                logger=None,  # Suppress MoviePy's progress bar
                ffmpeg_params=ffmpeg_params
            )
            
            # Post-process to copy rotation metadata if detected
            if video_rotation:
                logger.info(f"Post-processing to preserve rotation metadata: {video_rotation}")
                temp_output = output_video + ".temp.mp4"
                
                try:
                    # Use FFmpeg to copy rotation metadata
                    cmd = [
                        'ffmpeg', '-i', output_video, '-i', input_video,
                        '-map', '0:v:0', '-map', '0:a:0?',
                        '-map_metadata:s:v:0', '1:s:v:0',
                        '-c', 'copy',
                        '-y', temp_output
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    
                    # Replace original with metadata-preserved version
                    import shutil
                    shutil.move(temp_output, output_video)
                    logger.info(f"Rotation metadata preserved successfully")
                    
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to preserve rotation metadata: {e}")
                    # Clean up temp file if it exists
                    if os.path.exists(temp_output):
                        os.remove(temp_output)
                except Exception as e:
                    logger.warning(f"Error in rotation metadata preservation: {e}")
            
            # Close the clips to release resources
            video.close()
            final_clip.close()
            
            # Log processing statistics
            total_time = time.time() - start_time
            fps_processing = total_frames / total_time if total_time > 0 else 0
            logger.info(f"Text overlay complete in {total_time:.1f} seconds ({fps_processing:.1f} fps)")
            return True
            
        except Exception as e:
            logger.error(f"Error applying text overlay: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
