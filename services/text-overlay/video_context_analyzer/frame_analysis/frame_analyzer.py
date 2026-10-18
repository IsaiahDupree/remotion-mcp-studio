"""
Frame Analyzer

Analyzes video frames to extract contextual information and key visual elements.
Uses OpenAI Vision API for advanced visual content understanding.
"""

import os
import cv2
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
import tempfile
from pathlib import Path
import base64
import json
import requests
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('frame_analyzer')

class FrameAnalyzer:
    """
    Analyzes video frames to extract contextual information using computer vision techniques.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        frames_to_sample: int = 5,
        sampling_strategy: str = 'uniform',
        temp_dir: Optional[str] = None,
        model: str = 'gpt-4-vision-preview'
    ):
        """
        Initialize the Frame Analyzer.
        
        Args:
            api_key: OpenAI API key for vision analysis (defaults to env variable)
            frames_to_sample: Number of frames to sample from the video
            sampling_strategy: How to sample frames ('uniform', 'key_frames')
            temp_dir: Directory for temporary files (default system temp)
            model: OpenAI vision model to use
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Will use basic analysis only.")
        
        self.frames_to_sample = frames_to_sample
        self.sampling_strategy = sampling_strategy
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.model = model
        
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def extract_frames(self, video_path: str, interval_seconds: float = 30.0) -> List[Tuple[np.ndarray, float]]:
        """
        Extract frames at regular intervals for comprehensive video analysis.
        
        Args:
            video_path: Path to the video file
            interval_seconds: Interval between frame extractions (default: 30 seconds)
            
        Returns:
            List of tuples containing (frame, timestamp)
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Error opening video file: {video_path}")
                return []
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            logger.info(f"Video properties: {total_frames} frames, {fps} FPS, {duration:.2f} seconds")
            
            frames = []
        
            # Extract frames at regular intervals (every 30 seconds by default)
            current_time = 0.0
        
            while current_time < duration:
                # Calculate frame number for this timestamp
                frame_idx = int(current_time * fps)
                
                if frame_idx < total_frames:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                    ret, frame = cap.read()
                    if ret:
                        frames.append((frame, current_time))
                        logger.info(f"Extracted frame at {current_time:.1f}s (frame {frame_idx})")
                    else:
                        logger.warning(f"Could not read frame at {current_time:.1f}s (frame {frame_idx})")
                
                # Move to next interval
                current_time += interval_seconds
        
            # Always include the first frame if we haven't already
            if not frames or frames[0][1] > 1.0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if ret:
                    frames.insert(0, (frame, 0.0))
                    logger.info("Added opening frame at 0.0s")
        
            # Always include a frame near the end
            if duration > interval_seconds:
                end_time = max(0, duration - 5.0)  # 5 seconds before end
                end_frame_idx = int(end_time * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, end_frame_idx)
                ret, frame = cap.read()
                if ret:
                    frames.append((frame, end_time))
                    logger.info(f"Added ending frame at {end_time:.1f}s")
            
            cap.release()
            return frames
            
        except Exception as e:
            logger.error(f"Error extracting frames: {e}")
            return []
    
    def analyze_frames_with_ai(self, frames: List[Tuple[np.ndarray, float]]) -> Dict[str, Any]:
        """
        Analyze frames using OpenAI Vision API.
        
        Args:
            frames: List of (frame, timestamp) tuples
            
        Returns:
            Dictionary with analysis results
        """
        if not self.api_key:
            logger.warning("OpenAI API key not provided. Skipping AI analysis.")
            return {"error": "API key not provided"}
        
        try:
            # Prepare frames for API
            content_items = []
            
            for idx, (frame, timestamp) in enumerate(frames):
                # Convert frame to base64
                _, buffer = cv2.imencode('.jpg', frame)
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Add to content items
                content_items.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_base64}",
                    }
                })
            
            # Single API call with all frames
            messages = [
                {
                    "role": "system", 
                    "content": "You are a video content analyzer. Analyze these frames from a video and provide insights. Focus on the main subject, actions, setting, and any text visible. Generate a concise, engaging phrase (max 6 words) that would make good text overlay for social media."
                },
                {
                    "role": "user",
                    "content": [
                        "These are key frames from a video. Analyze what's happening and suggest a catchy text overlay that would engage viewers on social media. Be brief and focus on the main subject or action. Keep the suggested overlay text under 6 words.",
                        *content_items
                    ]
                }
            ]
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": "gpt-4o",
                "messages": messages,
                "max_tokens": 300
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code}, {response.text}")
                return {"error": f"API error: {response.status_code}"}
            
            result = response.json()
            
            # Extract the analysis
            analysis_text = result['choices'][0]['message']['content']
            
            # Parse the response to extract the catchy text
            catchy_text = ""
            analysis_parts = {}
            
            # Simple parsing of response to find catchy text suggestion
            for line in analysis_text.split('\n'):
                line = line.strip()
                if "catchy text:" in line.lower() or "suggested overlay:" in line.lower() or "overlay text:" in line.lower():
                    catchy_text = line.split(':', 1)[1].strip().strip('"').strip("'")
                    break
            
            # If we couldn't find it with a label, just take the last short line
            if not catchy_text:
                for line in analysis_text.split('\n'):
                    line = line.strip()
                    if len(line) <= 50 and line and not line.endswith(':'):
                        catchy_text = line.strip('"').strip("'")
            
            return {
                "full_analysis": analysis_text,
                "catchy_text": catchy_text or "Epic content you can't miss",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing frames with AI: {e}")
            return {
                "error": str(e),
                "full_analysis": "Frame analysis failed",
                "catchy_text": "Amazing video content",
                "timestamp": datetime.now().isoformat()
            }
    
    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Complete video frame analysis pipeline.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Analysis results including suggested catchy text
        """
        try:
            # Extract frames
            frames = self.extract_frames(video_path)
            if not frames:
                return {"error": "Failed to extract frames", "catchy_text": "Check out this amazing video"}
            
            # Save frames for debugging if needed
            debug_frames = []
            for idx, (frame, timestamp) in enumerate(frames):
                frame_path = os.path.join(self.temp_dir, f"frame_{idx}.jpg")
                cv2.imwrite(frame_path, frame)
                debug_frames.append(frame_path)
            
            # Analyze with OpenAI if API key is available
            if self.api_key:
                result = self.analyze_frames_with_ai(frames)
                result['debug_frames'] = debug_frames
                return result
            else:
                # Basic fallback analysis without AI
                return {
                    "message": "Basic analysis only (no API key provided)",
                    "catchy_text": "Must-see content right here",
                    "debug_frames": debug_frames
                }
                
        except Exception as e:
            logger.error(f"Error in video analysis pipeline: {e}")
            return {"error": str(e), "catchy_text": "Amazing video content"}
