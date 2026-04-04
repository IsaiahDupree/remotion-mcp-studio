#!/usr/bin/env python3
"""
Music-Video Matching System
=========================

Intelligent system for matching music tracks with video content based on:
- Video transcript analysis
- Frame-by-frame visual analysis using GPT-4o
- Music mood and energy analysis
- Context-aware pairing recommendations

This creates a comprehensive index for optimal music-video combinations.
"""

import os
import sys
import json
import hashlib
import logging
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import openai

# Import our existing modules
from local_music_selector import LocalMusicSelector
from video_context_analyzer.frame_analysis.frame_analyzer import FrameAnalyzer
from video_context_analyzer.audio_analysis.audio_analyzer import AudioAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VideoContext:
    """Container for video analysis results"""
    video_path: str
    transcript: str
    frame_analysis: str
    visual_mood: str
    content_type: str
    energy_level: str
    themes: List[str]
    duration: float

@dataclass
class MusicContext:
    """Container for music analysis results"""
    file_path: str
    name: str
    genre: str
    mood: str
    energy_level: str
    tempo: str
    themes: List[str]
    size_mb: float

@dataclass
class MusicVideoMatch:
    """Container for music-video match results"""
    video_path: str
    music_path: str
    compatibility_score: float
    reasoning: str
    mood_match: str
    energy_match: str
    theme_match: str

class MusicVideoMatcher:
    """Intelligent music-video matching system"""
    
    def __init__(self, music_index_path: str = "music_library/music_index.json"):
        """Initialize the matcher with music library and AI capabilities"""
        self.music_index_path = music_index_path
        self.music_selector = LocalMusicSelector()
        self.frame_analyzer = FrameAnalyzer()
        self.audio_analyzer = AudioAnalyzer()
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI()
        
        # Cache for analyzed content
        self.video_context_cache = {}
        self.music_context_cache = {}
        self.match_index = {}
        
        # Load existing indexes
        self._load_existing_indexes()
        
        logger.info("MusicVideoMatcher initialized")
    
    def _load_existing_indexes(self):
        """Load existing analysis and match indexes"""
        try:
            # Load video context cache
            video_cache_path = Path("music_library/video_context_cache.json")
            if video_cache_path.exists():
                with open(video_cache_path, 'r') as f:
                    self.video_context_cache = json.load(f)
                logger.info(f"Loaded {len(self.video_context_cache)} video contexts")
            
            # Load music context cache  
            music_cache_path = Path("music_library/music_context_cache.json")
            if music_cache_path.exists():
                with open(music_cache_path, 'r') as f:
                    self.music_context_cache = json.load(f)
                logger.info(f"Loaded {len(self.music_context_cache)} music contexts")
            
            # Load match index
            match_index_path = Path("music_library/music_video_match_index.json")
            if match_index_path.exists():
                with open(match_index_path, 'r') as f:
                    self.match_index = json.load(f)
                logger.info(f"Loaded {len(self.match_index)} music-video matches")
                
        except Exception as e:
            logger.error(f"Error loading existing indexes: {e}")
    
    def _save_indexes(self):
        """Save analysis and match indexes"""
        try:
            os.makedirs("music_library", exist_ok=True)
            
            # Save video context cache
            with open("music_library/video_context_cache.json", 'w') as f:
                json.dump(self.video_context_cache, f, indent=2)
            
            # Save music context cache
            with open("music_library/music_context_cache.json", 'w') as f:
                json.dump(self.music_context_cache, f, indent=2)
            
            # Save match index
            with open("music_library/music_video_match_index.json", 'w') as f:
                json.dump(self.match_index, f, indent=2)
                
            logger.info("Saved all indexes successfully")
            
        except Exception as e:
            logger.error(f"Error saving indexes: {e}")
    
    def analyze_video_context(self, video_path: str) -> VideoContext:
        """Analyze video for context using transcript and frame analysis"""
        
        # Create cache key
        video_key = hashlib.md5(video_path.encode()).hexdigest()
        
        # Check cache first
        if video_key in self.video_context_cache:
            data = self.video_context_cache[video_key]
            return VideoContext(**data)
        
        logger.info(f"Analyzing video context: {Path(video_path).name}")
        
        try:
            # Step 1: Extract transcript
            transcript = self.audio_analyzer.transcribe_audio(video_path)
            if not transcript:
                transcript = "No speech detected"
            
            # Step 2: Extract and analyze frames
            frames = self.frame_analyzer.extract_frames(video_path, interval_seconds=30.0)
            frame_result = self.frame_analyzer.analyze_frames_with_ai(frames)
            frame_analysis = frame_result.get('full_analysis', 'Frame analysis failed')
            
            # Step 3: Get video duration
            duration = self._get_video_duration(video_path)
            
            # Step 4: Use GPT-4o to analyze combined context
            # Ensure transcript and frame_analysis are strings before slicing
            safe_transcript = str(transcript) if transcript else "No transcript available"
            safe_frame_analysis = str(frame_analysis) if frame_analysis else "No frame analysis available"
            
            context_prompt = f"""
            Analyze this video content and provide a comprehensive context analysis:
            
            TRANSCRIPT: {safe_transcript[:1000]}...
            
            VISUAL ANALYSIS: {safe_frame_analysis}
            
            VIDEO DURATION: {duration} seconds
            
            Please provide analysis in this exact JSON format:
            {{
                "visual_mood": "energetic/calm/dramatic/upbeat/melancholic/etc",
                "content_type": "educational/entertainment/sports/music/documentary/etc",
                "energy_level": "high/medium/low",
                "themes": ["theme1", "theme2", "theme3"],
                "summary": "Brief summary of video content and mood"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a video content analyzer. Provide accurate, structured analysis."},
                    {"role": "user", "content": context_prompt}
                ],
                temperature=0.1
            )
            
            # Parse AI response
            response_content = response.choices[0].message.content.strip()
            
            if not response_content:
                raise ValueError("Empty response from AI")
            
            # Try to extract JSON from response if it contains extra text
            try:
                if response_content.startswith('```json'):
                    response_content = response_content.split('```json')[1].split('```')[0].strip()
                elif response_content.startswith('```'):
                    response_content = response_content.split('```')[1].split('```')[0].strip()
                
                ai_analysis = json.loads(response_content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}. Raw response: {response_content}")
                # Use default analysis
                ai_analysis = {
                    "visual_mood": "neutral",
                    "content_type": "general",
                    "energy_level": "medium",
                    "themes": [],
                    "summary": "Analysis failed"
                }
            
            # Create VideoContext object
            video_context = VideoContext(
                video_path=video_path,
                transcript=safe_transcript[:500] if safe_transcript else "No transcript",  # Truncate for storage
                frame_analysis=safe_frame_analysis[:300] if safe_frame_analysis else "No frame analysis",  # Truncate for storage
                visual_mood=ai_analysis.get("visual_mood", "neutral"),
                content_type=ai_analysis.get("content_type", "general"),
                energy_level=ai_analysis.get("energy_level", "medium"),
                themes=ai_analysis.get("themes", []),
                duration=duration
            )
            
            # Cache the result
            self.video_context_cache[video_key] = {
                "video_path": video_context.video_path,
                "transcript": video_context.transcript,
                "frame_analysis": video_context.frame_analysis,
                "visual_mood": video_context.visual_mood,
                "content_type": video_context.content_type,
                "energy_level": video_context.energy_level,
                "themes": video_context.themes,
                "duration": video_context.duration
            }
            
            logger.info(f"Video analysis complete: {ai_analysis.get('visual_mood')} mood, {ai_analysis.get('energy_level')} energy")
            return video_context
            
        except Exception as e:
            logger.error(f"Error analyzing video context: {e}")
            # Return basic context as fallback
            return VideoContext(
                video_path=video_path,
                transcript="Analysis failed",
                frame_analysis="Analysis failed", 
                visual_mood="neutral",
                content_type="general",
                energy_level="medium",
                themes=[],
                duration=0.0
            )
    
    def analyze_music_context(self, music_path: str, music_name: str, music_genre: str) -> MusicContext:
        """Analyze music track for mood, energy, and characteristics"""
        
        # Create cache key
        music_key = hashlib.md5(music_path.encode()).hexdigest()
        
        # Check cache first
        if music_key in self.music_context_cache:
            data = self.music_context_cache[music_key]
            return MusicContext(**data)
        
        logger.info(f"Analyzing music context: {music_name}")
        
        try:
            # Use GPT-4o to analyze music based on filename and genre
            music_prompt = f"""
            Analyze this music track and provide characteristics for video matching:
            
            TRACK NAME: {music_name}
            GENRE: {music_genre}
            FILE PATH: {Path(music_path).name}
            
            Based on the track name and genre, provide analysis in this exact JSON format:
            {{
                "mood": "energetic/calm/dramatic/upbeat/melancholic/chill/intense/etc",
                "energy_level": "high/medium/low",
                "tempo": "fast/medium/slow",
                "themes": ["theme1", "theme2", "theme3"],
                "description": "Brief description of the music style and mood"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a music analyst. Analyze tracks for mood, energy, and video compatibility."},
                    {"role": "user", "content": music_prompt}
                ],
                temperature=0.1
            )
            
            # Parse AI response
            response_content = response.choices[0].message.content.strip()
            
            if not response_content:
                raise ValueError("Empty response from AI")
            
            # Try to extract JSON from response if it contains extra text
            try:
                if response_content.startswith('```json'):
                    response_content = response_content.split('```json')[1].split('```')[0].strip()
                elif response_content.startswith('```'):
                    response_content = response_content.split('```')[1].split('```')[0].strip()
                
                ai_analysis = json.loads(response_content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}. Raw response: {response_content}")
                # Use default analysis
                ai_analysis = {
                    "mood": "neutral",
                    "energy_level": "medium",
                    "tempo": "medium",
                    "themes": ["general"],
                    "description": "Analysis failed"
                }
            
            # Get file size
            file_size = Path(music_path).stat().st_size / (1024 * 1024)  # MB
            
            # Create MusicContext object
            music_context = MusicContext(
                file_path=music_path,
                name=music_name,
                genre=music_genre,
                mood=ai_analysis.get("mood", "neutral"),
                energy_level=ai_analysis.get("energy_level", "medium"),
                tempo=ai_analysis.get("tempo", "medium"),
                themes=ai_analysis.get("themes", []),
                size_mb=round(file_size, 2)
            )
            
            # Cache the result
            self.music_context_cache[music_key] = {
                "file_path": music_context.file_path,
                "name": music_context.name,
                "genre": music_context.genre,
                "mood": music_context.mood,
                "energy_level": music_context.energy_level,
                "tempo": music_context.tempo,
                "themes": music_context.themes,
                "size_mb": music_context.size_mb
            }
            
            logger.info(f"Music analysis complete: {ai_analysis.get('mood')} mood, {ai_analysis.get('energy_level')} energy")
            return music_context
            
        except Exception as e:
            logger.error(f"Error analyzing music context: {e}")
            # Return basic context as fallback
            return MusicContext(
                file_path=music_path,
                name=music_name,
                genre=music_genre,
                mood="neutral",
                energy_level="medium", 
                tempo="medium",
                themes=[],
                size_mb=0.0
            )
    
    def calculate_compatibility(self, video_context: VideoContext, music_context: MusicContext) -> MusicVideoMatch:
        """Calculate compatibility between video and music using AI"""
        
        try:
            compatibility_prompt = f"""
            Analyze the compatibility between this video and music track for background music selection:
            
            VIDEO CONTEXT:
            - Content Type: {video_context.content_type}
            - Visual Mood: {video_context.visual_mood}
            - Energy Level: {video_context.energy_level}
            - Themes: {video_context.themes}
            - Duration: {video_context.duration} seconds
            - Sample Transcript: {video_context.transcript[:200]}...
            
            MUSIC CONTEXT:
            - Name: {music_context.name}
            - Genre: {music_context.genre}
            - Mood: {music_context.mood}
            - Energy Level: {music_context.energy_level}
            - Tempo: {music_context.tempo}
            - Themes: {music_context.themes}
            
            Provide compatibility analysis in this exact JSON format:
            {{
                "compatibility_score": 0.85,
                "reasoning": "Detailed explanation of why this music fits or doesn't fit",
                "mood_match": "excellent/good/fair/poor",
                "energy_match": "excellent/good/fair/poor", 
                "theme_match": "excellent/good/fair/poor",
                "recommendation": "highly_recommended/recommended/acceptable/not_recommended"
            }}
            
            Score should be 0.0-1.0 where 1.0 is perfect match.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert in music-video pairing for optimal viewer experience."},
                    {"role": "user", "content": compatibility_prompt}
                ],
                temperature=0.1
            )
            
            # Parse AI response
            response_content = response.choices[0].message.content.strip()
            
            if not response_content:
                raise ValueError("Empty response from AI")
            
            # Try to extract JSON from response if it contains extra text
            try:
                if response_content.startswith('```json'):
                    response_content = response_content.split('```json')[1].split('```')[0].strip()
                elif response_content.startswith('```'):
                    response_content = response_content.split('```')[1].split('```')[0].strip()
                
                ai_analysis = json.loads(response_content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}. Raw response: {response_content}")
                # Use default analysis
                ai_analysis = {
                    "compatibility_score": 0.5,
                    "reasoning": "Analysis failed due to parsing error",
                    "mood_match": "fair",
                    "energy_match": "fair",
                    "theme_match": "fair",
                    "recommendation": "acceptable"
                }
            
            return MusicVideoMatch(
                video_path=video_context.video_path,
                music_path=music_context.file_path,
                compatibility_score=ai_analysis.get("compatibility_score", 0.5),
                reasoning=ai_analysis.get("reasoning", "Analysis unavailable"),
                mood_match=ai_analysis.get("mood_match", "fair"),
                energy_match=ai_analysis.get("energy_match", "fair"),
                theme_match=ai_analysis.get("theme_match", "fair")
            )
            
        except Exception as e:
            logger.error(f"Error calculating compatibility: {e}")
            # Return basic compatibility as fallback
            return MusicVideoMatch(
                video_path=video_context.video_path,
                music_path=music_context.file_path,
                compatibility_score=0.5,
                reasoning="Analysis failed - using default compatibility",
                mood_match="fair",
                energy_match="fair", 
                theme_match="fair"
            )
    
    def create_match_index_for_video(self, video_path: str) -> List[MusicVideoMatch]:
        """Create comprehensive music match index for a specific video"""
        
        logger.info(f"Creating match index for: {Path(video_path).name}")
        
        # Step 1: Analyze video context
        video_context = self.analyze_video_context(video_path)
        
        # Step 2: Get all available music tracks
        music_tracks = self.music_selector.music_index
        if not music_tracks:
            logger.warning("No music tracks available for matching")
            return []
        
        # Step 3: Analyze each music track and calculate compatibility
        matches = []
        
        for i, track in enumerate(music_tracks):
            logger.info(f"Analyzing track {i+1}/{len(music_tracks)}: {track['name']}")
            
            # Analyze music context
            music_context = self.analyze_music_context(
                track['file'], 
                track['name'], 
                track['genre']
            )
            
            # Calculate compatibility
            match = self.calculate_compatibility(video_context, music_context)
            matches.append(match)
            
            # Small delay to respect API limits
            time.sleep(0.5)
        
        # Step 4: Sort by compatibility score
        matches.sort(key=lambda x: x.compatibility_score, reverse=True)
        
        # Step 5: Store in match index
        video_key = hashlib.md5(video_path.encode()).hexdigest()
        self.match_index[video_key] = {
            "video_path": video_path,
            "matches": [
                {
                    "music_path": match.music_path,
                    "compatibility_score": match.compatibility_score,
                    "reasoning": match.reasoning,
                    "mood_match": match.mood_match,
                    "energy_match": match.energy_match,
                    "theme_match": match.theme_match
                }
                for match in matches
            ],
            "created_at": time.time()
        }
        
        # Save indexes
        self._save_indexes()
        
        logger.info(f"Match index created with {len(matches)} music options")
        return matches
    
    def get_best_music_for_video(self, video_path: str, min_score: float = 0.7) -> Optional[str]:
        """Get the best music track for a video"""
        
        video_key = hashlib.md5(video_path.encode()).hexdigest()
        
        # Check if we have matches for this video
        if video_key not in self.match_index:
            logger.info("No existing matches found, creating new match index...")
            matches = self.create_match_index_for_video(video_path)
        else:
            matches = self.match_index[video_key]["matches"]
        
        # Find best match above minimum score
        if matches:
            best_match = matches[0]  # Already sorted by score
            if best_match["compatibility_score"] >= min_score:
                logger.info(f"Best music match: {Path(best_match['music_path']).name} (score: {best_match['compatibility_score']:.2f})")
                return best_match["music_path"]
            else:
                logger.info(f"Best match score ({best_match['compatibility_score']:.2f}) below minimum ({min_score})")
        
        return None
    
    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds"""
        try:
            import subprocess
            result = subprocess.run([
                'ffprobe', '-i', video_path,
                '-show_entries', 'format=duration',
                '-v', 'quiet', '-of', 'csv=p=0'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception as e:
            logger.warning(f"Could not get video duration: {e}")
        
        return 0.0
    
    def print_match_report(self, video_path: str):
        """Print detailed match report for a video"""
        
        video_key = hashlib.md5(video_path.encode()).hexdigest()
        
        if video_key not in self.match_index:
            print(f"❌ No match index found for: {Path(video_path).name}")
            return
        
        match_data = self.match_index[video_key]
        matches = match_data["matches"]
        
        print(f"\n🎬 Music Match Report: {Path(video_path).name}")
        print("=" * 60)
        
        # Show top 5 matches
        for i, match in enumerate(matches[:5]):
            print(f"\n🎵 #{i+1} - {Path(match['music_path']).name}")
            print(f"   📊 Compatibility: {match['compatibility_score']:.2f}/1.0")
            print(f"   🎭 Mood Match: {match['mood_match']}")
            print(f"   ⚡ Energy Match: {match['energy_match']}")
            print(f"   🎯 Theme Match: {match['theme_match']}")
            print(f"   💭 Reasoning: {match['reasoning'][:100]}...")


if __name__ == "__main__":
    # Test the music-video matcher
    matcher = MusicVideoMatcher()
    
    # Example usage
    test_video = "C:/Users/Isaia/Documents/Coding/N8N/shared/videos/test.mp4"
    if Path(test_video).exists():
        matches = matcher.create_match_index_for_video(test_video)
        matcher.print_match_report(test_video)
    else:
        print("Test video not found")
