"""
Flask API for Music System Integration with n8n workflows
"""
import json
import logging
from flask import Flask, request, jsonify
from pathlib import Path
from main_system import MusicSystem
from config import CACHE_DIR
from music_preprocessor import MusicPreprocessor
from video_processor import VideoProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize Music System
class MusicAnalysisAPI:
    def __init__(self):
        self.music_system = MusicSystem()
        self.music_preprocessor = MusicPreprocessor()
        self.video_processor = VideoProcessor()
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Music Analysis API',
        'version': '1.0.0'
    })

@app.route('/analyze-music-match', methods=['POST'])
def analyze_music_match():
    """
    Enhanced music analysis endpoint compatible with existing n8n workflow
    Maintains backward compatibility while adding new features
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Extract input parameters
        video_path = data.get('video_path', '')
        transcript = data.get('transcript', '')
        visual_analysis = data.get('visual_analysis', '')
        
        if not video_path:
            return jsonify({'error': 'video_path is required'}), 400
        
        logger.info(f"Analyzing music match for: {Path(video_path).name}")
        
        # Find music recommendations using the new system
        result = MusicAnalysisAPI().music_system.find_music_for_video(
            video_path=video_path,
            transcript=transcript,
            visual_analysis=visual_analysis
        )
        
        if result['status'] == 'error':
            return jsonify({'error': result['message']}), 500
        
        # Format response for n8n compatibility
        response = {
            'detected_mood': result['video_analysis']['detected_mood'],
            'energy_level': result['video_analysis']['energy_level'],
            'music_style_preferences': result['video_analysis']['music_style_preference'],
            'total_tracks_analyzed': result['total_tracks_analyzed']
        }
        
        # Add best music recommendation
        if 'best_match' in result:
            best_match = result['best_match']
            response['music_recommendation'] = {
                'file_path': best_match['file_path'],
                'file_name': best_match['file_name'],
                'compatibility_score': round(best_match.get('final_score', best_match['compatibility_score']), 3),
                'mood': best_match.get('mood', 'unknown'),
                'genre': best_match.get('genre', 'unknown'),
                'energy_level': best_match.get('energy_level', 0.5),
                'duration': best_match.get('duration', 0),
                'reasoning': f"Selected based on {result['video_analysis']['detected_mood']} mood detection and {result['video_analysis']['energy_level']:.2f} energy level"
            }
        else:
            # Fallback to existing system behavior
            response['music_recommendation'] = {
                'file_path': '/srv/music_library/General/default.mp3',
                'file_name': 'default.mp3',
                'compatibility_score': 0.5,
                'mood': 'neutral',
                'genre': 'general',
                'energy_level': 0.5,
                'reasoning': 'No specific music match found, using default'
            }
        
        # Add alternative recommendations
        if len(result.get('music_recommendations', [])) > 1:
            response['alternative_recommendations'] = [
                {
                    'file_path': track['file_path'],
                    'file_name': track['file_name'],
                    'compatibility_score': round(track.get('final_score', track['compatibility_score']), 3),
                    'mood': track.get('mood', 'unknown'),
                    'genre': track.get('genre', 'unknown')
                }
                for track in result['music_recommendations'][1:4]  # Top 3 alternatives
            ]
        
        # Add trending suggestions
        if result.get('trending_suggestions'):
            response['trending_genres'] = result['trending_suggestions']
        
        logger.info(f"Music analysis complete: {response['music_recommendation']['file_name']} (score: {response['music_recommendation']['compatibility_score']})")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in music analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/system-status', methods=['GET'])
def system_status():
    """Get comprehensive system status"""
    try:
        status = MusicAnalysisAPI().music_system.get_system_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/setup-soundcloud', methods=['POST'])
def setup_soundcloud():
    """Setup SoundCloud music library"""
    try:
        logger.info("Starting SoundCloud setup...")
        result = MusicAnalysisAPI().music_system.setup_soundcloud_music()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error setting up SoundCloud: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-music-libraries', methods=['POST'])
def analyze_music_libraries():
    """Analyze all existing music libraries"""
    try:
        logger.info("Starting music library analysis...")
        result = MusicAnalysisAPI().music_system.analyze_existing_music_libraries()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error analyzing music libraries: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/update-trends', methods=['POST'])
def update_trends():
    """Update trend analysis data"""
    try:
        logger.info("Updating music trends...")
        result = MusicAnalysisAPI().music_system.update_trends()
        trend_summary = MusicAnalysisAPI().music_system.trend_analyzer.get_trend_summary()
        return jsonify({
            'status': 'success',
            'last_updated': result['last_updated'],
            'trend_summary': trend_summary
        })
    except Exception as e:
        logger.error(f"Error updating trends: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/bulk-analyze-videos', methods=['POST'])
def bulk_analyze_videos():
    """Bulk analyze videos for music recommendations"""
    try:
        data = request.get_json()
        video_directory = Path(data.get('video_directory', '/home/node/shared/videos'))
        
        if not video_directory.exists():
            return jsonify({'error': f'Video directory not found: {video_directory}'}), 400
        
        logger.info(f"Starting bulk video analysis for: {video_directory}")
        results = MusicAnalysisAPI().music_system.bulk_process_videos(video_directory)
        
        return jsonify({
            'status': 'success',
            'total_videos': len(results),
            'successful': len([r for r in results if r['status'] == 'success']),
            'failed': len([r for r in results if r['status'] == 'error']),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in bulk video analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-music-recommendations', methods=['POST'])
def get_music_recommendations():
    """Get music recommendations for given mood and energy"""
    try:
        data = request.get_json()
        mood = data.get('mood', 'neutral')
        energy = data.get('energy_level', 0.5)
        count = data.get('count', 5)
        
        # Get all available music
        all_music = []
        for library_tracks in MusicAnalysisAPI().music_system.music_index.values():
            if isinstance(library_tracks, dict):
                all_music.extend(library_tracks.values())
        
        if not all_music:
            return jsonify({'error': 'No music tracks available'}), 404
        
        # Find matching tracks
        matching_tracks = MusicAnalysisAPI().music_system.music_analyzer.find_matching_music(
            mood, energy, all_music
        )
        
        # Apply trend boosting
        for track in matching_tracks:
            trend_boost = MusicAnalysisAPI().music_system.trend_analyzer.get_trend_boost_score(track)
            track['final_score'] = track['compatibility_score'] + (trend_boost * 0.2)
        
        # Sort and limit results
        matching_tracks.sort(key=lambda x: x['final_score'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'mood': mood,
            'energy_level': energy,
            'recommendations': matching_tracks[:count],
            'total_available': len(all_music)
        })
        
    except Exception as e:
        logger.error(f"Error getting music recommendations: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Music Analysis API...")
    
    # Get system status on startup
    try:
        status = MusicAnalysisAPI().music_system.get_system_status()
        logger.info(f"System ready with {status['total_tracks']} tracks available")
    except Exception as e:
        logger.warning(f"Could not get initial system status: {e}")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)
