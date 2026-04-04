"""
Video Context Analyzer

A modular package for analyzing video content through multiple channels:
- Frame analysis for visual content understanding
- Audio analysis for sound and music detection
- Transcript analysis for speech content understanding
- Text styling for optimized video overlays
"""

from video_context_analyzer.frame_analysis import FrameAnalyzer
from video_context_analyzer.audio_analysis import AudioAnalyzer
from video_context_analyzer.transcript_analysis import TranscriptAnalyzer
from video_context_analyzer.styling import TextStyler

__all__ = ['FrameAnalyzer', 'AudioAnalyzer', 'TranscriptAnalyzer', 'TextStyler']
