#!/usr/bin/env python3
"""
pytest configuration and shared fixtures for the test suite
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def test_environment():
    """Set up test environment variables"""
    test_env = {
        'OPENAI_API_KEY': 'test-key-for-testing-only',
        'FLASK_ENV': 'testing',
        'TESTING': 'true'
    }
    
    with patch.dict(os.environ, test_env):
        yield test_env

@pytest.fixture(scope="session")
def temp_project_dir():
    """Create a temporary project directory for testing"""
    temp_dir = tempfile.mkdtemp(prefix='video_enhancer_test_')
    
    # Create directory structure
    directories = [
        'shared_data',
        'enhanced_videos', 
        'logs',
        'temp'
    ]
    
    for dir_name in directories:
        os.makedirs(os.path.join(temp_dir, dir_name), exist_ok=True)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def mock_openai_api():
    """Mock OpenAI API responses"""
    class MockOpenAIResponse:
        def __init__(self, content):
            self.content = content
    
    class MockChoice:
        def __init__(self, content):
            self.message = MockOpenAIResponse(content)
    
    class MockCompletion:
        def __init__(self, content):
            self.choices = [MockChoice(content)]
    
    def mock_create(**kwargs):
        # Return a mock response based on the type of request
        if 'model' in kwargs and 'gpt' in kwargs['model']:
            return MockCompletion("This is a test AI-generated text overlay")
        return MockCompletion("Mock response")
    
    with patch('openai.ChatCompletion.create', side_effect=mock_create):
        yield mock_create

@pytest.fixture
def mock_whisper():
    """Mock Whisper transcription"""
    class MockWhisperModel:
        def transcribe(self, audio_path):
            return {
                'text': 'This is a mock transcription of the audio content.',
                'segments': [
                    {'start': 0.0, 'end': 5.0, 'text': 'This is a mock'},
                    {'start': 5.0, 'end': 10.0, 'text': 'transcription of the'},
                    {'start': 10.0, 'end': 15.0, 'text': 'audio content.'}
                ]
            }
    
    def mock_load_model(model_name):
        return MockWhisperModel()
    
    with patch('whisper.load_model', side_effect=mock_load_model):
        yield mock_load_model

@pytest.fixture  
def mock_moviepy():
    """Mock MoviePy video processing"""
    from unittest.mock import Mock
    
    class MockVideoClip:
        def __init__(self, filename=None):
            self.filename = filename
            self.duration = 30.0
            self.fps = 30
            self.size = (1920, 1080)
            self.audio = Mock()
            self.audio.duration = 30.0
            
        def write_videofile(self, output_path, **kwargs):
            # Create a fake output file
            Path(output_path).touch()
            return output_path
            
        def resize(self, size):
            self.size = size
            return self
            
        def set_duration(self, duration):
            self.duration = duration
            return self
            
        def subclip(self, start, end):
            new_clip = MockVideoClip()
            new_clip.duration = end - start
            return new_clip
    
    class MockTextClip:
        def __init__(self, txt, **kwargs):
            self.txt = txt
            self.duration = 30.0
            
        def set_position(self, position):
            return self
            
        def set_duration(self, duration):
            self.duration = duration
            return self
            
        def set_start(self, start):
            return self
    
    class MockCompositeVideoClip:
        def __init__(self, clips):
            self.clips = clips
            self.duration = max(clip.duration for clip in clips if hasattr(clip, 'duration'))
            
        def write_videofile(self, output_path, **kwargs):
            Path(output_path).touch()
            return output_path
    
    mock_modules = {
        'moviepy.editor.VideoFileClip': MockVideoClip,
        'moviepy.editor.TextClip': MockTextClip, 
        'moviepy.editor.CompositeVideoClip': MockCompositeVideoClip
    }
    
    patches = []
    for module_path, mock_class in mock_modules.items():
        patches.append(patch(module_path, mock_class))
    
    # Start all patches
    for p in patches:
        p.start()
    
    yield mock_modules
    
    # Stop all patches
    for p in patches:
        p.stop()

@pytest.fixture
def sample_video_file(temp_project_dir):
    """Create a sample video file for testing"""
    video_path = os.path.join(temp_project_dir, 'shared_data', 'test_video.mp4')
    
    # Create a fake video file with some content
    with open(video_path, 'wb') as f:
        f.write(b'FAKE_VIDEO_CONTENT_FOR_TESTING')
    
    yield video_path
    
    # Cleanup is handled by temp_project_dir fixture

@pytest.fixture  
def sample_soundcloud_excel(temp_project_dir):
    """Create a sample SoundCloud Excel file for testing"""
    import pandas as pd
    
    excel_path = os.path.join(temp_project_dir, 'soundcloud_tracks.xlsx')
    
    # Create sample data
    data = [
        {
            'URL': 'https://soundcloud.com/test/track1',
            'Title': 'Test Track 1',
            'Artist': 'Test Artist 1',
            'Duration': '3:30',
            'Genre': 'Electronic',
            'BPM': '128',
            'Mood': 'Energetic'
        },
        {
            'URL': 'https://soundcloud.com/test/track2', 
            'Title': 'Test Track 2',
            'Artist': 'Test Artist 2',
            'Duration': '4:15',
            'Genre': 'Ambient',
            'BPM': '90', 
            'Mood': 'Relaxed'
        }
    ]
    
    df = pd.DataFrame(data)
    df.to_excel(excel_path, index=False)
    
    yield excel_path

# Test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )

# Pytest collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Add slow marker to tests that might take a long time
        if "video_processing" in item.nodeid or "enhance_video" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        
        # Add integration marker to tests that test multiple components
        if "integration" in item.nodeid or "workflow" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add API marker to Flask API tests
        if "test_flask_api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        
        # Add unit marker to isolated tests
        if not any(marker.name in ['slow', 'integration'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
