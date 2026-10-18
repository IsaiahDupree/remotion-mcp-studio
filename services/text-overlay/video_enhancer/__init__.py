"""
Video Enhancer Module
====================

A modular system for enhancing videos with text overlays and background music.
This module provides components for:
1. Adding text overlays with customizable styles and positions
2. Adding background music with speech emphasis
3. Auto-detecting existing background music to avoid redundant processing
4. Analyzing video content for optimal enhancements

The module integrates with existing utilities for SoundCloud downloads and OpenAI analysis.
"""

from .text_overlay import TextOverlayEnhancer
from .music_enhancer import MusicEnhancer
from .enhancer import VideoEnhancer

__all__ = ['TextOverlayEnhancer', 'MusicEnhancer', 'VideoEnhancer']
