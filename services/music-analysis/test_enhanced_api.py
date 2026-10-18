#!/usr/bin/env python3
"""
Script to test the enhanced Flask API capabilities
"""
import os
import sys
import time
import requests
from pathlib import Path
import json

# Configuration
ENHANCED_API_BASE_URL = "http://localhost:5003"
VIDEOS_DIRECTORY = os.path.join(os.getcwd(), "shared", "videos")
SAMPLE_VIDEO_PATH = os.path.join(VIDEOS_DIRECTORY, "089FB8C6-5DF9-4084-877E-344DFEC38B0D.mp4") # Default sample video

def print_section(title):
    """Print a formatted section title"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def test_health_check():
    """Test the health check endpoint"""
    print_section("Testing Health Check Endpoint")
    url = f"{ENHANCED_API_BASE_URL}/health"
    
    try:
        start_time = time.time()
        response = requests.get(url)
        elapsed = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {elapsed:.2f}s")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_api_root():
    """Test the API root endpoint"""
    print_section("Testing API Root Endpoint")
    url = f"{ENHANCED_API_BASE_URL}/"
    
    try:
        start_time = time.time()
        response = requests.get(url)
        elapsed = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {elapsed:.2f}s")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def verify_sample_video():
    """Verify that the sample video exists"""
    global SAMPLE_VIDEO_PATH
    print_section("Verifying Sample Video")
    
    if not os.path.exists(SAMPLE_VIDEO_PATH):
        print(f"Error: Sample video not found at {SAMPLE_VIDEO_PATH}")
        print("Checking for other videos in shared_videos directory...")
        
        shared_videos_dir = os.path.join(os.getcwd(), "shared_videos")
        
        if not os.path.exists(shared_videos_dir):
            print(f"Error: shared_videos directory not found at {shared_videos_dir}")
            return False
        
        video_files = [f for f in os.listdir(shared_videos_dir) 
                      if f.endswith(('.mp4', '.mov', '.avi', '.webm'))]
        
        if not video_files:
            print("No video files found in shared_videos directory.")
            return False
        
        SAMPLE_VIDEO_PATH = os.path.join(shared_videos_dir, video_files[0])
        print(f"Using alternative video: {SAMPLE_VIDEO_PATH}")
    else:
        print(f"Sample video found: {SAMPLE_VIDEO_PATH}")
    
    return True

def test_openai_video_analysis():
    """Test the OpenAI video analysis endpoint"""
    print_section("Testing OpenAI Video Analysis Endpoint")
    url = f"{ENHANCED_API_BASE_URL}/video/analyze-with-openai"
    
    if not verify_sample_video():
        return False
    
    try:
        # Create a multipart form-data request
        files = {'video': open(SAMPLE_VIDEO_PATH, 'rb')}
        
        print(f"Analyzing video: {SAMPLE_VIDEO_PATH}")
        print("Sending request to OpenAI video analysis endpoint...")
        
        start_time = time.time()
        response = requests.post(url, files=files)
        elapsed = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Analysis Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Suggested Text Overlay: {result.get('suggested_text', 'No text generated')}")
            print(f"Confidence Score: {result.get('confidence_score', 'N/A')}")
            print(f"Processing Time: {result.get('processing_time', 'N/A')}s")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        # Close the file if it's still open
        if 'files' in locals() and 'video' in files:
            files['video'].close()

def test_enhanced_video_processing():
    """Test the enhanced video processing endpoint"""
    print_section("Testing Enhanced Video Processing Endpoint")
    url = f"{ENHANCED_API_BASE_URL}/video/process-enhanced"
    
    if not verify_sample_video():
        return False
    
    try:
        # Create a multipart form-data request
        files = {'video': open(SAMPLE_VIDEO_PATH, 'rb')}
        data = {
            'text_overlay': 'Empower Your Learning Journey',
            'text_position': 'smart',  # Use smart positioning
            'add_background_music': 'true',
            'music_volume': '-25',  # -25 dB
        }
        
        print(f"Processing video: {SAMPLE_VIDEO_PATH}")
        print(f"Text Overlay: {data['text_overlay']}")
        print(f"Text Position: {data['text_position']}")
        print(f"Add Background Music: {data['add_background_music']}")
        print(f"Music Volume: {data['music_volume']} dB")
        print("Sending request to enhanced video processing endpoint...")
        
        start_time = time.time()
        response = requests.post(url, files=files, data=data)
        elapsed = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Processing Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Output Filename: {result.get('output_filename', 'No output file')}")
            print(f"Processing Time: {result.get('processing_time', 'N/A')}s")
            
            # Get the download URL
            download_url = f"{ENHANCED_API_BASE_URL}/download/{result.get('output_filename')}"
            print(f"Download URL: {download_url}")
            
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        # Close the file if it's still open
        if 'files' in locals() and 'video' in files:
            files['video'].close()

def test_complete_pipeline():
    """Test the complete video analysis and processing pipeline"""
    print_section("Testing Complete Video Pipeline")
    url = f"{ENHANCED_API_BASE_URL}/video/analyze-and-process"
    
    if not verify_sample_video():
        return False
    
    try:
        # Create a multipart form-data request
        files = {'video': open(SAMPLE_VIDEO_PATH, 'rb')}
        data = {
            'text_position': 'smart',
            'add_background_music': 'true',
            'music_volume': '-25',
        }
        
        print(f"Processing video: {SAMPLE_VIDEO_PATH}")
        print("Sending request to complete pipeline endpoint...")
        
        start_time = time.time()
        response = requests.post(url, files=files, data=data)
        elapsed = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Total Pipeline Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Suggested Text Overlay: {result.get('suggested_text', 'No text generated')}")
            print(f"Confidence Score: {result.get('confidence_score', 'N/A')}")
            print(f"Analysis Time: {result.get('analysis_time', 'N/A')}s")
            print(f"Output Filename: {result.get('output_filename', 'No output file')}")
            print(f"Processing Time: {result.get('processing_time', 'N/A')}s")
            print(f"Total Time: {result.get('total_time', 'N/A')}s")
            
            # Get the download URL
            download_url = f"{ENHANCED_API_BASE_URL}/download/{result.get('output_filename')}"
            print(f"Download URL: {download_url}")
            
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        # Close the file if it's still open
        if 'files' in locals() and 'video' in files:
            files['video'].close()

def find_video_files(directory=None):
    """Find all video files in the specified directory"""
    if directory is None:
        directory = VIDEOS_DIRECTORY
    
    if not os.path.exists(directory):
        print(f"Error: Directory not found: {directory}")
        return []
    
    video_files = [os.path.join(directory, f) for f in os.listdir(directory) 
                  if f.lower().endswith(('.mp4', '.mov', '.avi', '.webm'))]
    
    # Limit to 5 videos to avoid excessive processing
    return video_files[:5]

def run_automated_tests():
    """Run all tests automatically using real video data"""
    print_section("Running Automated Tests")
    
    # Find real video files to test with
    video_files = find_video_files()
    
    if not video_files:
        print("Error: No video files found in shared_videos directory.")
        return False
    
    # Select a sample video file for testing
    global SAMPLE_VIDEO_PATH
    SAMPLE_VIDEO_PATH = video_files[0]
    print(f"Using video file: {os.path.basename(SAMPLE_VIDEO_PATH)}")
    
    # Track test results
    results = {
        "health_check": False,
        "api_root": False,
        "video_analysis": False,
        "video_processing": False,
        "complete_pipeline": False
    }
    
    # Run all tests
    print("\n1. Testing API Health and Root Endpoints")
    results["health_check"] = test_health_check()
    results["api_root"] = test_api_root()
    
    if results["health_check"] and results["api_root"]:
        print("\n2. Testing OpenAI Video Analysis")
        results["video_analysis"] = test_openai_video_analysis()
        
        print("\n3. Testing Enhanced Video Processing")
        results["video_processing"] = test_enhanced_video_processing()
        
        print("\n4. Testing Complete Pipeline")
        results["complete_pipeline"] = test_complete_pipeline()
    
    # Print summary
    print_section("Test Results Summary")
    for test, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test.replace('_', ' ').title()}: {status}")
    
    # Overall success
    overall_success = all(results.values())
    print("\nOverall Test Result: " + ("✅ PASSED" if overall_success else "❌ FAILED"))
    
    return overall_success

if __name__ == "__main__":
    print("=" * 60)
    print(" ENHANCED FLASK API AUTOMATED TEST SUITE ".center(60, "="))
    print("=" * 60)
    print(f"API Base URL: {ENHANCED_API_BASE_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run all tests automatically
    success = run_automated_tests()
    
    # Exit with appropriate status code
    if not success:
        print("\nSome tests failed. Please check the logs above for details.")
        sys.exit(1)
    else:
        print("\nAll tests passed successfully!")
        sys.exit(0)
