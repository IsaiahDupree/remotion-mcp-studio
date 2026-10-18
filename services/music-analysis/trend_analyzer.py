"""
Trend Analysis Module - Analyzes music trends for scaffolding recommendations
"""
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import logging
from config import TREND_CONFIG, DATABASE_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrendAnalyzer:
    def __init__(self):
        self.config = TREND_CONFIG
        self.cache_file = DATABASE_CONFIG['trend_cache']
        self.update_interval = self.config['update_interval']
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load existing trend cache"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading trend cache: {e}")
        
        return {
            'last_updated': None,
            'trending_genres': [],
            'trending_artists': [],
            'trending_keywords': [],
            'mood_trends': {},
            'tempo_trends': {},
            'platform_trends': {}
        }
    
    def _save_cache(self):
        """Save trend cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving trend cache: {e}")
    
    def should_update_trends(self) -> bool:
        """Check if trends need updating"""
        if not self.cache.get('last_updated'):
            return True
        
        last_update = datetime.fromisoformat(self.cache['last_updated'])
        time_since_update = datetime.now() - last_update
        
        return time_since_update.total_seconds() > self.update_interval
    
    def update_all_trends(self) -> Dict:
        """Update trends from all configured sources"""
        if not self.should_update_trends():
            logger.info("Trends are up to date, skipping update")
            return self.cache
        
        logger.info("Updating music trends...")
        
        trend_data = {
            'last_updated': datetime.now().isoformat(),
            'trending_genres': [],
            'trending_artists': [],
            'trending_keywords': [],
            'mood_trends': {},
            'tempo_trends': {},
            'platform_trends': {}
        }
        
        # Update trends from different sources
        for source in self.config['sources']:
            try:
                source_trends = self._get_trends_from_source(source)
                if source_trends:
                    trend_data = self._merge_trend_data(trend_data, source_trends, source)
            except Exception as e:
                logger.error(f"Error getting trends from {source}: {e}")
        
        # Analyze and process trends
        trend_data = self._process_trend_data(trend_data)
        
        # Update cache
        self.cache = trend_data
        self._save_cache()
        
        logger.info("Trend update complete")
        return trend_data
    
    def _get_trends_from_source(self, source: str) -> Optional[Dict]:
        """Get trend data from specific source"""
        if source == 'spotify':
            return self._get_spotify_trends()
        elif source == 'youtube':
            return self._get_youtube_trends()
        elif source == 'soundcloud':
            return self._get_soundcloud_trends()
        else:
            logger.warning(f"Unknown trend source: {source}")
            return None
    
    def _get_spotify_trends(self) -> Dict:
        """Get trending data from Spotify (simulated - requires API keys)"""
        # Note: In a real implementation, you'd use Spotify Web API
        # For now, return simulated trending data
        return {
            'genres': ['electronic', 'pop', 'hip-hop', 'indie', 'dance'],
            'moods': {'energetic': 0.8, 'happy': 0.7, 'chill': 0.6},
            'tempo_ranges': {'fast': 0.4, 'medium': 0.4, 'slow': 0.2},
            'artists': ['Various Electronic Artists', 'Indie Pop Artists']
        }
    
    def _get_youtube_trends(self) -> Dict:
        """Get trending music data from YouTube"""
        # Simulated YouTube Music trends
        return {
            'genres': ['lofi', 'ambient', 'electronic', 'pop'],
            'moods': {'calm': 0.6, 'focus': 0.5, 'energetic': 0.4},
            'tempo_ranges': {'slow': 0.5, 'medium': 0.3, 'fast': 0.2},
            'keywords': ['study music', 'work music', 'chill beats']
        }
    
    def _get_soundcloud_trends(self) -> Dict:
        """Get trending data from SoundCloud"""
        # Simulated SoundCloud trends
        return {
            'genres': ['electronic', 'ambient', 'experimental', 'house'],
            'moods': {'creative': 0.7, 'energetic': 0.6, 'experimental': 0.5},
            'tempo_ranges': {'medium': 0.5, 'fast': 0.4, 'slow': 0.1},
            'artists': ['Independent Electronic Artists']
        }
    
    def _merge_trend_data(self, main_data: Dict, source_data: Dict, source: str) -> Dict:
        """Merge trend data from a specific source"""
        # Merge genres
        if 'genres' in source_data:
            main_data['trending_genres'].extend(source_data['genres'])
        
        # Merge artists
        if 'artists' in source_data:
            main_data['trending_artists'].extend(source_data['artists'])
        
        # Merge keywords
        if 'keywords' in source_data:
            main_data['trending_keywords'].extend(source_data['keywords'])
        
        # Merge mood trends
        if 'moods' in source_data:
            for mood, score in source_data['moods'].items():
                if mood in main_data['mood_trends']:
                    main_data['mood_trends'][mood] = max(main_data['mood_trends'][mood], score)
                else:
                    main_data['mood_trends'][mood] = score
        
        # Merge tempo trends
        if 'tempo_ranges' in source_data:
            for tempo, score in source_data['tempo_ranges'].items():
                if tempo in main_data['tempo_trends']:
                    main_data['tempo_trends'][tempo] = max(main_data['tempo_trends'][tempo], score)
                else:
                    main_data['tempo_trends'][tempo] = score
        
        # Store platform-specific data
        main_data['platform_trends'][source] = source_data
        
        return main_data
    
    def _process_trend_data(self, trend_data: Dict) -> Dict:
        """Process and clean trend data"""
        # Remove duplicates and sort by popularity
        trend_data['trending_genres'] = list(set(trend_data['trending_genres']))
        trend_data['trending_artists'] = list(set(trend_data['trending_artists']))
        trend_data['trending_keywords'] = list(set(trend_data['trending_keywords']))
        
        # Calculate weighted trend scores
        trend_data['genre_weights'] = self._calculate_genre_weights(trend_data['trending_genres'])
        trend_data['mood_rankings'] = sorted(trend_data['mood_trends'].items(), 
                                           key=lambda x: x[1], reverse=True)
        trend_data['tempo_rankings'] = sorted(trend_data['tempo_trends'].items(), 
                                            key=lambda x: x[1], reverse=True)
        
        return trend_data
    
    def _calculate_genre_weights(self, genres: List[str]) -> Dict:
        """Calculate weights for trending genres"""
        genre_counts = {}
        for genre in genres:
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Normalize weights
        total_count = sum(genre_counts.values())
        if total_count > 0:
            return {genre: count / total_count for genre, count in genre_counts.items()}
        else:
            return {}
    
    def get_trend_boost_score(self, music_metadata: Dict) -> float:
        """Calculate trend boost score for a music track"""
        if not self.cache.get('last_updated'):
            return 0.0
        
        boost_score = 0.0
        
        # Genre trend boost
        track_genre = music_metadata.get('genre', '').lower()
        genre_weights = self.cache.get('genre_weights', {})
        if track_genre in genre_weights:
            boost_score += genre_weights[track_genre] * 0.4
        
        # Mood trend boost
        track_mood = music_metadata.get('mood', '').lower()
        mood_trends = self.cache.get('mood_trends', {})
        if track_mood in mood_trends:
            boost_score += mood_trends[track_mood] * 0.3
        
        # Tempo trend boost
        track_tempo = music_metadata.get('tempo', 120)
        tempo_category = self._categorize_tempo(track_tempo)
        tempo_trends = self.cache.get('tempo_trends', {})
        if tempo_category in tempo_trends:
            boost_score += tempo_trends[tempo_category] * 0.3
        
        return min(boost_score, 1.0)  # Cap at 1.0
    
    def _categorize_tempo(self, tempo: float) -> str:
        """Categorize tempo into slow/medium/fast"""
        if tempo < 90:
            return 'slow'
        elif tempo < 130:
            return 'medium'
        else:
            return 'fast'
    
    def get_trending_recommendations(self, video_mood: str, count: int = 5) -> List[str]:
        """Get trending music recommendations based on video mood"""
        recommendations = []
        
        # Get mood-based genre recommendations
        mood_trends = self.cache.get('mood_trends', {})
        if video_mood in mood_trends:
            # Find genres associated with this mood
            trending_genres = self.cache.get('trending_genres', [])
            mood_genres = self._get_genres_for_mood(video_mood, trending_genres)
            recommendations.extend(mood_genres[:count])
        
        # Add general trending genres if not enough recommendations
        if len(recommendations) < count:
            trending_genres = self.cache.get('trending_genres', [])
            for genre in trending_genres:
                if genre not in recommendations:
                    recommendations.append(genre)
                if len(recommendations) >= count:
                    break
        
        return recommendations[:count]
    
    def _get_genres_for_mood(self, mood: str, genres: List[str]) -> List[str]:
        """Map mood to appropriate genres"""
        mood_genre_mapping = {
            'happy': ['pop', 'upbeat', 'electronic', 'dance'],
            'energetic': ['electronic', 'dance', 'house', 'hip-hop'],
            'calm': ['ambient', 'lofi', 'chillout', 'acoustic'],
            'sad': ['ambient', 'indie', 'alternative', 'melancholic'],
            'creative': ['experimental', 'electronic', 'indie'],
            'focus': ['lofi', 'ambient', 'instrumental']
        }
        
        mood_genres = mood_genre_mapping.get(mood.lower(), [])
        return [genre for genre in genres if genre.lower() in mood_genres]
    
    def get_trend_summary(self) -> Dict:
        """Get a summary of current trends"""
        if not self.cache.get('last_updated'):
            self.update_all_trends()
        
        return {
            'last_updated': self.cache['last_updated'],
            'top_genres': self.cache['trending_genres'][:5],
            'top_moods': dict(self.cache.get('mood_rankings', [])[:5]),
            'top_tempos': dict(self.cache.get('tempo_rankings', [])[:3]),
            'trending_keywords': self.cache['trending_keywords'][:10]
        }
