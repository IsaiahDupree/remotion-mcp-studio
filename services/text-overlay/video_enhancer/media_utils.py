"""
Media Utilities Module
=====================

This module provides common media utility functions for video enhancement:
- FFmpeg wrappers for common operations
- Media file information extraction
- File format detection and handling
- Temporary file management

Used by other modules for reusable media processing functionality.
"""

import os
import re
import json
import logging
import tempfile
import subprocess
from typing import Dict, Any, Optional, Tuple, List, Union
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("media_utils")


class MediaUtils:
    """
    Utility class for common media operations used across video enhancement modules.
    
    This class provides functionality to:
    1. Extract media file information
    2. Run FFmpeg commands with proper error handling
    3. Create and manage temporary files
    4. Check system requirements
    """
    
    @staticmethod
    def check_ffmpeg_available() -> bool:
        """
        Check if FFmpeg and FFprobe are available on the system.
        
        Returns:
            True if both FFmpeg and FFprobe are available, False otherwise
        """
        try:
            # Check ffmpeg
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            # Check ffprobe
            subprocess.run(['ffprobe', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("FFmpeg or FFprobe not found. Please install FFmpeg with FFprobe.")
            return False
    
    @staticmethod
    def get_media_info(file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a media file using ffprobe.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            Dictionary with media information
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return {}
                
            # Run ffprobe command to get media information in JSON format
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.stdout:
                try:
                    media_info = json.loads(result.stdout)
                    
                    # Extract useful high-level information
                    info = {
                        'duration': float(media_info.get('format', {}).get('duration', 0)),
                        'size_bytes': int(media_info.get('format', {}).get('size', 0)),
                        'bitrate': int(media_info.get('format', {}).get('bit_rate', 0)),
                        'format': media_info.get('format', {}).get('format_name', ''),
                        'audio_streams': 0,
                        'video_streams': 0,
                        'width': 0,
                        'height': 0,
                        'audio_codec': '',
                        'video_codec': '',
                        'container': os.path.splitext(file_path)[1].strip('.').lower(),
                    }
                    
                    # Count streams by type and get details
                    for stream in media_info.get('streams', []):
                        stream_type = stream.get('codec_type')
                        
                        if stream_type == 'video':
                            info['video_streams'] += 1
                            # Get details from first video stream
                            if info['video_streams'] == 1:
                                info['width'] = int(stream.get('width', 0))
                                info['height'] = int(stream.get('height', 0))
                                info['video_codec'] = stream.get('codec_name', '')
                                info['frame_rate'] = eval(stream.get('r_frame_rate', '0/1'))
                                
                        elif stream_type == 'audio':
                            info['audio_streams'] += 1
                            # Get details from first audio stream
                            if info['audio_streams'] == 1:
                                info['audio_codec'] = stream.get('codec_name', '')
                                info['sample_rate'] = int(stream.get('sample_rate', 0))
                                info['channels'] = int(stream.get('channels', 0))
                    
                    return info
                    
                except json.JSONDecodeError:
                    logger.error("Failed to parse ffprobe output")
                    return {}
            else:
                logger.error("No output from ffprobe")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting media info: {e}")
            return {}
    
    @staticmethod
    def run_ffmpeg_command(cmd: List[str], timeout: int = 300) -> Tuple[bool, str]:
        """
        Run an FFmpeg command with proper error handling.
        
        Args:
            cmd: List of command arguments
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            logger.debug(f"Running FFmpeg command: {' '.join(cmd)}")
            
            # Run the command with timeout
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                timeout=timeout
            )
            
            # Check for errors in stderr
            if result.returncode != 0:
                error_msg = result.stderr
                logger.error(f"FFmpeg command failed with return code {result.returncode}: {error_msg}")
                return False, error_msg
            
            # Look for specific error messages in output
            for line in result.stderr.split('\n'):
                if 'Error' in line and 'No such file or directory' not in line:
                    logger.error(f"FFmpeg error: {line}")
                    return False, line
            
            return True, ""
            
        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg command timed out after {timeout} seconds")
            return False, f"Command timed out after {timeout} seconds"
            
        except Exception as e:
            logger.error(f"Error executing FFmpeg command: {e}")
            return False, str(e)
    
    @staticmethod
    def create_temp_dir() -> Tuple[str, Any]:
        """
        Create a temporary directory with a context manager.
        
        Returns:
            Tuple of (path, context_manager)
        """
        temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temporary directory: {temp_dir}")
        return temp_dir, None
        
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """
        Get the file extension without the dot.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File extension (e.g. 'mp4', 'mp3')
        """
        return os.path.splitext(file_path)[1].strip('.').lower()
        
    @staticmethod
    def ensure_dir_exists(dir_path: str) -> bool:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            dir_path: Path to the directory
            
        Returns:
            True if directory exists or was created, False on error
        """
        try:
            os.makedirs(dir_path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {dir_path}: {e}")
            return False
            
    @staticmethod
    def is_valid_media_file(file_path: str) -> bool:
        """
        Check if a file is a valid media file that ffmpeg can process.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if valid media file, False otherwise
        """
        if not os.path.exists(file_path) or os.path.getsize(file_path) < 1000:
            logger.warning(f"File does not exist or is too small: {file_path}")
            return False
            
        try:
            # Try to get media info
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',  # Check for at least one video stream
                '-show_entries', 'stream=codec_type',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                file_path
            ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # If we can read a video stream, it's a valid media file
            return 'video' in result.stdout.lower()
            
        except Exception as e:
            logger.error(f"Error checking if file is valid media: {e}")
            return False
    
    @staticmethod
    def get_video_dimensions(video_path: str) -> Tuple[int, int]:
        """
        Get the dimensions of a video.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Tuple of (width, height), (0, 0) on error
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=s=x:p=0',
                video_path
            ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if 'x' in result.stdout:
                width_str, height_str = result.stdout.strip().split('x')
                return int(width_str), int(height_str)
                
            return 0, 0
            
        except Exception as e:
            logger.error(f"Error getting video dimensions: {e}")
            return 0, 0
