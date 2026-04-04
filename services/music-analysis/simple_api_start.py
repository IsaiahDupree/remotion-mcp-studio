#!/usr/bin/env python3
"""
Simple API Startup - Start Flask API with minimal dependencies
"""
import sys
import os
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    logger.info("🚀 Starting Simple Flask API...")
    
    # Import Flask and basic dependencies
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    
    # Create Flask app
    app = Flask(__name__)
    CORS(app)
    
    logger.info("✅ Flask app created")
    
    # Simple health check endpoint
    @app.route('/system/status', methods=['GET'])
    def system_status():
        """Simple system status"""
        return jsonify({
            'status': 'healthy',
            'message': 'Simple API is running',
            'endpoints': ['/system/status', '/video/process-simple']
        })
    
    # Simple video processing endpoint
    @app.route('/video/process-simple', methods=['POST'])
    def process_video_simple():
        """Simple video processing with text overlay only"""
        try:
            data = request.get_json()
            video_path = data.get('video_path')
            output_path = data.get('output_path', 'output.mp4')
            text_overlay = data.get('text_overlay', 'Test Text')
            
            if not video_path or not Path(video_path).exists():
                return jsonify({'error': 'Video file not found'}), 400
            
            # Import video processor only when needed
            logger.info("📽️ Loading video processor...")
            from video_processor import VideoProcessor
            
            processor = VideoProcessor()
            logger.info("✅ Video processor loaded")
            
            # Process video with text overlay
            logger.info(f"🎬 Processing video: {Path(video_path).name}")
            result = processor.add_text_overlay(
                video_path=video_path,
                output_path=output_path,
                text=text_overlay,
                position='bottom_center'
            )
            
            if result.get('success'):
                logger.info("✅ Video processing completed")
                return jsonify({
                    'success': True,
                    'output_path': result['output_path'],
                    'processing_time': result.get('processing_time', 0),
                    'message': 'Video processed successfully'
                })
            else:
                logger.error(f"❌ Video processing failed: {result.get('error')}")
                return jsonify({'error': result.get('error', 'Processing failed')}), 500
                
        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
            return jsonify({'error': str(e)}), 500
    
    logger.info("✅ Routes configured")
    
    if __name__ == '__main__':
        logger.info("🚀 Starting server on http://localhost:5001")
        app.run(host='0.0.0.0', port=5001, debug=True)
        
except Exception as e:
    logger.error(f"❌ Failed to start API: {e}")
    sys.exit(1)
