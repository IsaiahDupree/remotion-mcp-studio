"""
Video Analysis Module - Handles video content analysis for music matching
"""
import json
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from config import VIDEO_ANALYSIS_CONFIG, DATABASE_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoAnalyzer:
    def __init__(self):
        self.config = VIDEO_ANALYSIS_CONFIG
        self.supported_formats = self.config['supported_formats']
        self.cache_file = DATABASE_CONFIG['video_cache']
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load existing video analysis cache"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save video analysis cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def analyze_video_file(self, file_path: Path, transcript: str = "", 
                          visual_analysis: str = "") -> Optional[Dict]:
        """Analyze video file and extract characteristics for music matching"""
        if not file_path.exists() or file_path.suffix.lower() not in self.supported_formats:
            return None
        
        file_key = str(file_path)
        if file_key in self.cache:
            logger.info(f"Using cached analysis for {file_path.name}")
            cached_result = self.cache[file_key].copy()
            # Update with new transcript/visual analysis if provided
            if transcript:
                cached_result['transcript'] = transcript
            if visual_analysis:
                cached_result['visual_analysis'] = visual_analysis
            return cached_result
        
        try:
            logger.info(f"Analyzing video file: {file_path.name}")
            
            # Extract video metadata
            video_data = self._extract_video_metadata(file_path)
            if not video_data:
                return None
            
            # Analyze visual content
            visual_features = self._analyze_visual_content(file_path)
            video_data.update(visual_features)
            
            # Analyze transcript if provided
            if transcript:
                transcript_features = self._analyze_transcript(transcript)
                video_data.update(transcript_features)
                video_data['transcript'] = transcript
            
            # Analyze visual analysis if provided
            if visual_analysis:
                visual_text_features = self._analyze_visual_description(visual_analysis)
                video_data.update(visual_text_features)
                video_data['visual_analysis'] = visual_analysis
            
            # Determine overall mood and energy
            video_data['detected_mood'] = self._determine_mood(video_data)
            video_data['energy_level'] = self._calculate_energy_level(video_data)
            video_data['music_style_preference'] = self._suggest_music_style(video_data)
            
            # Cache the results
            self.cache[file_key] = video_data
            self._save_cache()
            
            return video_data
            
        except Exception as e:
            logger.error(f"Error analyzing video {file_path}: {e}")
            return None
    
    def _extract_video_metadata(self, file_path: Path) -> Optional[Dict]:
        """Extract basic video metadata using OpenCV"""
        try:
            cap = cv2.VideoCapture(str(file_path))
            
            if not cap.isOpened():
                logger.error(f"Could not open video: {file_path}")
                return None
            
            metadata = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            }
            
            metadata['duration'] = metadata['frame_count'] / metadata['fps'] if metadata['fps'] > 0 else 0
            metadata['aspect_ratio'] = metadata['width'] / metadata['height'] if metadata['height'] > 0 else 1
            
            cap.release()
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return None
    
    def _analyze_visual_content(self, file_path: Path) -> Dict:
        """Analyze visual content of video frames"""
        try:
            cap = cv2.VideoCapture(str(file_path))
            
            if not cap.isOpened():
                return {}
            
            frame_features = []
            frame_interval = self.config['frame_extraction']['interval']
            max_frames = self.config['frame_extraction']['max_frames']
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Sample frames at regular intervals
            frame_indices = np.linspace(0, total_frames - 1, 
                                      min(max_frames, total_frames // (frame_interval * fps)), 
                                      dtype=int)
            
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if ret:
                    features = self._analyze_frame(frame)
                    frame_features.append(features)
            
            cap.release()
            
            # Aggregate frame features
            if frame_features:
                return self._aggregate_frame_features(frame_features)
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error analyzing visual content: {e}")
            return {}
    
    def _analyze_frame(self, frame: np.ndarray) -> Dict:
        """Analyze individual frame characteristics"""
        try:
            # Convert to different color spaces
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            features = {}
            
            # Brightness analysis
            features['brightness'] = np.mean(gray) / 255.0
            
            # Contrast analysis
            features['contrast'] = np.std(gray) / 255.0
            
            # Color analysis
            features['saturation'] = np.mean(hsv[:, :, 1]) / 255.0
            features['hue_variance'] = np.var(hsv[:, :, 0]) / (180 ** 2)
            
            # Edge analysis (motion/activity indicator)
            edges = cv2.Canny(gray, 50, 150)
            features['edge_density'] = np.sum(edges > 0) / edges.size
            
            # Color distribution
            b, g, r = cv2.split(frame)
            features['color_balance'] = {
                'red_mean': float(np.mean(r)) / 255.0,
                'green_mean': float(np.mean(g)) / 255.0,
                'blue_mean': float(np.mean(b)) / 255.0
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Frame analysis error: {e}")
            return {}
    
    def _aggregate_frame_features(self, frame_features: List[Dict]) -> Dict:
        """Aggregate features from multiple frames"""
        if not frame_features:
            return {}
        
        aggregated = {}
        
        # Calculate means for numerical features
        numerical_keys = ['brightness', 'contrast', 'saturation', 'hue_variance', 'edge_density']
        
        for key in numerical_keys:
            values = [f.get(key, 0) for f in frame_features if key in f]
            if values:
                aggregated[f'avg_{key}'] = np.mean(values)
                aggregated[f'std_{key}'] = np.std(values)
        
        # Color balance aggregation
        color_keys = ['red_mean', 'green_mean', 'blue_mean']
        for color_key in color_keys:
            values = [f.get('color_balance', {}).get(color_key, 0) for f in frame_features]
            if values:
                aggregated[f'avg_{color_key}'] = np.mean(values)
        
        # Visual activity level
        edge_values = [f.get('edge_density', 0) for f in frame_features]
        aggregated['visual_activity'] = np.mean(edge_values) if edge_values else 0
        
        return aggregated
    
    def _analyze_transcript(self, transcript: str) -> Dict:
        """Analyze transcript text for mood and energy indicators"""
        if not transcript:
            return {}
        
        transcript_lower = transcript.lower()
        
        # Energy keywords
        energy_keywords = self.config['transcript_analysis']['energy_keywords']
        calm_keywords = self.config['transcript_analysis']['calm_keywords']
        
        energy_count = sum(1 for keyword in energy_keywords if keyword in transcript_lower)
        calm_count = sum(1 for keyword in calm_keywords if keyword in transcript_lower)
        
        # Emotional indicators
        positive_words = ['happy', 'excited', 'amazing', 'wonderful', 'great', 'fantastic', 'love']
        negative_words = ['sad', 'worried', 'problem', 'difficult', 'challenging', 'frustrated']
        
        positive_count = sum(1 for word in positive_words if word in transcript_lower)
        negative_count = sum(1 for word in negative_words if word in transcript_lower)
        
        return {
            'transcript_energy_score': energy_count / max(len(transcript.split()), 1),
            'transcript_calm_score': calm_count / max(len(transcript.split()), 1),
            'transcript_positive_score': positive_count / max(len(transcript.split()), 1),
            'transcript_negative_score': negative_count / max(len(transcript.split()), 1),
            'transcript_length': len(transcript),
            'word_count': len(transcript.split())
        }
    
    def _analyze_visual_description(self, visual_analysis: str) -> Dict:
        """Analyze visual description text for mood and style indicators"""
        if not visual_analysis:
            return {}
        
        visual_lower = visual_analysis.lower()
        
        # Visual energy indicators
        high_energy_terms = ['fast', 'quick', 'rapid', 'energetic', 'dynamic', 'action', 'movement']
        low_energy_terms = ['slow', 'calm', 'peaceful', 'still', 'gentle', 'quiet']
        
        # Visual mood indicators
        bright_terms = ['bright', 'colorful', 'vibrant', 'vivid', 'cheerful']
        dark_terms = ['dark', 'dim', 'muted', 'somber', 'serious']
        
        high_energy_count = sum(1 for term in high_energy_terms if term in visual_lower)
        low_energy_count = sum(1 for term in low_energy_terms if term in visual_lower)
        bright_count = sum(1 for term in bright_terms if term in visual_lower)
        dark_count = sum(1 for term in dark_terms if term in visual_lower)
        
        return {
            'visual_energy_score': high_energy_count / max(len(visual_analysis.split()), 1),
            'visual_calm_score': low_energy_count / max(len(visual_analysis.split()), 1),
            'visual_brightness_score': bright_count / max(len(visual_analysis.split()), 1),
            'visual_darkness_score': dark_count / max(len(visual_analysis.split()), 1)
        }
    
    def _determine_mood(self, video_data: Dict) -> str:
        """Determine overall mood of the video"""
        # Combine different indicators
        brightness = video_data.get('avg_brightness', 0.5)
        activity = video_data.get('visual_activity', 0.5)
        transcript_positive = video_data.get('transcript_positive_score', 0)
        transcript_negative = video_data.get('transcript_negative_score', 0)
        visual_energy = video_data.get('visual_energy_score', 0)
        
        # Calculate mood scores
        happy_score = brightness * 0.3 + transcript_positive * 0.4 + visual_energy * 0.3
        sad_score = transcript_negative * 0.5 + (1 - brightness) * 0.3 + video_data.get('visual_darkness_score', 0) * 0.2
        energetic_score = activity * 0.4 + visual_energy * 0.4 + video_data.get('transcript_energy_score', 0) * 0.2
        calm_score = video_data.get('visual_calm_score', 0) * 0.5 + video_data.get('transcript_calm_score', 0) * 0.5
        
        # Determine dominant mood
        mood_scores = {
            'happy': happy_score,
            'sad': sad_score,
            'energetic': energetic_score,
            'calm': calm_score
        }
        
        return max(mood_scores, key=mood_scores.get)
    
    def _calculate_energy_level(self, video_data: Dict) -> float:
        """Calculate overall energy level (0-1 scale)"""
        activity = video_data.get('visual_activity', 0.5)
        contrast = video_data.get('avg_contrast', 0.5)
        transcript_energy = video_data.get('transcript_energy_score', 0)
        visual_energy = video_data.get('visual_energy_score', 0)
        
        # Combine indicators
        energy_level = (activity * 0.3 + contrast * 0.2 + transcript_energy * 0.25 + visual_energy * 0.25)
        
        return min(max(energy_level, 0), 1)  # Clamp to 0-1 range
    
    def _suggest_music_style(self, video_data: Dict) -> List[str]:
        """Suggest appropriate music styles based on video characteristics"""
        styles = []
        
        mood = video_data.get('detected_mood', 'neutral')
        energy = video_data.get('energy_level', 0.5)
        duration = video_data.get('duration', 0)
        
        # Map mood to music styles
        if mood == 'happy':
            styles.extend(['pop', 'upbeat', 'cheerful'])
        elif mood == 'sad':
            styles.extend(['ambient', 'melancholic', 'emotional'])
        elif mood == 'energetic':
            styles.extend(['electronic', 'dance', 'energetic'])
        elif mood == 'calm':
            styles.extend(['ambient', 'peaceful', 'relaxing'])
        
        # Add energy-based styles
        if energy > 0.7:
            styles.extend(['fast-paced', 'dynamic'])
        elif energy < 0.3:
            styles.extend(['slow', 'gentle'])
        
        # Duration-based suggestions
        if duration > 300:  # 5+ minutes
            styles.append('extended')
        elif duration < 60:  # Under 1 minute
            styles.append('short-form')
        
        return list(set(styles))  # Remove duplicates
