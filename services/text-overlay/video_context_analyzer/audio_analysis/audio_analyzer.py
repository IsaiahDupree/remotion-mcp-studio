"""
Audio Analyzer

Analyzes video audio content to determine music presence, speech content, and overall audio quality.
Integrates with existing audiovideotools functionality and extends with deeper analysis.
"""

import os
import sys
import numpy as np
import logging
import tempfile
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import json
import re
import requests
from datetime import datetime

# For audio extraction and processing
from moviepy.editor import VideoFileClip
import librosa
from scipy.signal import spectrogram
import soundfile as sf

# Import existing audio analysis tools if available
try:
    from audiovideotools.audio_analysis.audio_analyzer import has_background_music
except ImportError:
    # Fallback implementation if the module isn't available
    def has_background_music(audio_path, threshold=0.15):
        """Simple fallback implementation to detect background music."""
        try:
            y, sr = librosa.load(audio_path, sr=None)
            
            # Calculate spectral flatness (high = noise/music, low = speech)
            spec_flatness = librosa.feature.spectral_flatness(y=y).mean()
            
            # Calculate low-frequency content (often higher in music)
            spec = np.abs(librosa.stft(y))
            low_freq_energy = np.sum(spec[:10,:]) / np.sum(spec)
            
            # Simple heuristic
            if spec_flatness > 0.05 and low_freq_energy > threshold:
                return True
            return False
        except Exception as e:
            logging.error(f"Error in fallback has_background_music: {e}")
            return False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('audio_analyzer')

class AudioAnalyzer:
    """
    Analyzes audio from video files to extract insights about speech, music, and audio quality.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        temp_dir: Optional[str] = None,
        model: str = "whisper-1",
        speech_threshold: float = 0.6,
        music_threshold: float = 0.15
    ):
        """
        Initialize the Audio Analyzer.
        
        Args:
            api_key: OpenAI API key for speech-to-text (defaults to env var)
            temp_dir: Directory for temporary audio files
            model: OpenAI Whisper API model to use
            speech_threshold: Threshold for speech detection
            music_threshold: Threshold for music detection
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Will use basic analysis only.")
            
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.model = model
        self.speech_threshold = speech_threshold
        self.music_threshold = music_threshold
        
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def extract_audio(self, video_path: str) -> str:
        """
        Extract audio from video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Path to extracted audio file
        """
        video_filename = Path(video_path).stem
        audio_path = os.path.join(self.temp_dir, f"{video_filename}_audio.wav")
        
        try:
            with VideoFileClip(video_path) as video:
                if video.audio:
                    video.audio.write_audiofile(
                        audio_path,
                        codec='pcm_s16le',  # Uncompressed for best quality analysis
                        verbose=False,
                        logger=None
                    )
                    logger.info(f"Audio extracted to {audio_path}")
                    return audio_path
                else:
                    logger.warning(f"No audio track in video {video_path}")
                    return ""
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return ""
    
    def analyze_audio_features(self, audio_path: str) -> Dict[str, Any]:
        """
        Extract and analyze audio features.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary of audio features and analysis
        """
        try:
            y, sr = librosa.load(audio_path, sr=None)
            
            # Extract audio features
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Speech presence (voiced segments)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            
            # Spectral features
            spec_flatness = librosa.feature.spectral_flatness(y=y).mean()
            spec_contrast = librosa.feature.spectral_contrast(y=y, sr=sr).mean()
            
            # Volume analysis
            rms = librosa.feature.rms(y=y).mean()
            
            # Low frequency content
            spec = np.abs(librosa.stft(y))
            low_freq_energy = np.sum(spec[:10,:]) / np.sum(spec)
            
            # Detect background music using existing tool
            has_music = has_background_music(audio_path, threshold=self.music_threshold)
            
            # Calculate additional speech characteristics
            zero_crossings = librosa.feature.zero_crossing_rate(y).mean()
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_means = mfccs.mean(axis=1)
            
            # Speech detection heuristic
            has_speech = (zero_crossings > 0.05 and mfcc_means[0] > self.speech_threshold)
            
            # Volume consistency (less variance = more likely music)
            rms_frames = librosa.feature.rms(y=y)[0]
            volume_variance = np.var(rms_frames) / np.mean(rms_frames) if np.mean(rms_frames) > 0 else 0
            
            return {
                "duration": float(duration),
                "tempo": float(tempo),
                "spectral_flatness": float(spec_flatness),
                "spectral_contrast": float(spec_contrast),
                "rms_volume": float(rms),
                "low_frequency_energy": float(low_freq_energy),
                "has_background_music": bool(has_music),
                "has_speech": bool(has_speech),
                "volume_variance": float(volume_variance),
                "speech_confidence": float(1.0 - spec_flatness) if has_speech else 0.0,
                "suggested_background_music": not has_music
            }
            
        except Exception as e:
            logger.error(f"Error analyzing audio features: {e}")
            return {
                "error": str(e),
                "has_background_music": False,
                "has_speech": False,
                "suggested_background_music": True
            }
    
    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio using OpenAI Whisper API.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcription results
        """
        if not self.api_key or not os.path.exists(audio_path):
            return {"error": "API key not provided or audio file not found"}
        
        try:
            # Check file size (OpenAI limit is 25MB)
            file_size = os.path.getsize(audio_path) / (1024 * 1024)  # MB
            logger.info(f"Audio file size: {file_size:.2f} MB")
            
            # If file is too large, compress it or skip transcription
            if file_size > 24:  # Leave 1MB buffer
                logger.warning(f"Audio file too large ({file_size:.2f} MB). Skipping transcription.")
                return {
                    "text": "Audio file too large for transcription",
                    "segments": [],
                    "language": "unknown",
                    "timestamp": datetime.now().isoformat(),
                    "error": "File size exceeds API limit"
                }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with open(audio_path, 'rb') as audio_file:
                files = {
                    'file': (os.path.basename(audio_path), audio_file, 'audio/wav'),
                    'model': (None, self.model),
                    'response_format': (None, 'verbose_json'),
                }
                
                response = requests.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers=headers,
                    files=files
                )
                
                if response.status_code != 200:
                    logger.error(f"API error: {response.status_code}, {response.text}")
                    return {"error": f"API error: {response.status_code}"}
                
                result = response.json()
                
                # Process segments to get timing information
                segments = []
                if "segments" in result:
                    segments = [
                        {
                            "start": segment.get("start", 0),
                            "end": segment.get("end", 0),
                            "text": segment.get("text", "")
                        }
                        for segment in result.get("segments", [])
                    ]
                
                return {
                    "text": result.get("text", ""),
                    "segments": segments,
                    "language": result.get("language", ""),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return {"error": str(e)}
    
    def generate_catchy_text_from_audio(self, transcription: Dict[str, Any]) -> str:
        """
        Generate catchy text overlay suggestion based on transcription.
        
        Args:
            transcription: Transcription result from transcribe_audio
            
        Returns:
            Suggested catchy text
        """
        if "error" in transcription or not transcription.get("text"):
            return ""
        
        try:
            text = transcription["text"]
            
            # Very basic approach: Find 4-6 word sequences that might be impactful
            words = re.findall(r'\b\w+\b', text)
            
            # Try to find phrases with important keywords
            important_keywords = ["amazing", "incredible", "best", "ultimate", "perfect", 
                                "stunning", "awesome", "essential", "top", "super", 
                                "extreme", "mind", "blow", "insane", "crazy", "learn"]
            
            # Find sequences containing important words
            candidates = []
            for i in range(len(words) - 5):
                phrase = " ".join(words[i:i+6])
                if any(keyword in phrase.lower() for keyword in important_keywords):
                    candidates.append(phrase)
            
            if candidates:
                return max(candidates, key=lambda x: sum(1 for keyword in important_keywords if keyword in x.lower()))
            
            # Fallback: Just take first 6 words or a random 6-word segment
            if len(words) <= 6:
                return " ".join(words)
            else:
                # Choose a segment from the middle for better context
                mid_point = len(words) // 2
                return " ".join(words[mid_point - 3:mid_point + 3])
                
        except Exception as e:
            logger.error(f"Error generating catchy text: {e}")
            return ""
    
    def analyze_video_audio(self, video_path: str) -> Dict[str, Any]:
        """
        Complete audio analysis pipeline for a video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Complete analysis results
        """
        try:
            # Extract audio
            audio_path = self.extract_audio(video_path)
            if not audio_path:
                return {
                    "error": "Failed to extract audio",
                    "has_background_music": False,
                    "suggested_background_music": True,
                    "catchy_text": ""
                }
            
            # Analyze audio features
            features = self.analyze_audio_features(audio_path)
            
            # Transcribe if API key available
            transcription = {}
            if self.api_key:
                transcription = self.transcribe_audio(audio_path)
                features["transcription"] = transcription.get("text", "")
                
                # Generate catchy text from transcription
                catchy_text = self.generate_catchy_text_from_audio(transcription)
                features["catchy_text_from_audio"] = catchy_text
            
            # Clean up temp file
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            except:
                pass
                
            return features
            
        except Exception as e:
            logger.error(f"Error in audio analysis pipeline: {e}")
            return {
                "error": str(e),
                "has_background_music": False,
                "suggested_background_music": True,
                "catchy_text": ""
            }
