#!/usr/bin/env python3
"""
Unit tests for the text placement algorithm of the smart overlay tool.
"""

import unittest
import sys
import os
import numpy as np
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_overlay import find_text_placement, detect_faces_and_objects, create_saliency_mask, create_safe_zones_mask


class TestPlacementAlgorithm(unittest.TestCase):
    """Test cases for text placement algorithm."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a simple test frame (640x360)
        self.test_frame = np.zeros((360, 640, 3), dtype=np.uint8)
        # Add a simulated face in the center
        self.test_frame[130:230, 270:370] = 200

    @patch('smart_overlay.detect_faces_and_objects')
    @patch('smart_overlay.create_saliency_mask')
    @patch('smart_overlay.create_safe_zones_mask')
    def test_find_text_placement_basic(self, mock_safe_zones, mock_saliency, mock_faces):
        """Test basic text placement functionality."""
        # Mock the mask creation functions
        mock_faces.return_value = np.ones((360, 640), dtype=np.float32)
        mock_saliency.return_value = np.ones((360, 640), dtype=np.float32)
        mock_safe_zones.return_value = np.ones((360, 640), dtype=np.float32)
        
        # Set the center area (where the face would be) to 0 in the face mask
        face_mask = np.ones((360, 640), dtype=np.float32)
        face_mask[130:230, 270:370] = 0
        mock_faces.return_value = face_mask

        # Call the function
        x, y = find_text_placement(self.test_frame, "Test text", 40)

        # Verify the text is not placed over the face
        self.assertTrue((x < 270 or x > 370) or (y < 130 or y > 230))

    @patch('smart_overlay.mp')
    @patch('smart_overlay.yolo_model')
    def test_detect_faces_and_objects(self, mock_yolo, mock_mp):
        """Test face and object detection."""
        # Mock the face detection
        mock_face_detection = MagicMock()
        mock_mp.solutions.face_detection.FaceDetection.return_value.__enter__.return_value = mock_face_detection
        
        # Mock detection results
        mock_results = MagicMock()
        mock_results.detections = []  # No faces detected
        mock_face_detection.process.return_value = mock_results
        
        # Mock YOLO detection
        mock_yolo_results = [MagicMock()]
        mock_yolo_results[0].boxes = []  # No objects detected
        mock_yolo.return_value = mock_yolo_results
        
        # Call the function
        result = detect_faces_and_objects(self.test_frame)
        
        # Verify the result is a mask of all ones (no areas to avoid)
        self.assertEqual(result.shape, (360, 640))
        self.assertTrue(np.all(result == 1))

    def test_create_saliency_mask(self):
        """Test saliency mask creation."""
        # This is a more complex test that would require mocking OpenCV's saliency module
        # For simplicity, we'll just test that the function returns a mask of the right shape
        with patch('cv2.saliency.StaticSaliencySpectralResidual_create') as mock_saliency:
            mock_saliency_instance = MagicMock()
            mock_saliency.return_value = mock_saliency_instance
            mock_saliency_instance.computeSaliency.return_value = (True, np.ones((360, 640), dtype=np.float32))
            
            result = create_saliency_mask(self.test_frame)
            
            self.assertEqual(result.shape, (360, 640))

    def test_create_safe_zones_mask(self):
        """Test safe zones mask creation."""
        # Mock the config
        with patch('smart_overlay.config') as mock_config:
            mock_config.video = {'safe_caption_height_pct': 15}
            
            result = create_safe_zones_mask(self.test_frame)
            
            # Verify the mask has the right shape
            self.assertEqual(result.shape, (360, 640))
            
            # Verify edges are masked (0)
            self.assertTrue(np.all(result[:32, :] == 0))  # Top margin
            self.assertTrue(np.all(result[-32:, :] == 0))  # Bottom margin
            self.assertTrue(np.all(result[:, :32] == 0))  # Left margin
            self.assertTrue(np.all(result[:, -32:] == 0))  # Right margin
            
            # Verify caption area is masked (bottom 15%)
            caption_height = int(360 * 0.15)
            self.assertTrue(np.all(result[-caption_height:, :] == 0))


if __name__ == '__main__':
    unittest.main()
