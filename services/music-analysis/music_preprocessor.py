#!/usr/bin/env python3
"""
Music Pre-processor - Analyzes all music files and creates searchable CSV database
"""
import os
import pandas as pd
import librosa
import numpy as np
from pathlib import Path
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

from config import SOUNDCLOUD_DIR, MUSIC_DIR, CACHE_DIR
from music_analyzer import MusicAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MusicPreprocessor:
    """Pre-process and analyze all music files into searchable database"""
    
    def __init__(self):
        self.music_analyzer = MusicAnalyzer()
        self.csv_file = CACHE_DIR / "music_database.csv"
        self.analysis_cache = CACHE_DIR / "music_analysis_cache.json"
        self.supported_formats = ['.mp3', '.m4a', '.wav', '.flac', '.ogg']
        
        # Ensure cache directory exists
        CACHE_DIR.mkdir(exist_ok=True)
    
    def get_all_music_files(self) -> List[Path]:
        """Get all music files from all sources"""
        music_files = []
        
        # SoundCloud downloads
        if SOUNDCLOUD_DIR.exists():
            for ext in self.supported_formats:
                music_files.extend(SOUNDCLOUD_DIR.glob(f"*{ext}"))
        
        # WordsOnText music library
        if MUSIC_DIR.exists():
            for ext in self.supported_formats:
                music_files.extend(MUSIC_DIR.rglob(f"*{ext}"))
        
        logger.info(f"Found {len(music_files)} music files across all sources")
        return music_files
    
    def get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of file for change detection"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return str(file_path.stat().st_mtime)
    
    def load_analysis_cache(self) -> Dict:
        """Load existing analysis cache"""
        if self.analysis_cache.exists():
            try:
                with open(self.analysis_cache, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading cache: {e}")
        return {}
    
    def save_analysis_cache(self, cache: Dict):
        """Save analysis cache"""
        try:
            with open(self.analysis_cache, 'w') as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def analyze_music_file(self, file_path: Path) -> Optional[Dict]:
        """Analyze a single music file"""
        try:
            logger.info(f"Analyzing: {file_path.name}")
            
            # Basic file info
            file_stats = file_path.stat()
            analysis = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size_mb': round(file_stats.st_size / (1024 * 1024), 2),
                'source': 'soundcloud' if 'soundcloud' in str(file_path) else 'wordsOntext',
                'analyzed_at': datetime.now().isoformat()
            }
            
            # Audio analysis using librosa
            try:
                y, sr = librosa.load(str(file_path), duration=30)  # Load first 30 seconds
                
                # Basic audio properties
                analysis['duration_seconds'] = round(float(librosa.get_duration(y=y, sr=sr)), 2)
                analysis['sample_rate'] = int(sr)
                
                # Tempo and beat tracking
                tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                analysis['tempo_bpm'] = round(float(tempo), 1)
                
                # Spectral features
                spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
                analysis['spectral_centroid_mean'] = round(float(np.mean(spectral_centroids)), 2)
                analysis['spectral_centroid_std'] = round(float(np.std(spectral_centroids)), 2)
                
                # Zero crossing rate (indicates percussive content)
                zcr = librosa.feature.zero_crossing_rate(y)[0]
                analysis['zero_crossing_rate'] = round(float(np.mean(zcr)), 4)
                
                # RMS energy (loudness)
                rms = librosa.feature.rms(y=y)[0]
                analysis['rms_energy_mean'] = round(float(np.mean(rms)), 4)
                analysis['rms_energy_std'] = round(float(np.std(rms)), 4)
                
                # MFCC features (timbre characteristics)
                mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
                for i in range(13):
                    analysis[f'mfcc_{i+1}_mean'] = round(float(np.mean(mfccs[i])), 3)
                    analysis[f'mfcc_{i+1}_std'] = round(float(np.std(mfccs[i])), 3)
                
                # Chroma features (harmonic content)
                try:
                    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
                    analysis['chroma_mean'] = round(float(np.mean(chroma)), 3)
                    analysis['chroma_std'] = round(float(np.std(chroma)), 3)
                except Exception as e:
                    logger.warning(f"Chroma analysis failed: {e}")
                    analysis['chroma_mean'] = 0.0
                    analysis['chroma_std'] = 0.0
                
                # Spectral rolloff
                rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
                analysis['spectral_rolloff_mean'] = round(float(np.mean(rolloff)), 2)
                
            except Exception as e:
                logger.error(f"Error in audio analysis for {file_path.name}: {e}")
                analysis['analysis_error'] = str(e)
            
            # Simple mood/genre classification based on audio features
            try:
                # Energy-based mood classification
                energy_level = analysis.get('rms_energy_mean', 0)
                tempo_bpm = analysis.get('tempo_bpm', 120)
                spectral_centroid = analysis.get('spectral_centroid_mean', 0)
                
                # Calculate energy level (0-1 scale)
                normalized_energy = min(1.0, energy_level * 1000)  # Scale RMS energy
                
                # Mood classification based on energy and tempo
                if normalized_energy > 0.7 and tempo_bpm > 130:
                    detected_mood = 'energetic'
                elif normalized_energy > 0.5 and tempo_bpm > 110:
                    detected_mood = 'upbeat'
                elif normalized_energy < 0.3 and tempo_bpm < 90:
                    detected_mood = 'calm'
                elif spectral_centroid > 3000:
                    detected_mood = 'bright'
                else:
                    detected_mood = 'neutral'
                
                # Genre classification based on tempo and spectral features
                if tempo_bpm > 140 and normalized_energy > 0.6:
                    if spectral_centroid > 4000:
                        predicted_genre = 'electronic'
                    else:
                        predicted_genre = 'dance'
                elif tempo_bpm < 85:
                    if normalized_energy < 0.4:
                        predicted_genre = 'ambient'
                    else:
                        predicted_genre = 'downtempo'
                elif 90 < tempo_bpm < 120:
                    if normalized_energy > 0.5:
                        predicted_genre = 'pop'
                    else:
                        predicted_genre = 'indie'
                else:
                    predicted_genre = 'general'
                
                analysis.update({
                    'detected_mood': detected_mood,
                    'energy_level': round(normalized_energy, 2),
                    'predicted_genre': predicted_genre,
                    'danceability': round(min(1.0, (tempo_bpm - 60) / 140), 2),
                    'valence': round(normalized_energy, 2)
                })
                
            except Exception as e:
                logger.warning(f"Mood/genre classification failed for {file_path.name}: {e}")
                analysis.update({
                    'detected_mood': 'neutral',
                    'energy_level': 0.5,
                    'predicted_genre': 'general',
                    'danceability': 0.5,
                    'valence': 0.5
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return None
    
    def process_all_music(self, force_reanalyze: bool = False) -> pd.DataFrame:
        """Process all music files and create database"""
        logger.info("🎵 Starting music pre-processing...")
        
        # Get all music files
        music_files = self.get_all_music_files()
        if not music_files:
            logger.warning("No music files found!")
            return pd.DataFrame()
        
        # Load existing cache
        cache = self.load_analysis_cache()
        all_analyses = []
        
        for i, file_path in enumerate(music_files, 1):
            logger.info(f"Processing {i}/{len(music_files)}: {file_path.name}")
            
            # Check if analysis is cached and file hasn't changed
            file_key = str(file_path)
            file_hash = self.get_file_hash(file_path)
            
            if not force_reanalyze and file_key in cache:
                cached_analysis = cache[file_key]
                if cached_analysis.get('file_hash') == file_hash:
                    logger.info("  ✅ Using cached analysis")
                    all_analyses.append(cached_analysis)
                    continue
            
            # Analyze the file
            analysis = self.analyze_music_file(file_path)
            if analysis:
                analysis['file_hash'] = file_hash
                all_analyses.append(analysis)
                cache[file_key] = analysis
                
                # Save cache every 10 files
                if i % 10 == 0:
                    self.save_analysis_cache(cache)
                    logger.info(f"  💾 Progress saved: {i}/{len(music_files)}")
        
        # Save final cache
        self.save_analysis_cache(cache)
        
        # Create DataFrame
        if all_analyses:
            df = pd.DataFrame(all_analyses)
            
            # Add derived features for matching
            df['tempo_category'] = pd.cut(df['tempo_bpm'], 
                                         bins=[0, 90, 120, 140, 180, 300], 
                                         labels=['slow', 'moderate', 'upbeat', 'fast', 'very_fast'])
            
            df['energy_category'] = pd.cut(df['energy_level'], 
                                          bins=[0, 0.3, 0.6, 1.0], 
                                          labels=['low', 'medium', 'high'])
            
            # Save to CSV
            df.to_csv(self.csv_file, index=False)
            logger.info(f"✅ Music database saved: {self.csv_file}")
            logger.info(f"📊 Total tracks analyzed: {len(df)}")
            
            return df
        else:
            logger.warning("No music files could be analyzed")
            return pd.DataFrame()
    
    def load_music_database(self) -> pd.DataFrame:
        """Load existing music database"""
        if self.csv_file.exists():
            return pd.read_csv(self.csv_file)
        else:
            logger.warning("Music database not found. Run process_all_music() first.")
            return pd.DataFrame()
    
    def search_music(self, 
                    mood: Optional[str] = None,
                    genre: Optional[str] = None,
                    energy_min: Optional[float] = None,
                    energy_max: Optional[float] = None,
                    tempo_min: Optional[float] = None,
                    tempo_max: Optional[float] = None,
                    duration_min: Optional[float] = None,
                    duration_max: Optional[float] = None) -> pd.DataFrame:
        """Search music database with filters"""
        df = self.load_music_database()
        
        if df.empty:
            return df
        
        # Apply filters
        if mood:
            df = df[df['detected_mood'].str.contains(mood, case=False, na=False)]
        
        if genre:
            df = df[df['predicted_genre'].str.contains(genre, case=False, na=False)]
        
        if energy_min is not None:
            df = df[df['energy_level'] >= energy_min]
        
        if energy_max is not None:
            df = df[df['energy_level'] <= energy_max]
        
        if tempo_min is not None:
            df = df[df['tempo_bpm'] >= tempo_min]
        
        if tempo_max is not None:
            df = df[df['tempo_bpm'] <= tempo_max]
        
        if duration_min is not None:
            df = df[df['duration_seconds'] >= duration_min]
        
        if duration_max is not None:
            df = df[df['duration_seconds'] <= duration_max]
        
        return df
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the music database"""
        df = self.load_music_database()
        
        if df.empty:
            return {"error": "No music database found"}
        
        stats = {
            'total_tracks': len(df),
            'total_duration_hours': round(df['duration_seconds'].sum() / 3600, 2),
            'total_size_gb': round(df['file_size_mb'].sum() / 1024, 2),
            'sources': df['source'].value_counts().to_dict(),
            'moods': df['detected_mood'].value_counts().to_dict(),
            'genres': df['predicted_genre'].value_counts().to_dict(),
            'tempo_range': {
                'min': df['tempo_bpm'].min(),
                'max': df['tempo_bpm'].max(),
                'mean': round(df['tempo_bpm'].mean(), 1)
            },
            'energy_range': {
                'min': df['energy_level'].min(),
                'max': df['energy_level'].max(),
                'mean': round(df['energy_level'].mean(), 2)
            }
        }
        
        return stats

if __name__ == "__main__":
    processor = MusicPreprocessor()
    
    print("🎵 Music Pre-Processor")
    print("=" * 50)
    
    # Process all music
    df = processor.process_all_music()
    
    if not df.empty:
        print(f"✅ Successfully processed {len(df)} tracks")
        
        # Show stats
        stats = processor.get_database_stats()
        print(f"📊 Database Statistics:")
        print(f"   Total tracks: {stats['total_tracks']}")
        print(f"   Total duration: {stats['total_duration_hours']} hours")
        print(f"   Total size: {stats['total_size_gb']} GB")
        print(f"   Sources: {stats['sources']}")
        print(f"   Top moods: {dict(list(stats['moods'].items())[:5])}")
        print(f"   Top genres: {dict(list(stats['genres'].items())[:5])}")
    else:
        print("❌ No music files processed")
