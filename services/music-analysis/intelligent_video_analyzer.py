#!/usr/bin/env python3
"""
Intelligent Video Content Analyzer
- Detects existing captions in video
- Extracts transcript from audio 
- Samples frames efficiently based on video length
- Uses AI to analyze visual content
- Blends transcript + visual context for perfect text overlay
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
            logger.error(f"❌ Failed to load Whisper model: {e}")
            self.whisper_model = None
    
    def get_video_info(self, video_path: str) -> Dict:
        """Get comprehensive video information"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                
                # Find video and audio streams
                video_stream = None
                audio_stream = None
                
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'video' and not video_stream:
                        video_stream = stream
                    elif stream.get('codec_type') == 'audio' and not audio_stream:
                        audio_stream = stream
                
                return {
                    'video_stream': video_stream,
                    'audio_stream': audio_stream,
                    'format': info.get('format'),
                    'duration': float(video_stream.get('duration', 0)) if video_stream else 0,
                    'width': video_stream.get('width') if video_stream else 0,
                    'height': video_stream.get('height') if video_stream else 0,
                    'has_audio': audio_stream is not None
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return {}
    
    def detect_existing_captions(self, video_path: str) -> Tuple[bool, Optional[str]]:
        """Detect if video already has burned-in captions or text overlays"""
        try:
            logger.info("🔍 Analyzing video for existing captions...")
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False, None
            
            # Sample frames to check for text
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            # Sample 3-5 frames across the video
            sample_points = [0.2, 0.5, 0.8]  # 20%, 50%, 80% through video
            detected_text_regions = []
            
            for point in sample_points:
                frame_number = int(total_frames * point)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                
                if ret:
                    # Look for text-like regions (high contrast areas that could be text)
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    # Detect high-contrast regions that might be text
                    # Bottom third of frame (common caption area)
                    h, w = gray.shape
                    bottom_third = gray[int(h*0.67):, :]
                    
                    # Calculate variance in bottom third (text areas have high variance)
                    variance = np.var(bottom_third)
                    
                    # Look for consistent dark/light regions (text backgrounds)
                    mean_brightness = np.mean(bottom_third)
                    
                    detected_text_regions.append({
                        'variance': variance,
                        'mean_brightness': mean_brightness,
                        'frame_time': point * duration
                    })
            
            cap.release()
            
            # Analyze if consistent text regions exist
            high_variance_count = sum(1 for region in detected_text_regions if region['variance'] > 1000)
            
            if high_variance_count >= 2:  # At least 2 frames show potential text
                logger.info("✅ Potential existing captions detected")
                return True, "Potential captions detected in video"
            else:
                logger.info("❌ No existing captions detected")
                return False, None
                
        except Exception as e:
            logger.error(f"Error detecting captions: {e}")
            return False, None
    
    def extract_audio_transcript(self, video_path: str) -> Optional[str]:
        """Extract audio and generate transcript using Whisper"""
        if not self.whisper_model:
            logger.warning("Whisper model not available")
            return None
        
        try:
            logger.info("🎤 Extracting audio for transcription...")
            
            # Extract audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            
            # Use ffmpeg to extract audio
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM 16-bit
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite
                temp_audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg audio extraction failed: {result.stderr}")
                return None
            
            # Transcribe with Whisper
            logger.info("🎯 Generating transcript with Whisper...")
            result = self.whisper_model.transcribe(temp_audio_path)
            transcript = result['text'].strip()
            
            # Clean up
            os.unlink(temp_audio_path)
            
            if transcript:
                logger.info(f"✅ Transcript generated: {len(transcript)} characters")
                return transcript
            else:
                logger.warning("❌ No transcript generated")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting transcript: {e}")
            return None
    
    def sample_frames_efficiently(self, video_path: str, video_info: Dict) -> List[str]:
        """Sample frames at cost-efficient ratio based on video length"""
        try:
            duration = video_info.get('duration', 0)
            
            # Determine sampling strategy based on video length
            if duration <= 10:
                # Short video: 2-3 frames
                sample_points = [0.25, 0.75]
            elif duration <= 30:
                # Medium video: 3-4 frames  
                sample_points = [0.2, 0.5, 0.8]
            elif duration <= 120:
                # Long video: 4-5 frames
                sample_points = [0.15, 0.35, 0.55, 0.75, 0.9]
            else:
                # Very long video: 5-6 frames (cost control)
                sample_points = [0.1, 0.25, 0.4, 0.6, 0.8, 0.95]
            
            logger.info(f"📸 Sampling {len(sample_points)} frames from {duration:.1f}s video")
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return []
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_data = []
            
            for i, point in enumerate(sample_points):
                frame_number = int(total_frames * point)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                
                if ret:
                    # Resize frame for cost efficiency (max 512px width)
                    h, w = frame.shape[:2]
                    if w > 512:
                        new_w = 512
                        new_h = int(h * (512 / w))
                        frame = cv2.resize(frame, (new_w, new_h))
                    
                    # Convert to base64
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frame_b64 = base64.b64encode(buffer).decode('utf-8')
                    frame_data.append(frame_b64)
            
            cap.release()
            logger.info(f"✅ Successfully sampled {len(frame_data)} frames")
            return frame_data
            
        except Exception as e:
            logger.error(f"Error sampling frames: {e}")
            return []
    
    def analyze_frames_with_ai(self, frames: List[str], transcript: Optional[str]) -> Optional[str]:
        """Analyze frames using GPT-4 Vision API"""
        if not self.openai_api_key or not frames:
            logger.warning("OpenAI API key not available or no frames to analyze")
            return None
        
        try:
            logger.info("🤖 Analyzing frames with GPT-4 Vision...")
            
            # Prepare messages for GPT-4 Vision
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert video content analyst. Analyze the provided video frames to understand the visual content, mood, setting, and key elements. Be concise and focus on the most important visual elements that would help create a perfect text overlay."
                },
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text",
                            "text": f"Analyze these video frames. {'The transcript is: ' + transcript if transcript else 'No audio transcript available.'} Describe the key visual elements, mood, setting, and what type of content this appears to be. Focus on elements that would help create a perfect text overlay."
                        }
                    ]
                }
            ]
            
            # Add frame images (limit to first 4 for cost control)
            for i, frame in enumerate(frames[:4]):
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{frame}",
                        "detail": "low"  # Cost-efficient analysis
                    }
                })
            
            # Call OpenAI API
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o",  # GPT-4 with vision
                "messages": messages,
                "max_tokens": 300,  # Keep cost down
                "temperature": 0.3
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result['choices'][0]['message']['content']
                logger.info("✅ Frame analysis completed")
                return analysis
            else:
                logger.error(f"OpenAI API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing frames: {e}")
            return None
    
    def generate_perfect_overlay(self, transcript: Optional[str], visual_analysis: Optional[str], video_info: Dict) -> str:
        """Generate one perfect text overlay that matches video content"""
        try:
            logger.info("✨ Generating perfect text overlay...")
            
            # Analyze available content
            content_elements = []
            
            if transcript:
                # Extract key phrases from transcript
                words = transcript.lower().split()
                # Remove common words and find meaningful phrases
                key_words = [w for w in words if len(w) > 4 and w not in ['that', 'this', 'with', 'from', 'they', 'were', 'been', 'have']]
                if key_words:
                    content_elements.append(f"Audio: {' '.join(key_words[:5])}")
            
            if visual_analysis:
                # Extract key insights from visual analysis
                content_elements.append(f"Visual: {visual_analysis[:100]}")
            
            # Determine video characteristics
            duration = video_info.get('duration', 0)
            width = video_info.get('width', 0)
            height = video_info.get('height', 0)
            
            # Create contextual overlay based on analysis
            if transcript and visual_analysis:
                # Blend both transcript and visual context
                if any(word in transcript.lower() for word in ['tutorial', 'how to', 'learn', 'guide']):
                    overlay = "Educational Content"
                elif any(word in transcript.lower() for word in ['music', 'song', 'beat', 'dance']):
                    overlay = "Music & Entertainment"
                elif any(word in transcript.lower() for word in ['business', 'work', 'company', 'professional']):
                    overlay = "Business Insights"
                elif any(word in visual_analysis.lower() for word in ['person', 'people', 'speaking', 'talking']):
                    overlay = "Personal Story"
                elif any(word in visual_analysis.lower() for word in ['nature', 'outdoor', 'landscape']):
                    overlay = "Nature & Lifestyle"
                else:
                    # Extract the most meaningful phrase
                    if len(transcript) > 50:
                        # Find the most impactful sentence
                        sentences = re.split('[.!?]', transcript)
                        if sentences:
                            shortest_sentence = min(sentences, key=len).strip()
                            if len(shortest_sentence) <= 50 and len(shortest_sentence) > 10:
                                overlay = shortest_sentence
                            else:
                                overlay = "Enhanced Content"
                        else:
                            overlay = "Enhanced Content"
                    else:
                        overlay = transcript[:30] + "..." if len(transcript) > 30 else transcript
            
            elif transcript:
                # Only transcript available
                if len(transcript) <= 40:
                    overlay = transcript
                else:
                    # Find key phrase
                    sentences = re.split('[.!?]', transcript)
                    if sentences and len(sentences[0]) <= 40:
                        overlay = sentences[0].strip()
                    else:
                        overlay = transcript[:37] + "..."
            
            elif visual_analysis:
                # Only visual analysis available
                if 'person' in visual_analysis.lower() or 'people' in visual_analysis.lower():
                    overlay = "Personal Content"
                elif 'text' in visual_analysis.lower() or 'writing' in visual_analysis.lower():
                    overlay = "Informational"
                elif 'colorful' in visual_analysis.lower() or 'bright' in visual_analysis.lower():
                    overlay = "Creative Content"
                else:
                    overlay = "Visual Story"
            
            else:
                # Fallback based on video characteristics
                if duration < 15:
                    overlay = "Quick Clip"
                elif height > width:
                    overlay = "Mobile Content"
                elif width > height:
                    overlay = "Widescreen Experience"
                else:
                    overlay = "Square Format"
            
            # Ensure overlay is appropriate length
            if len(overlay) > 60:
                overlay = overlay[:57] + "..."
            
            logger.info(f"✅ Generated overlay: '{overlay}'")
            return overlay
            
        except Exception as e:
            logger.error(f"Error generating overlay: {e}")
            return "Enhanced Video"
    
    def analyze_video_intelligently(self, video_path: str) -> VideoAnalysis:
        """Complete intelligent video analysis workflow"""
        start_time = time.time()
        logger.info(f"🚀 Starting intelligent analysis of: {Path(video_path).name}")
        
        try:
            # Step 1: Get video information
            video_info = self.get_video_info(video_path)
            if not video_info:
                raise Exception("Could not analyze video file")
            
            duration = video_info.get('duration', 0)
            logger.info(f"📹 Video: {duration:.1f}s, {video_info.get('width')}x{video_info.get('height')}")
            
            # Step 2: Check for existing captions
            has_captions, existing_captions = self.detect_existing_captions(video_path)
            
            if has_captions and existing_captions:
                logger.info("✅ Using existing captions")
                processing_time = time.time() - start_time
                return VideoAnalysis(
                    has_existing_captions=True,
                    existing_captions=existing_captions,
                    transcript=None,
                    visual_analysis=None,
                    suggested_overlay=existing_captions,
                    confidence_score=0.8,
                    frame_samples=[],
                    processing_time=processing_time
                )
            
            # Step 3: Extract transcript (if audio available)
            transcript = None
            if video_info.get('has_audio'):
                transcript = self.extract_audio_transcript(video_path)
            
            # Step 4: Sample frames efficiently
            frame_samples = self.sample_frames_efficiently(video_path, video_info)
            
            # Step 5: Analyze frames with AI
            visual_analysis = self.analyze_frames_with_ai(frame_samples, transcript)
            
            # Step 6: Generate perfect overlay
            suggested_overlay = self.generate_perfect_overlay(transcript, visual_analysis, video_info)
            
            # Calculate confidence score
            confidence = 0.5  # Base confidence
            if transcript:
                confidence += 0.3
            if visual_analysis:
                confidence += 0.2
            if len(frame_samples) >= 3:
                confidence += 0.1
            
            processing_time = time.time() - start_time
            
            logger.info(f"✅ Analysis complete in {processing_time:.1f}s")
            logger.info(f"🎯 Suggested overlay: '{suggested_overlay}'")
            
            return VideoAnalysis(
                has_existing_captions=False,
                existing_captions=None,
                transcript=transcript,
                visual_analysis=visual_analysis,
                suggested_overlay=suggested_overlay,
                confidence_score=confidence,
                frame_samples=frame_samples,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            processing_time = time.time() - start_time
            
            return VideoAnalysis(
                has_existing_captions=False,
                existing_captions=None,
                transcript=None,
                visual_analysis=None,
                suggested_overlay="Enhanced Video",
                confidence_score=0.1,
                frame_samples=[],
                processing_time=processing_time
            )
    
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
            if api_key and transcript:
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

def main():
    """Test the intelligent video analyzer"""
    # Test with the specific video
    video_path = r"C:\Users\Isaia\Documents\Coding\N8N\shared\videos\1D1A43E4-3B05-CBE2-4E54-46875AD60179.MP4"
    
    analyzer = IntelligentVideoAnalyzer()
    result = analyzer.analyze_video_intelligently(video_path)
    
    print("\n🎯 INTELLIGENT VIDEO ANALYSIS RESULTS")
    print("=" * 50)
    print(f"📁 Video: {Path(video_path).name}")
    print(f"⏱️ Processing Time: {result.processing_time:.1f}s")
    print(f"🎯 Confidence Score: {result.confidence_score:.1f}")
    print(f"📝 Has Existing Captions: {result.has_existing_captions}")
    
    if result.existing_captions:
        print(f"📋 Existing Captions: {result.existing_captions}")
    
    if result.transcript:
        print(f"🎤 Transcript: {result.transcript[:100]}...")
    
    if result.visual_analysis:
        print(f"👁️ Visual Analysis: {result.visual_analysis[:100]}...")
    
    print(f"✨ PERFECT OVERLAY: '{result.suggested_overlay}'")
    print(f"📸 Frame Samples: {len(result.frame_samples)} frames")
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
                'analysis_strategy': 'enhanced_ai_blend'
            }
            
            # Step 1: Get video information
            video_info = self.get_video_info(video_path)
            result['video_info'] = {
                'duration': video_info.get('duration', 0),
                'width': video_info.get('width', 0),
                'height': video_info.get('height', 0),
                'has_audio': video_info.get('has_audio', False)
            }
            
            duration = float(video_info.get('duration', 0))
            logger.info(f"📹 Video duration: {duration:.1f}s")
            
            # Step 2: Check for existing captions
            logger.info("🔍 Checking for existing captions...")
            has_captions, existing_captions = self.detect_existing_captions(video_path)
            result['has_existing_captions'] = has_captions
            result['existing_captions'] = existing_captions
            
            if has_captions and existing_captions:
                logger.info("✅ Found existing captions, using them")
                result['suggested_overlay'] = existing_captions[:80] + "..." if len(existing_captions) > 80 else existing_captions
                result['confidence_score'] = 0.95
                result['processing_time'] = time.time() - start_time
                return result
            
            # Step 3: Extract transcript if no captions found
            logger.info("🎤 Extracting audio transcript...")
            if video_info.get('has_audio', False):
                transcript = self.extract_audio_transcript(video_path)
                result['transcript'] = transcript
                logger.info(f"📝 Transcript extracted: {len(transcript) if transcript else 0} characters")
            else:
                logger.info("🔇 No audio found, skipping transcript")
                transcript = ""
            
            # Step 4: Smart frame sampling based on video length
            logger.info("🖼️ Sampling frames for visual analysis...")
            if duration <= 30:
                sample_count = 3  # Short videos: 3 frames
            elif duration <= 120:
                sample_count = 5  # Medium videos: 5 frames
            elif duration <= 300:
                sample_count = 8  # Long videos: 8 frames
            else:
                sample_count = 12  # Very long videos: 12 frames
            
            frame_base64_list = self.sample_video_frames(video_path, sample_count)
            result['frame_samples_count'] = len(frame_base64_list)
            logger.info(f"📸 Sampled {len(frame_base64_list)} frames")
            
            # Step 5: AI-powered visual analysis
            logger.info("🤖 Performing AI visual analysis...")
            visual_analysis = self.analyze_frames_with_ai(
                frame_base64_list, 
                openai_api_key or self.openai_api_key
            )
            result['visual_analysis'] = visual_analysis
            
            # Step 6: Blend transcript + visual context for perfect overlay
            logger.info("🎯 Generating perfect text overlay...")
            perfect_overlay = self.generate_perfect_overlay(
                transcript=transcript,
                visual_analysis=visual_analysis,
                video_duration=duration,
                openai_api_key=openai_api_key or self.openai_api_key
            )
            
            result['suggested_overlay'] = perfect_overlay['text']
            result['confidence_score'] = perfect_overlay['confidence']
            result['processing_time'] = time.time() - start_time
            
            logger.info(f"✅ Analysis completed in {result['processing_time']:.1f}s")
            logger.info(f"🎯 Generated overlay: '{result['suggested_overlay'][:50]}...'")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced analysis failed: {e}")
            return {
                'error': str(e),
                'video_path': video_path,
                'processing_time': time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def generate_perfect_overlay(self, transcript: str, visual_analysis: str, 
                               video_duration: float, openai_api_key: str) -> Dict:
        """
        Generate perfect text overlay by blending transcript and visual context
        """
        try:
            if not openai_api_key:
                # Fallback to rule-based generation
                return self._generate_fallback_overlay(transcript, visual_analysis)
            
            # Prepare context for AI analysis
            context = f"""
Video Duration: {video_duration:.1f} seconds

Transcript: {transcript[:500] if transcript else 'No audio transcript available'}

Visual Analysis: {visual_analysis[:500] if visual_analysis else 'No visual analysis available'}
"""
            
            prompt = f"""
Analyze this video content and create ONE perfect, short text overlay that captures the essence of the video.

Context:
{context}

Requirements:
1. Maximum 5-8 words for optimal readability
2. High-impact, attention-grabbing
3. Matches the video's mood and content perfectly
4. Suitable for social media overlay
5. No generic phrases - be specific to this content

Respond with ONLY the overlay text, nothing else.
"""
            
            headers = {
                'Authorization': f'Bearer {openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-4o-mini',
                'messages': [
                    {'role': 'system', 'content': 'You are an expert at creating perfect, concise video overlay text that maximizes engagement.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 50,
                'temperature': 0.7
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                overlay_text = result['choices'][0]['message']['content'].strip()
                
                # Clean up the response
                overlay_text = overlay_text.replace('"', '').replace("'", "").strip()
                
                return {
                    'text': overlay_text,
                    'confidence': 0.85,
                    'method': 'ai_generated'
                }
            else:
                logger.warning(f"OpenAI API error: {response.status_code}")
                return self._generate_fallback_overlay(transcript, visual_analysis)
                
        except Exception as e:
            logger.error(f"AI overlay generation failed: {e}")
            return self._generate_fallback_overlay(transcript, visual_analysis)
    
    def _generate_fallback_overlay(self, transcript: str, visual_analysis: str) -> Dict:
        """
        Fallback overlay generation when AI is not available
        """
        # Extract key words from transcript and visual analysis
        text_content = f"{transcript} {visual_analysis}".lower()
        
        # Simple keyword extraction
        keywords = []
        for word in text_content.split():
            if len(word) > 3 and word.isalpha():
                keywords.append(word.title())
        
        if keywords:
            # Take first few meaningful words
            overlay = " ".join(keywords[:3])
        else:
            overlay = "Watch This"
        
        return {
            'text': overlay,
            'confidence': 0.6,
            'method': 'fallback_generated'
        }


if __name__ == "__main__":
    main()
