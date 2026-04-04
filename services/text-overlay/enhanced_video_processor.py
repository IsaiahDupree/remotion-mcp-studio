#!/usr/bin/env python
"""
Enhanced Modular Video Processor
===============================
A modular video enhancement system with customizable text overlays and background music from Excel.
Supports various styling options, custom fonts, and automated music selection.
"""

import os
import sys
import time
import logging
import argparse
import json
import random
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd

# Add parent directory to path if needed
if not os.path.exists(os.path.join(os.path.dirname(__file__), "video_enhancer")):
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our custom modules
from video_enhancer.composite_overlay import CompositeTextOverlayEnhancer
from video_enhancer.text_styler import Position, Style
from video_enhancer.transcript_processor import TranscriptProcessor
from video_enhancer.music_enhancer import MusicEnhancer
from video_context_analyzer.frame_analysis.frame_analyzer import FrameAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("enhanced_processor.log")
    ]
)
logger = logging.getLogger("enhanced_video_processor")

class VideoStyleConfig:
    """Configuration class for video styling options"""
    
    def __init__(self):
        self.styles = {
            'classic': Style.BLACK_BG_WHITE_TEXT,
            'modern': Style.TRANSPARENT_BG_WHITE_TEXT,
            'elegant': Style.WHITE_BG_BLACK_TEXT,
            'minimal': Style.TRANSPARENT_BG_WHITE_TEXT  # Use white text on transparent as minimal
        }
        
        self.positions = {
            'top': Position.TOP,
            'center': Position.CENTER,
            'bottom': Position.BOTTOM
        }
        
        # Common font paths (Windows)
        self.fonts = {
            'arial': "C:/Windows/Fonts/Arial.ttf",
            'helvetica': "C:/Windows/Fonts/Arial.ttf",  # Arial is similar to Helvetica
            'times': "C:/Windows/Fonts/Times.ttf",
            'courier': "C:/Windows/Fonts/CourierNew.ttf",
            'impact': "C:/Windows/Fonts/Impact.ttf",
            'comic': "C:/Windows/Fonts/ComicSansMS.ttf",
            'calibri': "C:/Windows/Fonts/Calibri.ttf",
            'georgia': "C:/Windows/Fonts/Georgia.ttf"
        }

class MusicSelector:
    """Advanced music selection from Excel files"""
    
    def __init__(self, excel_path: str, track_column: str = "Track URL"):
        self.excel_path = excel_path
        self.track_column = track_column
        self.df = None
        self._load_excel()
    
    def _load_excel(self):
        """Load and validate Excel file"""
        try:
            if not os.path.exists(self.excel_path):
                raise FileNotFoundError(f"Excel file not found: {self.excel_path}")
            
            self.df = pd.read_excel(self.excel_path)
            logger.info(f"Loaded Excel file with {len(self.df)} rows")
            
            if self.track_column not in self.df.columns:
                available_columns = list(self.df.columns)
                logger.warning(f"Column '{self.track_column}' not found. Available columns: {available_columns}")
                # Try to find a URL-like column
                url_candidates = ['Track URL', 'URL', 'track_url', 'url', 'link', 'Link']
                for col in url_candidates:
                    if col in available_columns:
                        self.track_column = col
                        logger.info(f"Using column '{col}' instead")
                        break
            
            # Log available data
            logger.info(f"Available columns: {list(self.df.columns)}")
            valid_tracks = self.df[self.track_column].dropna()
            logger.info(f"Found {len(valid_tracks)} valid track URLs")
            
            # Show sample data
            if len(valid_tracks) > 0:
                logger.info(f"Sample track: {valid_tracks.iloc[0]}")
            
        except Exception as e:
            logger.error(f"Error loading Excel file: {str(e)}")
            raise
    
    def get_random_track(self) -> Optional[str]:
        """Select a random track URL from the Excel file"""
        if self.df is None or self.df.empty:
            return None
        
        # Filter out empty/null values
        valid_tracks = self.df[self.track_column].dropna().tolist()
        if not valid_tracks:
            logger.warning("No valid track URLs found in Excel file")
            return None
        
        selected_track = random.choice(valid_tracks)
        
        # Get additional info about the selected track
        track_info = self._get_track_info(selected_track)
        logger.info(f"Selected random track: {selected_track}")
        if track_info:
            logger.info(f"Track details: {track_info}")
        
        return selected_track
    
    def _get_track_info(self, track_url: str) -> Optional[Dict[str, Any]]:
        """Get additional information about a track"""
        if self.df is None:
            return None
        
        # Find the row with this track URL
        track_row = self.df[self.df[self.track_column] == track_url]
        if track_row.empty:
            return None
        
        # Extract relevant information
        info = {}
        for col in ['Track Title', 'Author', 'Genre', 'Tags']:
            if col in self.df.columns:
                value = track_row[col].iloc[0]
                if pd.notna(value):
                    info[col] = value
        
        return info if info else None
    
    def get_track_by_criteria(self, criteria: Dict[str, Any]) -> Optional[str]:
        """Select track based on specific criteria (genre, author, etc.)"""
        if self.df is None or self.df.empty:
            return None
        
        filtered_df = self.df.copy()
        
        # Apply filters based on criteria
        for column, value in criteria.items():
            if column in self.df.columns:
                if isinstance(value, list):
                    # Filter by multiple values (OR condition)
                    filtered_df = filtered_df[filtered_df[column].isin(value)]
                elif isinstance(value, str):
                    # String contains filter (case insensitive)
                    filtered_df = filtered_df[
                        filtered_df[column].str.contains(value, case=False, na=False)
                    ]
                else:
                    # Exact match
                    filtered_df = filtered_df[filtered_df[column] == value]
        
        if filtered_df.empty:
            logger.warning(f"No tracks found matching criteria: {criteria}")
            return self.get_random_track()  # Fallback to random
        
        valid_tracks = filtered_df[self.track_column].dropna().tolist()
        if not valid_tracks:
            return self.get_random_track()  # Fallback to random
        
        selected_track = random.choice(valid_tracks)
        track_info = self._get_track_info(selected_track)
        
        logger.info(f"Selected track matching criteria {criteria}: {selected_track}")
        if track_info:
            logger.info(f"Track details: {track_info}")
        
        return selected_track
    
    def get_tracks_by_genre(self, genre: str) -> List[str]:
        """Get all tracks of a specific genre"""
        if self.df is None or self.df.empty:
            return []
        
        if 'Genre' not in self.df.columns:
            logger.warning("Genre column not found in Excel file")
            return []
        
        genre_tracks = self.df[
            self.df['Genre'].str.contains(genre, case=False, na=False)
        ][self.track_column].dropna().tolist()
        
        logger.info(f"Found {len(genre_tracks)} tracks in genre '{genre}'")
        return genre_tracks

class EnhancedVideoProcessor:
    """Main video processing class with modular components"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_api_key()
        self.style_config = VideoStyleConfig()
        
        # Initialize frame analyzer for 30-second interval analysis
        self.frame_analyzer = FrameAnalyzer(
            api_key=self.api_key,
            sampling_strategy='uniform',  # Will be overridden by interval_seconds in extract_frames
            frames_to_sample=10  # Not used when interval_seconds is specified
        )
        
    def _get_api_key(self) -> Optional[str]:
        """Get API key from .env file or environment variables"""
        # First try .env file
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_path):
            env_vars = self._read_env_file(env_path)
            api_key = env_vars.get('OPENAI_API_KEY')
            if api_key:
                return api_key
        
        # Then try environment variable
        return os.environ.get('OPENAI_API_KEY')
    
    def _read_env_file(self, env_path: str) -> Dict[str, str]:
        """Read key=value pairs from .env file"""
        env_vars = {}
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    key_value = line.split('=', 1)
                    if len(key_value) == 2:
                        key, value = key_value
                        env_vars[key.strip()] = value.strip()
        except Exception as e:
            logger.error(f"Error reading .env file: {str(e)}")
        return env_vars
    
    def enhance_video(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        text_config: Optional[Dict[str, Any]] = None,
        music_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enhanced video processing with modular configuration
        
        Args:
            video_path: Path to input video
            output_path: Path for output video
            text_config: Text overlay configuration
            music_config: Background music configuration
            
        Returns:
            Processing results dictionary
        """
        start_time = time.time()
        
        # Validate input
        if not os.path.exists(video_path):
            return {"success": False, "error": f"Video not found: {video_path}"}
        
        # Setup default configurations
        text_config = text_config or {}
        music_config = music_config or {}
        
        # Determine output path
        if not output_path:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enhanced_videos")
            os.makedirs(output_dir, exist_ok=True)
            video_basename = os.path.basename(video_path).split('.')[0]
            timestamp = int(time.time())
            output_path = os.path.join(output_dir, f"{video_basename}_enhanced_{timestamp}.mp4")
        
        logger.info(f"=== ENHANCED VIDEO PROCESSING STARTED ===")
        logger.info(f"Input: {video_path}")
        logger.info(f"Output: {output_path}")
        
        # Create output directory
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        results = {
            "success": False,
            "input_video": video_path,
            "output_video": output_path,
            "processing_start": start_time
        }
        
        # Step 1: Process text overlay
        text_result = self._process_text_overlay(video_path, output_path, text_config)
        results.update(text_result)
        
        if not text_result.get("success", False):
            return results
        
        # Step 2: Process background music (if requested)
        if music_config.get("enabled", False):
            music_result = self._process_background_music(
                text_result["intermediate_video"], 
                output_path, 
                music_config
            )
            results.update(music_result)
        else:
            # Copy text-only video to final output
            try:
                import shutil
                shutil.copy2(text_result["intermediate_video"], output_path)
                results["success"] = True
            except Exception as e:
                results["error"] = f"Error finalizing video: {str(e)}"
        
        # Final processing time
        results["processing_time_seconds"] = time.time() - start_time
        
        logger.info(f"=== ENHANCED VIDEO PROCESSING COMPLETE ({results['processing_time_seconds']:.1f}s) ===")
        
        return results
    
    def _process_text_overlay(
        self, 
        video_path: str, 
        output_path: str, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process text overlay with enhanced styling options"""
        
        logger.info("Processing text overlay...")
        
        # Extract configuration
        style_name = config.get("style", "classic")
        position_name = config.get("position", "top")
        font_name = config.get("font", "arial")
        font_scale = config.get("font_scale", 1.2)
        custom_text = config.get("custom_text")
        
        # Convert to enums
        style = self.style_config.styles.get(style_name, Style.BLACK_BG_WHITE_TEXT)
        position = self.style_config.positions.get(position_name, Position.TOP)
        font_path = self.style_config.fonts.get(font_name)
        
        # Validate font file
        if font_path and not os.path.exists(font_path):
            logger.warning(f"Font file not found: {font_path}, using default")
            font_path = None
        
        logger.info(f"Text overlay config: style={style_name}, position={position_name}, font={font_name}, scale={font_scale}")

        # Create intermediate file path
        intermediate_video = output_path.replace('.mp4', '_text_only.mp4')

        try:
            # If custom text is not provided, use enhanced frame analysis for better context
            if not custom_text:
                logger.info("Analyzing video frames every 30 seconds with GPT-4o...")

                # Extract frames every 30 seconds
                frames = self.frame_analyzer.extract_frames(video_path, interval_seconds=30.0)
                logger.info(f"Extracted {len(frames)} frames for analysis")

                if frames:
                    # Analyze frames with GPT-4o
                    frame_analysis = self.frame_analyzer.analyze_frames_with_ai(frames)

                    if frame_analysis.get('catchy_text'):
                        custom_text = frame_analysis['catchy_text']
                        logger.info(f"Generated text from 30-second frame analysis: '{custom_text}'")
                    else:
                        logger.warning("Frame analysis did not produce catchy text, using fallback")
                        custom_text = "Engage and inspire"
                else:
                    logger.warning("No frames extracted, using fallback text")
                    custom_text = "Epic content ahead"

            # Initialize text overlay enhancer
            text_overlay = CompositeTextOverlayEnhancer(
                style=style,
                position=position,
                font_scale=font_scale,
                openai_api_key=self.api_key,
                font_file=font_path
            )

            # Apply text overlay with our enhanced text
            success = text_overlay.enhance_video(
                video_path=video_path,
                output_path=intermediate_video,
                custom_text=custom_text,
                analyze_first=False  # We already did our enhanced analysis
            )

            # Verify output exists
            if not success or not os.path.exists(intermediate_video):
                return {
                    "success": False,
                    "error": "Text overlay failed or output file was not created"
                }
            
            # Get the actual text used
            used_text = custom_text if custom_text else "AI-generated text"
            if hasattr(text_overlay, 'text') and text_overlay.text:
                used_text = text_overlay.text
            
            return {
                "success": True,
                "text_overlay_applied": True,
                "text_used": used_text,
                "intermediate_video": intermediate_video,
                "text_style": style_name,
                "text_position": position_name,
                "font_used": font_name
            }
            
        except Exception as e:
            logger.error(f"Text overlay error: {str(e)}")
            return {
                "success": False,
                "error": f"Text overlay failed: {str(e)}"
            }
    
    def _process_background_music(
        self, 
        video_path: str, 
        output_path: str, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process background music with Excel integration"""
        
        logger.info("Processing background music...")
        
        music_path = None
        music_source = "none"
        
        # Try to get music from Excel file
        excel_path = config.get("excel_path")
        if excel_path and os.path.exists(excel_path):
            try:
                music_selector = MusicSelector(
                    excel_path=excel_path,
                    track_column=config.get("track_column", "Track URL")
                )
                
                # Check if specific criteria are provided
                criteria = config.get("criteria", {})
                if criteria:
                    music_path = music_selector.get_track_by_criteria(criteria)
                    music_source = f"excel_criteria_{criteria}"
                else:
                    music_path = music_selector.get_random_track()
                    music_source = "excel_random"
                    
            except Exception as e:
                logger.error(f"Error selecting music from Excel: {str(e)}")
        
        # Fallback to provided music path
        if not music_path:
            music_path = config.get("music_path")
            music_source = "manual"
        
        if not music_path:
            logger.warning("No music source available")
            return {
                "success": True,
                "music_added": False,
                "music_source": "none",
                "message": "No music source configured"
            }
        
        try:
            # Initialize music enhancer
            music_enhancer = MusicEnhancer()
            
            # Apply background music
            music_result = music_enhancer.enhance_video_with_music(
                video_path=video_path,
                output_path=output_path,
                music_path=music_path,
                auto_detect_existing_music=config.get("auto_detect", True),
                speech_emphasis=config.get("speech_emphasis", 0.7)
            )
            
            if music_result and music_result.get("success", False):
                return {
                    "success": True,
                    "music_added": True,
                    "music_source": music_source,
                    "music_path": music_path,
                    "has_existing_music": music_result.get("has_existing_music", False)
                }
            else:
                return {
                    "success": False,
                    "error": music_result.get("error", "Unknown music error") if music_result else "Music enhancement failed",
                    "music_source": music_source
                }
                
        except Exception as e:
            logger.error(f"Background music error: {str(e)}")
            return {
                "success": False,
                "error": f"Music processing failed: {str(e)}"
            }

def main():
    """Main function with enhanced argument parsing"""
    
    parser = argparse.ArgumentParser(
        description="Enhanced Video Processor with modular styling and music selection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic text overlay
  python enhanced_video_processor.py --input video.mp4 --text-style modern --position center
  
  # With custom font and music from Excel
  python enhanced_video_processor.py --input video.mp4 --font calibri --music-excel tracks.xlsx
  
  # Full customization
  python enhanced_video_processor.py --input video.mp4 --text-style elegant --position bottom --font impact --scale 1.5 --music-excel tracks.xlsx --speech-emphasis 0.6 --custom-text "Amazing Content!"
        """
    )
    
    # Required arguments
    parser.add_argument("--input", "-i", required=True, help="Input video file path")
    
    # Output options
    parser.add_argument("--output", "-o", help="Output video file path (optional)")
    
    # Text styling options
    parser.add_argument("--text-style", choices=['classic', 'modern', 'elegant', 'minimal'], 
                       default='classic', help="Text overlay style")
    parser.add_argument("--position", choices=['top', 'center', 'bottom'], 
                       default='top', help="Text position")
    parser.add_argument("--font", choices=['arial', 'helvetica', 'times', 'courier', 'impact', 'comic', 'calibri', 'georgia'], 
                       default='arial', help="Font family")
    parser.add_argument("--scale", type=float, default=1.2, help="Font scale factor")
    parser.add_argument("--custom-text", help="Custom text to overlay (bypasses AI analysis)")
    
    # Music options
    parser.add_argument("--music", action="store_true", help="Add background music")
    parser.add_argument("--music-excel", help="Excel file with music tracks")
    parser.add_argument("--music-column", default="Track URL", help="Column name for music URLs")
    parser.add_argument("--music-path", help="Direct path to music file")
    parser.add_argument("--speech-emphasis", type=float, default=0.7, 
                       help="Speech emphasis factor (lower = quieter music during speech)")
    
    # Advanced options
    parser.add_argument("--api-key", help="OpenAI API key")
    parser.add_argument("--skip-music-detection", action="store_true", 
                       help="Skip automatic background music detection")
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = EnhancedVideoProcessor(api_key=args.api_key)
    
    # Setup text configuration
    text_config = {
        "style": args.text_style,
        "position": args.position,
        "font": args.font,
        "font_scale": args.scale,
        "custom_text": args.custom_text
    }
    
    # Setup music configuration
    music_config = {
        "enabled": args.music,
        "excel_path": args.music_excel,
        "track_column": args.music_column,
        "music_path": args.music_path,
        "speech_emphasis": args.speech_emphasis,
        "auto_detect": not args.skip_music_detection
    }
    
    # Process video
    result = processor.enhance_video(
        video_path=args.input,
        output_path=args.output,
        text_config=text_config,
        music_config=music_config
    )
    
    # Display results
    print("\n" + "="*60)
    if result.get("success", False):
        print("✅ VIDEO ENHANCEMENT SUCCESSFUL!")
        print(f"📁 Output: {result['output_video']}")
        print(f"⏱️  Processing time: {result.get('processing_time_seconds', 0):.1f} seconds")
        
        if result.get("text_overlay_applied", False):
            print(f"📝 Text: '{result.get('text_used', 'N/A')}'")
            print(f"🎨 Style: {result.get('text_style', 'N/A')} | Position: {result.get('text_position', 'N/A')} | Font: {result.get('font_used', 'N/A')}")
        
        if result.get("music_added", False):
            print(f"🎵 Music: Added from {result.get('music_source', 'unknown')}")
            if result.get("has_existing_music", False):
                print("⚠️  Note: Existing background music detected")
        elif music_config.get("enabled", False):
            print("🎵 Music: Not added (see logs for details)")
            
    else:
        print("❌ VIDEO ENHANCEMENT FAILED!")
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
