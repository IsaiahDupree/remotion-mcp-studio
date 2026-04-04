#!/usr/bin/env python3
"""
Focused test script for video analysis with OpenAI integration
Uses the enhanced Flask API to test the OpenAI video analysis endpoint
"""
import os
import sys
import time
import json
import requests
from pathlib import Path

# Configuration
ENHANCED_API_BASE_URL = "http://localhost:5003"
VIDEOS_DIRECTORY = os.path.join(os.getcwd(), "shared", "videos")

def find_smallest_video(max_size_mb=10):
    """Find the smallest video file in the videos directory"""
    if not os.path.exists(VIDEOS_DIRECTORY):
        print(f"Error: Videos directory not found: {VIDEOS_DIRECTORY}")
        return None
    
    video_files = []
    for f in os.listdir(VIDEOS_DIRECTORY):
        file_path = os.path.join(VIDEOS_DIRECTORY, f)
        if f.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb < max_size_mb:  # Only include files smaller than max_size_mb
                video_files.append((file_path, size_mb))
    
    if not video_files:
        print(f"No video files found under {max_size_mb}MB in {VIDEOS_DIRECTORY}")
        return None
    
    # Sort by size and return the smallest
    video_files.sort(key=lambda x: x[1])
    return video_files[0]

def test_video_analysis():
    """Test the OpenAI video analysis endpoint"""
    print("\n======== TESTING OPENAI VIDEO ANALYSIS ========")
    
    # Find a small video file
    video_info = find_smallest_video(max_size_mb=5)  # Find videos under 5MB
    if not video_info:
        print("❌ No suitable video files found. Please add a small video file to the videos directory.")
        return False
    
    video_path, video_size = video_info
    video_name = os.path.basename(video_path)
    
    print(f"Testing with video: {video_name} ({video_size:.2f} MB)")
    
    # Test the analyze endpoint
    url = f"{ENHANCED_API_BASE_URL}/video/analyze-with-openai"
    print(f"API endpoint: {url}")
    
    try:
        print("Sending video for AI analysis...")
        start_time = time.time()
        
        # Open the file and send the request
        with open(video_path, 'rb') as video_file:
            files = {'video': (video_name, video_file, 'video/mp4')}
            response = requests.post(url, files=files, timeout=120)
        
        elapsed_time = time.time() - start_time
        print(f"Request completed in {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Analysis successful!")
            print(f"AI-generated overlay text: \"{result.get('suggested_text', 'N/A')}\"")
            print(f"Confidence score: {result.get('confidence_score', 'N/A')}")
            print(f"Processing time: {result.get('processing_time', 'N/A')} seconds")
            return True
        else:
            print(f"❌ Analysis failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_complete_pipeline():
    """Test the complete video analysis and processing pipeline"""
    print("\n======== TESTING COMPLETE PIPELINE ========")
    
    # Find a small video file
    video_info = find_smallest_video(max_size_mb=5)  # Find videos under 5MB
    if not video_info:
        print("❌ No suitable video files found. Please add a small video file to the videos directory.")
        return False
    
    video_path, video_size = video_info
    video_name = os.path.basename(video_path)
    
    print(f"Testing with video: {video_name} ({video_size:.2f} MB)")
    
    # Test the complete pipeline endpoint
    url = f"{ENHANCED_API_BASE_URL}/video/analyze-and-process"
    print(f"API endpoint: {url}")
    
    try:
        print("Sending video for complete AI analysis and processing...")
        start_time = time.time()
        
        # Open the file and send the request
        with open(video_path, 'rb') as video_file:
            files = {'video': (video_name, video_file, 'video/mp4')}
            data = {
                'text_position': 'smart',
                'add_background_music': 'true',
                'music_volume': '-25'
            }
            response = requests.post(url, files=files, data=data, timeout=300)  # 5-min timeout
        
        elapsed_time = time.time() - start_time
        print(f"Request completed in {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Complete pipeline successful!")
            print(f"AI-generated overlay text: \"{result.get('suggested_text', 'N/A')}\"")
            print(f"Output filename: {result.get('output_filename', 'N/A')}")
            print(f"Total processing time: {elapsed_time:.2f} seconds")
            
            # Check if output file is available for download
            output_file = result.get('output_filename')
            if output_file:
                download_url = f"{ENHANCED_API_BASE_URL}/download/{output_file}"
                print(f"Video available at: {download_url}")
            
            return True
        else:
            print(f"❌ Pipeline processing failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n======== ENHANCED FLASK API TESTING ========")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API URL: {ENHANCED_API_BASE_URL}")
    print(f"Videos directory: {VIDEOS_DIRECTORY}")
    
    # Test API health
    try:
        health_response = requests.get(f"{ENHANCED_API_BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"\n✅ API is healthy (version {health_data.get('version', 'unknown')})")
            print(f"OpenAI API configured: {health_data.get('openai_configured', False)}")
        else:
            print(f"\n❌ API health check failed with status: {health_response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error connecting to API: {str(e)}")
        sys.exit(1)
    
    # Run the tests
    analysis_success = test_video_analysis()
    
    if analysis_success:
        print("\nProceed with complete pipeline test? (This may take several minutes)")
        complete_success = test_complete_pipeline()
    else:
        print("\nSkipping complete pipeline test due to analysis failure.")
        complete_success = False
    
    # Print final results
    print("\n======== TEST RESULTS ========")
    print(f"OpenAI Video Analysis: {'✅ PASSED' if analysis_success else '❌ FAILED'}")
    print(f"Complete Pipeline: {'✅ PASSED' if complete_success else '❌ FAILED or SKIPPED'}")
    
    # Provide next steps
    print("\n======== NEXT STEPS ========")
    if analysis_success and complete_success:
        print("✅ The enhanced Flask API is fully operational!")
        print("\nNext steps:")
        print("1. Import the workflow into n8n at http://localhost:5679")
        print("2. Configure the workflow to use the enhanced API endpoints")
        print("3. Test the end-to-end workflow with a real video file")
    else:
        print("⚠️ Some tests failed. Consider the following:")
        print("1. Check Docker logs for any errors: docker logs music_system-enhanced-flask-api-1")
        print("2. Verify OpenAI API key is correctly configured")
        print("3. Make sure FFmpeg is installed and working in the container")
        print("4. Try testing with a different video file")
