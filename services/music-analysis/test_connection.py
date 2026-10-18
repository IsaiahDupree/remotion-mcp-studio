#!/usr/bin/env python3
import requests
import time
import sys

BASE_URL = "http://localhost:5001"
ENDPOINTS = [
    "/health",
    "/system/status",
    "/fonts/list",
    "/music/database/stats"
]

def test_endpoint(endpoint):
    url = f"{BASE_URL}{endpoint}"
    try:
        print(f"Testing {url}...")
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.text[:200]}...")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    success_count = 0
    for endpoint in ENDPOINTS:
        if test_endpoint(endpoint):
            success_count += 1
        time.sleep(1)  # Small delay between requests
    
    print(f"\nSummary: {success_count}/{len(ENDPOINTS)} endpoints successful")
    return success_count == len(ENDPOINTS)

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
