#!/usr/bin/env python3
"""
Video Processor - Apply music and text overlays to videos
"""
import os
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import shutil

from config import CACHE_DIR

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoProcessor:
    """Process videos with music and text overlays using FFmpeg"""
    
    def __init__(self):
        self.temp_dir = CACHE_DIR / "temp_video"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Check FFmpeg availability
        self.ffmpeg_path = self._find_ffmpeg()
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable"""
        try:
            # Try common locations
            for cmd in ['ffmpeg', 'ffmpeg.exe', '/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg']:
                try:
                    result = subprocess.run([cmd, '-version'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        logger.info(f"Found FFmpeg: {cmd}")
                        return cmd
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            return None
        except Exception as e:
            logger.error(f"Error finding FFmpeg: {e}")
            return None
    
    def get_video_info(self, video_path: str) -> Dict:
        """Get video information using FFprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                raise RuntimeError(f"FFprobe failed: {result.stderr}")
            
            info = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = None
            for stream in info['streams']:
                if stream['codec_type'] == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                raise RuntimeError("No video stream found")
            
            return {
                'duration': float(info['format']['duration']),
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'fps': eval(video_stream['r_frame_rate']),  # Convert fraction to float
                'codec': video_stream['codec_name'],
                'bitrate': int(info['format'].get('bit_rate', 0))
            }
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return {}
    
    def create_text_overlay_filter(self, 
                                  text_lines: List[str],
                                  video_width: int,
                                  video_height: int,
                                  font_size: int = None,
                                  position: str = 'bottom') -> str:
        """Create FFmpeg text overlay filter"""
        
        if not text_lines:
            return ""
        
        # Auto-calculate font size based on video resolution
        if font_size is None:
            font_size = max(24, int(video_height * 0.04))  # 4% of video height
        
        # Position settings
        if position == 'bottom':
            y_start = f"h-{len(text_lines) * font_size * 1.5}-20"
        elif position == 'top':
            y_start = "20"
        elif position == 'center':
            y_start = f"(h-{len(text_lines) * font_size * 1.5})/2"
        else:
            y_start = "20"
        
        # Create text filter for each line
        text_filters = []
        for i, line in enumerate(text_lines):
            # Escape special characters for FFmpeg
            escaped_text = line.replace("'", "'\\\\\\''").replace(":", "\\:")
            
            y_pos = f"{y_start}+{i * font_size * 1.5}"
            
            text_filter = (
                f"drawtext=text='{escaped_text}'"
                f":fontsize={font_size}"
                f":fontcolor=white"
                f":x=(w-text_w)/2"  # Center horizontally
                f":y={y_pos}"
                f":box=1"
                f":boxcolor=black@0.7"
                f":boxborderw=5"
            )
            text_filters.append(text_filter)
        
        return ",".join(text_filters)
    
    def process_video_with_music_and_text(self,
                                        video_path: str,
                                        music_path: str,
                                        text_lines: List[str],
                                        output_path: str,
                                        music_volume_db: float = -25.0,
                                        text_position: str = 'bottom',
                                        preserve_audio: bool = True) -> bool:
        """
        Process video with background music and text overlay
        
        Args:
            video_path: Input video file path
            music_path: Background music file path
            text_lines: List of text lines to overlay
            output_path: Output video file path
            music_volume_db: Music volume in dB (negative = quieter)
            text_position: Text position ('top', 'bottom', 'center')
            preserve_audio: Whether to preserve original video audio
        """
        try:
            logger.info(f"Processing video: {Path(video_path).name}")
            logger.info(f"Music: {Path(music_path).name}")
            logger.info(f"Text lines: {len(text_lines)}")
            
            # Get video info
            video_info = self.get_video_info(video_path)
            if not video_info:
                raise RuntimeError("Could not get video information")
            
            video_duration = video_info['duration']
            video_width = video_info['width']
            video_height = video_info['height']
            
            logger.info(f"Video: {video_width}x{video_height}, {video_duration:.1f}s")
            
            # Build FFmpeg command
            cmd = [self.ffmpeg_path, '-y']  # -y to overwrite output
            
            # Input files
            cmd.extend(['-i', video_path])  # Video input
            cmd.extend(['-i', music_path])  # Music input
            
            # Video filters
            filters = []
            
            # Text overlay filter
            if text_lines:
                text_filter = self.create_text_overlay_filter(
                    text_lines, video_width, video_height, position=text_position
                )
                if text_filter:
                    filters.append(f"[0:v]{text_filter}[v]")
            
            # Audio mixing
            if preserve_audio:
                # Mix original audio with background music
                audio_filter = (
                    f"[1:a]volume={music_volume_db}dB[music];"
                    f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[audio]"
                )
            else:
                # Use only background music
                audio_filter = f"[1:a]volume={music_volume_db}dB[audio]"
            
            filters.append(audio_filter)
            
            # Apply filters
            if filters:
                cmd.extend(['-filter_complex', ';'.join(filters)])
                
                # Map outputs
                if text_lines:
                    cmd.extend(['-map', '[v]'])  # Video with text
                else:
                    cmd.extend(['-map', '0:v'])  # Original video
                
                cmd.extend(['-map', '[audio]'])  # Mixed audio
            else:
                # No filters, just copy
                cmd.extend(['-c:v', 'copy', '-c:a', 'copy'])
            
            # Output settings
            cmd.extend([
                '-c:v', 'libx264',  # Video codec
                '-preset', 'medium',  # Encoding speed vs quality
                '-crf', '23',  # Quality (lower = better)
                '-c:a', 'aac',  # Audio codec
                '-b:a', '128k',  # Audio bitrate
                '-shortest',  # Stop when shortest input ends
                output_path
            ])
            
            logger.info("Starting FFmpeg processing...")
            logger.debug(f"FFmpeg command: {' '.join(cmd)}")
            
            # Run FFmpeg
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=video_duration * 5 + 300  # Allow extra time
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg failed: {result.stderr}")
                return False
            
            # Verify output file
            if not Path(output_path).exists():
                logger.error("Output file was not created")
                return False
            
            output_size = Path(output_path).stat().st_size
            if output_size < 1024:  # Less than 1KB
                logger.error("Output file is too small, probably corrupt")
                return False
            
            logger.info(f"✅ Video processing complete: {Path(output_path).name}")
            logger.info(f"   Output size: {output_size / (1024*1024):.1f}MB")
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg processing timed out")
            return False
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return False
    
    def batch_process_videos(self,
                           video_music_pairs: List[Dict],
                           output_dir: str,
                           music_volume_db: float = -25.0) -> Dict:
        """
        Batch process multiple videos
        
        Args:
            video_music_pairs: List of dicts with 'video_path', 'music_path', 'text_lines', 'output_name'
            output_dir: Output directory
            music_volume_db: Music volume in dB
        """
        results = {
            'processed': 0,
            'failed': 0,
            'outputs': []
        }
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for i, pair in enumerate(video_music_pairs, 1):
            try:
                logger.info(f"\n--- Processing video {i}/{len(video_music_pairs)} ---")
                
                video_path = pair['video_path']
                music_path = pair['music_path']
                text_lines = pair.get('text_lines', [])
                output_name = pair.get('output_name', f"processed_video_{i}.mp4")
                
                output_file = output_path / output_name
                
                success = self.process_video_with_music_and_text(
                    video_path=video_path,
                    music_path=music_path,
                    text_lines=text_lines,
                    output_path=str(output_file),
                    music_volume_db=music_volume_db
                )
                
                if success:
                    results['processed'] += 1
                    results['outputs'].append(str(output_file))
                    logger.info(f"✅ Success: {output_name}")
                else:
                    results['failed'] += 1
                    logger.error(f"❌ Failed: {output_name}")
                
            except Exception as e:
                logger.error(f"Error processing pair {i}: {e}")
                results['failed'] += 1
        
        logger.info(f"\n📊 Batch processing complete:")
        logger.info(f"   ✅ Processed: {results['processed']}")
        logger.info(f"   ❌ Failed: {results['failed']}")
        
        return results
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(exist_ok=True)
                logger.info("🧹 Temporary files cleaned up")
        except Exception as e:
            logger.warning(f"Error cleaning temp files: {e}")

if __name__ == "__main__":
    # Test video processor
    processor = VideoProcessor()
    
    print("🎬 Video Processor Test")
    print(f"FFmpeg found: {processor.ffmpeg_path}")
    
    # Example usage (uncomment to test)
    # processor.process_video_with_music_and_text(
    #     video_path="test_video.mp4",
    #     music_path="test_music.mp3",
    #     text_lines=["Hello World", "This is a test"],
    #     output_path="output_video.mp4",
    #     music_volume_db=-25
    # )
