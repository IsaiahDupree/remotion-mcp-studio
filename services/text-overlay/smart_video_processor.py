#!/usr/bin/env python3
"""
Smart Video Processor with Intelligent Music Matching
====================================================

Enhanced video processor that uses AI-powered music-video matching for optimal background music selection.
Combines all previous enhancements with intelligent context-aware music selection.
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_video_processor import EnhancedVideoProcessor
from music_video_matcher import MusicVideoMatcher
from local_music_selector import LocalMusicSelector
from video_enhancer.music_enhancer import MusicEnhancer
from video_enhancer.composite_text_styler import CompositeTextStyler
from video_enhancer.text_styler import Style, Position

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartVideoProcessor:
    """
    Enhanced video processor with intelligent music matching capabilities
    
    Features:
    - AI-powered music-video context matching using GPT-4o
    - Frame analysis every 30 seconds with visual context understanding
    - Transcript analysis for content understanding
    - Intelligent music selection based on video mood, energy, and themes
    - Background music at optimized -25 to -30dB levels
    - Resolution preservation throughout processing
    - Comprehensive caching for performance
    """
    
    def __init__(self, 
                 use_intelligent_matching: bool = True,
                 fallback_to_random: bool = True,
                 min_compatibility_score: float = 0.7,
                 cache_analyses: bool = True):
        """
        Initialize the smart video processor
        
        Args:
            use_intelligent_matching: Whether to use AI-powered music matching
            fallback_to_random: Fall back to random selection if no good matches
            min_compatibility_score: Minimum score required for music selection
            cache_analyses: Whether to cache video and music analyses
        """
        self.use_intelligent_matching = use_intelligent_matching
        self.fallback_to_random = fallback_to_random
        self.min_compatibility_score = min_compatibility_score
        self.cache_analyses = cache_analyses
        
        # Initialize components
        try:
            self.video_processor = EnhancedVideoProcessor()
            logger.info("✅ Enhanced video processor initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing video processor: {e}")
            raise
        
        try:
            self.music_matcher = MusicVideoMatcher() if use_intelligent_matching else None
            if self.music_matcher:
                logger.info("✅ Intelligent music matcher initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize music matcher: {e}")
            self.music_matcher = None
        
        try:
            self.music_selector = LocalMusicSelector()
            logger.info("✅ Local music selector initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize music selector: {e}")
            self.music_selector = None
        
        try:
            self.music_enhancer = MusicEnhancer(use_local_library=True)
            logger.info("✅ Music enhancer initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize music enhancer: {e}")
            self.music_enhancer = None
        
        try:
            self.text_styler = CompositeTextStyler(
                style=Style.BLACK_BG_WHITE_TEXT,
                position=Position.TOP,
                font_scale=1.0
            )
            logger.info("✅ Text styler initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize text styler: {e}")
            self.text_styler = None
        
        logger.info("🚀 SmartVideoProcessor initialized successfully")
    
    def select_optimal_music(self, video_path: str) -> Optional[str]:
        """
        Select optimal music for video using intelligent matching
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Path to selected music file or None if no suitable music found
        """
        
        if not self.use_intelligent_matching or not self.music_matcher:
            logger.info("Using fallback music selection (intelligent matching disabled)")
            return self._fallback_music_selection()
        
        try:
            logger.info(f"🎯 Selecting optimal music for: {Path(video_path).name}")
            
            # Get best music match using AI analysis
            best_music = self.music_matcher.get_best_music_for_video(
                video_path, 
                min_score=self.min_compatibility_score
            )
            
            if best_music:
                logger.info(f"🎵 Selected AI-matched music: {Path(best_music).name}")
                return best_music
            else:
                logger.info(f"⚠️ No music meets minimum compatibility score ({self.min_compatibility_score})")
                
                if self.fallback_to_random:
                    logger.info("🎲 Falling back to random music selection")
                    return self._fallback_music_selection()
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error in intelligent music selection: {e}")
            
            if self.fallback_to_random:
                logger.info("🎲 Falling back to random music selection due to error")
                return self._fallback_music_selection()
            else:
                return None
    
    def _fallback_music_selection(self) -> Optional[str]:
        """Fallback music selection using local music selector"""
        
        if not self.music_selector:
            return None
        
        try:
            # Prefer smaller files for faster processing
            return self.music_selector.select_by_criteria({'max_size_mb': 30})
        except Exception as e:
            logger.error(f"Error in fallback music selection: {e}")
            return None
    
    def process_video_with_smart_music(self, 
                                     video_path: str, 
                                     output_path: str,
                                     config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process video with intelligent music selection and enhanced features
        
        Args:
            video_path: Path to input video
            output_path: Path for output video
            config: Optional configuration overrides
            
        Returns:
            Dictionary with processing results and metadata
        """
        
        if not os.path.exists(video_path):
            return {"success": False, "error": f"Video file not found: {video_path}"}
        
        # Default configuration
        default_config = {
            'use_smart_music': True,
            'text_style': 'modern',
            'text_position': 'bottom',
            'music_volume': 0.04,  # -28dB optimized for -25 to -30dB range
            'frame_analysis_interval': 30.0,
            'preserve_resolution': True,
            'detect_existing_music': True
        }
        
        # Merge with user config
        if config:
            default_config.update(config)
        
        processing_start_time = time.time()
        
        try:
            logger.info(f"🎬 Processing video with smart features: {Path(video_path).name}")
            
            # Step 1: Select optimal music
            selected_music = None
            if default_config['use_smart_music']:
                logger.info("🎯 Step 1: Selecting optimal music...")
                selected_music = self.select_optimal_music(video_path)
                
                if selected_music:
                    logger.info(f"✅ Music selected: {Path(selected_music).name}")
                else:
                    logger.warning("⚠️ No music selected")
            
            # Step 2: Process video with enhanced features
            logger.info("🎬 Step 2: Processing video with enhanced features...")
            
            # Prepare processing parameters
            processing_params = {
                'video_path': video_path,
                'output_path': output_path,
                'music_path': selected_music,
                'config': {
                    'text_style': default_config['text_style'],
                    'text_position': default_config['text_position'],
                    'music_volume_factor': default_config['music_volume'],
                    'frame_analysis_interval': default_config['frame_analysis_interval'],
                    'preserve_resolution': default_config['preserve_resolution'],
                    'detect_existing_music': default_config['detect_existing_music']
                }
            }
            
            # Process the video
            result = self.video_processor.process_video(**processing_params)
            
            # Calculate processing time
            processing_time = time.time() - processing_start_time
            
            # Add smart processing metadata
            if result.get('success', False):
                result.update({
                    'smart_processing': True,
                    'selected_music': selected_music,
                    'music_selection_method': 'intelligent' if self.use_intelligent_matching and selected_music else 'fallback',
                    'processing_time_seconds': round(processing_time, 2),
                    'config_used': default_config
                })
                
                logger.info(f"✅ Smart video processing completed in {processing_time:.1f}s")
            else:
                logger.error("❌ Video processing failed")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in smart video processing: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time_seconds": time.time() - processing_start_time
            }
    
    def batch_process_with_smart_music(self, 
                                     video_paths: List[str], 
                                     output_dir: str,
                                     config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Batch process multiple videos with intelligent music matching
        
        Args:
            video_paths: List of video file paths
            output_dir: Directory for output videos
            config: Optional configuration
            
        Returns:
            Dictionary with batch processing results
        """
        
        os.makedirs(output_dir, exist_ok=True)
        
        results = {
            'total_videos': len(video_paths),
            'processed': 0,
            'failed': 0,
            'results': [],
            'start_time': time.time()
        }
        
        logger.info(f"🎬 Starting batch processing of {len(video_paths)} videos")
        
        for i, video_path in enumerate(video_paths):
            logger.info(f"📹 Processing video {i+1}/{len(video_paths)}: {Path(video_path).name}")
            
            # Generate output path
            video_name = Path(video_path).stem
            output_path = os.path.join(output_dir, f"{video_name}_smart_enhanced.mp4")
            
            # Process video
            result = self.process_video_with_smart_music(video_path, output_path, config)
            
            # Track results
            if result.get('success', False):
                results['processed'] += 1
                logger.info(f"✅ Successfully processed: {video_name}")
            else:
                results['failed'] += 1
                logger.error(f"❌ Failed to process: {video_name}")
            
            results['results'].append({
                'video_path': video_path,
                'output_path': output_path,
                'result': result
            })
        
        # Calculate total time
        results['total_time_seconds'] = round(time.time() - results['start_time'], 2)
        
        logger.info(f"🎉 Batch processing completed: {results['processed']} success, {results['failed']} failed")
        return results
    
    def get_music_compatibility_report(self, video_path: str) -> Dict[str, Any]:
        """
        Generate detailed music compatibility report for a video
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with compatibility analysis
        """
        
        if not self.music_matcher:
            return {"error": "Intelligent music matching not available"} 
        
        try:
            logger.info(f"📊 Generating music compatibility report for: {Path(video_path).name}")
            
            # Create match index if not exists
            matches = self.music_matcher.create_match_index_for_video(video_path)
            
            # Get video context
            video_context = self.music_matcher.analyze_video_context(video_path)
            
            report = {
                'video_path': video_path,
                'video_context': {
                    'content_type': video_context.content_type,
                    'visual_mood': video_context.visual_mood,
                    'energy_level': video_context.energy_level,
                    'themes': video_context.themes,
                    'duration': video_context.duration
                },
                'total_music_options': len(matches),
                'top_matches': [
                    {
                        'music_name': Path(match.music_path).name,
                        'compatibility_score': match.compatibility_score,
                        'mood_match': match.mood_match,
                        'energy_match': match.energy_match,
                        'theme_match': match.theme_match,
                        'reasoning': match.reasoning
                    }
                    for match in matches[:5]  # Top 5 matches
                ],
                'best_match': matches[0].music_path if matches else None,
                'recommendation': 'highly_recommended' if matches and matches[0].compatibility_score >= 0.8 else 'acceptable' if matches else 'no_suitable_match'
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating compatibility report: {e}")
            return {"error": str(e)}
    
    def process_video_with_specified_music(self, video_path: str, output_path: str, music_path: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process video with manually specified music track
        
        Args:
            video_path: Path to input video
            output_path: Path for output video
            music_path: Path to specific music track to use
            config: Optional processing configuration
            
        Returns:
            Processing results
        """
        try:
            logger.info(f"🎬 Processing video with specified music: {Path(video_path).name}")
            logger.info(f"🎵 Using music: {Path(music_path).name}")
            
            config = config or {}
            
            # Validate inputs
            if not os.path.exists(video_path):
                return {"success": False, "error": "Video file not found"}
            
            if not os.path.exists(music_path):
                return {"success": False, "error": "Music file not found"}
            
            # Step 1: Create working copy to preserve metadata
            working_copy_path = None
            try:
                working_copy_path = self._create_working_copy(video_path)
                logger.info(f"📁 Created working copy: {working_copy_path}")
            except Exception as e:
                logger.warning(f"Working copy creation failed, using original: {e}")
                working_copy_path = video_path
            
            # Step 2: Extract transcript and generate text overlay
            text_overlay = "Amazing Content"
            transcript = ""
            
            if self.use_transcript_analysis:
                try:
                    logger.info("🔍 Extracting and analyzing transcript...")
                    transcript_result = self.transcript_processor.process_video_transcript(working_copy_path)
                    if transcript_result and not transcript_result.get('error'):
                        transcript = transcript_result.get('transcript', '')
                        text_overlay = transcript_result.get('catchy_text', 'Amazing Content')
                        logger.info(f"📝 Generated text overlay: {text_overlay}")
                    else:
                        logger.warning("Transcript analysis failed, using frame analysis")
                        raise Exception("Transcript failed")
                except Exception as e:
                    logger.info("🖼️ Using frame analysis for text generation...")
                    try:
                        frame_result = self.frame_analyzer.analyze_video(working_copy_path)
                        if frame_result and not frame_result.get('error'):
                            text_overlay = frame_result.get('catchy_text', 'Amazing Content')
                            logger.info(f"🖼️ Generated text from frames: {text_overlay}")
                    except Exception as fe:
                        logger.warning(f"Frame analysis also failed: {fe}")
            
            # Step 3: Add background music
            logger.info(f"🎵 Adding background music: {Path(music_path).name}")
            
            # Create temporary path for video with music
            temp_with_music = os.path.join(os.path.dirname(output_path), f"temp_music_{int(time.time())}.mp4")
            
            music_result = self.music_enhancer.add_background_music(
                video_path=working_copy_path,
                music_path=music_path,
                output_path=temp_with_music,
                volume_factor=config.get('music_volume', 0.04)  # Default -28dB
            )
            
            if not music_result.get('success'):
                # Clean up
                if working_copy_path != video_path and os.path.exists(working_copy_path):
                    os.remove(working_copy_path)
                return {"success": False, "error": f"Music enhancement failed: {music_result.get('error')}"}
            
            # Step 4: Add text overlay
            logger.info(f"📝 Adding text overlay: {text_overlay}")
            
            overlay_success = self.text_styler.apply_text_to_video(
                input_video=temp_with_music,
                output_video=output_path,
                text=text_overlay
            )
            overlay_result = {'success': overlay_success}
            
            # Clean up temporary files
            if os.path.exists(temp_with_music):
                os.remove(temp_with_music)
            if working_copy_path != video_path and os.path.exists(working_copy_path):
                os.remove(working_copy_path)
            
            if overlay_result.get('success'):
                # Get compatibility score if using intelligent matching
                compatibility_score = 0.0
                if self.music_matcher:
                    try:
                        matches = self.music_matcher.find_best_music_matches(video_path, limit=1)
                        if matches:
                            for match in matches:
                                if match.music_path == music_path:
                                    compatibility_score = match.compatibility_score
                                    break
                    except:
                        pass
                
                return {
                    "success": True,
                    "output_path": output_path,
                    "music_used": Path(music_path).name,
                    "compatibility_score": compatibility_score,
                    "text_overlay": text_overlay,
                    "transcript": transcript,
                    "processing_details": {
                        "music_path": music_path,
                        "working_copy_used": working_copy_path != video_path,
                        "transcript_analysis_used": bool(transcript),
                        "music_volume": config.get('music_volume', 0.04)
                    }
                }
            else:
                return {"success": False, "error": f"Text overlay failed: {overlay_result.get('error')}"}
        
        except Exception as e:
            logger.error(f"Error processing video with specified music: {e}")
            return {"success": False, "error": str(e)}
    
    def get_music_compatibility_report(self, video_path: str) -> Dict[str, Any]:
        """Generate comprehensive music compatibility report for a video"""
        try:
            logger.info(f"Generating music compatibility report for: {Path(video_path).name}")
            
            # Create match index using the intelligent matcher
            matches = self.music_matcher.create_match_index_for_video(video_path)
            
            if not matches:
                logger.warning("No music matches found")
                return {
                    "video_path": video_path,
                    "matches": [],
                    "video_context": {},
                    "status": "no_matches"
                }
            
            # Get video context for additional details
            video_context = self.music_matcher.analyze_video_context(video_path)
            
            # Convert matches to serializable format
            serializable_matches = []
            for match in matches:
                serializable_matches.append({
                    "music_path": match.music_path,
                    "music_name": Path(match.music_path).stem,
                    "compatibility_score": match.compatibility_score,
                    "reasoning": match.reasoning,
                    "mood_match": match.mood_match,
                    "energy_match": match.energy_match,
                    "theme_match": match.theme_match
                })
            
            # Create comprehensive report
            report = {
                "video_path": video_path,
                "video_context": {
                    "content_type": video_context.content_type,
                    "visual_mood": video_context.visual_mood,
                    "themes": video_context.themes if hasattr(video_context, 'themes') else [],
                    "transcript": video_context.transcript[:200] + "..." if len(video_context.transcript) > 200 else video_context.transcript,
                    "duration": self._get_video_duration(video_path)
                },
                "matches": serializable_matches,
                "summary": {
                    "total_matches": len(matches),
                    "best_score": matches[0].compatibility_score if matches else 0,
                    "recommended_music": matches[0].music_path if matches else None
                },
                "timestamp": time.time()
            }
            
            logger.info(f"Music compatibility report generated: {len(matches)} matches, best score: {matches[0].compatibility_score if matches else 0}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating music compatibility report: {e}")
            return {
                "video_path": video_path,
                "error": str(e),
                "matches": [],
                "status": "error"
            }
    
    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds using ffprobe"""
        try:
            import subprocess
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', video_path
            ], capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception as e:
            logger.warning(f"Could not get video duration: {e}")
            return 0.0
    
    def _create_working_copy(self, video_path: str) -> str:
        """Create a working copy of the video to preserve original"""
        try:
            import shutil
            video_dir = os.path.dirname(video_path)
            video_name = Path(video_path).stem
            video_ext = Path(video_path).suffix
            working_copy_path = os.path.join(video_dir, f"{video_name}_working_copy{video_ext}")
            
            if not os.path.exists(working_copy_path):
                shutil.copy2(video_path, working_copy_path)
                logger.info(f"Created working copy: {working_copy_path}")
            
            return working_copy_path
        except Exception as e:
            logger.warning(f"Failed to create working copy: {e}")
            return video_path
    
    def use_transcript_analysis(self, video_path: str, music_path: str) -> Dict[str, Any]:
        """Use transcript analysis for video processing decisions"""
        try:
            # Extract transcript
            transcript = self.audio_analyzer.transcribe_audio(video_path)
            
            if not transcript or transcript == "No speech detected":
                return {
                    "has_speech": False,
                    "transcript": "",
                    "suggested_volume": 0.08,  # Higher volume when no speech
                    "overlay_text": "Music Experience"
                }
            
            # Analyze transcript for content
            analysis_prompt = f"""
            Analyze this video transcript and suggest processing parameters:
            
            TRANSCRIPT: {transcript[:500]}
            
            Provide response in JSON format:
            {{
                "has_speech": true/false,
                "content_type": "educational/entertainment/presentation/etc",
                "suggested_volume": 0.02-0.08,
                "overlay_text": "short catchy text for overlay"
            }}
            """
            
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a video processing assistant. Provide JSON analysis."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    temperature=0.1
                )
                
                response_content = response.choices[0].message.content.strip()
                if response_content.startswith('```json'):
                    response_content = response_content.split('```json')[1].split('```')[0].strip()
                
                analysis = json.loads(response_content)
                analysis["transcript"] = transcript[:200] + "..." if len(transcript) > 200 else transcript
                return analysis
                
            except Exception as e:
                logger.warning(f"Transcript analysis failed: {e}")
                return {
                    "has_speech": True,
                    "transcript": transcript[:200] + "..." if len(transcript) > 200 else transcript,
                    "suggested_volume": 0.04,
                    "overlay_text": "Enhanced Video"
                }
                
        except Exception as e:
            logger.error(f"Error in transcript analysis: {e}")
            return {
                "has_speech": False,
                "transcript": "",
                "suggested_volume": 0.06,
                "overlay_text": "Video Content"
            }

# Convenience function for quick processing
def smart_process_video(video_path: str, 
                       output_path: str, 
                       use_intelligent_music: bool = True,
                       config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function for quick smart video processing
    
    Args:
        video_path: Input video path
        output_path: Output video path
        use_intelligent_music: Whether to use AI music matching
        config: Optional configuration
        
    Returns:
        Processing results
    """
    
    processor = SmartVideoProcessor(use_intelligent_matching=use_intelligent_music)
    return processor.process_video_with_smart_music(video_path, output_path, config)


if __name__ == "__main__":
    # Example usage
    processor = SmartVideoProcessor()
    
    # Test with a sample video if available
    video_dir = Path("C:/Users/Isaia/Documents/Coding/N8N/shared/videos")
    if video_dir.exists():
        video_files = list(video_dir.glob("*.mp4"))[:3]  # First 3 videos
        
        if video_files:
            test_video = video_files[0]
            output_path = f"enhanced_{test_video.name}"
            
            print(f"🧪 Testing smart processing with: {test_video.name}")
            
            # Generate compatibility report
            report = processor.get_music_compatibility_report(str(test_video))
            print(f"📊 Compatibility report generated: {report.get('total_music_options', 0)} options analyzed")
            
            # Note: Actual processing would be run here
            print("📝 Note: Actual video processing skipped for demo")
        else:
            print("⚠️ No test videos found")
    else:
        print("⚠️ Video directory not found")
    
    print("✅ SmartVideoProcessor demonstration complete")
