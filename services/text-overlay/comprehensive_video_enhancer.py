#!/usr/bin/env python3
"""
Comprehensive Video Enhancer
============================

Integrates AI analysis, transcript analysis, music enhancement, and text overlay
to create a complete video enhancement solution.

Features:
- AI-powered transcript analysis for catchy text generation
- SoundCloud music integration from Excel files
- Proper aspect ratio preservation
- Advanced speech detection and emphasis
- Configurable text styling and positioning
"""

import os
import sys
import logging
import argparse
import json
import random
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import cv2  # Add this import for resolution analysis

# Add project modules to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import existing modules
from video_context_analyzer.transcript_analysis.transcript_analyzer import TranscriptAnalyzer
from video_context_analyzer.frame_analysis.frame_analyzer import FrameAnalyzer
from video_enhancer.transcript_processor import TranscriptProcessor
from video_enhancer.improved_music_enhancer import ImprovedMusicEnhancer
from video_enhancer.composite_text_styler import CompositeTextStyler
from video_enhancer.text_styler import Style, Position
from utils.soundcloud_ytdlp import SoundCloudYtDlp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("comprehensive_video_enhancer.log")
    ]
)
logger = logging.getLogger("comprehensive_video_enhancer")

class VideoStyleConfig:
    """Configuration for video styling options"""
    
    def __init__(self):
        self.styles = {
            'classic': Style.BLACK_BG_WHITE_TEXT,
            'modern': Style.TRANSPARENT_BG_WHITE_TEXT,
            'elegant': Style.WHITE_BG_BLACK_TEXT,
            'minimal': Style.TRANSPARENT_BG_WHITE_TEXT
        }
        
        self.positions = {
            'top': Position.TOP,
            'center': Position.CENTER,
            'bottom': Position.BOTTOM
        }

class SoundCloudMusicSelector:
    """Music selection from SoundCloud URLs in Excel files"""
    
    def __init__(self, excel_path: str, track_column: str = "Track URL", music_dir: str = "enhanced_videos/music"):
        self.excel_path = excel_path
        self.track_column = track_column
        self.music_dir = music_dir
        self.df = None
        self.downloader = SoundCloudYtDlp(output_dir=music_dir)
        
        # Create music directory
        os.makedirs(music_dir, exist_ok=True)
        
        self._load_excel()
    
    def _load_excel(self):
        """Load and validate Excel file"""
        try:
            if not os.path.exists(self.excel_path):
                raise FileNotFoundError(f"Excel file not found: {self.excel_path}")
            
            self.df = pd.read_excel(self.excel_path)
            logger.info(f"Loaded Excel file with {len(self.df)} rows")
            
            # Find the correct column for track URLs
            if self.track_column not in self.df.columns:
                url_candidates = ['Track URL', 'URL', 'track_url', 'url', 'link', 'Link']
                for col in url_candidates:
                    if col in self.df.columns:
                        self.track_column = col
                        logger.info(f"Using column '{col}' for track URLs")
                        break
                else:
                    logger.warning(f"No URL column found. Available columns: {list(self.df.columns)}")
            
            # Filter valid SoundCloud URLs
            valid_tracks = self.df[self.track_column].dropna()
            soundcloud_tracks = valid_tracks[valid_tracks.str.contains('soundcloud.com', case=False, na=False)]
            logger.info(f"Found {len(soundcloud_tracks)} SoundCloud track URLs")
            
        except Exception as e:
            logger.error(f"Error loading Excel file: {str(e)}")
            raise
    
    def get_random_track_url(self) -> Optional[str]:
        """Get a random SoundCloud track URL"""
        if self.df is None or self.df.empty:
            return None
        
        # Filter SoundCloud URLs
        valid_tracks = self.df[self.track_column].dropna()
        soundcloud_tracks = valid_tracks[valid_tracks.str.contains('soundcloud.com', case=False, na=False)]
        
        if soundcloud_tracks.empty:
            logger.warning("No SoundCloud URLs found")
            return None
        
        selected_url = random.choice(soundcloud_tracks.tolist())
        logger.info(f"Selected random SoundCloud track: {selected_url}")
        return selected_url
    
    def download_track(self, url: str) -> Optional[str]:
        """Download a SoundCloud track and return the path"""
        try:
            logger.info(f"Downloading SoundCloud track: {url}")
            result = self.downloader.download_track(url)
            if result and os.path.exists(result):
                logger.info(f"Successfully downloaded: {result}")
                return result
            else:
                logger.error(f"Failed to download track: {url}")
                return None
        except Exception as e:
            logger.error(f"Error downloading track {url}: {str(e)}")
            return None
    
    def get_random_music_file(self) -> Optional[str]:
        """Get a random music file by downloading a random track"""
        url = self.get_random_track_url()
        if url:
            return self.download_track(url)
        return None

class ComprehensiveVideoEnhancer:
    """Main video enhancement class with AI analysis and music integration"""
    
    def __init__(self, api_key: Optional[str] = None, output_dir: str = "enhanced_videos"):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.output_dir = output_dir
        self.music_dir = os.path.join(output_dir, "music")
        
        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.music_dir, exist_ok=True)
        
        # Initialize components
        self.transcript_analyzer = TranscriptAnalyzer(api_key=self.api_key)
        self.frame_analyzer = FrameAnalyzer(api_key=self.api_key, frames_to_sample=6)  # Every ~10 seconds for 60s video
        self.transcript_processor = TranscriptProcessor(openai_api_key=self.api_key)
        self.music_enhancer = ImprovedMusicEnhancer(output_dir=output_dir, music_dir=self.music_dir)
        self.style_config = VideoStyleConfig()
        
        logger.info("Comprehensive Video Enhancer initialized")
    
    def get_video_resolution(self, video_path: str) -> Tuple[int, int]:
        """Get video resolution using FFprobe for consistency (encoded dimensions)"""
        try:
            import subprocess
            cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 
                   'stream=width,height', '-of', 'default=noprint_wrappers=1', video_path]
            output = subprocess.check_output(cmd).decode('utf-8').strip().split('\n')
            
            width = height = 0
            for line in output:
                if line.startswith('width='):
                    width = int(line.split('=')[1].strip())
                elif line.startswith('height='):
                    height = int(line.split('=')[1].strip())
            
            if width > 0 and height > 0:
                logger.info(f"Video encoded resolution: {width}x{height}")
                return width, height
            else:
                raise ValueError("Could not parse resolution")
                
        except Exception as e:
            logger.warning(f"FFprobe failed, falling back to OpenCV: {e}")
            # Fallback to OpenCV
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                logger.info(f"Video resolution (OpenCV): {width}x{height}")
                return width, height
            else:
                logger.error("Could not open video with OpenCV")
                return 1920, 1080  # Default fallback
    
    def create_working_copy(self, video_path: str) -> str:
        """Create a working copy of the original video to preserve the original"""
        try:
            import subprocess
            
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Generate working copy filename
            video_basename = os.path.splitext(os.path.basename(video_path))[0]
            working_copy = os.path.join(self.output_dir, f"{video_basename}_working_copy.mp4")
            
            # Copy the original video to working directory using FFmpeg to preserve all metadata
            cmd = [
                'ffmpeg', '-i', video_path,
                '-c', 'copy',  # Copy streams without re-encoding
                '-map_metadata', '0',  # Copy all metadata
                '-y', working_copy  # Overwrite if exists
            ]
            
            logger.info(f"Creating working copy: {working_copy}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Verify the copy was created successfully
            if os.path.exists(working_copy):
                # Verify resolution matches
                orig_w, orig_h = self.get_video_resolution(video_path)
                copy_w, copy_h = self.get_video_resolution(working_copy)
                
                if orig_w == copy_w and orig_h == copy_h:
                    logger.info(f"✅ Working copy created successfully: {copy_w}x{copy_h}")
                    return working_copy
                else:
                    logger.error(f"⚠️ Working copy resolution mismatch: {orig_w}x{orig_h} → {copy_w}x{copy_h}")
                    return video_path  # Fall back to original
            else:
                logger.error(f"Failed to create working copy")
                return video_path  # Fall back to original
                
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error creating working copy: {e}")
            logger.error(f"FFmpeg stderr: {e.stderr}")
            return video_path  # Fall back to original
        except Exception as e:
            logger.error(f"Error creating working copy: {e}")
            return video_path  # Fall back to original
    
    def analyze_video_content(self, video_path: str) -> Dict[str, Any]:
        """Analyze video content using transcript and frame analysis"""
        try:
            logger.info(f"Analyzing video content: {video_path}")
            
            # Step 1: Extract and analyze transcript
            transcript_result = self.transcript_processor.process_video_transcript(video_path)
            
            # Step 2: Analyze frames (every 10 seconds as requested)
            frame_result = self.frame_analyzer.analyze_video(video_path)
            
            # Combine results for comprehensive analysis
            combined_text = ""
            
            if transcript_result.get("success") and transcript_result.get("transcript"):
                transcript_text = transcript_result["transcript"]
                # Use transcript analyzer to generate catchy text
                transcript_analysis = self.transcript_analyzer.analyze_transcript(transcript_text)
                combined_text = transcript_analysis.get("catchy_text", "")
                logger.info(f"Transcript-based text: {combined_text}")
            
            # If transcript analysis failed or produced poor results, use frame analysis
            if not combined_text or len(combined_text.split()) < 2:
                frame_catchy_text = frame_result.get("catchy_text", "")
                if frame_catchy_text and len(frame_catchy_text.split()) >= 2:
                    combined_text = frame_catchy_text
                    logger.info(f"Frame-based text: {combined_text}")
            
            # Final fallback
            if not combined_text:
                combined_text = "Must-see amazing content"
            
            # Ensure text is concise (max 6 words as specified in transcript analyzer)
            words = combined_text.split()
            if len(words) > 6:
                combined_text = " ".join(words[:6])
            
            return {
                "catchy_text": combined_text,
                "transcript_result": transcript_result,
                "frame_result": frame_result,
                "analysis_method": "combined_ai_analysis"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing video content: {str(e)}")
            return {
                "catchy_text": "Amazing content you must see",
                "error": str(e),
                "analysis_method": "fallback"
            }
    
    def add_text_overlay(self, video_path: str, text: str, style_name: str = "modern", 
                        position_name: str = "top", font_scale: float = 2.0) -> str:
        """Add text overlay to video with proper aspect ratio preservation and responsive sizing"""
        try:
            # Get video resolution for responsive text sizing (use passed video_path which should be working copy)
            width, height = self.get_video_resolution(video_path)
            
            logger.info(f"Video resolution: {width}x{height}")
            
            # Calculate responsive font scale based on video resolution
            # Base scale for 1080p video, adjust proportionally
            base_width = 1920
            base_scale = 2.0
            responsive_font_scale = (width / base_width) * base_scale
            
            # Ensure minimum and maximum font scales
            responsive_font_scale = max(0.8, min(responsive_font_scale, 4.0))
            
            # Use provided font_scale as a multiplier
            final_font_scale = responsive_font_scale * (font_scale / 2.0)
            
            logger.info(f"Using responsive font scale: {final_font_scale} (base: {responsive_font_scale}, multiplier: {font_scale/2.0})")
            
            # Get style and position enums
            style = self.style_config.styles.get(style_name, Style.TRANSPARENT_BG_WHITE_TEXT)
            position = self.style_config.positions.get(position_name, Position.TOP)
            
            # Create text styler with responsive sizing
            text_styler = CompositeTextStyler(
                style=style,
                position=position,
                font_scale=final_font_scale
            )
            
            # Generate output path
            video_basename = os.path.splitext(os.path.basename(video_path))[0]
            text_output = os.path.join(self.output_dir, f"{video_basename.replace('_working_copy', '')}_with_text.mp4")
            
            logger.info(f"Adding text overlay: '{text}' to {video_path}")
            logger.info(f"Target resolution: {width}x{height}, Font scale: {final_font_scale}")
            
            # Apply text overlay with resolution preservation
            result = text_styler.apply_text_to_video(
                input_video=video_path,
                output_video=text_output,
                text=text,
                high_quality=True
            )
            
            if result and os.path.exists(text_output):
                # Verify output resolution matches input
                try:
                    output_w, output_h = self.get_video_resolution(text_output)
                    if output_w == width and output_h == height:
                        logger.info(f"✅ Resolution preserved: {output_w}x{output_h}")
                    else:
                        logger.warning(f"⚠️ Resolution changed: {width}x{height} → {output_w}x{output_h}")
                except Exception as e:
                    logger.warning(f"Could not verify output resolution: {e}")
                
                logger.info(f"Text overlay completed: {text_output}")
                return text_output
            else:
                logger.error("Text overlay failed")
                return video_path
                
        except Exception as e:
            logger.error(f"Error adding text overlay: {str(e)}")
            return video_path
    
    def add_background_music(self, video_path: str, music_excel: Optional[str] = None, 
                           music_file: Optional[str] = None, speech_emphasis: float = 0.7) -> str:
        """Add background music to video"""
        try:
            music_path = None
            
            # Get music from Excel file
            if music_excel and os.path.exists(music_excel):
                logger.info(f"Selecting music from Excel: {music_excel}")
                music_selector = SoundCloudMusicSelector(music_excel, music_dir=self.music_dir)
                music_path = music_selector.get_random_music_file()
            
            # Fallback to direct music file
            if not music_path and music_file and os.path.exists(music_file):
                music_path = music_file
            
            if not music_path:
                logger.warning("No music available, skipping music enhancement")
                return video_path
            
            # Generate output path
            video_basename = os.path.splitext(os.path.basename(video_path))[0]
            music_output = os.path.join(self.output_dir, f"{video_basename}_with_music.mp4")
            
            logger.info(f"Adding background music: {music_path}")
            
            # Add background music
            result = self.music_enhancer.add_background_music(
                video_path=video_path,
                music_path=music_path,
                output_path=music_output,
                speech_emphasis_factor=speech_emphasis
            )
            
            if result and os.path.exists(result):
                logger.info(f"Music enhancement completed: {result}")
                return result
            else:
                logger.error("Music enhancement failed")
                return video_path
                
        except Exception as e:
            logger.error(f"Error adding background music: {str(e)}")
            return video_path
    
    def enhance_video(self, video_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Complete video enhancement pipeline"""
        try:
            logger.info(f"Starting comprehensive video enhancement: {video_path}")
            
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            # Create a working copy of the original video
            working_copy = self.create_working_copy(video_path)
            
            current_video = working_copy
            enhancement_steps = []
            
            # Step 1: Analyze video content for AI-generated text
            analysis_result = self.analyze_video_content(video_path)
            catchy_text = config.get('custom_text') or analysis_result.get('catchy_text', 'Amazing content!')
            
            # Step 2: Add text overlay if requested
            if config.get('add_text', True):
                logger.info("Adding AI-generated text overlay")
                current_video = self.add_text_overlay(
                    video_path=working_copy,
                    text=catchy_text,
                    style_name=config.get('text_style', 'modern'),
                    position_name=config.get('text_position', 'top'),
                    font_scale=config.get('font_scale', 2.0)
                )
                enhancement_steps.append("text_overlay")
            
            # Step 3: Add background music if requested
            if config.get('add_music', False):
                logger.info("Adding background music")
                current_video = self.add_background_music(
                    video_path=current_video,
                    music_excel=config.get('music_excel'),
                    music_file=config.get('music_file'),
                    speech_emphasis=config.get('speech_emphasis', 0.7)
                )
                enhancement_steps.append("background_music")
            
            # Generate final output name
            video_basename = os.path.splitext(os.path.basename(video_path))[0]
            final_output = os.path.join(self.output_dir, f"{video_basename}_enhanced_complete.mp4")
            
            # Move final result to proper name (handle existing files)
            if current_video != video_path and os.path.exists(current_video):
                # Remove existing file if it exists
                if os.path.exists(final_output):
                    logger.info(f"Removing existing file: {final_output}")
                    os.remove(final_output)
                
                # Move the file
                import shutil
                shutil.move(current_video, final_output)
                current_video = final_output
                logger.info(f"Final enhanced video saved: {final_output}")
            
            # Verify final video resolution matches original
            try:
                # Get original and final resolutions using same method (FFprobe)
                orig_w, orig_h = self.get_video_resolution(video_path)
                final_w, final_h = self.get_video_resolution(current_video)
                
                # Check for rotation metadata in both files
                try:
                    rotation_cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', 
                                   '-show_entries', 'stream_side_data=rotation', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
                    rotation_output = subprocess.check_output(rotation_cmd).decode('utf-8').strip()
                    original_rotation = rotation_output if rotation_output else None
                except:
                    original_rotation = None
                
                try:
                    rotation_cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', 
                                   '-show_entries', 'stream_side_data=rotation', '-of', 'default=noprint_wrappers=1:nokey=1', current_video]
                    rotation_output = subprocess.check_output(rotation_cmd).decode('utf-8').strip()
                    final_rotation = rotation_output if rotation_output else None
                except:
                    final_rotation = None
                
                # Resolution verification with rotation awareness
                if orig_w == final_w and orig_h == final_h:
                    rotation_status = ""
                    if original_rotation and final_rotation:
                        if original_rotation == final_rotation:
                            rotation_status = f" (rotation {final_rotation} preserved)"
                        else:
                            rotation_status = f" (rotation changed: {original_rotation} → {final_rotation})"
                    elif original_rotation and not final_rotation:
                        rotation_status = f" (original rotation {original_rotation} lost)"
                    elif not original_rotation and final_rotation:
                        rotation_status = f" (unexpected rotation {final_rotation} added)"
                    
                    logger.info(f"✅ Final resolution verification: {final_w}x{final_h} (preserved){rotation_status}")
                else:
                    logger.warning(f"⚠️ Resolution mismatch: {orig_w}x{orig_h} → {final_w}x{final_h}")
                    
            except Exception as e:
                logger.warning(f"Could not verify final resolution: {e}")
            
            return {
                "success": True,
                "input_video": video_path,
                "output_video": current_video,
                "catchy_text": catchy_text,
                "enhancement_steps": enhancement_steps,
                "analysis_result": analysis_result
            }
            
        except Exception as e:
            logger.error(f"Error in video enhancement: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "input_video": video_path
            }

def main():
    """Main command-line interface"""
    parser = argparse.ArgumentParser(description="Comprehensive Video Enhancer with AI and Music")
    
    # Input/Output
    parser.add_argument("--input", "-i", required=True, help="Input video file")
    parser.add_argument("--output-dir", default="enhanced_videos", help="Output directory")
    
    # Text overlay options
    parser.add_argument("--text-style", default="modern", 
                       choices=['classic', 'modern', 'elegant', 'minimal'],
                       help="Text overlay style")
    parser.add_argument("--text-position", default="top",
                       choices=['top', 'center', 'bottom'],
                       help="Text position")
    parser.add_argument("--font-scale", type=float, default=2.0, help="Font scale")
    parser.add_argument("--custom-text", help="Custom text (overrides AI generation)")
    parser.add_argument("--no-text", action="store_true", help="Skip text overlay")
    
    # Music options
    parser.add_argument("--music", action="store_true", help="Add background music")
    parser.add_argument("--music-excel", help="Excel file with SoundCloud URLs")
    parser.add_argument("--music-file", help="Direct path to music file")
    parser.add_argument("--speech-emphasis", type=float, default=0.7,
                       help="Speech emphasis factor (lower = quieter music)")
    
    # AI options
    parser.add_argument("--api-key", help="OpenAI API key (or use OPENAI_API_KEY env var)")
    
    args = parser.parse_args()
    
    try:
        # Initialize enhancer
        enhancer = ComprehensiveVideoEnhancer(
            api_key=args.api_key,
            output_dir=args.output_dir
        )
        
        # Configure enhancement
        config = {
            'add_text': not args.no_text,
            'text_style': args.text_style,
            'text_position': args.text_position,
            'font_scale': args.font_scale,
            'custom_text': args.custom_text,
            'add_music': args.music,
            'music_excel': args.music_excel,
            'music_file': args.music_file,
            'speech_emphasis': args.speech_emphasis
        }
        
        # Enhance video
        logger.info("Starting video enhancement...")
        result = enhancer.enhance_video(args.input, config)
        
        # Display results
        if result.get('success'):
            print("\n" + "="*50)
            print("🎉 VIDEO ENHANCEMENT COMPLETED!")
            print("="*50)
            print(f"📁 Input: {result['input_video']}")
            print(f"📁 Output: {result['output_video']}")
            print(f"💬 Text: {result['catchy_text']}")
            print(f"🔧 Steps: {', '.join(result['enhancement_steps'])}")
            print("="*50)
        else:
            print(f"\n❌ Enhancement failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"❌ Fatal error: {str(e)}")

if __name__ == "__main__":
    main()
