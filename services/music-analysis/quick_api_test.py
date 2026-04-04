#!/usr/bin/env python3
"""
Quick API test script for the enhanced Flask API
Tests only the most critical endpoints with a real video
"""
import os
import sys
import time
import requests
import json

# Configuration
ENHANCED_API_BASE_URL = "http://localhost:5003"
VIDEOS_DIRECTORY = os.path.join(os.getcwd(), "shared", "videos")
# Choose a small video file to speed up testing
TEST_VIDEO_FILE = "089FB8C6-5DF9-4084-877E-344DFEC38B0D.mp4"  
TEST_VIDEO_PATH = os.path.join(VIDEOS_DIRECTORY, TEST_VIDEO_FILE)

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def test_api_health():
    """Test the API health endpoint"""
    url = f"{ENHANCED_API_BASE_URL}/health"
    print(f"Testing: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_complete_pipeline():
    """Test the complete analyze-and-process pipeline endpoint"""
    print_header("Testing Complete Pipeline Endpoint")
    
    if not os.path.exists(TEST_VIDEO_PATH):
        print(f"Error: Test video not found at {TEST_VIDEO_PATH}")
        return False
        
    url = f"{ENHANCED_API_BASE_URL}/video/analyze-and-process"
    print(f"Endpoint: {url}")
    print(f"Video: {TEST_VIDEO_FILE}")
    
    try:
        # Prepare the multipart form data
        files = {'video': open(TEST_VIDEO_PATH, 'rb')}
        data = {
            'text_position': 'smart',
            'add_background_music': 'true',
            'music_volume': '-25'
        }
        
        # Send the request and time it
        print("Sending request...")
        start_time = time.time()
        response = requests.post(url, files=files, data=data, timeout=300)  # 5 minute timeout
        elapsed_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Total Processing Time: {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print(f"AI-Generated Text: {result.get('suggested_text', 'N/A')}")
            print(f"Confidence Score: {result.get('confidence_score', 'N/A')}")
            print(f"Analysis Time: {result.get('analysis_time', 'N/A')} seconds")
            print(f"Processing Time: {result.get('processing_time', 'N/A')} seconds")
            print(f"Output File: {result.get('output_filename', 'N/A')}")
            
            output_filename = result.get('output_filename')
            if output_filename:
                file_url = f"{ENHANCED_API_BASE_URL}/download/{output_filename}"
                print(f"File Download URL: {file_url}")
            
            return True
        else:
            print(f"Error Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        if 'files' in locals() and 'video' in files and hasattr(files['video'], 'close'):
            files['video'].close()

if __name__ == "__main__":
    print_header("ENHANCED FLASK API QUICK TEST")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base URL: {ENHANCED_API_BASE_URL}")
    print(f"Test Video: {TEST_VIDEO_PATH}")
    
    # First check if the API is healthy
    if test_api_health():
        print("\n✅ API is healthy, proceeding with pipeline test...\n")
        # Test the complete pipeline
        success = test_complete_pipeline()
        if success:
            print("\n✅ Complete pipeline test PASSED!")
            sys.exit(0)
        else:
            print("\n❌ Complete pipeline test FAILED!")
            sys.exit(1)
    else:
        print("\n❌ API health check FAILED! Make sure the enhanced Flask API is running.")
        sys.exit(1)
