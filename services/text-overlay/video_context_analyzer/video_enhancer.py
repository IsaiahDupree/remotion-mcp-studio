"""
Video Enhancer

Main integration module that combines frame analysis, audio analysis,
transcript analysis, and text styling into a complete video enhancement system.
"""

import os
import cv2
import numpy as np
import logging
import tempfile
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import json

# Import our analyzer components
from video_context_analyzer.frame_analysis import FrameAnalyzer
from video_context_analyzer.audio_analysis import AudioAnalyzer
from video_context_analyzer.transcript_analysis import TranscriptAnalyzer
from video_context_analyzer.styling import TextStyler, Style, Position

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('video_enhancer')

class VideoEnhancer:
    """
    Main class for enhancing videos with intelligent text overlays.
    Coordinates frame analysis, audio analysis, transcript analysis, and
    text styling to create optimized videos for social media.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        temp_dir: Optional[str] = None,
        output_dir: str = "./enhanced_videos",
        style: Style = Style.BLACK_BG_WHITE_TEXT,
        position: Position = Position.TOP,
        font_scale: float = 1.0,
        max_words: int = 6,
        high_quality: bool = True
    ):
        """
        Initialize the Video Enhancer.
        
        Args:
            api_key: OpenAI API key (from env var if not provided)
            temp_dir: Directory for temporary files
            output_dir: Directory for output videos
            style: Text overlay style
            position: Text overlay position
            font_scale: Font size scaling
            max_words: Maximum words in text overlay
            high_quality: Whether to use high quality settings
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.high_quality = high_quality
        
        # Initialize analyzers
        self.frame_analyzer = FrameAnalyzer(api_key=self.api_key)
        self.audio_analyzer = AudioAnalyzer(api_key=self.api_key)
        self.transcript_analyzer = TranscriptAnalyzer(
            api_key=self.api_key,
            max_words=max_words
        )
        self.text_styler = TextStyler(
            style=style,
            position=position,
            font_scale=font_scale,
            animation=True
        )
        
        # Track analysis results
        self.analysis_results = {}
        
    def analyze_video(self, video_path: str, skip_existing: bool = True) -> Dict[str, Any]:
        """
        Analyze a video to determine the best text overlay.
        
        Args:
            video_path: Path to video file
            skip_existing: Whether to skip analysis if results exist
            
        Returns:
            Analysis results
        """
        video_id = Path(video_path).stem
        
        # Check if we already have analysis for this video
        if skip_existing and video_id in self.analysis_results:
            logger.info(f"Using existing analysis for {video_id}")
            return self.analysis_results[video_id]
        
        logger.info(f"Starting analysis for video: {video_path}")
        
        # Create result dictionary
        results = {
            "video_id": video_id,
            "video_path": str(Path(video_path).resolve()),
            "timestamp": datetime.now().isoformat(),
            "catchy_text": ""
        }
        
        # Run analyses in parallel for efficiency
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Submit frame analysis
                frame_future = executor.submit(
                    self.frame_analyzer.analyze_video,
                    video_path
                )
                
                # Submit audio analysis
                audio_future = executor.submit(
                    self.audio_analyzer.analyze_video_audio,
                    video_path
                )
                
                # Get results when ready
                frame_results = frame_future.result()
                audio_results = audio_future.result()
                
                # Store in results dictionary
                results["frame_analysis"] = frame_results
                results["audio_analysis"] = audio_results
                
                # Extract transcript if available
                transcript = audio_results.get("transcription", "")
                
                # If we have a transcript, analyze it
                if transcript:
                    # Provide frame analysis as context
                    transcript_results = self.transcript_analyzer.analyze_transcript(
                        transcript,
                        video_context={"frame_analysis": frame_results}
                    )
                    results["transcript_analysis"] = transcript_results
                    
                    # Use transcript-based text if available
                    if "catchy_text" in transcript_results:
                        results["catchy_text"] = transcript_results["catchy_text"]
                else:
                    # No transcript, use frame-based text
                    results["catchy_text"] = frame_results.get("catchy_text", "Epic content")
                
                # Store results
                self.analysis_results[video_id] = results
                logger.info(f"Analysis complete for {video_id}")
                
                return results
                
        except Exception as e:
            logger.error(f"Error analyzing video {video_path}: {e}")
            results["error"] = str(e)
            results["catchy_text"] = "Must see content"
            return results
    
    def apply_text_overlay(
        self, 
        video_path: str, 
        text: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Apply text overlay to video.
        
        Args:
            video_path: Path to video file
            text: Text to overlay (if not provided, will be generated from analysis)
            output_path: Path for output video
            
        Returns:
            Path to enhanced video
        """
        try:
            # Generate output path if not provided
            if not output_path:
                video_id = Path(video_path).stem
                output_path = str(self.output_dir / f"{video_id}_enhanced.mp4")
            
            # Get text from analysis if not provided
            if not text:
                analysis = self.analyze_video(video_path)
                text = analysis.get("catchy_text", "Must-see content")
                
            logger.info(f"Applying text overlay '{text}' to {video_path}")
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Error opening video: {video_path}")
                return ""
            
            # Get video properties
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Configure output format based on quality settings
            if self.high_quality:
                fourcc = cv2.VideoWriter_fourcc(*'H264')  # H.264 codec
                if output_path.lower().endswith('.mp4'):
                    pass  # MP4 is fine for H.264
                else:
                    output_path = os.path.splitext(output_path)[0] + '.mp4'
            else:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Default codec
            
            # Create video writer
            out = cv2.VideoWriter(
                output_path,
                fourcc,
                fps,
                (frame_width, frame_height)
            )
            
            # Process each frame
            frame_count = 0
            last_progress = -1
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Apply text overlay
                result_frame = self.text_styler.apply_text_overlay(
                    frame, 
                    text,
                    frame_number=frame_count,
                    total_frames=total_frames
                )
                
                # Write frame
                out.write(result_frame)
                
                # Update progress
                frame_count += 1
                progress = int((frame_count / total_frames) * 100)
                
                if progress % 10 == 0 and progress != last_progress:
                    logger.info(f"Processing: {progress}% complete")
                    last_progress = progress
            
            # Release resources
            cap.release()
            out.release()
            
            logger.info(f"Enhanced video saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error applying text overlay: {e}")
            return ""
    
    def enhance_video(
        self, 
        video_path: str,
        output_path: Optional[str] = None,
        custom_text: Optional[str] = None,
        analyze_first: bool = True
    ) -> Dict[str, Any]:
        """
        Complete video enhancement pipeline.
        
        Args:
            video_path: Path to video file
            output_path: Path for enhanced video
            custom_text: Custom text overlay (if not provided, will be generated)
            analyze_first: Whether to analyze video before enhancement
            
        Returns:
            Dictionary with enhancement results
        """
        result = {
            "video_path": video_path,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Step 1: Analyze video if requested
            if analyze_first:
                analysis = self.analyze_video(video_path)
                result["analysis"] = analysis
                
                # Use generated catchy text if no custom text
                if not custom_text:
                    custom_text = analysis.get("catchy_text")
            
            # Step 2: Apply text overlay
            enhanced_path = self.apply_text_overlay(
                video_path,
                text=custom_text,
                output_path=output_path
            )
            
            result["enhanced_video_path"] = enhanced_path
            result["text_overlay"] = custom_text
            result["success"] = bool(enhanced_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error enhancing video: {e}")
            result["error"] = str(e)
            result["success"] = False
            return result
    
    def process_batch(
        self, 
        video_paths: List[str],
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of videos.
        
        Args:
            video_paths: List of video paths
            output_dir: Directory for enhanced videos
            
        Returns:
            List of results for each video
        """
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        for video_path in video_paths:
            logger.info(f"Processing {video_path}")
            result = self.enhance_video(video_path)
            results.append(result)
        
        # Save batch results summary
        summary_path = self.output_dir / "batch_results.json"
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        return results


def main():
    """
    Command-line interface for the video enhancer.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhance videos with intelligent text overlays")
    parser.add_argument("video", nargs="?", help="Path to input video")
    parser.add_argument("--text", help="Custom text overlay")
    parser.add_argument("--output", help="Path for output video")
    parser.add_argument("--style", choices=["black_bg_white_text", "white_bg_black_text", "transparent_outline"],
                      default="black_bg_white_text", help="Text style")
    parser.add_argument("--position", choices=["top", "middle", "bottom"], 
                      default="top", help="Text position")
    parser.add_argument("--font-scale", type=float, default=1.0, help="Font size scaling")
    parser.add_argument("--api-key", help="OpenAI API key")
    parser.add_argument("--high-quality", action="store_true", help="Use high quality settings")
    parser.add_argument("--batch", help="File with list of videos to process")
    
    args = parser.parse_args()
    
    # Convert style string to enum
    style_map = {
        "black_bg_white_text": Style.BLACK_BG_WHITE_TEXT,
        "white_bg_black_text": Style.WHITE_BG_BLACK_TEXT,
        "transparent_outline": Style.TRANSPARENT_OUTLINE
    }
    style = style_map.get(args.style, Style.BLACK_BG_WHITE_TEXT)
    
    # Convert position string to enum
    position_map = {
        "top": Position.TOP,
        "middle": Position.MIDDLE,
        "bottom": Position.BOTTOM
    }
    position = position_map.get(args.position, Position.TOP)
    
    # Initialize enhancer
    enhancer = VideoEnhancer(
        api_key=args.api_key,
        style=style,
        position=position,
        font_scale=args.font_scale,
        high_quality=args.high_quality
    )
    
    # Process batch if specified
    if args.batch:
        with open(args.batch, 'r') as f:
            video_paths = [line.strip() for line in f if line.strip()]
        enhancer.process_batch(video_paths)
    # Process single video
    elif args.video:
        enhancer.enhance_video(
            args.video,
            output_path=args.output,
            custom_text=args.text
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
