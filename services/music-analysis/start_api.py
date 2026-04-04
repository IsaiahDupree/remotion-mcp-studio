#!/usr/bin/env python3
"""
Startup script for the Enhanced Music Analysis API
"""
import os
import sys
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = [
        'flask', 'librosa', 'numpy', 'pandas', 
        'cv2', 'requests', 'mutagen'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        logger.error("Please install: pip install -r requirements.txt")
        return False
    
    return True

def check_system_setup():
    """Check system configuration and paths"""
    from config import PATHS, DATABASE_CONFIG
    
    # Check if directories exist
    for name, path in PATHS.items():
        if not path.exists() and name in ['cache', 'analysis', 'soundcloud_music']:
            logger.info(f"Creating directory: {path}")
            path.mkdir(parents=True, exist_ok=True)
    
    # Check for Excel file
    soundcloud_excel = PATHS['base'] / "WordsOnText" / "SoundCloud to X Reposter.xlsx"
    if soundcloud_excel.exists():
        logger.info(f"✅ SoundCloud Excel file found: {soundcloud_excel}")
    else:
        logger.warning(f"⚠️  SoundCloud Excel file not found: {soundcloud_excel}")
        logger.info("   You can still use the system with WordsOnText library only")
    
    # Check WordsOnText library
    wot_path = PATHS['wordsontext_music']
    if wot_path.exists():
        music_files = list(wot_path.rglob("*.mp3")) + list(wot_path.rglob("*.wav"))
        logger.info(f"✅ WordsOnText music library found: {len(music_files)} audio files")
    else:
        logger.warning(f"⚠️  WordsOnText music library not found: {wot_path}")
        logger.info("   The system will work but no music will be available initially")
    
    return True

def initialize_system():
    """Initialize the music system"""
    try:
        from main_system import MusicSystem
        logger.info("🎵 Initializing Music System...")
        
        system = MusicSystem()
        status = system.get_system_status()
        
        logger.info(f"📊 System Status:")
        logger.info(f"   WordsOnText tracks: {status['music_libraries']['wordsOnText']['tracks']}")
        logger.info(f"   SoundCloud tracks: {status['music_libraries']['soundcloud']['tracks']}")
        logger.info(f"   Total tracks: {status['total_tracks']}")
        
        # Update trends on startup
        logger.info("🔄 Updating trend data...")
        system.update_trends()
        
        return system
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize system: {e}")
        return None

def start_api():
    """Start the Flask API server"""
    logger.info("🚀 Starting Enhanced Music Analysis API...")
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check system setup
    if not check_system_setup():
        return
    
    # Initialize system
    system = initialize_system()
    if not system:
        return
    
    # Start Flask API
    try:
        from flask_api import app
        logger.info("🌐 API Server starting on http://localhost:5001")
        logger.info("🎯 Ready to receive music analysis requests!")
        logger.info("📝 Available endpoints:")
        logger.info("   GET  /health - Health check")
        logger.info("   POST /analyze-music-match - Main analysis endpoint")
        logger.info("   GET  /system-status - System status")
        logger.info("   POST /setup-soundcloud - Setup SoundCloud library")
        logger.info("   POST /analyze-music-libraries - Analyze existing libraries")
        logger.info("   POST /update-trends - Update trend data")
        
        app.run(host='0.0.0.0', port=5001, debug=False)
        
    except Exception as e:
        logger.error(f"❌ Failed to start API: {e}")

if __name__ == "__main__":
    start_api()
