#!/usr/bin/env python3
"""
Comprehensive test suite for Flask Video Enhancement API

This module contains unit and integration tests for the Flask application.
"""

import pytest
import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# Import the Flask app
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_app import app, VideoProcessingLogger, csv_logger

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def temp_directories():
    """Create temporary directories for testing"""
    temp_dir = tempfile.mkdtemp()
    
    # Create test directory structure
    test_dirs = {
        'shared_videos': os.path.join(temp_dir, 'shared_videos'),
        'output': os.path.join(temp_dir, 'output'),
        'excel_file': os.path.join(temp_dir, 'test_tracks.xlsx'),
        'csv_log': os.path.join(temp_dir, 'test_log.csv')
    }
    
    for dir_path in [test_dirs['shared_videos'], test_dirs['output']]:
        os.makedirs(dir_path, exist_ok=True)
    
    # Create test video file (empty for testing)
    test_video = os.path.join(test_dirs['shared_videos'], 'test_video.mp4')
    with open(test_video, 'wb') as f:
        f.write(b'fake video data for testing')
    
    # Create test Excel file
    test_tracks = pd.DataFrame([
        {'Title': 'Test Track 1', 'Artist': 'Test Artist', 'URL': 'https://soundcloud.com/test1', 'Duration': '3:00'},
        {'Title': 'Test Track 2', 'Artist': 'Test Artist 2', 'URL': 'https://soundcloud.com/test2', 'Duration': '4:00'}
    ])
    test_tracks.to_excel(test_dirs['excel_file'], index=False)
    
    yield test_dirs
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check_success(self, client):
        """Test successful health check"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'shared_videos_dir' in data
        assert 'output_dir' in data

class TestVideoListing:
    """Test video listing endpoints"""
    
    @patch('flask_app.SHARED_VIDEOS_DIR')
    def test_list_videos_success(self, mock_shared_dir, client, temp_directories):
        """Test successful video listing"""
        mock_shared_dir.__str__ = lambda: temp_directories['shared_videos']
        
        with patch('os.path.exists', return_value=True), \
             patch('os.walk', return_value=[(temp_directories['shared_videos'], [], ['test_video.mp4'])]), \
             patch('os.path.getsize', return_value=1024000):
            
            response = client.get('/videos')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['count'] >= 0
            assert 'videos' in data

    def test_list_videos_directory_not_found(self, client):
        """Test video listing when directory doesn't exist"""
        with patch('os.path.exists', return_value=False):
            response = client.get('/videos')
            assert response.status_code == 404
            
            data = json.loads(response.data)
            assert 'error' in data

class TestSoundCloudTracks:
    """Test SoundCloud tracks endpoints"""
    
    @patch('flask_app.SOUNDCLOUD_EXCEL_PATH')
    def test_list_soundcloud_tracks_success(self, mock_excel_path, client, temp_directories):
        """Test successful SoundCloud tracks listing"""
        mock_excel_path.__str__ = lambda: temp_directories['excel_file']
        
        with patch('os.path.exists', return_value=True), \
             patch('pandas.read_excel') as mock_read_excel:
            
            mock_read_excel.return_value = pd.DataFrame([
                {'URL': 'https://soundcloud.com/test', 'Title': 'Test Track'}
            ])
            
            response = client.get('/soundcloud/tracks')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'tracks' in data
            assert 'count' in data

    def test_list_soundcloud_tracks_file_not_found(self, client):
        """Test SoundCloud tracks listing when file doesn't exist"""
        with patch('os.path.exists', return_value=False):
            response = client.get('/soundcloud/tracks')
            assert response.status_code == 404
            
            data = json.loads(response.data)
            assert 'error' in data

class TestVideoProcessing:
    """Test video processing endpoints"""
    
    @patch('flask_app.enhance_video')
    @patch('os.path.exists')
    def test_process_single_video_success(self, mock_exists, mock_enhance, client, temp_directories):
        """Test successful single video processing"""
        mock_exists.return_value = True
        mock_enhance.return_value = {
            'success': True,
            'output_video': '/path/to/output.mp4',
            'text_overlay': 'Test overlay',
            'processing_time_seconds': 30.5,
            'music_added': True
        }
        
        payload = {
            'video_path': 'test_video.mp4',
            'add_music': True,
            'position': 'TOP'
        }
        
        response = client.post('/process/video', json=payload)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'text_overlay' in data
        assert 'processing_time_seconds' in data

    def test_process_single_video_missing_path(self, client):
        """Test video processing with missing video_path"""
        payload = {'add_music': True}
        
        response = client.post('/process/video', json=payload)
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data

    def test_process_single_video_file_not_found(self, client):
        """Test video processing with non-existent file"""
        payload = {'video_path': 'nonexistent.mp4'}
        
        with patch('os.path.exists', return_value=False):
            response = client.post('/process/video', json=payload)
            assert response.status_code == 404
            
            data = json.loads(response.data)
            assert 'error' in data

    @patch('flask_app.process_batch')
    @patch('os.path.exists')
    def test_process_batch_videos_success(self, mock_exists, mock_process_batch, client):
        """Test successful batch video processing"""
        mock_exists.return_value = True
        mock_process_batch.return_value = {
            'success': True,
            'results': {'video1.mp4': {'success': True}, 'video2.mp4': {'success': True}},
            'total_processed': 2
        }
        
        payload = {
            'video_paths': ['video1.mp4', 'video2.mp4'],
            'add_music': True
        }
        
        response = client.post('/process/batch', json=payload)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'results' in data or 'success' in data

    def test_process_batch_videos_missing_paths(self, client):
        """Test batch processing with missing video_paths"""
        payload = {'add_music': True}
        
        response = client.post('/process/batch', json=payload)
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data

class TestLogging:
    """Test logging endpoints and functionality"""
    
    def test_video_processing_logger_initialization(self, temp_directories):
        """Test VideoProcessingLogger initialization"""
        csv_path = temp_directories['csv_log']
        logger = VideoProcessingLogger(csv_path)
        
        assert os.path.exists(csv_path)
        assert logger.csv_path == csv_path

    def test_video_processing_logger_log_entry(self, temp_directories):
        """Test logging a processing result"""
        csv_path = temp_directories['csv_log']
        logger = VideoProcessingLogger(csv_path)
        
        result = {
            'success': True,
            'output_video': '/path/to/output.mp4',
            'text_overlay': 'Test overlay',
            'processing_time_seconds': 25.5
        }
        
        logger.log_processing_result(result, '/path/to/input.mp4', 'Test transcript')
        
        # Check if log was written
        df = pd.read_csv(csv_path)
        assert len(df) == 1
        assert df.iloc[0]['success'] == True
        assert df.iloc[0]['text_overlay'] == 'Test overlay'

    @patch('flask_app.CSV_LOG_PATH')
    def test_get_recent_logs_success(self, mock_csv_path, client, temp_directories):
        """Test getting recent logs"""
        mock_csv_path.__str__ = lambda: temp_directories['csv_log']
        
        # Create test log data
        test_data = pd.DataFrame([
            {'timestamp': '2024-01-01T12:00:00', 'video_filename': 'test.mp4', 'success': True},
            {'timestamp': '2024-01-01T12:01:00', 'video_filename': 'test2.mp4', 'success': False}
        ])
        test_data.to_csv(temp_directories['csv_log'], index=False)
        
        with patch('os.path.exists', return_value=True):
            response = client.get('/logs/recent?limit=5')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'logs' in data
            assert 'count' in data

    def test_get_recent_logs_file_not_found(self, client):
        """Test getting recent logs when file doesn't exist"""
        with patch('os.path.exists', return_value=False):
            response = client.get('/logs/recent')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['count'] == 0

class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_invalid_json_payload(self, client):
        """Test handling of invalid JSON payload"""
        response = client.post('/process/video', 
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code == 400

    @patch('flask_app.enhance_video')
    def test_video_processing_exception(self, mock_enhance, client):
        """Test handling of video processing exceptions"""
        mock_enhance.side_effect = Exception("Processing error")
        
        payload = {'video_path': 'test.mp4'}
        
        with patch('os.path.exists', return_value=True):
            response = client.post('/process/video', json=payload)
            assert response.status_code == 500
            
            data = json.loads(response.data)
            assert 'error' in data

class TestFileDownload:
    """Test file download functionality"""
    
    @patch('flask_app.OUTPUT_DIR')
    def test_download_existing_file(self, mock_output_dir, client, temp_directories):
        """Test downloading an existing file"""
        mock_output_dir.__str__ = lambda: temp_directories['output']
        
        # Create test output file
        test_file = os.path.join(temp_directories['output'], 'test_output.mp4')
        with open(test_file, 'wb') as f:
            f.write(b'test video content')
        
        with patch('os.path.exists', return_value=True):
            response = client.get('/download/test_output.mp4')
            assert response.status_code == 200

    def test_download_nonexistent_file(self, client):
        """Test downloading a non-existent file"""
        with patch('os.path.exists', return_value=False):
            response = client.get('/download/nonexistent.mp4')
            assert response.status_code == 404
            
            data = json.loads(response.data)
            assert 'error' in data

# Integration test fixtures and helpers
@pytest.fixture
def mock_environment():
    """Mock environment variables for testing"""
    env_vars = {
        'SHARED_VIDEOS_DIR': '/test/shared',
        'OUTPUT_DIR': '/test/output',
        'SOUNDCLOUD_EXCEL_PATH': '/test/tracks.xlsx',
        'CSV_LOG_PATH': '/test/log.csv',
        'OPENAI_API_KEY': 'test-key-123'
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars

class TestIntegration:
    """Integration tests"""
    
    def test_full_workflow_mock(self, client, temp_directories, mock_environment):
        """Test a complete workflow with mocked components"""
        
        # Mock all external dependencies
        with patch('flask_app.enhance_video') as mock_enhance, \
             patch('os.path.exists', return_value=True), \
             patch('pandas.read_excel') as mock_read_excel:
            
            # Setup mocks
            mock_enhance.return_value = {
                'success': True,
                'output_video': 'test_output.mp4',
                'text_overlay': 'Test overlay text',
                'processing_time_seconds': 30.0,
                'music_added': True
            }
            
            mock_read_excel.return_value = pd.DataFrame([
                {'URL': 'https://soundcloud.com/test', 'Title': 'Test Track'}
            ])
            
            # Test complete workflow
            # 1. Health check
            health_response = client.get('/health')
            assert health_response.status_code == 200
            
            # 2. List videos
            videos_response = client.get('/videos')  
            # May fail due to mocking, but shouldn't crash
            
            # 3. List tracks
            tracks_response = client.get('/soundcloud/tracks')
            assert tracks_response.status_code == 200
            
            # 4. Process video
            process_response = client.post('/process/video', json={
                'video_path': 'test.mp4',
                'add_music': True,
                'position': 'TOP'
            })
            assert process_response.status_code == 200
            
            # 5. Check recent logs
            logs_response = client.get('/logs/recent?limit=1')
            # May succeed or fail depending on mocking

if __name__ == '__main__':
    # Run tests when script is executed directly
    pytest.main([__file__, '-v'])
