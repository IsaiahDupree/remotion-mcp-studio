#!/usr/bin/env python3
"""
Simple Flask API to test Docker container startup
"""
import json
import logging
import os
from datetime import datetime
from flask import Flask, request, jsonify
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

@app.route('/', methods=['GET'])
def root():
    """Root endpoint to test if API is running"""
    return jsonify({
        "status": "running",
        "service": "Enhanced Video Processing API",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0"
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "video-generator"
    })

@app.route('/system/status', methods=['GET'])
def system_status():
    """Get system status"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "video_processor": {
            "ffmpeg_available": True,
            "ffmpeg_path": "ffmpeg"
        },
        "music_system": {
            "total_tracks": 197
        },
        "font_system": {
            "status": "ready",
            "fonts_available": True
        }
    })

@app.route('/fonts/list', methods=['GET'])
def list_fonts():
    """List available fonts"""
    return jsonify({
        "status": "success",
        "total_fonts": 10,
        "custom_fonts": 7,
        "system_fonts": 3,
        "fonts": [
            {
                "name": "Sunny Spells",
                "file": "SunnyspellsRegular-MV9ze.otf",
                "style": "creative",
                "available": True
            },
            {
                "name": "Mountain King",
                "file": "MountainKingRegular-woBYn.ttf", 
                "style": "bold",
                "available": True
            }
        ]
    })

@app.route('/music/search', methods=['POST'])
def search_music():
    """Search music database"""
    data = request.get_json()
    query = data.get('query', '')
    limit = data.get('limit', 10)
    
    return jsonify({
        "status": "success",
        "query": query,
        "tracks": [
            {
                "name": "04collective - Rusherz - Before You Go.mp3",
                "path": "/srv/soundcloud_music/04collective - Rusherz - Before You Go.mp3",
                "mood": "upbeat",
                "energy": 0.8
            }
        ],
        "total_results": 1
    })

if __name__ == '__main__':
    logger.info("Starting Simple Video Processing API...")
    app.run(host='0.0.0.0', port=5000, debug=False)
