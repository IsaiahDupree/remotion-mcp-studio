#!/usr/bin/env python3
"""
Enhanced Video Processor with Intelligent Text Placement and Audio Mixing
"""
import os
import subprocess
import json
import logging
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import shutil

from config import CACHE_DIR

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedVideoProcessor:
    """Enhanced video processor with smart text placement and audio mixing"""
    
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
    
    def detect_faces_in_video(self, video_path: str, sample_count: int = 5) -> List[Dict]:
        """
        Detect faces in video frames to avoid text placement over faces
        Returns list of face regions for smart text positioning
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.warning("Could not open video for face detection")
                return []
            
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            face_regions = []
            sample_frames = np.linspace(0, total_frames - 1, sample_count, dtype=int)
            
            for frame_idx in sample_frames:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    continue
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                height, width = frame.shape[:2]
                for (x, y, w, h) in faces:
                    # Normalize face coordinates (0-1 range)
                    face_regions.append({
                        'x': x / width,
                        'y': y / height,
                        'w': w / width,
                        'h': h / height,
                        'frame': frame_idx
                    })
            
            cap.release()
            return face_regions
            
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return []
    
    def calculate_smart_text_position(self, video_path: str, text_lines: List[str]) -> Dict:
        """
        Calculate optimal text position avoiding faces and important content
        Returns position parameters for FFmpeg
        """
        try:
            # Get video dimensions
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.warning("Could not get video info, using default position")
                return self._get_default_position(text_lines)
            
            info = json.loads(result.stdout)
            video_stream = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
            
            if not video_stream:
                return self._get_default_position(text_lines)
            
            width = int(video_stream.get('width', 1920))
            height = int(video_stream.get('height', 1080))
            
            # Detect faces to avoid placing text over them
            face_regions = self.detect_faces_in_video(video_path)
            
            # Calculate safe zones
            safe_zones = [
                {'name': 'top', 'y_ratio': 0.05, 'priority': 1},      # Top 5%
                {'name': 'upper', 'y_ratio': 0.15, 'priority': 2},    # Upper 15%
                {'name': 'bottom', 'y_ratio': 0.85, 'priority': 3},   # Bottom 15%
                {'name': 'center', 'y_ratio': 0.5, 'priority': 4}     # Center (last resort)
            ]
            
            # Check which zones are clear of faces
            for zone in safe_zones:
                zone_clear = True
                zone_y = zone['y_ratio']
                
                # Check if this zone conflicts with faces
                for face in face_regions:
                    face_top = face['y']
                    face_bottom = face['y'] + face['h']
                    
                    # Check if zone overlaps with face region
                    if (zone_y >= face_top - 0.1 and zone_y <= face_bottom + 0.1):
                        zone_clear = False
                        break
                
                if zone_clear:
                    # Use this zone
                    return self._format_position_for_ffmpeg(zone, text_lines, width, height)
            
            # If all zones have faces, use top (most likely to be clear)
            return self._format_position_for_ffmpeg(safe_zones[0], text_lines, width, height)
            
        except Exception as e:
            logger.error(f"Smart positioning failed: {e}")
            return self._get_default_position(text_lines)
    
    def _get_default_position(self, text_lines: List[str]) -> Dict:
        """Default text position when smart detection fails"""
        return {
            'y_position': '20',  # Top of video
            'x_position': '(w-text_w)/2',  # Centered horizontally
            'font_size': '32',
            'position_name': 'top_center'
        }
    
    def _format_position_for_ffmpeg(self, zone: Dict, text_lines: List[str], width: int, height: int) -> Dict:
        """Format position data for FFmpeg text overlay"""
        font_size = max(24, int(height * 0.035))  # 3.5% of video height
        
        if zone['name'] == 'top':
            y_pos = "20"
        elif zone['name'] == 'upper':
            y_pos = f"{int(height * 0.15)}"
        elif zone['name'] == 'bottom':
            y_pos = f"h-{len(text_lines) * font_size * 1.5}-20"
        else:  # center
            y_pos = f"(h-{len(text_lines) * font_size * 1.5})/2"
        
        return {
            'y_position': y_pos,
            'x_position': '(w-text_w)/2',  # Always center horizontally
            'font_size': str(font_size),
            'position_name': zone['name']
        }
    
    def get_optimal_text_size(self, text_lines: List[str], video_width: int, video_height: int) -> int:
        """
        Calculate optimal text size based on video dimensions and text content
        Ensures text is readable but doesn't overflow screen
        """
        try:
            # Base size calculation based on video resolution
            base_size = min(video_width, video_height) // 20  # Start with 1/20th of smaller dimension
            
            # Adjust based on text length - longer text gets smaller
            max_text_length = max(len(line) for line in text_lines) if text_lines else 20
            
            if max_text_length <= 10:
                size_multiplier = 1.2  # Short text can be bigger
            elif max_text_length <= 20:
                size_multiplier = 1.0  # Medium text - base size
            elif max_text_length <= 30:
                size_multiplier = 0.8  # Long text gets smaller
            else:
                size_multiplier = 0.6  # Very long text gets much smaller
            
            optimal_size = int(base_size * size_multiplier)
            
            # Ensure minimum readable size and maximum reasonable size
            min_size = max(24, video_height // 40)  # At least 24px or 1/40th of height
            max_size = min(120, video_height // 8)  # Max 120px or 1/8th of height
            
            optimal_size = max(min_size, min(optimal_size, max_size))
            
            logger.info(f"📐 Optimal text size: {optimal_size}px (video: {video_width}x{video_height}, max_length: {max_text_length})")
            return optimal_size
            
        except Exception as e:
            logger.error(f"Error calculating text size: {e}")
            return 48  # Safe fallback size
    
    def get_available_fonts(self) -> List[Dict]:
        """
        Get list of available fonts including custom fonts
        """
        # Define base path for shared fonts (for n8n compatibility)
        shared_fonts_path = Path(__file__).parent.parent / 'shared' / 'fonts'
        
        fonts = [
            # Creative/Fun Fonts
            {
                'name': 'Sunny Spells',
                'path': str(shared_fonts_path / 'sunny-spells' / 'SunnyspellsRegular-MV9ze.otf'),
                'style': 'creative',
                'description': 'Fun and energetic display font'
            },
            {
                'name': 'Edge of Galaxy',
                'path': str(shared_fonts_path / 'edge-of-galaxy' / 'EdgeOfTheGalaxyRegular-OVEa6.otf'),
                'style': 'creative',
                'description': 'Futuristic space-themed font'
            },
            {
                'name': 'Edge of Galaxy Poster',
                'path': str(shared_fonts_path / 'edge-of-galaxy' / 'EdgeOfTheGalaxyPoster-3zRAp.otf'),
                'style': 'bold',
                'description': 'Bold futuristic poster font'
            },
            # Bold/Strong Fonts
            {
                'name': 'Mountain King',
                'path': str(shared_fonts_path / 'mountain-king' / 'MountainKingRegular-woBYn.ttf'),
                'style': 'bold',
                'description': 'Strong mountain-inspired font'
            },
            {
                'name': 'Rony Siswadi Bold',
                'path': str(shared_fonts_path / 'rony-siswadi' / 'Ronysiswadi16Bold-axmdm.ttf'),
                'style': 'bold',
                'description': 'Bold modern sans-serif'
            },
            {
                'name': 'Rony Siswadi Black',
                'path': str(shared_fonts_path / 'rony-siswadi' / 'Ronysiswadi16Black-WyB8G.ttf'),
                'style': 'bold',
                'description': 'Extra bold black weight'
            },
            # Clean/Modern Fonts
            {
                'name': 'Rony Siswadi',
                'path': str(shared_fonts_path / 'rony-siswadi' / 'Ronysiswadi16-EaD2j.ttf'),
                'style': 'clean',
                'description': 'Clean modern sans-serif'
            },
            # System Fonts
            {
                'name': 'Arial Bold',
                'path': 'Arial-Bold',  # System font
                'style': 'clean',
                'description': 'Clean and professional'
            },
            {
                'name': 'Impact',
                'path': 'Impact',  # System font
                'style': 'bold',
                'description': 'Strong and impactful'
            },
            {
                'name': 'Segoe UI',
                'path': 'Segoe UI',  # System font
                'style': 'modern',
                'description': 'Modern and readable'
            }
        ]
        
        # Check which custom fonts exist
        available_fonts = []
        for font in fonts:
            if font['path'].endswith('.otf') or font['path'].endswith('.ttf') or '\\' in font['path'] or '/' in font['path']:
                # Custom font - check if file exists
                if Path(font['path']).exists():
                    available_fonts.append(font)
                    logger.info(f"✅ Custom font available: {font['name']}")
                else:
                    logger.warning(f"❌ Custom font missing: {font['name']} at {font['path']}")
            else:
                # System font - assume available
                available_fonts.append(font)
        
        return available_fonts
    
    def select_best_font(self, text_content: str, style_preference: str = 'auto') -> Dict:
        """
        Select the best font based on text content and style preference
        """
        available_fonts = self.get_available_fonts()
        
        if style_preference == 'auto':
            # Auto-select based on text content
            text_lower = text_content.lower()
            
            if any(word in text_lower for word in ['fun', 'creative', 'happy', 'joy', 'celebrate', 'party']):
                preferred_style = 'creative'
            elif any(word in text_lower for word in ['power', 'strong', 'bold', 'impact', 'force']):
                preferred_style = 'bold'
            elif any(word in text_lower for word in ['professional', 'business', 'corporate', 'work']):
                preferred_style = 'clean'
            else:
                preferred_style = 'modern'
        else:
            preferred_style = style_preference
        
        # Find font matching preferred style
        for font in available_fonts:
            if font['style'] == preferred_style:
                logger.info(f"🎨 Selected {preferred_style} font: {font['name']}")
                return font
        
        # Fallback to first available font
        if available_fonts:
            font = available_fonts[0]
            logger.info(f"🎨 Using fallback font: {font['name']}")
            return font
        
        # Ultimate fallback
        return {
            'name': 'Arial',
            'path': 'Arial',
            'style': 'default',
            'description': 'System default'
        }
    
    def sanitize_text_for_ffmpeg(self, text):
        """
        Sanitize text for FFmpeg drawtext filter
        """
        import re
        
        # Remove or replace problematic characters
        # Remove emojis and other unicode characters that FFmpeg can't handle
        text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII characters
        
        # Escape special characters for FFmpeg
        text = text.replace("'", "\\'")
        text = text.replace(":", "\\:")
        text = text.replace("\\", "/")
        
        return text.strip()
    
    def escape_font_path_for_ffmpeg(self, font_path):
        """
        Properly escape font file path for FFmpeg on Windows
        """
        if font_path.endswith(('.ttf', '.otf')):
            # Convert Windows backslashes to forward slashes for FFmpeg
            font_path = font_path.replace('\\', '/')
            # Ensure path is properly escaped
            font_path = font_path.replace(':', '\\:')
        return font_path
    
    def create_enhanced_text_overlay(self, text_lines, position_data, video_width=None, video_height=None, font_style='auto'):
        """
        Create enhanced text overlay with custom fonts and dynamic sizing
        """
        if not text_lines:
            return ""

        # Get optimal text size
        font_size = self.get_optimal_text_size(text_lines, video_width or 720, video_height or 1280)
        logger.info(f"📐 Optimal text size: {font_size}px (video: {video_width or 720}x{video_height or 1280}, max_length: {max(len(line) for line in text_lines)})")

        # Select best font
        text_content = ' '.join(text_lines)
        selected_font = self.select_best_font(text_content, font_style)

        drawtext_filters = []
        y_offset = 20  # Starting position
        line_spacing = font_size * 1.5  # 1.5x font size for line spacing

        for i, text in enumerate(text_lines):
            # Sanitize text for FFmpeg
            safe_text = self.sanitize_text_for_ffmpeg(text)
            if not safe_text.strip():  # Skip empty lines after sanitization
                continue

            # Calculate position
            y_pos = y_offset + (i * line_spacing)

            # Font configuration
            if selected_font['path'].endswith(('.ttf', '.otf')):
                # Custom font file - properly escape path
                escaped_path = self.escape_font_path_for_ffmpeg(selected_font['path'])
                logger.info(f"🎨 Using custom font: {selected_font['name']} at {escaped_path}")
                font_config = f"fontfile={escaped_path}"
            else:
                # System font
                logger.info(f"💻 Using system font: {selected_font['name']}")
                font_config = f"font={selected_font['path']}"

            # Create drawtext filter with enhanced styling
            border_width = max(2, font_size // 20)  # Dynamic border width
            box_border_width = max(2, font_size // 15)  # Dynamic box border width

            drawtext_filter = (
                f"drawtext=text='{safe_text}':"
                f"fontsize={font_size}:"
                f"{font_config}:"
                f"fontcolor=white:"
                f"x=(w-text_w)/2:"
                f"y={y_pos}:"
                f"borderw={border_width}:"
                f"bordercolor=black:"
                f"box=1:"
                f"boxcolor=black@0.5:"
                f"boxborderw={box_border_width}"
            )

            drawtext_filters.append(drawtext_filter)

        return ','.join(drawtext_filters)

    def process_video_with_enhanced_features(self,
                                           video_path: str,
                                           music_path: str,
                                           text_lines: List[str],
                                           output_path: str,
                                           music_volume_db: float = -25.0,
                                           preserve_audio: bool = True,
                                           smart_positioning: bool = True,
                                           font_style: str = 'auto') -> bool:
        """
        Enhanced video processing with smart text placement and proper audio mixing

        Args:
            video_path: Input video file path
            music_path: Background music file path
            text_lines: List of text lines to overlay
            output_path: Output video file path
            music_volume_db: Music volume in dB (-20 to -30 recommended)
            preserve_audio: Keep original video audio
            smart_positioning: Use intelligent text positioning
            font_style: Font style ('auto', 'creative', 'bold', 'clean', 'modern')
        """
        try:
            logger.info(f"Processing video with enhanced features: {Path(video_path).name}")

            # Validate inputs
            if not Path(video_path).exists():
                logger.error(f"Video file not found: {video_path}")
                return False

            if not Path(music_path).exists():
                logger.error(f"Music file not found: {music_path}")
                return False
            
            # Get video dimensions for optimal text sizing
            video_info = self.get_video_info(video_path)
            video_width = video_info.get('width', 1920)
            video_height = video_info.get('height', 1080)
            
            logger.info(f"📐 Video dimensions: {video_width}x{video_height}")
            
            # Get smart text positioning
            if smart_positioning and text_lines:
                position_data = self.calculate_smart_text_position(video_path, text_lines)
                text_filter = self.create_enhanced_text_overlay(
                    text_lines, position_data, video_width, video_height, font_style
                )
                logger.info(f"Using smart positioning: {position_data['position_name']}")
            else:
                # Fallback to simple positioning
                position_data = self._get_default_position(text_lines)
                text_filter = self.create_enhanced_text_overlay(
                    text_lines, position_data, video_width, video_height, font_style
                )
            
            # Build FFmpeg command with enhanced audio mixing
            cmd = [self.ffmpeg_path, '-y']  # -y to overwrite output
            
            # Input files
            cmd.extend(['-i', video_path])    # Video input
            cmd.extend(['-i', music_path])    # Music input
            
            # Enhanced audio mixing
            if preserve_audio:
                # Mix original audio with background music
                audio_filter = (
                    f"[0:a]volume=1.0[original_audio];"
                    f"[1:a]volume={10**(music_volume_db/20):.4f}[bg_music];"
                    f"[original_audio][bg_music]amix=inputs=2:duration=first:dropout_transition=2[mixed_audio]"
                )
                cmd.extend(['-filter_complex', f"{audio_filter};[0:v]{text_filter}[video_out]"])
                cmd.extend(['-map', '[video_out]', '-map', '[mixed_audio]'])
            else:
                # Only background music
                audio_filter = f"[1:a]volume={10**(music_volume_db/20):.4f}[bg_music]"
                cmd.extend(['-filter_complex', f"{audio_filter};[0:v]{text_filter}[video_out]"])
                cmd.extend(['-map', '[video_out]', '-map', '[bg_music]'])
            
            # Output settings optimized for quality and compatibility
            cmd.extend([
                '-c:v', 'libx264',           # H.264 video codec
                '-preset', 'medium',         # Encoding speed vs compression
                '-crf', '23',               # Quality setting (18-28 range)
                '-c:a', 'aac',              # AAC audio codec
                '-b:a', '192k',             # Audio bitrate
                '-movflags', '+faststart',   # Web optimization
                '-pix_fmt', 'yuv420p',      # Compatibility
                output_path
            ])
            
            logger.info("Starting enhanced video processing...")
            logger.info(f"Music volume: {music_volume_db}dB")
            logger.info(f"Text position: {position_data['position_name']}")
            logger.info(f"Preserve audio: {preserve_audio}")
            
            # Execute FFmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("✅ Enhanced video processing completed successfully")
                return True
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Video processing timed out")
            return False
        except Exception as e:
            logger.error(f"Error in enhanced video processing: {e}")
            return False
    
    def get_video_info(self, video_path: str) -> Dict:
        """Get comprehensive video information"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            return {}
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return {}

if __name__ == "__main__":
    # Test enhanced video processor
    processor = EnhancedVideoProcessor()
    
    test_video = "test_input.mp4"
    test_music = "test_music.mp3"
    test_output = "test_enhanced_output.mp4"
    test_text = ["Enhanced Video Processing", "Smart Text Placement"]
    
    if Path(test_video).exists() and Path(test_music).exists():
        success = processor.process_video_with_enhanced_features(
            video_path=test_video,
            music_path=test_music,
            text_lines=test_text,
            output_path=test_output,
            music_volume_db=-25.0,
            preserve_audio=True,
            smart_positioning=True
        )
        print(f"Enhanced processing result: {success}")
    else:
        print("Test files not found")
