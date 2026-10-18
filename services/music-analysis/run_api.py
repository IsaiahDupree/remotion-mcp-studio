#!/usr/bin/env python3
"""
Production startup script for Enhanced Music Analysis API
"""
import logging
from flask_api import app, music_system

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("🚀 Starting Enhanced Music Analysis API (Production Mode)...")
    
    # Get system status on startup
    try:
        status = music_system.get_system_status()
        logger.info(f"System ready with {status['total_tracks']} tracks available")
    except Exception as e:
        logger.warning(f"Could not get initial system status: {e}")
    
    logger.info("🌐 API Server starting on http://localhost:5001")
    logger.info("🎯 Ready for n8n integration!")
    
    # Run Flask app in production mode
    app.run(host='0.0.0.0', port=5001, debug=False)
