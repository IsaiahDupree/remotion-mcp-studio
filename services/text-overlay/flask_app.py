#!/usr/bin/env python3
"""
Flask Video Enhancement API for N8N Integration

This Flask application provides REST API endpoints for processing videos with:
- AI-generated text overlays
- Background music from SoundCloud tracks
- CSV logging of processing results
- Docker deployment for N8N integration
"""

import os
import csv
import json
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Import our existing video enhancement modules
from enhance_video_fast import enhance_video, process_batch
from video_enhancer.music_enhancer import MusicEnhancer
from video_enhancer.transcript_processor import TranscriptProcessor
from enhanced_video_processor import EnhancedVideoProcessor
from music_video_matcher import MusicVideoMatcher
from smart_video_processor import SmartVideoProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Configuration
SHARED_VIDEO_DIR = os.getenv('SHARED_VIDEO_DIR', r'C:\Users\Isaia\Documents\Coding\N8N\shared\videos')
ENHANCED_VIDEO_DIR = os.getenv('ENHANCED_VIDEO_DIR', 'enhanced_videos')
SOUNDCLOUD_EXCEL_PATH = os.getenv('SOUNDCLOUD_EXCEL_PATH', 'soundcloud_tracks.xlsx')
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'processing_log.csv')

# API Keys from .env file
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

# Set OpenAI API key for modules that need it
if OPENAI_API_KEY:
    os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# Ensure directories exist
os.makedirs(ENHANCED_VIDEO_DIR, exist_ok=True)
os.makedirs(SHARED_VIDEO_DIR, exist_ok=True)

# Create log file directory only if it has a directory path
log_dir = os.path.dirname(LOG_FILE_PATH)
if log_dir:  # Only create if there's actually a directory path
    os.makedirs(log_dir, exist_ok=True)

class VideoProcessingLogger:
    """Handles CSV logging of video processing results"""
    
    def __init__(self, csv_path=LOG_FILE_PATH):
        self.csv_path = csv_path
        self.fieldnames = [
            'timestamp', 'video_filename', 'video_path', 'output_path',
            'transcript', 'text_overlay', 'music_url', 'music_filename',
            'processing_time_seconds', 'success', 'error_message',
            'video_duration', 'original_codec', 'output_codec'
        ]
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Create CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                writer.writeheader()
    
    def log_processing_result(self, result: Dict[str, Any], video_path: str, 
                            transcript: str = "", music_info: Dict = None):
        """Log video processing result to CSV"""
        try:
            music_info = music_info or {}
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'video_filename': os.path.basename(video_path),
                'video_path': video_path,
                'output_path': result.get('output_video', ''),
                'transcript': transcript[:500] + '...' if len(transcript) > 500 else transcript,
                'text_overlay': result.get('text_overlay', ''),
                'music_url': music_info.get('url', ''),
                'music_filename': music_info.get('filename', ''),
                'processing_time_seconds': result.get('processing_time_seconds', 0),
                'success': result.get('success', False),
                'error_message': result.get('error', ''),
                'video_duration': result.get('video_duration_seconds', 0),
                'original_codec': result.get('original_codec', ''),
                'output_codec': result.get('output_codec', '')
            }
            
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                writer.writerow(log_entry)
                
            logger.info(f"Logged processing result for {os.path.basename(video_path)}")
            
        except Exception as e:
            logger.error(f"Error logging to CSV: {str(e)}")

# Initialize CSV logger
csv_logger = VideoProcessingLogger(LOG_FILE_PATH)

# Initialize intelligent music matching components
music_matcher = MusicVideoMatcher()
smart_processor = SmartVideoProcessor(use_intelligent_matching=True)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Docker/N8N monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'shared_videos_dir': SHARED_VIDEO_DIR,
        'output_dir': ENHANCED_VIDEO_DIR,
        'soundcloud_excel_exists': os.path.exists(SOUNDCLOUD_EXCEL_PATH),
        'openai_api_configured': bool(OPENAI_API_KEY)
    })

@app.route('/videos', methods=['GET'])
def list_videos():
    """List available videos in shared directory"""
    try:
        if not os.path.exists(SHARED_VIDEO_DIR):
            return jsonify({'error': 'Shared video directory not found'}), 404
        
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
        videos = []
        
        for root, dirs, files in os.walk(SHARED_VIDEO_DIR):
            for file in files:
                if Path(file).suffix.lower() in video_extensions:
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, SHARED_VIDEO_DIR)
                    videos.append({
                        'filename': file,
                        'relative_path': relative_path,
                        'full_path': full_path,
                        'size_mb': round(os.path.getsize(full_path) / (1024*1024), 2)
                    })
        
        return jsonify({
            'videos': videos,
            'count': len(videos),
            'directory': SHARED_VIDEO_DIR
        })
        
    except Exception as e:
        logger.error(f"Error listing videos: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/soundcloud/tracks', methods=['GET'])
def list_soundcloud_tracks():
    """List available SoundCloud tracks from Excel file"""
    try:
        if not os.path.exists(SOUNDCLOUD_EXCEL_PATH):
            return jsonify({'error': 'SoundCloud Excel file not found'}), 404
        
        df = pd.read_excel(SOUNDCLOUD_EXCEL_PATH)
        tracks = []
        
        for index, row in df.iterrows():
            track_info = {
                'index': index,
                'url': row.get('URL', ''),
                'title': row.get('Title', ''),
                'artist': row.get('Artist', ''),
                'duration': row.get('Duration', ''),
                'genre': row.get('Genre', '')
            }
            tracks.append(track_info)
        
        return jsonify({
            'tracks': tracks,
            'count': len(tracks),
            'excel_path': SOUNDCLOUD_EXCEL_PATH
        })
        
    except Exception as e:
        logger.error(f"Error listing SoundCloud tracks: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/process/video', methods=['POST'])
def process_single_video():
    """Process a single video with text overlay and background music"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if not data or 'video_path' not in data:
            return jsonify({'error': 'video_path is required'}), 400
        
        video_path = data['video_path']
        
        # If relative path, make it absolute from shared directory
        if not os.path.isabs(video_path):
            video_path = os.path.join(SHARED_VIDEO_DIR, video_path)
        
        if not os.path.exists(video_path):
            return jsonify({'error': f'Video file not found: {video_path}'}), 404
        
        # Extract parameters with defaults
        add_music = data.get('add_music', True)
        position = data.get('position', 'TOP')
        custom_text = data.get('custom_text')
        speech_emphasis = data.get('speech_emphasis', 0.6)
        
        # Generate output path
        video_name = Path(video_path).stem
        timestamp = int(datetime.now().timestamp())
        output_filename = f"{video_name}_enhanced_{timestamp}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        logger.info(f"Processing video: {video_path}")
        logger.info(f"Output will be saved to: {output_path}")
        
        # Process the video
        result = enhance_video(
            video_path=video_path,
            output_path=output_path,
            add_music=add_music,
            position=position,
            custom_text=custom_text,
            api_key=OPENAI_API_KEY,
            speech_emphasis_factor=speech_emphasis,
            soundcloud_excel=SOUNDCLOUD_EXCEL_PATH if os.path.exists(SOUNDCLOUD_EXCEL_PATH) else None,
            auto_detect_music=True
        )
        
        # Get transcript for logging
        transcript = ""
        music_info = {}
        
        if result.get('transcript_analysis'):
            try:
                with open(result['transcript_analysis'], 'r', encoding='utf-8') as f:
                    transcript_data = json.load(f)
                    transcript = transcript_data.get('original_transcript', '')
                    # Extract music info if available
                    if 'music_track' in result:
                        music_info = result['music_track']
            except Exception as e:
                logger.warning(f"Could not read transcript file: {str(e)}")
        
        # Log to CSV
        csv_logger.log_processing_result(result, video_path, transcript, music_info)
        
        # Prepare response
        response_data = {
            'success': result.get('success', False),
            'video_path': video_path,
            'output_path': output_path,
            'text_overlay': result.get('text_overlay', ''),
            'processing_time_seconds': result.get('processing_time_seconds', 0),
            'music_added': result.get('music_added', False),
            'transcript_excerpt': transcript[:200] + '...' if len(transcript) > 200 else transcript,
            'error': result.get('error')
        }
        
        # Add download URL if successful
        if result.get('success') and os.path.exists(output_path):
            response_data['download_url'] = f'/download/{output_filename}'
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/process/enhanced', methods=['POST'])
def process_enhanced_video():
    """Process a single video with enhanced 30-second frame analysis and optimized music volume"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if not data or 'video_path' not in data:
            return jsonify({'error': 'video_path is required'}), 400
        
        video_path = data['video_path']
        
        # If relative path, make it absolute from shared directory
        if not os.path.isabs(video_path):
            video_path = os.path.join(SHARED_VIDEO_DIR, video_path)
        
        if not os.path.exists(video_path):
            return jsonify({'error': f'Video file not found: {video_path}'}), 404
        
        # Extract parameters with defaults
        add_music = data.get('add_music', True)
        text_style = data.get('text_style', 'classic')
        position = data.get('position', 'top')
        font = data.get('font', 'arial')
        custom_text = data.get('custom_text')
        speech_emphasis = data.get('speech_emphasis', 0.7)
        
        # Generate output path
        video_name = Path(video_path).stem
        timestamp = int(datetime.now().timestamp())
        output_filename = f"{video_name}_enhanced_{timestamp}.mp4"
        output_path = os.path.join(ENHANCED_VIDEO_DIR, output_filename)
        
        logger.info(f"Processing video with enhanced features: {video_path}")
        logger.info(f"Output will be saved to: {output_path}")
        
        # Initialize enhanced processor
        processor = EnhancedVideoProcessor(api_key=OPENAI_API_KEY)
        
        # Setup text configuration
        text_config = {
            "style": text_style,
            "position": position,
            "font": font,
            "font_scale": 1.2,
            "custom_text": custom_text
        }
        
        # Setup music configuration
        music_config = {
            "enabled": add_music,
            "excel_path": SOUNDCLOUD_EXCEL_PATH if os.path.exists(SOUNDCLOUD_EXCEL_PATH) else None,
            "track_column": "Track URL",
            "speech_emphasis": speech_emphasis,
            "auto_detect": True
        }
        
        # Process the video with enhanced features
        result = processor.enhance_video(
            video_path=video_path,
            output_path=output_path,
            text_config=text_config,
            music_config=music_config
        )
        
        # Log to CSV
        transcript = ""
        music_info = {
            "source": result.get('music_source', ''),
            "path": result.get('music_path', '')
        }
        csv_logger.log_processing_result(result, video_path, transcript, music_info)
        
        # Prepare response
        response_data = {
            'success': result.get('success', False),
            'video_path': video_path,
            'output_path': output_path,
            'text_overlay': result.get('text_used', ''),
            'text_style': result.get('text_style', text_style),
            'processing_time_seconds': result.get('processing_time_seconds', 0),
            'music_added': result.get('music_added', False),
            'music_source': result.get('music_source', 'none'),
            'frame_analysis_used': True,  # Always true for enhanced processing
            'analysis_interval': '30_seconds',
            'music_volume_range': '-25_to_-30dB',
            'error': result.get('error')
        }
        
        # Add download URL if successful
        if result.get('success') and os.path.exists(output_path):
            response_data['download_url'] = f'/download/{output_filename}'
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing enhanced video: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/process/batch', methods=['POST'])
def process_batch_videos():
    """Process multiple videos in batch mode"""
    try:
        data = request.get_json()
        
        if not data or 'video_paths' not in data:
            return jsonify({'error': 'video_paths array is required'}), 400
        
        video_paths = data['video_paths']
        
        # Convert relative paths to absolute
        absolute_paths = []
        for path in video_paths:
            if not os.path.isabs(path):
                path = os.path.join(SHARED_VIDEOS_DIR, path)
            if os.path.exists(path):
                absolute_paths.append(path)
            else:
                logger.warning(f"Video not found: {path}")
        
        if not absolute_paths:
            return jsonify({'error': 'No valid video files found'}), 404
        
        # Extract parameters
        add_music = data.get('add_music', True) 
        position = data.get('position', 'TOP')
        speech_emphasis = data.get('speech_emphasis', 0.6)
        
        logger.info(f"Processing {len(absolute_paths)} videos in batch mode")
        
        # Process batch
        batch_result = process_batch(
            video_list=absolute_paths,
            output_dir=OUTPUT_DIR,
            add_music=add_music,
            position=position,
            api_key=OPENAI_API_KEY,
            soundcloud_excel=SOUNDCLOUD_EXCEL_PATH if os.path.exists(SOUNDCLOUD_EXCEL_PATH) else None,
            speech_emphasis_factor=speech_emphasis
        )
        
        # Log each result to CSV
        for video_path, result in batch_result.get('results', {}).items():
            transcript = result.get('transcript', '')
            music_info = result.get('music_info', {})
            csv_logger.log_processing_result(result, video_path, transcript, music_info)
        
        return jsonify(batch_result)
        
    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download processed video file"""
    try:
        file_path = os.path.join(OUTPUT_DIR, secure_filename(filename))
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/logs/csv', methods=['GET'])
def get_csv_logs():
    """Download CSV processing logs"""
    try:
        if not os.path.exists(CSV_LOG_PATH):
            return jsonify({'error': 'CSV log file not found'}), 404
        
        return send_file(CSV_LOG_PATH, as_attachment=True, download_name='video_processing_log.csv')
        
    except Exception as e:
        logger.error(f"Error downloading CSV logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/logs/recent', methods=['GET'])
def get_recent_logs():
    """Get recent processing logs as JSON"""
    try:
        if not os.path.exists(CSV_LOG_PATH):
            return jsonify({'logs': [], 'count': 0})
        
        # Read last N records
        limit = request.args.get('limit', 10, type=int)
        
        df = pd.read_csv(CSV_LOG_PATH)
        recent_logs = df.tail(limit).to_dict('records')
        
        return jsonify({
            'logs': recent_logs,
            'count': len(recent_logs),
            'total_records': len(df)
        })
        
    except Exception as e:
        logger.error(f"Error getting recent logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze/music-match/<video_filename>', methods=['GET'])
def analyze_music_match(video_filename):
    """Analyze video and return ideal music recommendations"""
    try:
        # Validate video file exists
        video_path = os.path.join(SHARED_VIDEO_DIR, secure_filename(video_filename))
        if not os.path.exists(video_path):
            return jsonify({'error': 'Video file not found'}), 404
        
        logger.info(f"Analyzing music match for video: {video_filename}")
        
        # Generate music compatibility report
        report = smart_processor.get_music_compatibility_report(video_path)
        
        if not report or 'matches' not in report:
            return jsonify({
                'error': 'Failed to generate music compatibility analysis',
                'video_filename': video_filename
            }), 500
        
        # Get the best match
        best_match = None
        if report['matches']:
            best_match = max(report['matches'], key=lambda x: x.get('compatibility_score', 0))
        
        response = {
            'video_filename': video_filename,
            'video_analysis': {
                'content_type': report.get('video_context', {}).get('content_type', 'unknown'),
                'visual_mood': report.get('video_context', {}).get('visual_mood', 'unknown'),
                'energy_level': report.get('video_context', {}).get('energy_level', 'unknown'),
                'themes': report.get('video_context', {}).get('themes', []),
                'duration': report.get('video_context', {}).get('duration', 0)
            },
            'music_recommendations': {
                'total_tracks_analyzed': len(report.get('matches', [])),
                'best_match': best_match,
                'all_matches': report.get('matches', [])[:10],  # Top 10 matches
                'recommendation': {
                    'music_path': best_match.get('music_path') if best_match else None,
                    'compatibility_score': best_match.get('compatibility_score') if best_match else 0,
                    'reasoning': best_match.get('reasoning') if best_match else 'No suitable match found'
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Music analysis complete for {video_filename}. Best match score: {best_match.get('compatibility_score', 0) if best_match else 0}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error analyzing music match for {video_filename}: {str(e)}")
        return jsonify({
            'error': str(e),
            'video_filename': video_filename
        }), 500

@app.route('/process/smart-video', methods=['POST'])
def process_smart_video():
    """Combine video with selected music and text overlay using intelligent processing"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        video_filename = data.get('video_filename')
        music_path = data.get('music_path')  # Optional - if not provided, will use AI selection
        output_filename = data.get('output_filename')
        config = data.get('config', {})
        
        if not video_filename:
            return jsonify({'error': 'video_filename is required'}), 400
        
        # Validate video file exists
        video_path = os.path.join(SHARED_VIDEO_DIR, secure_filename(video_filename))
        if not os.path.exists(video_path):
            return jsonify({'error': 'Video file not found'}), 404
        
        # Generate output filename if not provided
        if not output_filename:
            base_name = os.path.splitext(video_filename)[0]
            output_filename = f"{base_name}_smart_enhanced.mp4"
        
        output_path = os.path.join(ENHANCED_VIDEO_DIR, secure_filename(output_filename))
        
        logger.info(f"Processing smart video: {video_filename} -> {output_filename}")
        
        # Set processing configuration
        processing_config = {
            'min_compatibility_score': config.get('min_compatibility_score', 0.6),
            'music_volume': config.get('music_volume', 0.04),  # -28dB
            'text_style': config.get('text_style', 'modern'),
            'frame_analysis_interval': config.get('frame_analysis_interval', 30.0)
        }
        
        start_time = datetime.now()
        
        # Process video with smart music selection
        if music_path:
            # Use specified music
            result = smart_processor.process_video_with_specified_music(
                video_path=video_path,
                output_path=output_path,
                music_path=music_path,
                config=processing_config
            )
        else:
            # Use AI-selected music
            result = smart_processor.process_video_with_smart_music(
                video_path=video_path,
                output_path=output_path,
                config=processing_config
            )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if result.get('success'):
            # Log the processing
            csv_logger.log_processing_result(
                result=result,
                video_path=video_path,
                transcript=result.get('transcript', ''),
                music_info={
                    'filename': result.get('music_used', ''),
                    'compatibility_score': result.get('compatibility_score', 0)
                }
            )
            
            response = {
                'success': True,
                'video_filename': video_filename,
                'output_filename': output_filename,
                'output_path': output_path,
                'processing_time_seconds': round(processing_time, 2),
                'music_used': result.get('music_used'),
                'compatibility_score': result.get('compatibility_score'),
                'text_overlay': result.get('text_overlay'),
                'transcript_preview': result.get('transcript', '')[:200] + '...' if result.get('transcript') else '',
                'download_url': f'/download/{output_filename}',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Smart video processing completed: {video_filename} -> {output_filename} in {processing_time:.2f}s")
            return jsonify(response)
        else:
            # Log the failure
            csv_logger.log_processing_result(
                result=result,
                video_path=video_path,
                transcript='',
                music_info={'filename': '', 'compatibility_score': 0}
            )
            
            return jsonify({
                'success': False,
                'error': result.get('error', 'Processing failed'),
                'video_filename': video_filename,
                'processing_time_seconds': round(processing_time, 2)
            }), 500
            
    except Exception as e:
        logger.error(f"Error in smart video processing: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Development server
    logger.info("Starting Flask Video Enhancement API")
    logger.info(f"Shared videos directory: {SHARED_VIDEO_DIR}")
    logger.info(f"Output directory: {ENHANCED_VIDEO_DIR}")
    logger.info(f"SoundCloud Excel: {SOUNDCLOUD_EXCEL_PATH}")
    logger.info(f"CSV log path: {LOG_FILE_PATH}")
    
    app.run(host='0.0.0.0', port=5003, debug=False)
