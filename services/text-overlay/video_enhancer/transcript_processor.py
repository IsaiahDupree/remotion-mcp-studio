"""
Transcript Processing Module
===========================

This module provides functionality for extracting and analyzing video transcripts.
It leverages OpenAI APIs for transcription and analysis.

Classes:
    TranscriptProcessor: Main class for transcript extraction and analysis
"""

import os
import sys
import logging
import tempfile
import subprocess
import json
import requests
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("transcript_processor")

class TranscriptProcessor:
    """
    Class for processing video transcripts.
    
    This class provides functionality to:
    1. Extract audio from videos
    2. Transcribe audio using OpenAI Whisper API
    3. Analyze transcripts for insights
    4. Generate concise text summaries
    
    Attributes:
        openai_api_key (str): OpenAI API key for transcription and analysis
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the TranscriptProcessor.
        
        Args:
            openai_api_key: OpenAI API key
        """
        # Set OpenAI API key if provided
        if openai_api_key:
            self.openai_api_key = openai_api_key
        elif "OPENAI_API_KEY" in os.environ:
            self.openai_api_key = os.environ["OPENAI_API_KEY"]
            logger.info("Using OpenAI API key from environment variable")
        else:
            self.openai_api_key = None
            logger.warning("No OpenAI API key provided. Transcription features will be limited.")
            
    def extract_audio(self, video_path: str) -> Optional[str]:
        """
        Extract audio from video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to extracted audio file or None if extraction failed
        """
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return None
            
        try:
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                audio_path = temp_file.name
                
            logger.info(f"Extracting audio from {video_path} to {audio_path}")
            
            # Use FFmpeg to extract audio
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-q:a", "0",  # High quality
                "-map", "a",  # Extract audio only
                "-y",  # Overwrite output file
                audio_path
            ]
            
            process = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            if process.returncode != 0:
                logger.error(f"Error extracting audio: {process.stderr.decode('utf-8')}")
                return None
                
            logger.info(f"Audio extracted successfully to {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            return None
    
    def transcribe_audio(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio using OpenAI's Whisper API.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with transcription results or None if transcription failed
        """
        if not self.openai_api_key:
            logger.error("OpenAI API key is required for transcription")
            return None
            
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return None
            
        try:
            logger.info(f"Transcribing audio file: {audio_path}")
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            # OpenAI requires specific file handling for audio uploads
            with open(audio_path, "rb") as audio_file:
                files = {
                    "file": (os.path.basename(audio_path), audio_file, "audio/mpeg"),
                    "model": (None, "whisper-1")
                }
                
                response = requests.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers=headers,
                    files=files
                )
                
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Transcription complete: {len(result.get('text', ''))} characters")
            return result
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return None
    
    def analyze_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        Analyze transcript content using OpenAI API.
        
        Args:
            transcript: Text transcript to analyze
            
        Returns:
            Dictionary with analysis results
        """
        if not self.openai_api_key:
            logger.error("OpenAI API key is required for transcript analysis")
            return {"error": "API key missing"}
            
        if not transcript or len(transcript) < 10:
            logger.warning("Transcript too short or empty for meaningful analysis")
            return {"error": "Transcript too short", "insights": [], "summary": ""}
            
        try:
            logger.info(f"Analyzing transcript ({len(transcript)} characters)")
            
            # Prepare API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are an expert video content analyzer. Extract key insights, themes and generate a concise, engaging summary for this video transcript."
                    },
                    {
                        "role": "user", 
                        "content": f"Analyze this video transcript and provide: 1) 3-5 key insights, 2) main themes, 3) a catchy 1-sentence summary suitable for a text overlay, and 4) emotional tone. Format as JSON. Transcript: {transcript}"
                    }
                ],
                "response_format": {"type": "json_object"}
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract the content from the response
            content = result["choices"][0]["message"]["content"]
            analysis = json.loads(content)
            
            logger.info(f"Transcript analysis complete")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing transcript: {str(e)}")
            return {"error": str(e), "insights": [], "summary": "Interesting conversation"}
    
    def generate_catchy_text(self, analysis: Dict[str, Any]) -> str:
        """
        Generate catchy text for video overlay from transcript analysis.
        
        Args:
            analysis: Transcript analysis results
            
        Returns:
            Catchy text suitable for video overlay
        """
        if "error" in analysis:
            return "Must-see video content"
            
        try:
            # Extract catchy text from analysis
            catchy_text = analysis.get("catchy_summary", "")
            if not catchy_text:
                themes = ", ".join(analysis.get("themes", [])[:2])
                insights = analysis.get("insights", [])
                
                if insights and len(insights) > 0:
                    catchy_text = insights[0]
                elif themes:
                    catchy_text = f"Exploring {themes}"
                else:
                    catchy_text = "Must-see video content"
                    
            return catchy_text
            
        except Exception as e:
            logger.error(f"Error generating catchy text: {str(e)}")
            return "Must-see video content"
    
    def process_video_transcript(self, video_path: str) -> Dict[str, Any]:
        """
        Process video to extract and analyze transcript.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with transcript, analysis, and suggested text overlay
        """
        result = {
            "success": False,
            "video_path": video_path,
            "transcript": "",
            "analysis": {},
            "suggested_text": "Must-see video content"
        }
        
        try:
            # Extract audio
            audio_path = self.extract_audio(video_path)
            if not audio_path:
                result["error"] = "Failed to extract audio"
                return result
                
            # Transcribe audio
            transcription = self.transcribe_audio(audio_path)
            if not transcription:
                result["error"] = "Failed to transcribe audio"
                return result
                
            # Clean up temporary audio file
            try:
                os.remove(audio_path)
                logger.debug(f"Deleted temporary audio file: {audio_path}")
            except Exception as e:
                logger.warning(f"Error cleaning up audio file: {str(e)}")
                
            # Get transcript text
            transcript = transcription.get("text", "")
            result["transcript"] = transcript
            
            if not transcript:
                result["error"] = "Empty transcript"
                return result
                
            # Analyze transcript
            analysis = self.analyze_transcript(transcript)
            result["analysis"] = analysis
            
            # Generate catchy text
            catchy_text = self.generate_catchy_text(analysis)
            result["suggested_text"] = catchy_text
            
            result["success"] = True
            return result
            
        except Exception as e:
            logger.error(f"Error processing video transcript: {str(e)}")
            result["error"] = str(e)
            return result

if __name__ == "__main__":
    # Simple test if module is run directly
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        processor = TranscriptProcessor()
        result = processor.process_video_transcript(video_path)
        
        if result["success"]:
            print(f"Transcript: {result['transcript'][:100]}...")
            print(f"Suggested text: {result['suggested_text']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    else:
        print("Usage: python transcript_processor.py <video_path>")
