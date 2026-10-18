#!/usr/bin/env python3
"""
Basic API test script for the enhanced Flask API
Tests only the health endpoint and API information
"""
import os
import sys
import time
import requests
import json
from pathlib import Path

# Configuration
ENHANCED_API_BASE_URL = "http://localhost:5003"

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def test_api_health():
    """Test the API health endpoint"""
    print_header("Testing API Health")
    url = f"{ENHANCED_API_BASE_URL}/health"
    print(f"Testing: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"API Status: {data.get('status', 'unknown')}")
            print(f"API Version: {data.get('version', 'unknown')}")
            print(f"OpenAI Configured: {data.get('openai_configured', False)}")
            return True
        else:
            print(f"Error: Unexpected status code {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_api_root():
    """Test the API root endpoint"""
    print_header("Testing API Root")
    url = f"{ENHANCED_API_BASE_URL}/"
    print(f"Testing: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Message: {data.get('message', 'No message')}")
            
            # List available endpoints
            print("\nAvailable Endpoints:")
            endpoints = data.get('endpoints', {})
            for endpoint, description in endpoints.items():
                print(f"  {endpoint}: {description}")
            return True
        else:
            print(f"Error: Unexpected status code {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def check_docker_container():
    """Check the Docker container status"""
    print_header("Checking Docker Container")
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=music_system-enhanced-flask-api", "--format", "{{.Status}}"],
            capture_output=True, text=True, check=True
        )
        status = result.stdout.strip()
        print(f"Container Status: {status}")
        
        # Check logs for errors
        result = subprocess.run(
            ["docker", "logs", "--tail", "10", "music_system-enhanced-flask-api-1"],
            capture_output=True, text=True
        )
        print("\nRecent Container Logs:")
        print(result.stdout.strip())
        
        return "Up" in status and "(healthy)" in status
    except Exception as e:
        print(f"Error checking container: {str(e)}")
        return False

if __name__ == "__main__":
    print_header("ENHANCED FLASK API BASIC TEST")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base URL: {ENHANCED_API_BASE_URL}")
    
    # Check container status first
    container_ok = check_docker_container()
    
    if container_ok:
        print("\n✅ Container appears to be running healthy")
    else:
        print("\n⚠️ Container may have issues, but proceeding with tests anyway")
    
    # Test API health
    health_ok = test_api_health()
    
    # Test API root
    root_ok = test_api_root()
    
    # Print summary
    print_header("TEST SUMMARY")
    print(f"Container Status: {'✅ OK' if container_ok else '❌ Issues'}")
    print(f"API Health: {'✅ OK' if health_ok else '❌ Failed'}")
    print(f"API Root: {'✅ OK' if root_ok else '❌ Failed'}")
    
    if health_ok and root_ok:
        print("\n✅ Basic API tests PASSED!")
        print("\nTo test video processing functionality:")
        print("1. Use a smaller video file (<5MB)")
        print("2. Increase connection timeouts")
        print("3. Consider testing directly with n8n workflow")
        sys.exit(0)
    else:
        print("\n❌ Some API tests FAILED!")
        sys.exit(1)
