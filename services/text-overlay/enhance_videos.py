#!/usr/bin/env python3
"""
Video Enhancement Script

Processes videos based on content report analysis to:
1. Add catchy text overlays optimized for social media
2. Add background music to videos that need it (using SoundCloud tracks)

Integrates with the existing audio/video tools for a complete enhancement pipeline.
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
import logging
from pathlib import Path
import random
from typing import List, Dict, Tuple, Optional, Any

# Import the text overlay functionality
from add_text_simple import SimpleVideoTextOverlay

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import relevant audiovideotools modules
from audiovideotools.audio_analysis.audio_analyzer import has_background_music
from audiovideotools.downloaders.soundcloud import SoundCloudDownloader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger('enhance_videos')

class VideoEnhancer:
    """Class to enhance videos with text overlays and background music."""
    
    def __init__(
        self,
        report_path: str,
        video_dir: str,
        output_dir: str,
        soundcloud_excel: Optional[str] = None,
        target_ratio: float = 0.15,
        speech_emphasis: float = 0.7,
        font_scale: float = 1.5,
        position: str = 'top'
    ):
        """
        Initialize the Video Enhancer.
        
        Args:
            report_path: Path to video content report Excel file
            video_dir: Directory containing videos
            output_dir: Directory to save enhanced videos
            soundcloud_excel: Path to Excel with SoundCloud track URLs
            target_ratio: Target ratio of music to speech volume
            speech_emphasis: Factor to emphasize speech clarity
            font_scale: Font size scale for text overlays
            position: Position of text ('top', 'middle', 'bottom')
        """
        self.report_path = report_path
        self.video_dir = Path(video_dir)
        self.output_dir = Path(output_dir)
        self.soundcloud_excel = soundcloud_excel
        self.target_ratio = target_ratio
        self.speech_emphasis = speech_emphasis
        self.font_scale = font_scale
        self.position = position
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Text overlay processor
        self.text_processor = SimpleVideoTextOverlay(
            output_dir=str(self.output_dir / "with_text"),
            font_scale=self.font_scale,
            position=self.position
        )
        
        # Track music downloads
        self.music_dir = self.output_dir / "music"
        self.music_dir.mkdir(parents=True, exist_ok=True)
        
        # Load report data
        self.load_report()
        
        # If soundcloud_excel is provided, initialize the downloader
        self.soundcloud_tracks = []
        if self.soundcloud_excel:
            self.init_soundcloud()
            
    def load_report(self):
        """Load and process the video content report."""
        try:
            self.report_df = pd.read_excel(self.report_path)
            log.info(f"Loaded report with {len(self.report_df)} videos")
            
            # Group videos by enhancement needs
            self.needs_text = self.report_df
            self.needs_music = self.report_df[self.report_df['needs_background_music'] == 'Yes']
            self.needs_both = self.needs_music.copy()
            
            log.info(f"Found {len(self.needs_text)} videos to enhance with text")
            log.info(f"Found {len(self.needs_music)} videos that need background music")
            
        except Exception as e:
            log.error(f"Error loading report: {e}")
            self.report_df = None
    
    def init_soundcloud(self):
        """Initialize SoundCloud downloader and download tracks."""
        try:
            # Initialize SoundCloud downloader
            self.soundcloud = SoundCloudDownloader(str(self.music_dir))
            
            # Download tracks
            log.info(f"Downloading SoundCloud tracks from {self.soundcloud_excel}")
            self.soundcloud_tracks = self.soundcloud.download_from_excel(self.soundcloud_excel)
            log.info(f"Downloaded {len(self.soundcloud_tracks)} SoundCloud tracks")
            
        except Exception as e:
            log.error(f"Error initializing SoundCloud: {e}")
            self.soundcloud_tracks = []
    
    def add_text_to_video(self, video_path: str, text: str) -> Optional[str]:
        """
        Add text overlay to a video.
        
        Args:
            video_path: Path to video file
            text: Text to overlay
            
        Returns:
            Path to output video or None if failed
        """
        try:
            return self.text_processor.add_text_to_video(video_path, text)
        except Exception as e:
            log.error(f"Error adding text to {os.path.basename(video_path)}: {e}")
            return None
    
    def add_music_to_video(self, video_path: str) -> Optional[str]:
        """
        Add background music to a video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to output video or None if failed
        """
        if not self.soundcloud_tracks:
            log.warning("No SoundCloud tracks available for adding background music")
            return None
        
        try:
            # Import here to avoid dependency issues
            from process_videos_with_music import add_music_to_video
            
            # Select a random track
            track = random.choice(self.soundcloud_tracks)
            
            # Output path
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = str(self.output_dir / f"{video_name}_with_music.mp4")
            
            log.info(f"Adding music track {os.path.basename(track)} to {os.path.basename(video_path)}")
            
            # Add music
            result = add_music_to_video(
                video_path, 
                track, 
                output_path,
                target_ratio=self.target_ratio,
                speech_emphasis=self.speech_emphasis
            )
            
            if result and os.path.exists(output_path):
                log.info(f"Successfully added music, saved to {output_path}")
                return output_path
            else:
                log.error(f"Failed to add music to {os.path.basename(video_path)}")
                return None
                
        except Exception as e:
            log.error(f"Error adding music to {os.path.basename(video_path)}: {e}")
            return None
    
    def process_video(self, filename: str) -> Dict[str, Any]:
        """
        Process a single video based on its enhancement needs.
        
        Args:
            filename: Name of the video file
            
        Returns:
            Dictionary with results
        """
        results = {
            'filename': filename,
            'original_path': str(self.video_dir / filename),
            'text_added': False,
            'music_added': False,
            'text_output_path': None,
            'music_output_path': None,
            'final_output_path': None,
            'errors': []
        }
        
        video_path = self.video_dir / filename
        
        # Filter for this video in the report
        video_info = self.report_df[self.report_df['filename'] == filename]
        
        if video_info.empty:
            log.warning(f"Video {filename} not found in report")
            results['errors'].append("Video not found in report")
            return results
            
        video_info = video_info.iloc[0]
        
        # Check if text overlay is needed
        try:
            # Get catchy description
            text = video_info['catchy_description']
            
            # Add text
            text_output = self.add_text_to_video(str(video_path), text)
            
            if text_output:
                results['text_added'] = True
                results['text_output_path'] = text_output
                
                # For the next step, use the video with text
                video_path = text_output
        except Exception as e:
            log.error(f"Error adding text to {filename}: {e}")
            results['errors'].append(f"Text error: {str(e)}")
        
        # Check if music is needed
        if video_info['needs_background_music'] == 'Yes' and self.soundcloud_tracks:
            try:
                # Add music
                music_output = self.add_music_to_video(str(video_path))
                
                if music_output:
                    results['music_added'] = True
                    results['music_output_path'] = music_output
                    results['final_output_path'] = music_output
            except Exception as e:
                log.error(f"Error adding music to {filename}: {e}")
                results['errors'].append(f"Music error: {str(e)}")
        
        # If only text was added, set final output
        if results['text_added'] and not results['music_added']:
            results['final_output_path'] = results['text_output_path']
            
        return results
    
    def process_all_videos(self) -> List[Dict[str, Any]]:
        """
        Process all videos in the report.
        
        Returns:
            List of result dictionaries for each processed video
        """
        results = []
        
        for _, row in self.report_df.iterrows():
            filename = row['filename']
            video_path = self.video_dir / filename
            
            if not os.path.exists(video_path):
                log.warning(f"Video file not found: {video_path}")
                continue
                
            log.info(f"Processing video: {filename}")
            video_results = self.process_video(filename)
            results.append(video_results)
            
            # Log results
            if video_results['text_added'] or video_results['music_added']:
                log.info(f"Enhanced {filename}: " 
                        f"Text={video_results['text_added']}, "
                        f"Music={video_results['music_added']}")
            else:
                log.warning(f"No enhancements applied to {filename}")
                
        return results
    
    def process_specific_video(self, filename: str) -> Dict[str, Any]:
        """
        Process a specific video.
        
        Args:
            filename: Name of the video file
            
        Returns:
            Results dictionary
        """
        video_path = self.video_dir / filename
        
        if not os.path.exists(video_path):
            log.error(f"Video file not found: {video_path}")
            return {
                'filename': filename,
                'errors': ["File not found"]
            }
            
        log.info(f"Processing specific video: {filename}")
        return self.process_video(filename)
    
    def save_results(self, results: List[Dict[str, Any]], output_path: Optional[str] = None):
        """
        Save processing results to Excel.
        
        Args:
            results: List of result dictionaries
            output_path: Path to save Excel file
        """
        if not results:
            log.warning("No results to save")
            return
            
        if not output_path:
            output_path = str(self.output_dir / "enhancement_results.xlsx")
            
        try:
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            # Save to Excel
            df.to_excel(output_path, index=False)
            log.info(f"Results saved to {output_path}")
        except Exception as e:
            log.error(f"Error saving results: {e}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Enhance videos with text overlays and background music")
    
    parser.add_argument("--report", type=str, required=True,
                       help="Path to video content report Excel file")
    parser.add_argument("--video_dir", type=str, required=True,
                       help="Directory containing videos")
    parser.add_argument("--output", type=str, default="./enhanced_videos",
                       help="Directory to save enhanced videos")
    parser.add_argument("--soundcloud_excel", type=str,
                       help="Path to Excel file with SoundCloud track URLs")
    parser.add_argument("--video", type=str,
                       help="Process specific video (filename only)")
    parser.add_argument("--target_ratio", type=float, default=0.15,
                       help="Target ratio of music to speech volume")
    parser.add_argument("--speech_emphasis", type=float, default=0.7,
                       help="Factor to emphasize speech clarity")
    
    args = parser.parse_args()
    
    # Initialize enhancer
    enhancer = VideoEnhancer(
        report_path=args.report,
        video_dir=args.video_dir,
        output_dir=args.output,
        soundcloud_excel=args.soundcloud_excel,
        target_ratio=args.target_ratio,
        speech_emphasis=args.speech_emphasis
    )
    
    # Process videos
    if args.video:
        results = [enhancer.process_specific_video(args.video)]
    else:
        results = enhancer.process_all_videos()
    
    # Save results
    enhancer.save_results(results)

if __name__ == "__main__":
    main()
