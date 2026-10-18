"""
Video sanitization module for detecting and removing sensitive information from videos.

This module provides functionality to:
1. Detect text in video frames
2. Identify sensitive information (API keys, credentials, etc.)
3. Blur or redact detected sensitive information
4. Output sanitized videos
"""
import cv2
import numpy as np
import re
import os
from typing import List, Tuple, Dict, Optional, Union
import pytesseract
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('video_sanitizer')

# Common patterns for sensitive data
SENSITIVE_PATTERNS = {
    'api_key': r'(?i)api[-_]?key[=:]\s*["\'`]?([a-zA-Z0-9_\-]{20,})["\'`]?',
    'access_token': r'(?i)access[-_]?token[=:]\s*["\'`]?([a-zA-Z0-9_\-]{20,})["\'`]?',
    'secret_key': r'(?i)secret[-_]?key[=:]\s*["\'`]?([a-zA-Z0-9_\-]{20,})["\'`]?',
    'password': r'(?i)password[=:]\s*["\'`]?([a-zA-Z0-9_\-@!#$%^&*]{8,})["\'`]?',
    'credentials': r'(?i)credentials[=:]\s*["\'`]?([a-zA-Z0-9_\-]{8,})["\'`]?',
    # Add more patterns as needed
}

class VideoSanitizer:
    """Class for sanitizing videos to remove sensitive information."""
    
    def __init__(self, 
                 custom_patterns: Optional[Dict[str, str]] = None, 
                 blur_strength: int = 25,
                 detection_confidence: float = 0.6):
        """
        Initialize the VideoSanitizer.
        
        Args:
            custom_patterns: Additional regex patterns for sensitive data detection
            blur_strength: Strength of the blur applied to detected regions (odd number)
            detection_confidence: Minimum confidence threshold for text detection
        """
        self.patterns = SENSITIVE_PATTERNS.copy()
        if custom_patterns:
            self.patterns.update(custom_patterns)
            
        # Ensure blur_strength is odd (required by GaussianBlur)
        self.blur_strength = blur_strength if blur_strength % 2 == 1 else blur_strength + 1
        self.detection_confidence = detection_confidence
        
        # Make sure pytesseract is available
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            logger.error(f"Tesseract not properly installed: {e}")
            logger.info("Please install Tesseract OCR and ensure it's in your PATH")
    
    def detect_text_regions(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect regions containing text in a video frame.
        
        Args:
            frame: Image as numpy array (BGR format)
            
        Returns:
            List of bounding boxes as (x, y, width, height)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # This is a placeholder implementation.
        # For production use, consider using a more robust text detection method 
        # such as EAST text detector or a deep learning model.
        
        # Example with Tesseract OCR (basic approach)
        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
        
        boxes = []
        for i in range(len(data['text'])):
            # Filter by confidence level
            if float(data['conf'][i]) > self.detection_confidence and data['text'][i].strip():
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                boxes.append((x, y, w, h))
        
        return boxes
    
    def is_sensitive_text(self, text: str) -> Tuple[bool, Optional[str]]:
        """Check if text contains sensitive information and return the pattern name.
        
        Args:
            text: Text to check
            
        Returns:
            Tuple of (is_sensitive, pattern_name) where pattern_name is None if not sensitive
        """
        """
        Check if text contains sensitive information.
        
        Args:
            text: Text to check
            
        Returns:
            True if sensitive information is found, False otherwise
        """
        for pattern_name, pattern in self.patterns.items():
            match = re.search(pattern, text)
            if match:
                logger.info(f"Detected sensitive information matching pattern: {pattern_name}")
                return True, pattern_name
        return False, None
    
    def sanitize_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict[str, any]]]:
        """Sanitize a single frame by blurring detected sensitive information.
        
        Args:
            frame: Input frame as numpy array
            
        Returns:
            Tuple of (sanitized frame, list of detection info dictionaries)
        """
        """
        Sanitize a single frame by blurring detected sensitive information.
        
        Args:
            frame: Input frame as numpy array
            
        Returns:
            Sanitized frame
        """
        # Detect text regions
        text_regions = self.detect_text_regions(frame)
        
        # Clone the frame to avoid modifying the original
        output_frame = frame.copy()
        
        # Keep track of detections in this frame
        detections = []
        
        # Process each detected text region
        for x, y, w, h in text_regions:
            # Extract the region
            region = frame[y:y+h, x:x+w]
            
            # Get the text in the region
            text = pytesseract.image_to_string(region)
            
            # Check if text contains sensitive information
            is_sensitive, pattern_name = self.is_sensitive_text(text)
            if is_sensitive:
                # Record the detection
                detection = {
                    'text': text,
                    'pattern': pattern_name,
                    'region': (x, y, w, h)
                }
                detections.append(detection)
                
                # Apply Gaussian blur to the region
                blurred_region = cv2.GaussianBlur(
                    region, 
                    (self.blur_strength, self.blur_strength), 
                    0
                )
                # Replace the region with the blurred version
                output_frame[y:y+h, x:x+w] = blurred_region
        
        return output_frame, detections
    
    def sanitize_video(self, 
                      input_path: str, 
                      output_path: str, 
                      start_time: float = 0, 
                      end_time: Optional[float] = None,
                      frame_skip: int = 5,
                      report_only: bool = False) -> Union[bool, List[Dict[str, any]]]:
        """
        Sanitize a video file by detecting and blurring sensitive information.
        
        Args:
            input_path: Path to the input video
            output_path: Path where the sanitized video will be saved
            start_time: Start time in seconds for processing
            end_time: End time in seconds for processing (None for full video)
            frame_skip: Process every Nth frame for efficiency
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Open the video
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                logger.error(f"Could not open video: {input_path}")
                return False
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Calculate start and end frames
            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps) if end_time else total_frames
            
            # Set up video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # You might want to use a different codec
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Process the video
            frame_count = 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # Store detection results
            all_detections = []
            
            while cap.isOpened() and frame_count < end_frame - start_frame:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Calculate current timestamp
                timestamp = start_time + (frame_count / fps)
                
                # Only process every nth frame to improve speed
                if frame_count % frame_skip == 0:
                    sanitized_frame, detections = self.sanitize_frame(frame)
                    
                    # Add timestamp to each detection
                    for detection in detections:
                        detection['timestamp'] = timestamp
                        detection['frame_number'] = start_frame + frame_count
                        all_detections.append(detection)
                    
                    if not report_only:
                        out.write(sanitized_frame)
                elif not report_only:
                    # Skip processing but still write the frame
                    out.write(frame)
                
                frame_count += 1
                
                # Log progress
                if frame_count % 100 == 0:
                    logger.info(f"Processed {frame_count} frames out of {end_frame - start_frame}")
            
            # Clean up
            cap.release()
            if not report_only:
                out.release()
                logger.info(f"Video sanitization complete: {output_path}")
            
            if report_only:
                return all_detections
            else:
                return True
            
        except Exception as e:
            logger.error(f"Error sanitizing video: {str(e)}")
            return False

    def add_custom_pattern(self, name: str, pattern: str) -> None:
        """
        Add a custom pattern for sensitive data detection.
        
        Args:
            name: Name of the pattern
            pattern: Regex pattern string
        """
        self.patterns[name] = pattern
        logger.info(f"Added custom pattern: {name}")
