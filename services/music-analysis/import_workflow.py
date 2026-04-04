#!/usr/bin/env python3
"""
Script to import the enhanced workflow into n8n
"""
import os
import sys
import time
import json
import requests
from pathlib import Path

# Configuration
N8N_BASE_URL = "http://localhost:5679"
WORKFLOW_PATH = os.path.join(
    os.getcwd(), "workflows", "complete-video-production-workflow-enhanced.json"
)

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def check_n8n_api():
    """Check if the n8n API is accessible"""
    print_header("Checking n8n API")
    url = f"{N8N_BASE_URL}/api/v1/settings"
    print(f"Testing: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            return True
        else:
            print(f"Error: Unexpected status code {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def import_workflow():
    """Import the workflow into n8n"""
    print_header("Importing Workflow")
    
    if not os.path.exists(WORKFLOW_PATH):
        print(f"Error: Workflow file not found: {WORKFLOW_PATH}")
        return False
    
    # Load the workflow JSON
    try:
        with open(WORKFLOW_PATH, 'r') as f:
            workflow_data = json.load(f)
        
        print(f"Loaded workflow: {workflow_data.get('name', 'Unknown')}")
        
        # Format for n8n API
        import_data = {
            "name": workflow_data.get("name", "Imported Workflow"),
            "nodes": workflow_data.get("nodes", []),
            "connections": workflow_data.get("connections", {}),
            "active": True,
            "settings": workflow_data.get("settings", {})
        }
        
        # API endpoint for workflow import
        url = f"{N8N_BASE_URL}/api/v1/workflows"
        
        # Send the request
        print(f"Sending import request to: {url}")
        response = requests.post(
            url, 
            json=import_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Handle response
        if response.status_code in (200, 201):
            workflow_id = response.json().get("id")
            print(f"✅ Workflow imported successfully with ID: {workflow_id}")
            print(f"Access at: {N8N_BASE_URL}/workflow/{workflow_id}")
            return True
        else:
            print(f"❌ Import failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error during import: {str(e)}")
        return False

if __name__ == "__main__":
    print_header("N8N WORKFLOW IMPORT")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"n8n URL: {N8N_BASE_URL}")
    print(f"Workflow: {WORKFLOW_PATH}")
    
    # Check n8n API
    if not check_n8n_api():
        print("❌ n8n API is not accessible. Make sure n8n is running.")
        sys.exit(1)
    
    # Import workflow
    if import_workflow():
        print("\n✅ Workflow import process completed successfully!")
        print("\nNext Steps:")
        print("1. Open the workflow in n8n")
        print("2. Configure any necessary credentials")
        print("3. Activate the workflow")
        print("4. Test with a small video file")
        sys.exit(0)
    else:
        print("\n❌ Workflow import failed!")
        sys.exit(1)
