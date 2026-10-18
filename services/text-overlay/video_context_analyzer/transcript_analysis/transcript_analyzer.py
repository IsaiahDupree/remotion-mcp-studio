"""
Transcript Analyzer

Analyzes video transcripts to extract meaning, generate summaries, and create
engaging text overlays optimized for social media impact.
"""

import os
import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('transcript_analyzer')

class TranscriptAnalyzer:
    """
    Analyzes transcripts to extract key insights and generate engaging text overlays.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = 'gpt-4-turbo',
        temperature: float = 0.7,
        max_words: int = 6
    ):
        """
        Initialize the Transcript Analyzer.
        
        Args:
            api_key: OpenAI API key (defaults to env variable)
            model: GPT model to use
            temperature: Temperature for text generation
            max_words: Maximum words for catchy text
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Will use basic analysis only.")
            
        self.model = model
        self.temperature = temperature
        self.max_words = max_words
    
    def extract_key_points(self, transcript: str) -> List[str]:
        """
        Extract key points from a transcript using simple heuristics.
        
        Args:
            transcript: Full transcript text
            
        Returns:
            List of key points
        """
        if not transcript:
            return []
            
        # Split into sentences
        sentences = re.split(r'[.!?]', transcript)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Simple heuristic: key sentences often have important keywords
        key_indicators = [
            'important', 'key', 'main', 'significant', 'critical',
            'essential', 'crucial', 'vital', 'primary', 'core',
            'fundamental', 'best', 'top', 'ultimate', 'greatest',
            'must', 'should', 'need to', 'have to', 'amazing',
            'incredible', 'impressive', 'fantastic', 'excellent'
        ]
        
        # Score sentences based on keyword presence
        scored_sentences = []
        for sentence in sentences:
            score = sum(1 for indicator in key_indicators if indicator.lower() in sentence.lower())
            # Score shorter sentences higher
            length_factor = 1.0 if len(sentence.split()) < 20 else 0.5
            scored_sentences.append((sentence, score * length_factor))
        
        # Sort by score and take top 3
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        key_points = [s[0] for s in scored_sentences[:3]]
        
        return key_points
    
    def generate_catchy_text_with_ai(
        self, 
        transcript: str, 
        video_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate catchy text overlay using OpenAI API.
        
        Args:
            transcript: Video transcript
            video_context: Additional video context information
            
        Returns:
            Dictionary with generated text and analysis
        """
        if not self.api_key or not transcript:
            return {"error": "API key not provided or transcript empty"}
        
        try:
            # Prepare context information
            context_str = ""
            if video_context:
                context_parts = []
                if "has_background_music" in video_context:
                    context_parts.append(f"The video {'has' if video_context['has_background_music'] else 'does not have'} background music.")
                if "frame_analysis" in video_context:
                    frame_desc = video_context.get("frame_analysis", {}).get("full_analysis", "")
                    if frame_desc:
                        context_parts.append(f"Visual content: {frame_desc[:300]}...")
                context_str = " ".join(context_parts)
            
            # Create the prompt
            messages = [
                {
                    "role": "system", 
                    "content": f"You are an expert in creating viral social media content. Create a compelling, catchy text overlay for a video based on its transcript. The text should be attention-grabbing, concise (maximum {self.max_words} words), and make viewers want to watch the entire video. The text should be formatted exactly like a social media overlay - no quotes or formatting, just the exact text to display."
                },
                {
                    "role": "user",
                    "content": f"Create a catchy text overlay (maximum {self.max_words} words) for this video transcript:\n\n{transcript[:1000]}\n\n{context_str}"
                }
            ]
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": 50
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code}, {response.text}")
                return {"error": f"API error: {response.status_code}"}
            
            result = response.json()
            
            # Extract the generated text
            generated_text = result['choices'][0]['message']['content'].strip()
            
            # Clean up the text (remove quotes, extra spaces, etc.)
            generated_text = generated_text.strip('"\'').strip()
            
            # Validate word count
            words = generated_text.split()
            if len(words) > self.max_words:
                # Truncate to max words
                generated_text = " ".join(words[:self.max_words])
            
            return {
                "catchy_text": generated_text,
                "word_count": len(generated_text.split()),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating catchy text: {e}")
            return {"error": str(e)}
    
    def generate_fallback_text(self, transcript: str) -> str:
        """
        Generate fallback catchy text without AI.
        
        Args:
            transcript: Video transcript
            
        Returns:
            Generated catchy text
        """
        if not transcript:
            return "Must see this amazing content"
            
        # Extract key points
        key_points = self.extract_key_points(transcript)
        
        if not key_points:
            return "Epic content you can't miss"
        
        # Get shortest key point
        key_point = min(key_points, key=len)
        words = key_point.split()
        
        if len(words) <= self.max_words:
            return key_point
        
        # Find important words in the first point
        important_words = []
        for word in words:
            if len(word) > 4 or word.lower() in ["best", "top", "must", "how", "why"]:
                important_words.append(word)
        
        # Create catchy text from important words
        if len(important_words) > 0:
            catchy_words = important_words[:min(len(important_words), self.max_words)]
            return " ".join(catchy_words)
            
        # Fallback to first words
        return " ".join(words[:self.max_words])
    
    def analyze_transcript(
        self, 
        transcript: str, 
        video_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete transcript analysis pipeline.
        
        Args:
            transcript: Video transcript
            video_context: Additional video context
            
        Returns:
            Analysis results including catchy text
        """
        try:
            # Extract key points using basic NLP
            key_points = self.extract_key_points(transcript)
            
            # Generate catchy text with AI if available
            catchy_text = ""
            if self.api_key:
                ai_result = self.generate_catchy_text_with_ai(transcript, video_context)
                if "catchy_text" in ai_result and not ai_result.get("error"):
                    catchy_text = ai_result["catchy_text"]
            
            # Fallback to basic generation if AI failed or not available
            if not catchy_text:
                catchy_text = self.generate_fallback_text(transcript)
            
            return {
                "transcript_length": len(transcript),
                "key_points": key_points,
                "catchy_text": catchy_text,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in transcript analysis: {e}")
            return {
                "error": str(e),
                "catchy_text": "Must see this amazing content"
            }
