#!/usr/bin/env python3
"""
Unit tests for the text generation functionality of the smart overlay tool.
"""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_overlay import generate_overlay_text


class TestTextGeneration(unittest.TestCase):
    """Test cases for text generation functionality."""

    @patch('smart_overlay.client')
    def test_generate_overlay_text(self, mock_client):
        """Test that overlay text is generated correctly."""
        # Mock the OpenAI API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated overlay text"
        mock_client.chat.completions.create.return_value = mock_response

        # Test inputs
        prompt = "Test prompt"
        transcript_context = "This is a test transcript"
        frame_captions = ["A person speaking", "Office setting"]

        # Call the function
        result = generate_overlay_text(prompt, transcript_context, frame_captions)

        # Verify the result
        self.assertEqual(result, "Generated overlay text")
        mock_client.chat.completions.create.assert_called_once()

    @patch('smart_overlay.client')
    def test_generate_overlay_text_long_response(self, mock_client):
        """Test that long overlay text is truncated correctly."""
        # Mock the OpenAI API response with a long text
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "X" * 100  # 100 character string
        mock_client.chat.completions.create.return_value = mock_response

        # Test inputs
        prompt = "Test prompt"
        transcript_context = "This is a test transcript"
        frame_captions = ["A person speaking", "Office setting"]

        # Call the function
        result = generate_overlay_text(prompt, transcript_context, frame_captions)

        # Verify the result is truncated to 90 characters (87 + "...")
        self.assertEqual(len(result), 90)
        self.assertTrue(result.endswith("..."))

    @patch('smart_overlay.client')
    def test_generate_overlay_text_error(self, mock_client):
        """Test error handling in text generation."""
        # Mock the OpenAI API to raise an exception
        mock_client.chat.completions.create.side_effect = Exception("API error")

        # Test inputs
        prompt = "Test prompt"
        transcript_context = "This is a test transcript"
        frame_captions = ["A person speaking", "Office setting"]

        # Call the function
        result = generate_overlay_text(prompt, transcript_context, frame_captions)

        # Verify the result falls back to the prompt
        self.assertEqual(result, prompt)


if __name__ == '__main__':
    unittest.main()
