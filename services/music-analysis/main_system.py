"""
Main Music System Orchestrator - Coordinates all modules for intelligent music selection
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from config import (
    PATHS, DATABASE_CONFIG, MUSIC_ANALYSIS_CONFIG, 
    VIDEO_ANALYSIS_CONFIG, SOUNDCLOUD_CONFIG, TREND_CONFIG
)
from music_analyzer import MusicAnalyzer
from soundcloud_downloader import SoundCloudDownloader
from video_analyzer import VideoAnalyzer
from trend_analyzer import TrendAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MusicSystem:
    def __init__(self):
        """Initialize the complete music system"""
        logger.info("Initializing Music System...")
        
        # Initialize all modules
        self.music_analyzer = MusicAnalyzer()
        self.soundcloud_downloader = SoundCloudDownloader()
        self.video_analyzer = VideoAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        
        # Load music indexes
        self.music_index = self._load_music_index()
        
        logger.info("Music System initialized successfully")
    
    def _load_music_index(self) -> Dict:
        """Load or create music index"""
        index_file = DATABASE_CONFIG['music_index']
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading music index: {e}")
        
        return {'wordsOnText': {}, 'soundcloud': {}, 'last_updated': None}
    
    def _save_music_index(self):
        """Save music index"""
        try:
            with open(DATABASE_CONFIG['music_index'], 'w') as f:
                json.dump(self.music_index, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving music index: {e}")
    
    def setup_soundcloud_music(self) -> Dict:
        """Complete SoundCloud setup: download and analyze"""
        logger.info("Setting up SoundCloud music library...")
        
        # Load track data from Excel
        tracks = self.soundcloud_downloader.load_soundcloud_data()
        if not tracks:
            logger.warning("No SoundCloud tracks found in Excel file")
            return {'status': 'error', 'message': 'No tracks found'}
        
        # Download tracks
        download_results = self.soundcloud_downloader.bulk_download(tracks)
        
        # Analyze downloaded tracks
        downloaded_files = self.soundcloud_downloader.get_downloaded_tracks()
        analysis_results = []
        
        for file_path in downloaded_files:
            analysis = self.music_analyzer.analyze_audio_file(file_path)
            if analysis:
                analysis_results.append(analysis)
        
        # Update music index
        self.music_index['soundcloud'] = {
            result['file_path']: result for result in analysis_results
        }
        self.music_index['last_updated'] = datetime.now().isoformat()
        self._save_music_index()
        
        return {
            'status': 'success',
            'downloaded': len(download_results['successful']),
            'failed': len(download_results['failed']),
            'analyzed': len(analysis_results)
        }
    
    def analyze_existing_music_libraries(self) -> Dict:
        """Analyze all existing music libraries"""
        logger.info("Analyzing existing music libraries...")
        
        results = {'wordsOnText': [], 'soundcloud': []}
        
        # Analyze WordsOnText library
        if PATHS['wordsontext_music'].exists():
            wot_results = self.music_analyzer.bulk_analyze_directory(
                PATHS['wordsontext_music']
            )
            results['wordsOnText'] = wot_results
            
            # Update music index
            self.music_index['wordsOnText'] = {
                result['file_path']: result for result in wot_results
            }
        
        # Analyze SoundCloud library
        if PATHS['soundcloud_music'].exists():
            sc_results = self.music_analyzer.bulk_analyze_directory(
                PATHS['soundcloud_music']
            )
            results['soundcloud'] = sc_results
            
            # Update existing SoundCloud index
            for result in sc_results:
                self.music_index['soundcloud'][result['file_path']] = result
        
        self.music_index['last_updated'] = datetime.now().isoformat()
        self._save_music_index()
        
        total_analyzed = len(results['wordsOnText']) + len(results['soundcloud'])
        logger.info(f"Music analysis complete: {total_analyzed} tracks analyzed")
        
        return {
            'status': 'success',
            'wordsOnText_tracks': len(results['wordsOnText']),
            'soundcloud_tracks': len(results['soundcloud']),
            'total_tracks': total_analyzed
        }
    
    def find_music_for_video(self, video_path: str, transcript: str = "", 
                           visual_analysis: str = "") -> Dict:
        """Find the best music match for a video"""
        logger.info(f"Finding music for video: {Path(video_path).name}")
        
        # Analyze the video
        video_analysis = self.video_analyzer.analyze_video_file(
            Path(video_path), transcript, visual_analysis
        )
        
        if not video_analysis:
            return {'status': 'error', 'message': 'Video analysis failed'}
        
        # Get all available music tracks
        all_music = []
        for library_tracks in self.music_index.values():
            if isinstance(library_tracks, dict):
                all_music.extend(library_tracks.values())
        
        if not all_music:
            return {'status': 'error', 'message': 'No music tracks available'}
        
        # Find matching tracks
        video_mood = video_analysis['detected_mood']
        video_energy = video_analysis['energy_level']
        
        matching_tracks = self.music_analyzer.find_matching_music(
            video_mood, video_energy, all_music
        )
        
        # Apply trend boosting
        for track in matching_tracks:
            trend_boost = self.trend_analyzer.get_trend_boost_score(track)
            track['final_score'] = track['compatibility_score'] + (trend_boost * 0.2)
        
        # Re-sort by final score
        matching_tracks.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Get trend recommendations for additional context
        trend_recommendations = self.trend_analyzer.get_trending_recommendations(
            video_mood, count=3
        )
        
        result = {
            'status': 'success',
            'video_analysis': {
                'detected_mood': video_mood,
                'energy_level': video_energy,
                'music_style_preference': video_analysis.get('music_style_preference', [])
            },
            'music_recommendations': matching_tracks[:5],  # Top 5 matches
            'trending_suggestions': trend_recommendations,
            'total_tracks_analyzed': len(all_music)
        }
        
        if matching_tracks:
            result['best_match'] = matching_tracks[0]
        
        return result
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        # Count available tracks
        wot_count = len(self.music_index.get('wordsOnText', {}))
        sc_count = len(self.music_index.get('soundcloud', {}))
        
        # Check trend data freshness
        trend_status = 'outdated' if self.trend_analyzer.should_update_trends() else 'current'
        
        return {
            'music_libraries': {
                'wordsOnText': {
                    'tracks': wot_count,
                    'path': str(PATHS['wordsontext_music']),
                    'exists': PATHS['wordsontext_music'].exists()
                },
                'soundcloud': {
                    'tracks': sc_count,
                    'path': str(PATHS['soundcloud_music']),
                    'exists': PATHS['soundcloud_music'].exists()
                }
            },
            'total_tracks': wot_count + sc_count,
            'last_analysis': self.music_index.get('last_updated'),
            'trend_data': {
                'status': trend_status,
                'last_updated': self.trend_analyzer.cache.get('last_updated')
            },
            'cache_files': {
                'music_index': DATABASE_CONFIG['music_index'].exists(),
                'music_cache': DATABASE_CONFIG['music_cache'].exists(),
                'video_cache': DATABASE_CONFIG['video_cache'].exists(),
                'soundcloud_cache': DATABASE_CONFIG['soundcloud_cache'].exists(),
                'trend_cache': DATABASE_CONFIG['trend_cache'].exists()
            }
        }
    
    def update_trends(self) -> Dict:
        """Update trend analysis data"""
        logger.info("Updating trend analysis...")
        return self.trend_analyzer.update_all_trends()
    
    def bulk_process_videos(self, video_directory: Path) -> List[Dict]:
        """Process multiple videos for music recommendations"""
        results = []
        
        video_files = []
        for ext in VIDEO_ANALYSIS_CONFIG['supported_formats']:
            video_files.extend(video_directory.rglob(f"*{ext}"))
        
        logger.info(f"Processing {len(video_files)} videos for music recommendations")
        
        for video_file in video_files:
            try:
                result = self.find_music_for_video(str(video_file))
                result['video_path'] = str(video_file)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {video_file}: {e}")
                results.append({
                    'video_path': str(video_file),
                    'status': 'error',
                    'message': str(e)
                })
        
        return results
    
    def export_music_recommendations(self, video_results: List[Dict], 
                                   output_file: Path) -> bool:
        """Export music recommendations to JSON file"""
        try:
            export_data = {
                'export_date': datetime.now().isoformat(),
                'total_videos': len(video_results),
                'system_status': self.get_system_status(),
                'recommendations': video_results
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Recommendations exported to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            return False

def main():
    """Main function for testing the system"""
    system = MusicSystem()
    
    # Get system status
    status = system.get_system_status()
    print("\n=== MUSIC SYSTEM STATUS ===")
    print(json.dumps(status, indent=2))
    
    # Update trends
    print("\n=== UPDATING TRENDS ===")
    trend_summary = system.update_trends()
    print(f"Trends updated: {trend_summary.get('last_updated')}")
    
    # Example video analysis (if video exists)
    example_video = PATHS['videos'] / "IMG_3287.MP4"
    if example_video.exists():
        print(f"\n=== ANALYZING EXAMPLE VIDEO ===")
        result = system.find_music_for_video(
            str(example_video),
            transcript="Children playing energetically in the backyard",
            visual_analysis="Bright outdoor scene with fast movements"
        )
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
