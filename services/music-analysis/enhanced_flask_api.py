#!/usr/bin/env python3
"""
Enhanced Flask API for Complete Music & Video Processing System
Includes music pre-processing, matching, and video generation with music+text overlays
"""
import json
import logging
import os
from datetime import datetime
import pandas as pd
from flask import Flask, request, jsonify, send_file
from pathlib import Path
import tempfile
import uuid

from main_system import MusicSystem
from config import CACHE_DIR, SOUNDCLOUD_DIR
from music_preprocessor import MusicPreprocessor
from video_processor import VideoProcessor
from enhanced_video_processor import EnhancedVideoProcessor
from intelligent_video_analyzer_fixed import IntelligentVideoAnalyzer

# OpenAI API Key should be set via environment variable
# os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file upload

# Initialize components
class EnhancedMusicAPI:
    def __init__(self):
        self.music_system = MusicSystem()
        self.music_preprocessor = MusicPreprocessor()
        self.video_processor = VideoProcessor()
        self.enhanced_video_processor = EnhancedVideoProcessor()
        self.video_analyzer = IntelligentVideoAnalyzer()
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)

# Global API instance
api = EnhancedMusicAPI()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Enhanced Music & Video API',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    })

# ============================================================================
# MUSIC DATABASE ENDPOINTS
# ============================================================================

@app.route('/music/preprocess', methods=['POST'])
def preprocess_music():
    """Pre-process all music files into searchable database"""
    try:
        data = request.get_json() or {}
        force_reanalyze = data.get('force_reanalyze', False)
        
        logger.info(f"Starting music pre-processing (force={force_reanalyze})...")
        
        # Process all music
        df = api.music_preprocessor.process_all_music(force_reanalyze=force_reanalyze)
        
        if df.empty:
            return jsonify({
                'status': 'error',
                'message': 'No music files found to process'
            }), 404
        
        # Get database stats
        stats = api.music_preprocessor.get_database_stats()
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully processed {len(df)} music tracks',
            'database_stats': stats,
            'csv_path': str(api.music_preprocessor.csv_file),
            'processed_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in music preprocessing: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/music/database/stats', methods=['GET'])
def get_music_database_stats():
    """Get music database statistics"""
    try:
        stats = api.music_preprocessor.get_database_stats()
        if 'error' in stats:
            return jsonify(stats), 404
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/music/search', methods=['POST'])
def search_music_database():
    """Search music database with filters"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No search criteria provided'}), 400
        
        # Extract search parameters
        mood = data.get('mood')
        genre = data.get('genre')
        energy_min = data.get('energy_min')
        energy_max = data.get('energy_max')
        tempo_min = data.get('tempo_min')
        tempo_max = data.get('tempo_max')
        duration_min = data.get('duration_min')
        duration_max = data.get('duration_max')
        limit = data.get('limit', 50)
        
        # Search database
        results_df = api.music_preprocessor.search_music(
            mood=mood,
            genre=genre,
            energy_min=energy_min,
            energy_max=energy_max,
            tempo_min=tempo_min,
            tempo_max=tempo_max,
            duration_min=duration_min,
            duration_max=duration_max
        )
        
        if results_df.empty:
            return jsonify({
                'status': 'success',
                'results': [],
                'total_found': 0,
                'search_criteria': data
            })
        
        # Limit results and convert to dict
        limited_results = results_df.head(limit)
        results_list = limited_results.to_dict('records')
        
        return jsonify({
            'status': 'success',
            'results': results_list,
            'total_found': len(results_df),
            'returned': len(results_list),
            'search_criteria': data
        })
        
    except Exception as e:
        logger.error(f"Error searching music database: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# VIDEO ANALYSIS & MUSIC MATCHING ENDPOINTS
# ============================================================================

@app.route('/analyze-music-match', methods=['POST'])
def analyze_music_match():
    """
    Enhanced music analysis endpoint - finds best music match for video
    Compatible with existing n8n workflow
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        video_path = data.get('video_path')
        transcript = data.get('transcript', '')
        visual_analysis = data.get('visual_analysis', '')
        description = data.get('description', '')
        
        if not video_path:
            return jsonify({'error': 'video_path is required'}), 400
        
        if not Path(video_path).exists():
            return jsonify({'error': f'Video file not found: {video_path}'}), 404
        
        logger.info(f"Analyzing music match for: {Path(video_path).name}")
        
        # Use music database for enhanced matching
        df = api.music_preprocessor.load_music_database()
        
        if df.empty:
            # Fallback to original system
            result = api.music_system.find_music_for_video(
                video_path=video_path,
                transcript=transcript,
                visual_analysis=visual_analysis
            )
        else:
            # Enhanced matching with database
            video_analysis = api.music_system.video_analyzer.analyze_video_file(
                Path(video_path), transcript, visual_analysis
            )
            
            detected_mood = video_analysis.get('detected_mood', 'neutral')
            energy_level = video_analysis.get('energy_level', 0.5)
            
            # Search database for matching music
            matching_df = api.music_preprocessor.search_music(
                mood=detected_mood,
                energy_min=max(0, energy_level - 0.3),
                energy_max=min(1, energy_level + 0.3)
            )
            
            if not matching_df.empty:
                # Get top match
                best_match = matching_df.iloc[0]
                
                result = {
                    'status': 'success',
                    'detected_mood': detected_mood,
                    'energy_level': energy_level,
                    'music_recommendation': {
                        'file_path': best_match['file_path'],
                        'file_name': best_match['file_name'],
                        'mood': best_match['detected_mood'],
                        'genre': best_match['predicted_genre'],
                        'energy': best_match['energy_level'],
                        'tempo_bpm': best_match['tempo_bpm'],
                        'duration_seconds': best_match['duration_seconds'],
                        'compatibility_score': 0.9,  # High score from database match
                        'source': best_match['source']
                    },
                    'analysis_method': 'database_enhanced',
                    'alternatives': matching_df.head(5).to_dict('records')
                }
            else:
                # No database matches, use original system
                result = api.music_system.find_music_for_video(
                    video_path=video_path,
                    transcript=transcript,
                    visual_analysis=visual_analysis
                )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error analyzing music match: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/video/analyze-content', methods=['POST'])
def analyze_video_content():
    """
    Intelligent Video Content Analysis
    - Detects existing captions in video
    - Extracts transcript from audio if no captions
    - Samples frames efficiently based on video length
    - Uses AI to analyze visual content
    - Generates perfect contextual text overlay
    
    Request JSON:
    {
        "video_path": "/path/to/video.mp4",
        "openai_api_key": "optional_api_key_override"
    }
    
    Returns:
    {
        "video_path": "/path/to/video.mp4",
        "has_existing_captions": false,
        "existing_captions": null,
        "transcript": "extracted audio transcript...",
        "visual_analysis": "AI analysis of video frames...",
        "suggested_overlay": "Perfect contextual text",
        "confidence_score": 0.85,
        "frame_samples_count": 4,
        "processing_time": 12.3,
        "video_info": {
            "duration": 71.2,
            "width": 720,
            "height": 1280,
            "has_audio": true
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        video_path = data.get('video_path')
        if not video_path:
            return jsonify({'error': 'video_path is required'}), 400
        
        # Check if video file exists
        if not Path(video_path).exists():
            return jsonify({'error': f'Video file not found: {video_path}'}), 404
        
        # Override OpenAI API key if provided
        openai_key = data.get('openai_api_key')
        if openai_key:
            analyzer = IntelligentVideoAnalyzer(openai_api_key=openai_key)
        else:
            analyzer = api.video_analyzer
        
        logger.info(f"🎬 Starting intelligent analysis of: {Path(video_path).name}")
        
        # Perform intelligent video analysis
        analysis_result = analyzer.analyze_video_intelligently(video_path)
        
        # Get video info for response
        video_info = analyzer.get_video_info(video_path)
        
        # Prepare comprehensive response
        result = {
            'video_path': video_path,
            'video_name': Path(video_path).name,
            'has_existing_captions': analysis_result.has_existing_captions,
            'existing_captions': analysis_result.existing_captions,
            'transcript': analysis_result.transcript,
            'visual_analysis': analysis_result.visual_analysis,
            'suggested_overlay': analysis_result.suggested_overlay,
            'confidence_score': analysis_result.confidence_score,
            'frame_samples_count': len(analysis_result.frame_samples),
            'processing_time': analysis_result.processing_time,
            'video_info': {
                'duration': video_info.get('duration', 0),
                'width': video_info.get('width', 0),
                'height': video_info.get('height', 0),
                'has_audio': video_info.get('has_audio', False),
                'codec': video_info.get('video_stream', {}).get('codec_name', 'unknown') if video_info.get('video_stream') else 'unknown'
            },
            'analysis_strategy': {
                'caption_detection': 'Visual pattern analysis',
                'transcription': 'Whisper AI' if analysis_result.transcript else 'Not available',
                'frame_analysis': 'GPT-4 Vision' if analysis_result.visual_analysis else 'Not available',
                'overlay_generation': 'Context-aware blending'
            },
            'api_version': '2.0.0',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Analysis complete: '{analysis_result.suggested_overlay}' (confidence: {analysis_result.confidence_score:.2f})")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in intelligent video analysis: {e}")
        return jsonify({
            'error': str(e),
            'error_type': 'intelligent_analysis_error',
            'timestamp': datetime.now().isoformat()
        }), 500

# ============================================================================
# VIDEO PROCESSING ENDPOINTS
# ============================================================================

@app.route('/video/process', methods=['POST'])
def process_video_with_music_and_text():
    """
    Process video with background music and text overlay
    Core video processing endpoint
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Required parameters
        video_path = data.get('video_path')
        music_path = data.get('music_path')
        
        if not video_path or not music_path:
            return jsonify({'error': 'video_path and music_path are required'}), 400
        
        if not Path(video_path).exists():
            return jsonify({'error': f'Video file not found: {video_path}'}), 404
        
        if not Path(music_path).exists():
            return jsonify({'error': f'Music file not found: {music_path}'}), 404
        
        # Optional parameters
        text_lines = data.get('text_lines', [])
        music_volume_db = data.get('music_volume_db', -25.0)
        text_position = data.get('text_position', 'bottom')
        preserve_audio = data.get('preserve_audio', True)
        output_name = data.get('output_name')
        
        # Generate output path
        if not output_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"processed_{timestamp}.mp4"
        
        output_dir = CACHE_DIR / "processed_videos"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / output_name
        
        logger.info(f"Processing video with music and text...")
        logger.info(f"  Video: {Path(video_path).name}")
        logger.info(f"  Music: {Path(music_path).name}")
        logger.info(f"  Text lines: {len(text_lines)}")
        logger.info(f"  Music volume: {music_volume_db}dB")
        
        # Process the video
        success = api.video_processor.process_video_with_music_and_text(
            video_path=video_path,
            music_path=music_path,
            text_lines=text_lines,
            output_path=str(output_path),
            music_volume_db=music_volume_db,
            text_position=text_position,
            preserve_audio=preserve_audio
        )
        
        if success:
            file_size = output_path.stat().st_size
            return jsonify({
                'status': 'success',
                'message': 'Video processed successfully',
                'output_path': str(output_path),
                'output_name': output_name,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'processing_settings': {
                    'music_volume_db': music_volume_db,
                    'text_position': text_position,
                    'preserve_audio': preserve_audio,
                    'text_lines_count': len(text_lines)
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Video processing failed'
            }), 500
        
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/video/analyze-with-openai', methods=['POST'])
def analyze_video_with_openai():
    """
    Enhanced OpenAI-powered video analysis:
    - Detects existing captions or generates transcript
    - Samples frames efficiently based on video length
    - Uses AI to blend transcript + visual context
    - Returns perfect text overlay suggestion
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        video_path = data.get('video_path')
        openai_api_key = data.get('openai_api_key')
        
        if not video_path:
            return jsonify({'error': 'video_path is required'}), 400
        
        if not Path(video_path).exists():
            return jsonify({'error': f'Video file not found: {video_path}'}), 404
        
        logger.info(f"Starting OpenAI video analysis: {Path(video_path).name}")
        
        # Perform enhanced analysis using the intelligent video analyzer
        intelligent_analyzer = IntelligentVideoAnalyzer(openai_api_key=openai_api_key)
        result = intelligent_analyzer.analyze_video_for_perfect_overlay(
            video_path=video_path,
            openai_api_key=openai_api_key
        )
        
        if 'error' in result:
            return jsonify(result), 500
        
        logger.info(f"✅ OpenAI analysis completed: '{result['suggested_overlay']}'")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in OpenAI video analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/video/process-enhanced', methods=['POST'])
def process_video_enhanced():
    """
    Enhanced video processing with smart text placement and proper audio mixing
    Features:
    - Intelligent text positioning (avoiding faces)
    - Dynamic text sizing based on video dimensions
    - Custom fonts including Sunny Spells font
    - Smart font selection based on text content
    - Background music at -20 to -30dB
    - Preserve original audio
    - Smart frame analysis
    
    New Parameters:
    - font_style: 'auto', 'creative', 'bold', 'clean', 'modern' (default: 'auto')
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Required parameters
        video_path = data.get('video_path')
        
        if not video_path:
            return jsonify({'error': 'video_path is required'}), 400
        
        if not Path(video_path).exists():
            return jsonify({'error': f'Video file not found: {video_path}'}), 404
        
        # Optional parameters with smart defaults
        music_path = data.get('music_path')
        text_lines = data.get('text_lines', [])
        output_name = data.get('output_name')
        music_volume_db = data.get('music_volume_db', -25.0)  # Default -25dB
        preserve_audio = data.get('preserve_audio', True)  # Keep original audio
        smart_positioning = data.get('smart_positioning', True)  # Use AI positioning
        font_style = data.get('font_style', 'auto')  # Font style selection
        
        # Validate music volume is in recommended range
        if music_volume_db > -20 or music_volume_db < -35:
            logger.warning(f"Music volume {music_volume_db}dB outside recommended range (-20 to -35dB)")
        
        # Auto-select music if not provided
        if not music_path or music_path == 'auto':
            logger.info("Auto-selecting background music...")
            # Use first available music file as fallback
            try:
                music_files = list(Path(SOUNDCLOUD_DIR).glob("*.mp3"))
                if music_files:
                    music_path = str(music_files[0])
                    logger.info(f"Selected music: {Path(music_path).name}")
                else:
                    return jsonify({'error': 'No music files available and none specified'}), 400
            except Exception as e:
                return jsonify({'error': f'Could not auto-select music: {e}'}), 400
        
        if not Path(music_path).exists():
            return jsonify({'error': f'Music file not found: {music_path}'}), 404
        
        # Generate output path
        if not output_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"enhanced_processed_{timestamp}.mp4"
        
        output_path = Path(CACHE_DIR) / "processed_videos" / output_name
        output_path.parent.mkdir(exist_ok=True)
        
        logger.info(f"🎬 Starting enhanced video processing...")
        logger.info(f"  Video: {Path(video_path).name}")
        logger.info(f"  Music: {Path(music_path).name}")
        logger.info(f"  Text lines: {len(text_lines)}")
        logger.info(f"  Music volume: {music_volume_db}dB")
        logger.info(f"  Smart positioning: {smart_positioning}")
        logger.info(f"  Preserve audio: {preserve_audio}")
        logger.info(f"  Font style: {font_style}")
        
        # Process with enhanced features
        success = api.enhanced_video_processor.process_video_with_enhanced_features(
            video_path=video_path,
            music_path=music_path,
            text_lines=text_lines,
            output_path=str(output_path),
            music_volume_db=music_volume_db,
            preserve_audio=preserve_audio,
            smart_positioning=smart_positioning,
            font_style=font_style
        )
        
        if success and output_path.exists():
            file_size = output_path.stat().st_size
            return jsonify({
                'status': 'success',
                'message': 'Enhanced video processing completed successfully',
                'output_path': str(output_path),
                'output_name': output_name,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'processing_settings': {
                    'music_volume_db': music_volume_db,
                    'preserve_audio': preserve_audio,
                    'smart_positioning': smart_positioning,
                    'font_style': font_style,
                    'text_lines_count': len(text_lines)
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Enhanced video processing failed'
            }), 500
        
    except Exception as e:
        logger.error(f"Error in enhanced video processing: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/fonts/list', methods=['GET'])
def list_available_fonts():
    """
    List all available custom fonts with their details
    """
    try:
        fonts = api.enhanced_video_processor.get_available_fonts()
        
        # Check which fonts are actually available
        available_fonts = []
        missing_fonts = []
        
        for font in fonts:
            font_info = {
                'name': font['name'],
                'style': font['style'],
                'description': font['description'],
                'path': font['path']
            }
            
            if font['path'].endswith('.otf') or font['path'].endswith('.ttf'):
                # Custom font - check if exists
                from pathlib import Path
                if Path(font['path']).exists():
                    font_info['status'] = 'available'
                    font_info['file_size'] = Path(font['path']).stat().st_size
                    available_fonts.append(font_info)
                else:
                    font_info['status'] = 'missing'
                    missing_fonts.append(font_info)
            else:
                # System font
                font_info['status'] = 'system'
                available_fonts.append(font_info)
        
        return jsonify({
            'total_fonts': len(fonts),
            'available_fonts': available_fonts,
            'missing_fonts': missing_fonts,
            'font_styles': {
                'creative': len([f for f in available_fonts if f['style'] == 'creative']),
                'bold': len([f for f in available_fonts if f['style'] == 'bold']),
                'clean': len([f for f in available_fonts if f['style'] == 'clean']),
                'modern': len([f for f in available_fonts if f['style'] == 'modern'])
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing fonts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/fonts/test', methods=['POST'])
def test_font_rendering():
    """
    Test font rendering with sample text
    Creates a quick video sample with the specified font
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        font_style = data.get('font_style', 'auto')
        test_text = data.get('test_text', ['Font Test', 'Sample Text'])
        video_path = data.get('video_path')
        
        if not video_path:
            return jsonify({'error': 'video_path is required for font testing'}), 400
        
        if not Path(video_path).exists():
            return jsonify({'error': f'Video file not found: {video_path}'}), 404
        
        # Get selected font info
        selected_font = api.enhanced_video_processor.select_best_font(' '.join(test_text), font_style)
        
        # Create output path for test
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"font_test_{font_style}_{timestamp}.mp4"
        output_path = Path(CACHE_DIR) / "font_tests" / output_name
        output_path.parent.mkdir(exist_ok=True)
        
        logger.info(f"🎨 Testing font: {selected_font['name']} ({font_style} style)")
        
        # Process video with text overlay only (no music)
        success = api.enhanced_video_processor.process_video_with_enhanced_features(
            video_path=video_path,
            music_path=None,  # No music for font test
            text_lines=test_text,
            output_path=str(output_path),
            music_volume_db=-25.0,
            preserve_audio=True,
            smart_positioning=True,
            font_style=font_style
        )
        
        if success and output_path.exists():
            file_size = output_path.stat().st_size
            return jsonify({
                'status': 'success',
                'message': 'Font test completed successfully',
                'output_path': str(output_path),
                'output_name': output_name,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'font_used': {
                    'name': selected_font['name'],
                    'style': selected_font['style'],
                    'description': selected_font['description'],
                    'path': selected_font['path']
                },
                'test_settings': {
                    'font_style': font_style,
                    'test_text': test_text
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Font test failed'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in font test: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/video/analyze-and-process', methods=['POST'])
def analyze_and_process_video():
    """
    Complete pipeline: Analyze video, find music, process with music and text
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        video_path = data.get('video_path')
        transcript = data.get('transcript', '')
        visual_analysis = data.get('visual_analysis', '')
        text_lines = data.get('text_lines', [])
        music_volume_db = data.get('music_volume_db', -25.0)
        
        if not video_path:
            return jsonify({'error': 'video_path is required'}), 400
        
        if not Path(video_path).exists():
            return jsonify({'error': f'Video file not found: {video_path}'}), 404
        
        logger.info(f"Complete pipeline for: {Path(video_path).name}")
        
        # Step 1: Find best music match
        music_match_data = {
            'video_path': video_path,
            'transcript': transcript,
            'visual_analysis': visual_analysis
        }
        
        # Simulate internal call to music matching
        with app.test_request_context(json=music_match_data):
            request.json = music_match_data
            music_response = analyze_music_match()
            music_result = music_response.get_json()
        
        if music_result.get('status') != 'success':
            return jsonify({
                'status': 'error',
                'message': 'Could not find suitable music match',
                'music_analysis': music_result
            }), 400
        
        # Step 2: Process video with found music
        music_rec = music_result['music_recommendation']
        music_path = music_rec['file_path']
        
        process_data = {
            'video_path': video_path,
            'music_path': music_path,
            'text_lines': text_lines,
            'music_volume_db': music_volume_db
        }
        
        # Simulate internal call to video processing
        with app.test_request_context(json=process_data):
            request.json = process_data
            process_response = process_video_with_music_and_text()
            process_result = process_response.get_json()
        
        if process_result.get('status') != 'success':
            return jsonify({
                'status': 'error',
                'message': 'Video processing failed',
                'music_analysis': music_result,
                'processing_error': process_result
            }), 500
        
        # Return combined result
        return jsonify({
            'status': 'success',
            'message': 'Video analyzed and processed successfully',
            'music_analysis': music_result,
            'video_processing': process_result,
            'pipeline_summary': {
                'detected_mood': music_result.get('detected_mood'),
                'selected_music': music_rec.get('file_name'),
                'music_genre': music_rec.get('genre'),
                'output_file': process_result.get('output_path'),
                'processing_time': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in complete pipeline: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/video/batch-process', methods=['POST'])
def batch_process_videos():
    """
    Batch process multiple videos with automatic music matching
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        video_directory = data.get('video_directory')
        music_volume_db = data.get('music_volume_db', -25.0)
        include_text = data.get('include_text', True)
        
        if not video_directory:
            return jsonify({'error': 'video_directory is required'}), 400
        
        video_dir = Path(video_directory)
        if not video_dir.exists():
            return jsonify({'error': f'Directory not found: {video_directory}'}), 404
        
        # Find video files
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
        video_files = []
        for ext in video_extensions:
            video_files.extend(video_dir.glob(f"*{ext}"))
        
        if not video_files:
            return jsonify({'error': 'No video files found in directory'}), 404
        
        logger.info(f"Starting batch processing of {len(video_files)} videos")
        
        results = {
            'processed': 0,
            'failed': 0,
            'results': []
        }
        
        for video_file in video_files:
            try:
                logger.info(f"Processing: {video_file.name}")
                
                # Generate basic text if requested
                text_lines = []
                if include_text:
                    text_lines = [f"Video: {video_file.stem}"]
                
                # Process with complete pipeline
                pipeline_data = {
                    'video_path': str(video_file),
                    'transcript': '',
                    'visual_analysis': '',
                    'text_lines': text_lines,
                    'music_volume_db': music_volume_db
                }
                
                with app.test_request_context(json=pipeline_data):
                    request.json = pipeline_data
                    response = analyze_and_process_video()
                    result = response.get_json()
                
                if result.get('status') == 'success':
                    results['processed'] += 1
                    results['results'].append({
                        'video_file': str(video_file),
                        'status': 'success',
                        'output_path': result['video_processing']['output_path'],
                        'music_used': result['pipeline_summary']['selected_music']
                    })
                else:
                    results['failed'] += 1
                    results['results'].append({
                        'video_file': str(video_file),
                        'status': 'failed',
                        'error': result.get('message', 'Unknown error')
                    })
                
            except Exception as e:
                logger.error(f"Error processing {video_file.name}: {e}")
                results['failed'] += 1
                results['results'].append({
                    'video_file': str(video_file),
                    'status': 'failed',
                    'error': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'message': f'Batch processing complete: {results["processed"]} successful, {results["failed"]} failed',
            'summary': results
        })
        
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# SYSTEM STATUS & UTILITY ENDPOINTS
# ============================================================================

@app.route('/system/status', methods=['GET'])
def system_status():
    """Get comprehensive system status"""
    try:
        # Basic system status
        status = api.music_system.get_system_status()
        
        # Add database info
        db_stats = api.music_preprocessor.get_database_stats()
        
        # Add video processor status
        video_status = {
            'ffmpeg_available': api.video_processor.ffmpeg_path is not None,
            'ffmpeg_path': api.video_processor.ffmpeg_path,
            'temp_dir': str(api.video_processor.temp_dir)
        }
        
        # Check SoundCloud download status
        soundcloud_files = list(SOUNDCLOUD_DIR.glob("*.mp3")) + list(SOUNDCLOUD_DIR.glob("*.m4a"))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'music_system': status,
            'music_database': db_stats,
            'video_processor': video_status,
            'soundcloud_library': {
                'total_files': len(soundcloud_files),
                'directory': str(SOUNDCLOUD_DIR)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/file/<path:file_path>')
def download_file(file_path):
    """Download processed video file"""
    try:
        full_path = Path(file_path)
        if not full_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(str(full_path), as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Enhanced Music & Video Processing API...")
    
    # Get system status on startup
    try:
        with app.test_client() as client:
            response = client.get('/system/status')
            if response.status_code == 200:
                status = response.get_json()
                logger.info("System ready!")
                logger.info(f"  Music tracks: {status.get('music_database', {}).get('total_tracks', 0)}")
                logger.info(f"  FFmpeg: {'Available' if status.get('video_processor', {}).get('ffmpeg_available') else 'Not Available'}")
            else:
                logger.warning("Could not get initial system status")
    except Exception as e:
        logger.warning(f"Error getting startup status: {e}")
    
    # Start the server
    logger.info("🚀 Enhanced API ready on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
