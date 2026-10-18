#!/usr/bin/env python3
"""
Final verification script for the enhanced Flask API
Tests the complete video analysis and processing pipeline properly
"""
import os
import sys
import time
import json
import requests
import subprocess
from pathlib import Path

# Configuration
ENHANCED_API_BASE_URL = "http://localhost:5003"
VIDEOS_DIRECTORY = os.path.join(os.getcwd(), "shared", "videos")
TEMP_DIR = os.path.join(os.getcwd(), "music_system", "temp")
DEFAULT_VIDEO = os.path.join(VIDEOS_DIRECTORY, "optimized_IMG_3282.MP4")

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def check_api_health():
    """Check if the API is healthy"""
    try:
        response = requests.get(f"{ENHANCED_API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            return False, None
    except Exception as e:
        return False, str(e)

def test_video_directory():
    """Check if we can access shared directory in the Docker container"""
    print_header("CHECKING SHARED DIRECTORIES")
    
    # This is the expected path of the shared videos directory inside the container
    container_video_dir = "/app/shared/videos"
    
    try:
        # Execute a command to check if the directory exists in the container
        cmd = ["docker", "exec", "music_system-enhanced-flask-api-1", "ls", "-la", container_video_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Container can access shared videos directory: {container_video_dir}")
            print("\nFiles in shared directory:")
            for line in result.stdout.strip().split('\n'):
                if '.mp4' in line.lower() or '.mov' in line.lower():
                    print(f"  {line}")
            return True
        else:
            print(f"❌ Error accessing container directory: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error executing command: {str(e)}")
        return False

def test_analyze_endpoint():
    """Test the video analysis endpoint with the correct path approach"""
    print_header("TESTING OPENAI VIDEO ANALYSIS")
    
    # Use a known path inside the container
    container_video_path = "/app/shared/videos/optimized_IMG_3282.MP4"
    
    print(f"Testing with video path: {container_video_path}")
    
    # Prepare the JSON payload
    payload = {
        "video_path": container_video_path
    }
    
    try:
        # Send the request
        url = f"{ENHANCED_API_BASE_URL}/video/analyze-with-openai"
        print(f"Sending request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        start_time = time.time()
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 min timeout
        )
        elapsed_time = time.time() - start_time
        
        print(f"Response received in {elapsed_time:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Analysis successful!")
            print(f"Suggested overlay text: \"{result.get('suggested_text', 'N/A')}\"")
            print(f"Confidence score: {result.get('confidence_score', 'N/A')}")
            print(f"Processing time: {result.get('processing_time', 'N/A')} seconds")
            return True, result
        else:
            print(f"❌ Analysis failed: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, None

def test_complete_pipeline():
    """Test the complete analysis and processing pipeline"""
    print_header("TESTING COMPLETE PIPELINE")
    
    # Use a known path inside the container
    container_video_path = "/app/shared/videos/optimized_IMG_3282.MP4"
    
    print(f"Testing with video path: {container_video_path}")
    
    # Prepare the JSON payload
    payload = {
        "video_path": container_video_path,
        "text_position": "smart",
        "add_background_music": True,
        "music_volume": -25
    }
    
    try:
        # Send the request
        url = f"{ENHANCED_API_BASE_URL}/video/analyze-and-process"
        print(f"Sending request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        start_time = time.time()
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 min timeout
        )
        elapsed_time = time.time() - start_time
        
        print(f"Response received in {elapsed_time:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Complete pipeline successful!")
            print(f"Suggested overlay text: \"{result.get('suggested_text', 'N/A')}\"")
            print(f"Output filename: {result.get('output_filename', 'N/A')}")
            print(f"Total processing time: {elapsed_time:.2f} seconds")
            
            # Check if output file is available for download
            output_file = result.get('output_filename')
            if output_file:
                download_url = f"{ENHANCED_API_BASE_URL}/download/{output_file}"
                print(f"Video download URL: {download_url}")
                
            return True, result
        else:
            print(f"❌ Pipeline processing failed: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, None

def download_processed_file(filename):
    """Download the processed file"""
    if not filename:
        return False
    
    download_url = f"{ENHANCED_API_BASE_URL}/download/{filename}"
    output_path = os.path.join(os.getcwd(), "downloaded_" + filename)
    
    print(f"Downloading to: {output_path}")
    
    try:
        response = requests.get(download_url, stream=True, timeout=60)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ File downloaded successfully: {output_path}")
            print(f"File size: {os.path.getsize(output_path) / (1024*1024):.2f} MB")
            return True
        else:
            print(f"❌ Download failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Download error: {str(e)}")
        return False

if __name__ == "__main__":
    print_header("ENHANCED VIDEO PROCESSING VERIFICATION")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API URL: {ENHANCED_API_BASE_URL}")
    
    # Check API health
    healthy, health_data = check_api_health()
    if healthy:
        print(f"\n✅ API is healthy (version {health_data.get('version', 'unknown')})")
        print(f"OpenAI configured: {health_data.get('openai_configured', False)}")
    else:
        print(f"\n❌ API health check failed: {health_data}")
        sys.exit(1)
    
    # Check shared directory access
    if not test_video_directory():
        print("\n⚠️ Warning: Issues with shared directory access may affect testing")
    
    # Test video analysis
    analysis_success, analysis_result = test_analyze_endpoint()
    
    # Test complete pipeline if analysis was successful
    pipeline_success = False
    output_filename = None
    
    if analysis_success:
        pipeline_success, pipeline_result = test_complete_pipeline()
        if pipeline_success:
            output_filename = pipeline_result.get('output_filename')
    
    # Download the processed file if available
    download_success = False
    if output_filename:
        download_success = download_processed_file(output_filename)
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    print(f"API Health Check: {'✅ PASSED' if healthy else '❌ FAILED'}")
    print(f"OpenAI Video Analysis: {'✅ PASSED' if analysis_success else '❌ FAILED'}")
    print(f"Complete Processing Pipeline: {'✅ PASSED' if pipeline_success else '❌ FAILED'}")
    print(f"Output File Download: {'✅ PASSED' if download_success else '❌ FAILED or SKIPPED'}")
    
    overall_status = healthy and analysis_success and pipeline_success
    print(f"\nOverall Status: {'✅ FULLY OPERATIONAL' if overall_status else '⚠️ PARTIALLY OPERATIONAL'}")
    
    # Next steps
    print_header("NEXT STEPS")
    if overall_status:
        print("1. Import the enhanced workflow to n8n:")
        print(f"   - Access n8n at http://localhost:5679")
        print("   - Import workflows/complete-video-production-workflow-enhanced.json")
        print("   - Verify all node configurations")
        print("2. Run the workflow with a test video")
        print("3. Monitor logs during execution")
    else:
        print("1. Review the API logs for detailed error information:")
        print("   docker logs music_system-enhanced-flask-api-1")
        print("2. Check if all required dependencies are installed")
        print("3. Verify the OpenAI API key configuration")
        print("4. Ensure shared directories are properly mounted")
