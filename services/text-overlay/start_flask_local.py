#!/usr/bin/env python3
"""
Local development startup script for Flask Video Enhancement API

This script sets up the environment and starts the Flask API for local development and testing.
"""

import os
import sys
import subprocess
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_environment():
    """Set up environment variables for local development"""
    
    # Get current directory
    current_dir = Path(__file__).parent.absolute()
    
    # Set up environment variables
    env_vars = {
        'SHARED_VIDEOS_DIR': str(current_dir / 'shared_data'),
        'OUTPUT_DIR': str(current_dir / 'enhanced_videos'),
        'SOUNDCLOUD_EXCEL_PATH': str(current_dir / 'soundcloud_tracks.xlsx'),
        'CSV_LOG_PATH': str(current_dir / 'processing_log.csv'),
        'FLASK_APP': 'flask_app.py',
        'FLASK_ENV': 'development',
        'PYTHONPATH': str(current_dir)
    }
    
    # Load OpenAI API key from .env file if it exists
    env_file = current_dir / '.env'
    if env_file.exists():
        logger.info(f"Loading environment from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    else:
        logger.warning(".env file not found. Please create one with OPENAI_API_KEY=your_key_here")
    
    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value
        logger.info(f"Set {key} = {value}")
    
    return env_vars

def create_directories(env_vars):
    """Create necessary directories"""
    directories = [
        env_vars['SHARED_VIDEOS_DIR'],
        env_vars['OUTPUT_DIR'],
        Path(env_vars['CSV_LOG_PATH']).parent
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'flask',
        'pandas',
        'opencv-python',
        'moviepy',
        'openai',
        'yt-dlp',
        'librosa',
        'soundfile'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"❌ {package} is missing")
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.error("Please install missing packages with: pip install -r requirements.txt")
        return False
    
    return True

def check_external_tools():
    """Check if external tools are available"""
    tools = ['ffmpeg', 'ffprobe']
    
    for tool in tools:
        try:
            result = subprocess.run([tool, '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode == 0:
                logger.info(f"✅ {tool} is available")
            else:
                logger.warning(f"⚠️  {tool} may not be working correctly")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.error(f"❌ {tool} is not found in PATH")
            logger.error(f"Please install {tool} and ensure it's in your PATH")

def start_flask_app():
    """Start the Flask application"""
    logger.info("Starting Flask Video Enhancement API...")
    logger.info("The API will be available at: http://localhost:5000")
    logger.info("Health check: http://localhost:5000/health")
    logger.info("Press Ctrl+C to stop the server")
    
    try:
        # Import and run the Flask app
        from flask_app import app
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Flask app stopped by user")
    except Exception as e:
        logger.error(f"Error starting Flask app: {str(e)}")
        return False
    
    return True

def main():
    """Main startup function"""
    logger.info("=== Flask Video Enhancement API - Local Development Setup ===")
    
    try:
        # Setup environment
        logger.info("Setting up environment...")
        env_vars = setup_environment()
        
        # Create directories
        logger.info("Creating directories...")
        create_directories(env_vars)
        
        # Check dependencies
        logger.info("Checking Python dependencies...")
        if not check_dependencies():
            logger.error("Please install missing dependencies and try again")
            return False
        
        # Check external tools
        logger.info("Checking external tools...")
        check_external_tools()
        
        # Create sample files if they don't exist
        soundcloud_file = Path(env_vars['SOUNDCLOUD_EXCEL_PATH'])
        if not soundcloud_file.exists():
            logger.info("Creating sample SoundCloud tracks file...")
            try:
                subprocess.run([sys.executable, 'create_soundcloud_sample.py'], 
                             check=True, cwd=Path(__file__).parent)
                logger.info("Sample SoundCloud tracks file created")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Could not create sample SoundCloud file: {e}")
        
        # Start Flask app
        logger.info("All checks passed! Starting Flask application...")
        print("\n" + "="*60)
        print("🚀 FLASK API STARTING")
        print("="*60)
        print(f"📁 Videos directory: {env_vars['SHARED_VIDEOS_DIR']}")
        print(f"📁 Output directory: {env_vars['OUTPUT_DIR']}")
        print(f"📊 SoundCloud tracks: {env_vars['SOUNDCLOUD_EXCEL_PATH']}")
        print(f"📝 CSV logs: {env_vars['CSV_LOG_PATH']}")
        print(f"🌐 API URL: http://localhost:5000")
        print("="*60 + "\n")
        
        return start_flask_app()
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        return False

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)
