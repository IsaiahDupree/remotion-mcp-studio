#!/usr/bin/env python3
"""
Startup script to run the enhanced Flask API reliably
with all necessary environment variables and settings
"""
import os
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OpenAI API key should be set via environment variable
# os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')

# Import and run the Flask app
try:
    logger.info("Loading enhanced Flask API...")
    from enhanced_flask_api import app
    
    logger.info("Starting enhanced Flask API on port 5001...")
    # Run the app with Waitress for production stability
    try:
        from waitress import serve
        logger.info("Using Waitress WSGI server")
        serve(app, host="0.0.0.0", port=5001)
    except ImportError:
        # Fall back to Flask's development server
        logger.info("Waitress not available, using Flask development server")
        app.run(host="0.0.0.0", port=5001)
        
except Exception as e:
    logger.error(f"Failed to start the enhanced Flask API: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
