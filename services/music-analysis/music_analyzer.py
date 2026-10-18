"""
Music Analysis Module - Handles audio file analysis and feature extraction
"""
import json
import librosa
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from config import MUSIC_ANALYSIS_CONFIG, DATABASE_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MusicAnalyzer:
    def __init__(self):
        self.config = MUSIC_ANALYSIS_CONFIG
        self.supported_formats = self.config['supported_formats']
        self.cache_file = DATABASE_CONFIG['music_cache']
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load existing music analysis cache"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save music analysis cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def analyze_audio_file(self, file_path: Path) -> Optional[Dict]:
        """Analyze a single audio file and extract features"""
        if not file_path.exists() or file_path.suffix.lower() not in self.supported_formats:
            return None
        
        file_key = str(file_path)
        if file_key in self.cache:
            logger.info(f"Using cached analysis for {file_path.name}")
            return self.cache[file_key]
        
        try:
            logger.info(f"Analyzing audio file: {file_path.name}")
            y, sr = librosa.load(str(file_path))
            
            # Extract audio features
            features = self._extract_features(y, sr)
            features['file_path'] = str(file_path)
            features['file_name'] = file_path.name
            features['duration'] = librosa.get_duration(y=y, sr=sr)
            
            # Determine mood and genre
            features['mood'] = self._classify_mood(features)
            features['genre'] = self._classify_genre(features)
            features['energy_level'] = self._calculate_energy_level(features)
            
            # Cache the results
            self.cache[file_key] = features
            self._save_cache()
            
            return features
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return None
    
    def _extract_features(self, y: np.ndarray, sr: int) -> Dict:
        """Extract audio features using librosa"""
        features = {}
        
        try:
            # Tempo and beat features
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            features['tempo'] = float(tempo)
            features['beat_frames'] = len(beats)
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            features['spectral_centroid_mean'] = float(np.mean(spectral_centroids))
            features['spectral_centroid_std'] = float(np.std(spectral_centroids))
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            features['zero_crossing_rate'] = float(np.mean(zcr))
            
            # MFCC features
            mfccs = librosa.feature.mfcc(y=y, sr=sr)
            for i, mfcc in enumerate(mfccs[:13]):  # First 13 MFCCs
                features[f'mfcc_{i+1}'] = float(np.mean(mfcc))
            
            # Chroma features
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            features['chroma_mean'] = float(np.mean(chroma))
            
            # RMS energy
            rms = librosa.feature.rms(y=y)[0]
            features['rms_energy'] = float(np.mean(rms))
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return {}
    
    def _classify_mood(self, features: Dict) -> str:
        """Classify mood based on audio features"""
        tempo = features.get('tempo', 120)
        energy = features.get('rms_energy', 0.1)
        spectral_centroid = features.get('spectral_centroid_mean', 2000)
        
        if tempo > 140 and energy > 0.15:
            return 'energetic'
        elif tempo < 80 and energy < 0.1:
            return 'calm'
        elif spectral_centroid > 3000 and energy > 0.12:
            return 'happy'
        elif tempo < 100 and spectral_centroid < 2000:
            return 'sad'
        else:
            return 'neutral'
    
    def _classify_genre(self, features: Dict) -> str:
        """Classify genre based on audio features"""
        tempo = features.get('tempo', 120)
        zcr = features.get('zero_crossing_rate', 0.1)
        spectral_centroid = features.get('spectral_centroid_mean', 2000)
        
        if tempo > 120 and zcr > 0.15:
            return 'electronic'
        elif tempo < 90 and spectral_centroid < 2000:
            return 'ambient'
        elif 90 <= tempo <= 130 and zcr > 0.1:
            return 'pop'
        elif tempo > 130:
            return 'dance'
        else:
            return 'general'
    
    def _calculate_energy_level(self, features: Dict) -> float:
        """Calculate overall energy level (0-1 scale)"""
        tempo = features.get('tempo', 120)
        energy = features.get('rms_energy', 0.1)
        zcr = features.get('zero_crossing_rate', 0.1)
        
        # Normalize and combine features
        tempo_score = min(tempo / 180, 1.0)
        energy_score = min(energy / 0.3, 1.0)
        zcr_score = min(zcr / 0.3, 1.0)
        
        return (tempo_score + energy_score + zcr_score) / 3
    
    def bulk_analyze_directory(self, directory: Path) -> List[Dict]:
        """Analyze all audio files in a directory"""
        results = []
        audio_files = []
        
        for ext in self.supported_formats:
            audio_files.extend(directory.rglob(f"*{ext}"))
        
        logger.info(f"Found {len(audio_files)} audio files to analyze")
        
        for audio_file in audio_files:
            result = self.analyze_audio_file(audio_file)
            if result:
                results.append(result)
        
        logger.info(f"Successfully analyzed {len(results)} audio files")
        return results
    
    def find_matching_music(self, video_mood: str, video_energy: float, 
                          available_music: List[Dict]) -> List[Dict]:
        """Find music tracks that match video characteristics"""
        matches = []
        
        for track in available_music:
            compatibility_score = self._calculate_compatibility(
                video_mood, video_energy, track
            )
            
            if compatibility_score > 0.5:  # Threshold for good matches
                track['compatibility_score'] = compatibility_score
                matches.append(track)
        
        # Sort by compatibility score
        matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
        return matches[:10]  # Return top 10 matches
    
    def _calculate_compatibility(self, video_mood: str, video_energy: float, 
                               track: Dict) -> float:
        """Calculate compatibility score between video and music track"""
        score = 0.0
        
        # Mood matching
        track_mood = track.get('mood', 'neutral')
        if video_mood == track_mood:
            score += 0.4
        elif self._moods_compatible(video_mood, track_mood):
            score += 0.2
        
        # Energy level matching
        track_energy = track.get('energy_level', 0.5)
        energy_diff = abs(video_energy - track_energy)
        energy_score = max(0, 1 - energy_diff)
        score += energy_score * 0.3
        
        # Tempo matching (for energetic videos)
        if video_energy > 0.7:
            tempo = track.get('tempo', 120)
            if tempo > 120:
                score += 0.2
        
        # Duration preference (avoid very short tracks)
        duration = track.get('duration', 60)
        if duration > 30:
            score += 0.1
        
        return min(score, 1.0)
    
    def _moods_compatible(self, mood1: str, mood2: str) -> bool:
        """Check if two moods are compatible"""
        compatible_pairs = [
            ('happy', 'energetic'),
            ('calm', 'sad'),
            ('neutral', 'happy'),
            ('neutral', 'calm')
        ]
        
        return (mood1, mood2) in compatible_pairs or (mood2, mood1) in compatible_pairs
