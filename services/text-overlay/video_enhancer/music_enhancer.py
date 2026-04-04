"""
Music Enhancement Module
=====================

This module provides functionality for enhancing videos with background music and AI-generated text overlays.

Features include:
- Speech detection for dynamic volume adjustment
- Fast, multi-step processing for reliable video enhancing
- Automatic detection of existing background music
- Support for SoundCloud music download and integration
- AI-powered text overlay generation from video frames and transcripts
- Support for local music library selection
"""

import os
import sys
import time
import logging
import tempfile
import subprocess
import json
from typing import Dict, Any, Optional, Tuple, List, Union
from pathlib import Path

# Import our custom modules
from .audio_processor import AudioProcessor
from .media_utils import MediaUtils

# Try to import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import optional dependencies
try:
    from utils.soundcloud_ytdlp import SoundCloudYtDlp
    from audiovideotools.audio_analysis.audio_analyzer import has_background_music
    soundcloud_imports_success = True
except ImportError as e:
    logging.warning(f"Could not import SoundCloud utilities: {e}")
    soundcloud_imports_success = False

# Import text overlay
try:
    from .text_overlay import TextOverlayEnhancer
    text_overlay_imports_success = True
except ImportError as e:
    logging.warning(f"Could not import TextOverlayEnhancer: {e}")
    text_overlay_imports_success = False

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("music_enhancer")


class MusicEnhancer:
    """
    Class for enhancing videos with background music and optionally text overlays.

    This class provides functionality to:
    1. Detect existing background music in videos
    2. Download music from SoundCloud using yt-dlp
    3. Add background music with speech emphasis
    4. Optimize volume levels for best audio quality
    5. Optionally add AI-generated text overlays

    Attributes:
        output_dir (str): Directory for output files
        music_dir (str): Directory for downloaded/generated music
        speech_emphasis (float): Factor to emphasize speech over music (higher = quieter music)
        soundcloud_downloader (SoundCloudYtDlp): Downloader for SoundCloud tracks
        audio_processor (AudioProcessor): Handler for audio processing operations
        media_utils (MediaUtils): Utility for media operations
    """

    def __init__(
        self,
        output_dir: str = "./enhanced_videos",
        music_dir: Optional[str] = None,
        speech_emphasis: float = 1.5,
        soundcloud_excel_path=None,
        use_local_library=True,
    ):
        """
        Initialize the MusicEnhancer.

        Args:
            output_dir: Directory for output files
            music_dir: Directory for downloaded/generated music (default: output_dir/music)
            speech_emphasis: Factor to emphasize speech over music (higher = quieter music)
            soundcloud_excel_path: Path to SoundCloud tracks Excel file
            use_local_library: Whether to use local music library
        """
        self.output_dir = output_dir
        self.music_dir = music_dir or os.path.join(output_dir, "music")
        self.speech_emphasis = speech_emphasis
        self.soundcloud_excel_path = soundcloud_excel_path
        self.use_local_library = use_local_library
        self.local_music_index = None

        # Create directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.music_dir, exist_ok=True)

        # Initialize components
        self.audio_processor = AudioProcessor(speech_emphasis=speech_emphasis)
        self.media_utils = MediaUtils()

        # Check for FFmpeg availability
        if not self.media_utils.check_ffmpeg_available():
            logger.error("FFmpeg is required but not found. Please install FFmpeg.")
            raise RuntimeError("FFmpeg not available")

        # Try to load local music library first
        if use_local_library:
            self._load_local_music_library()
            if self.local_music_index:
                logger.info(f"Local music library loaded: {len(self.local_music_index)} tracks")

        # Initialize SoundCloud downloader if available
        if soundcloud_imports_success:
            self.soundcloud_downloader = SoundCloudYtDlp(output_dir=self.music_dir)
            logger.info("SoundCloud downloader initialized")
        else:
            self.soundcloud_downloader = None
            logger.warning("SoundCloud downloader not available - will use fallback methods")

        # Initialize Text Overlay enhancer if available
        if text_overlay_imports_success:
            try:
                self.text_enhancer = TextOverlayEnhancer()
                logger.info("Text overlay enhancer initialized")
            except Exception as e:
                logger.warning(f"Could not initialize TextOverlayEnhancer: {e}")
                self.text_enhancer = None
        else:
            self.text_enhancer = None
            logger.warning("Text overlay enhancer not available - text overlay features will be disabled")

    def _load_local_music_library(self):
        """Load local music library index"""
        try:
            music_index_path = Path("music_library/music_index.json")
            if music_index_path.exists():
                with open(music_index_path, 'r') as f:
                    self.local_music_index = json.load(f)
                logger.info(f"Loaded local music library: {len(self.local_music_index)} tracks")
            else:
                logger.warning("Local music index not found: music_library/music_index.json")
                self.local_music_index = None
        except Exception as e:
            logger.error(f"Error loading local music library: {e}")
            self.local_music_index = None

    def _select_local_music(self, criteria=None):
        """Select music from local library"""
        if not self.local_music_index:
            return None
        
        filtered_tracks = self.local_music_index
        
        # Apply criteria if provided
        if criteria:
            if 'genre' in criteria:
                filtered_tracks = [t for t in filtered_tracks 
                                 if t['genre'].lower() == criteria['genre'].lower()]
            
            if 'max_size_mb' in criteria:
                filtered_tracks = [t for t in filtered_tracks 
                                 if t['size_mb'] <= criteria['max_size_mb']]
            
            if 'name_contains' in criteria:
                name_filter = criteria['name_contains'].lower()
                filtered_tracks = [t for t in filtered_tracks 
                                 if name_filter in t['name'].lower()]
        
        if filtered_tracks:
            selected = random.choice(filtered_tracks)
            logger.info(f"Selected local music: {selected['name']} ({selected['genre']}, {selected['size_mb']} MB)")
            return selected['file']
        
        # Fallback to any track
        if self.local_music_index:
            selected = random.choice(self.local_music_index)
            logger.info(f"Selected fallback local music: {selected['name']}")
            return selected['file']
        
        return None

    def detect_background_music(self, video_path: str) -> bool:
        """
        Detect if a video already has background music.

        Args:
            video_path: Path to the video file
            
        Returns:
            True if background music detected, False otherwise
        """
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False
            
        try:
            # Extract audio for analysis
            temp_dir = tempfile.mkdtemp()
            audio_path = os.path.join(temp_dir, "temp_audio.wav")
            
            # Use ffmpeg to extract audio with improved error handling
            extract_cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-vn',  # Disable video recording
                '-acodec', 'pcm_s16le',  # Use PCM format for better compatibility
                '-ar', '44100',  # Standard sample rate
                '-ac', '2',  # Stereo
                audio_path
            ]
            
            logger.info("Extracting audio for background music detection...")
            result = subprocess.run(
                extract_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            # Log any extraction errors
            if result.returncode != 0:
                logger.warning(f"Audio extraction error: {result.stderr[:200]}...")
            
            # Check if audio file was created
            if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
                logger.warning("Could not extract audio or audio file is too small. Assuming no background music.")
                return False
                
            # Use audio analyzer if available
            if 'has_background_music' in globals() or 'has_background_music' in locals():
                has_music = has_background_music(video_path, audio_path)
                logger.info(f"Background music detection result: {'Present' if has_music else 'Not present'}")
                
                # Clean up temp files
                os.remove(audio_path)
                os.rmdir(temp_dir)
                
                return has_music
            else:
                logger.warning("Audio analyzer not available. Using basic heuristics.")
                
                # Use ffprobe to analyze audio characteristics
                analyze_cmd = [
                    'ffprobe', '-i', audio_path,
                    '-show_entries', 'format=duration',
                    '-v', 'quiet',
                    '-of', 'csv=p=0'
                ]
                
                result = subprocess.run(analyze_cmd, capture_output=True, text=True)
                
                # Clean up temp files
                os.remove(audio_path)
                os.rmdir(temp_dir)
                
                try:
                    # Very basic heuristic: if audio is present, assume no background music
                    # This is a fallback when proper analysis isn't available
                    duration = float(result.stdout.strip())
                    return duration > 10  # Arbitrary threshold for "likely has music"
                except (ValueError, IndexError):
                    logger.error("Could not parse audio analysis output")
                    return False
                    
        except Exception as e:
            logger.error(f"Error detecting background music: {e}")
            return False
    
    def download_music_from_soundcloud(self, url: str, output_filename: Optional[str] = None) -> Optional[str]:
        """
        Download a music track from SoundCloud.
        
        Args:
            url: SoundCloud track URL
            output_filename: Desired output filename (None for auto-generated)
            
        Returns:
            Path to downloaded music file or None if download failed
        """
        if not self.soundcloud_downloader:
            logger.error("SoundCloud downloader not available")
            return None
            
        try:
            logger.info(f"Downloading SoundCloud track: {url}")
            
            # Prepare output template if filename specified
            output_template = None
            if output_filename:
                output_template = os.path.join(self.music_dir, output_filename)
            
            # Download the track
            track_path = self.soundcloud_downloader.download_track(url, output_template)
            
            if track_path and os.path.exists(track_path):
                logger.info(f"Successfully downloaded track to: {track_path}")
                return track_path
                
            logger.error("Failed to download track")
            return None
            
        except Exception as e:
            logger.error(f"Error downloading SoundCloud track: {e}")
            return None
    
    def create_sample_music(self, output_path: Optional[str] = None, duration: int = 60) -> Optional[str]:
        """
        Create a sample music file for testing or when downloads fail.
        
        Args:
            output_path: Path to save the sample music file (None for auto-generated)
            duration: Duration of the sample music in seconds
            
        Returns:
            Path to the created sample music file or None if failed
        """
        try:
            if not output_path:
                output_path = os.path.join(self.music_dir, "sample_music.mp3")
                
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Generate a pleasant sample music file (major chord progression)
            cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi',
                # Use a more pleasant sound than a simple sine wave
                '-i', f'aevalsrc=0.3*sin(440*2*PI*t)+0.3*sin(550*2*PI*t)+0.3*sin(660*2*PI*t):s=44100:d={duration}',
                '-c:a', 'mp3',
                '-b:a', '192k',
                output_path
            ]
            
            logger.info(f"Creating sample music file: {output_path}")
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if os.path.exists(output_path):
                logger.info(f"Created sample music: {output_path}")
                return output_path
            
            logger.error("Failed to create sample music file")
            return None
            
        except Exception as e:
            logger.error(f"Exception creating sample music: {e}")
            return None
    
    def check_video_has_speech(self, video_path: str) -> bool:
        """
        Check if a video has speech audio.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            True if speech detected, False otherwise
        """
        try:
            # Extract audio to temporary file
            temp_dir = tempfile.mkdtemp()
            audio_path = os.path.join(temp_dir, "temp_audio.wav")
            
            # Extract audio using ffmpeg with improved settings
            extract_cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-vn',  # Disable video
                '-acodec', 'pcm_s16le',  # Use PCM format for better compatibility
                '-ar', '44100',  # Standard sample rate
                '-ac', '1',  # Mono (better for speech detection)
                '-t', '30',   # Limit to first 30 seconds for faster processing
                audio_path
            ]
            
            result = subprocess.run(
                extract_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            # Log any extraction errors
            if result.returncode != 0:
                logger.warning(f"Audio extraction error: {result.stderr[:200]}...")
            
            # Check if audio file was created
            if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
                logger.warning("Could not extract audio for speech detection or audio file is too small")
                return False
                
            # Use ffprobe to analyze audio levels with silencedetect filter
            speech_cmd = [
                'ffprobe', '-i', audio_path,
                '-af', 'silencedetect=n=-30dB:d=0.5',
                '-f', 'null', '-'
            ]
            
            result = subprocess.run(
                speech_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Analyze silence detection output
            if result.stderr:
                # Count silence periods
                silence_count = result.stderr.count("silence_end")
                total_silence = 0
                
                # Extract silence durations
                import re
                silence_durations = re.findall(r"silence_duration: ([\d\.]+)", result.stderr)
                
                for duration in silence_durations:
                    total_silence += float(duration)
                
                # Calculate approximate audio duration
                duration_match = re.search(r"Duration: ([\d\.:]+)", result.stderr)
                duration = 0
                if duration_match:
                    time_parts = duration_match.group(1).split(":")
                    duration = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + float(time_parts[2])
                
                # If we have many silence periods or total silence is less than 60% of audio
                # This likely means there's speech
                if silence_count > 5 and (duration == 0 or total_silence / duration < 0.6):
                    logger.info("Speech detected in video")
                    return True
            
            logger.info("No speech detected in video")
            return False
        
        except Exception as e:
            logger.error(f"Error checking for speech: {e}")
            return False  # Assume no speech on error
            
    def preprocess_music_file(self, music_path: str) -> str:
        """
        Preprocess music file to optimize for faster addition to video.
        
        Args:
            music_path: Path to the original music file
            
        Returns:
            Path to the preprocessed music file
        """
        try:
            # Create temp directory for processed file
            temp_dir = tempfile.mkdtemp()
            processed_path = os.path.join(temp_dir, "processed_music.mp3")
            
            # Command to preprocess music - convert to mono, lower quality for faster processing
            cmd = [
                'ffmpeg', '-y',
                '-i', music_path,
                '-ac', '1',       # Convert to mono
                '-ar', '22050',   # Lower sample rate
                '-b:a', '64k',    # Lower bitrate
                '-acodec', 'mp3', # MP3 codec
                processed_path
            ]
            
            logger.info("Preprocessing music file for faster processing...")
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            
            if os.path.exists(processed_path):
                logger.info(f"Successfully preprocessed music: {processed_path}")
                return processed_path
            else:
                logger.warning("Failed to preprocess music, using original file")
                return music_path
        except Exception as e:
            logger.error(f"Error preprocessing music: {e}")
            return music_path
            
    def add_background_music(self, video_path: str, music_path: str,
                           output_path: str = None,
                           volume_factor: float = 0.04, # -28dB, optimized for -25 to -30dB range
                           speech_emphasis_factor: Optional[float] = None,
                           auto_adjust_volume: bool = True) -> Dict[str, Any]:
        """
        Add background music to a video file using the faster multi-step approach.
        
        Args:
            video_path: Path to input video
            music_path: Path to music file
            output_path: Path to save enhanced video (if None, will generate one)
            volume_factor: Base volume factor for music (lower = quieter music)
            speech_emphasis_factor: Factor to emphasize speech (higher = quieter music during speech)
            auto_adjust_volume: Whether to dynamically adjust volume based on speech
            
        Returns:
            Dictionary with results including success status and output path
        """
        # Validate inputs
        if not os.path.exists(video_path):
            logger.error(f"Input video not found: {video_path}")
            return {"success": False, "error": "Input video not found"}
            
        if not os.path.exists(music_path):
            logger.error(f"Music file not found: {music_path}")
            return {"success": False, "error": "Music file not found"}
        
        try:
            # Generate output path if not provided
            if output_path is None:
                video_basename = os.path.basename(video_path).split('.')[0]
                output_path = os.path.join(self.output_dir, f"{video_basename}_enhanced.mp4")
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Step 1: Preprocess the music file for better mixing
            preprocessed_music = self.preprocess_music_file(music_path)
            
            # Step 2: Use the AudioProcessor to add background music with dynamic volume adjustment
            has_speech = self.audio_processor.detect_speech_in_video(video_path)
            
            # Use provided speech emphasis factor or default
            emphasis = speech_emphasis_factor if speech_emphasis_factor is not None else self.speech_emphasis
            
            # If video has speech and auto_adjust_volume is enabled, use dynamic volume adjustment
            if has_speech and auto_adjust_volume:
                logger.info(f"Video has speech, using dynamic volume adjustment with emphasis factor {emphasis}")
                result_path = self.audio_processor.add_background_music_with_speech_emphasis(
                    video_path=video_path,
                    music_path=preprocessed_music,
                    output_path=output_path,
                    base_volume=volume_factor,
                    speech_emphasis_factor=emphasis
                )
            else:
                # Simple mixing for videos without speech or when auto_adjust_volume is disabled
                logger.info(f"Using simple audio mixing with constant volume {volume_factor}")
                result_path = self.audio_processor.add_background_music_simple(
                    video_path=video_path,
                    music_path=preprocessed_music,
                    output_path=output_path,
                    volume_factor=volume_factor
                )
            
            if not result_path or not os.path.exists(result_path):
                logger.error("Failed to add background music")
                return {"success": False, "error": "Failed to add background music"}
            
            logger.info(f"Successfully added background music to video: {result_path}")
            return {
                "success": True,
                "output_video": result_path,
                "music_added": True,
                "music_path": music_path,
                "has_speech": has_speech,
                "dynamic_volume": has_speech and auto_adjust_volume
            }
        except Exception as e:
            logger.error(f"Error adding background music: {e}")
            return {"success": False, "error": str(e)}
            
    def enhance_video_with_music(
        self,
        video_path: str,
        output_path: str,
        soundcloud_url: Optional[str] = None,
        music_path: Optional[str] = None,
        speech_emphasis: Optional[float] = None,
        auto_detect_existing_music: bool = True
    ) -> Dict[str, Any]:
        """
        Enhance a video by adding background music.
        
        This method handles the entire workflow of:
        1. Checking if the video already has background music
        2. Getting music from SoundCloud or using provided/sample music
        3. Adding the music with speech emphasis
        
        Args:
            video_path: Path to the input video
            output_path: Path for the enhanced output video
            soundcloud_url: URL to SoundCloud track (None to use music_path or sample music)
            music_path: Path to existing music file (None to download or generate)
            speech_emphasis: Factor to emphasize speech (higher = quieter music)
            auto_detect_existing_music: Whether to check for existing background music
            
        Returns:
            Dict with results including success status and metadata
        """
        if not os.path.exists(video_path):
            logger.error(f"Input video not found: {video_path}")
            return {"success": False, "error": "Input video not found"}
        
        try:
            # Step 1: Check if the video already has background music
            if auto_detect_existing_music and self.detect_background_music(video_path):
                logger.info("Video already has background music. Skipping enhancement.")
                return {
                    "success": True,
                    "output_video": video_path,
                    "music_added": False,
                    "reason": "Video already has background music"
                }
            
            # Step 2: Get music file (download, use provided, or create sample)
            music_file = None
            
            # Option 1: Use provided music path
            if music_path and os.path.exists(music_path):
                logger.info(f"Using provided music file: {music_path}")
                music_file = music_path
                
            # Option 2: Download from SoundCloud
            elif soundcloud_url and self.soundcloud_downloader:
                logger.info(f"Downloading music from SoundCloud: {soundcloud_url}")
                video_basename = os.path.basename(video_path).split('.')[0]
                output_filename = f"{video_basename}_music.mp3"
                music_file = self.download_music_from_soundcloud(soundcloud_url, output_filename)
            
            # Option 3: Create sample music as fallback
            if not music_file:
                logger.info("Creating sample music as fallback")
                video_basename = os.path.basename(video_path).split('.')[0]
                sample_path = os.path.join(self.music_dir, f"{video_basename}_sample_music.mp3")
                music_file = self.create_sample_music(sample_path)
            
            if not music_file:
                logger.error("Could not obtain music file")
                return {"success": False, "error": "Could not obtain music file"}
            
            # Step 3: Add background music to video
            logger.info(f"Adding background music to video: {video_path}")
            result = self.add_background_music(
                video_path=video_path,
                music_path=music_file,
                output_path=output_path,
                speech_emphasis_factor=speech_emphasis
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error enhancing video with music: {e}")
            return {"success": False, "error": str(e)}

    def enhance_video_with_text_overlay(self, video_path: str, output_path: str, custom_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhance a video with text overlay using the TextOverlayEnhancer.
        
        Args:
            video_path: Path to input video
            output_path: Path for output video
            custom_text: Optional custom text to use instead of AI-generated text
            
        Returns:
            Dictionary with results including success status and output path
        """
        if not self.text_enhancer:
            logger.warning("TextOverlayEnhancer not available. Skipping text overlay.")
            return {"success": False, "error": "TextOverlayEnhancer not available"}
        
        try:
            result = self.text_enhancer.enhance_video(
                video_path=video_path,
                output_path=output_path,
                custom_text=custom_text
            )
            logger.info("Text overlay added successfully")
            return {"success": True, **result}
        except Exception as e:
            logger.error(f"Error adding text overlay: {e}")
            return {"success": False, "error": str(e)}
            
    def enhance_video_with_music(
        self,
        video_path: str,
        output_path: str,
        soundcloud_url: Optional[str] = None,
        music_path: Optional[str] = None,
        speech_emphasis: Optional[float] = None,
        auto_detect_existing_music: bool = True
    ) -> Dict[str, Any]:
        """
        Enhance a video by adding background music.
        
        This method handles the entire workflow of:
        1. Checking if the video already has background music
        2. Getting music from SoundCloud or using provided/sample music
        3. Adding the music with speech emphasis
        
        Args:
            video_path: Path to the input video
            output_path: Path for the enhanced output video
            soundcloud_url: URL to SoundCloud track (None to use music_path or sample music)
            music_path: Path to existing music file (None to download or generate)
            speech_emphasis: Factor to emphasize speech (higher = quieter music)
            auto_detect_existing_music: Whether to check for existing background music
            
        Returns:
            Dict with results including success status and metadata
        """
        if not os.path.exists(video_path):
            logger.error(f"Input video not found: {video_path}")
            return {"success": False, "error": "Input video not found"}
        
        try:
            # Step 1: Check if the video already has background music
            if auto_detect_existing_music and self.detect_background_music(video_path):
                logger.info("Video already has background music. Skipping enhancement.")
                return {
                    "success": True,
                    "output_video": video_path,
                    "music_added": False,
                    "reason": "Video already has background music"
                }
            
            # Step 2: Get music file (download, use provided, or create sample)
            music_file = None
            
            # Option 1: Use provided music path
            if music_path and os.path.exists(music_path):
                logger.info(f"Using provided music file: {music_path}")
                music_file = music_path
                
            # Option 2: Download from SoundCloud
            elif soundcloud_url and self.soundcloud_downloader:
                logger.info(f"Downloading music from SoundCloud: {soundcloud_url}")
                video_basename = os.path.basename(video_path).split('.')[0]
                output_filename = f"{video_basename}_music.mp3"
                music_file = self.download_music_from_soundcloud(soundcloud_url, output_filename)
            
            # Option 3: Create sample music as fallback
            if not music_file:
                logger.info("Creating sample music as fallback")
                video_basename = os.path.basename(video_path).split('.')[0]
                sample_path = os.path.join(self.music_dir, f"{video_basename}_sample_music.mp3")
                music_file = self.create_sample_music(sample_path)
            
            if not music_file:
                logger.error("Could not obtain music file")
                return {"success": False, "error": "Could not obtain music file"}
            
            # Step 3: Add background music to video
            logger.info(f"Adding background music to video: {video_path}")
            result = self.add_background_music(
                video_path=video_path,
                music_path=music_file,
                output_path=output_path,
                speech_emphasis_factor=speech_emphasis,
                auto_adjust_volume=True
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error enhancing video with music: {e}")
            return {"success": False, "error": str(e)}
