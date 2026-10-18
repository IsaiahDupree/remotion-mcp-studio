#!/usr/bin/env python3
"""
Intelligent Video Content Analyzer - Fixed Version
- Simple method for enhanced video analysis with OpenAI integration
"""
import cv2
import whisper
import requests
import json
import os
import subprocess
import tempfile
import base64
from pathlib import Path
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
import time
import re
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VideoAnalysis:
    """Structure for video analysis results"""
    has_existing_captions: bool
    existing_captions: Optional[str]
    transcript: Optional[str]
    visual_analysis: Optional[str]
    suggested_overlay: str
    confidence_score: float
    frame_samples: List[str]
    processing_time: float

class IntelligentVideoAnalyzer:
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.whisper_model = None
        self.load_whisper_model()
    
    def load_whisper_model(self):
        """Load Whisper model for transcription"""
        try:
            logger.info("Loading Whisper model...")
            self.whisper_model = whisper.load_model("base")
            logger.info("✅ Whisper model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load Whisper model: {e}")
            self.whisper_model = None

    def get_video_info(self, video_path: str) -> Optional[Dict]:
        """Extract basic video information using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                video_stream = next(
                    (stream for stream in data['streams'] if stream['codec_type'] == 'video'),
                    None
                )
                
                if video_stream:
                    return {
                        'duration': float(data['format'].get('duration', 0)),
                        'width': int(video_stream.get('width', 0)),
                        'height': int(video_stream.get('height', 0)),
                        'fps': eval(video_stream.get('r_frame_rate', '30/1'))
                    }
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
        return None

    def detect_existing_captions(self, video_path: str) -> Optional[str]:
        """Try to detect existing captions using OCR on sample frames"""
        try:
            # Sample a few frames to check for text
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = frame_count / fps if fps > 0 else 0
            
            # Sample frames from different parts of the video
            sample_times = [duration * 0.25, duration * 0.5, duration * 0.75]
            detected_text = []
            
            for sample_time in sample_times:
                frame_number = int(sample_time * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                
                if ret:
                    # Simple text detection using contours (basic OCR alternative)
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    # Look for text-like rectangular areas
                    contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    text_regions = 0
                    for contour in contours:
                        x, y, w, h = cv2.boundingRect(contour)
                        aspect_ratio = w / h if h > 0 else 0
                        # Text typically has certain aspect ratios
                        if 0.1 < aspect_ratio < 10 and w > 50 and h > 10:
                            text_regions += 1
                    
                    if text_regions > 5:  # Likely has overlay text
                        detected_text.append(f"Text overlay detected at {sample_time:.1f}s")
            
            cap.release()
            
            if detected_text:
                return "; ".join(detected_text)
                
        except Exception as e:
            logger.error(f"Error detecting captions: {e}")
        
        return None

    def extract_transcript(self, video_path: str) -> Optional[str]:
        """Extract transcript using Whisper"""
        if not self.whisper_model:
            logger.warning("Whisper model not available for transcription")
            return None
            
        try:
            logger.info("Extracting audio transcript...")
            result = self.whisper_model.transcribe(video_path)
            transcript = result["text"].strip()
            
            if transcript:
                logger.info(f"Transcript extracted: {len(transcript)} characters")
                return transcript
                
        except Exception as e:
            logger.error(f"Error extracting transcript: {e}")
        
        return None

    def sample_frames_for_analysis(self, video_path: str, num_frames: int = 5) -> List[str]:
        """Sample frames and convert to base64 for AI analysis"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return []
            
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frames_to_sample = []
            
            # Sample frames evenly distributed
            for i in range(num_frames):
                frame_number = int((i + 1) * frame_count / (num_frames + 1))
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                
                if ret:
                    # Resize frame for efficiency
                    frame = cv2.resize(frame, (640, 360))
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_b64 = base64.b64encode(buffer).decode('utf-8')
                    frames_to_sample.append(frame_b64)
            
            cap.release()
            return frames_to_sample
            
        except Exception as e:
            logger.error(f"Error sampling frames: {e}")
            return []

    def analyze_frames_with_ai(self, frame_samples: List[str], openai_api_key: Optional[str] = None) -> Optional[str]:
        """Analyze frames using OpenAI Vision API"""
        api_key = openai_api_key or self.openai_api_key
        if not api_key or not frame_samples:
            return None
            
        try:
            # Use only the first frame for analysis to save costs
            frame_b64 = frame_samples[0]
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe this video frame in 2-3 sentences focusing on the main subject, activity, mood, and visual elements. Be concise and specific."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{frame_b64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 100
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                logger.warning(f"OpenAI Vision API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error in AI frame analysis: {e}")
            
        return None

    def analyze_video_for_perfect_overlay(self, video_path: str, openai_api_key: Optional[str] = None) -> Dict:
        """
        Enhanced video analysis for perfect text overlay generation:
        - Check for existing captions
        - Extract/generate transcript if needed
        - Sample frames efficiently based on video length
        - Blend transcript + frame context for optimal overlay text
        """
        try:
            start_time = time.time()
            logger.info(f"🎬 Starting enhanced video analysis: {Path(video_path).name}")
            
            # Initialize result structure
            result = {
                'video_path': video_path,
                'has_existing_captions': False,
                'existing_captions': None,
                'transcript': None,
                'visual_analysis': None,
                'suggested_overlay': '',
                'confidence_score': 0.0,
                'frame_samples_count': 0,
                'processing_time': 0.0,
                'video_info': {},
                'analysis_strategy': 'enhanced_ai_blend',
                'used_openai_analysis': False
            }
            
            # Step 1: Get video information
            video_info = self.get_video_info(video_path)
            if not video_info:
                raise Exception("Could not extract video information")
                
            result['video_info'] = {
                'duration': video_info.get('duration', 0),
                'resolution': f"{video_info.get('width', 0)}x{video_info.get('height', 0)}",
                'fps': video_info.get('fps', 30)
            }
            
            # Step 2: Check for existing captions
            logger.info("🔍 Checking for existing captions...")
            existing_captions = self.detect_existing_captions(video_path)
            result['has_existing_captions'] = bool(existing_captions)
            result['existing_captions'] = existing_captions
            
            if existing_captions:
                logger.info(f"📋 Found existing captions: {existing_captions[:50]}...")
                result['suggested_overlay'] = existing_captions
                result['confidence_score'] = 0.9
                result['processing_time'] = time.time() - start_time
                return result
            
            # Step 3: Extract transcript
            logger.info("🎤 Extracting transcript...")
            transcript = self.extract_transcript(video_path)
            result['transcript'] = transcript
            
            # Step 4: Sample frames efficiently based on video length
            duration = video_info.get('duration', 0)
            if duration <= 30:
                frame_count = 3  # Short videos: 3 frames
            elif duration <= 60:
                frame_count = 5  # Medium videos: 5 frames
            else:
                frame_count = 8  # Long videos: 8 frames
                
            logger.info(f"🖼️ Sampling {frame_count} frames from {duration:.1f}s video...")
            frame_samples = self.sample_frames_for_analysis(video_path, num_frames=frame_count)
            result['frame_samples_count'] = len(frame_samples)
            
            # Step 5: AI Visual Analysis
            visual_analysis = None
            if frame_samples:
                logger.info("👁️ Performing visual analysis...")
                visual_analysis = self.analyze_frames_with_ai(frame_samples, openai_api_key)
                result['visual_analysis'] = visual_analysis
                
            # Step 6: Generate perfect overlay using AI
            api_key = openai_api_key or self.openai_api_key
            if api_key and (transcript or visual_analysis):
                logger.info("🤖 Generating AI-powered overlay text...")
                
                # Create context for AI
                context = f"Video Analysis Context:\n"
                context += f"Duration: {duration:.1f} seconds\n"
                if transcript:
                    context += f"Audio Transcript: {transcript[:500]}\n"
                if visual_analysis:
                    context += f"Visual Content: {visual_analysis[:300]}\n"
                    
                try:
                    headers = {
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    }
                    
                    prompt = f"""
                    Analyze this video content and create ONE perfect, short text overlay (max 5 words) that captures the essence:
                    
                    {context}
                    
                    Requirements:
                    - Maximum 5 words
                    - High-impact and attention-grabbing
                    - Matches the video's mood and content
                    - Suitable for social media
                    - No quotes or punctuation
                    
                    Return only the overlay text, nothing else.
                    """
                    
                    data = {
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 20,
                        "temperature": 0.7
                    }
                    
                    response = requests.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers=headers,
                        json=data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        ai_response = response.json()
                        overlay_text = ai_response['choices'][0]['message']['content'].strip()
                        # Clean up the response
                        overlay_text = overlay_text.replace('"', '').replace("'", "").strip()
                        result['suggested_overlay'] = overlay_text
                        result['confidence_score'] = 0.8
                        result['used_openai_analysis'] = True
                        logger.info(f"✨ AI-generated overlay: '{overlay_text}'")
                    else:
                        logger.warning(f"OpenAI API error: {response.status_code}")
                        raise Exception("OpenAI API failed")
                        
                except Exception as e:
                    logger.warning(f"OpenAI analysis failed: {e}, using fallback")
                    # Fallback to intelligent text generation
                    result.update(self._generate_fallback_overlay(transcript, visual_analysis, duration))
            else:
                logger.info("🔄 Using fallback overlay generation...")
                result.update(self._generate_fallback_overlay(transcript, visual_analysis, duration))
            
            result['processing_time'] = time.time() - start_time
            logger.info(f"✅ Enhanced analysis completed in {result['processing_time']:.1f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced analysis failed: {e}")
            processing_time = time.time() - start_time
            return {
                'error': str(e),
                'video_path': video_path,
                'processing_time': processing_time,
                'suggested_overlay': 'Amazing Content',
                'confidence_score': 0.1
            }
    
    def _generate_fallback_overlay(self, transcript: Optional[str], visual_analysis: Optional[str], duration: float) -> Dict:
        """Generate fallback overlay when AI is not available"""
        overlay_options = [
            "Amazing Content",
            "Watch This",
            "Incredible Moments",
            "Must See",
            "Epic Video"
        ]
        
        # Try to be smart about selection based on available context
        if transcript:
            if any(word in transcript.lower() for word in ['music', 'song', 'beat']):
                overlay = "Music Vibes"
            elif any(word in transcript.lower() for word in ['funny', 'laugh', 'joke']):
                overlay = "Hilarious Content"
            elif any(word in transcript.lower() for word in ['amazing', 'incredible', 'wow']):
                overlay = "Mind Blowing"
            else:
                overlay = overlay_options[0]
        else:
            # Select based on duration
            if duration < 15:
                overlay = "Quick Watch"
            elif duration > 60:
                overlay = "Epic Journey"
            else:
                overlay = "Must Watch"
                
        return {
            'suggested_overlay': overlay,
            'confidence_score': 0.4,
            'used_openai_analysis': False
        }

if __name__ == "__main__":
    # Quick test
    analyzer = IntelligentVideoAnalyzer()
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    
    if Path(video_path).exists():
        result = analyzer.analyze_video_for_perfect_overlay(video_path)
        print("🎯 Test Result:", result.get('suggested_overlay', 'No result'))
    else:
        print("❌ Test video not found")
