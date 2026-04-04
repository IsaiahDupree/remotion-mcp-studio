#!/usr/bin/env python3
"""
Script to update workflow URLs to point to enhanced API endpoints
"""
import json
import sys
from pathlib import Path

def update_workflow_urls(workflow_path, output_path=None):
    """
    Update the workflow URLs to point to enhanced API endpoints
    """
    print(f"Reading workflow from: {workflow_path}")
    
    # Load the workflow JSON
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    # Count of replacements
    replacements = 0
    
    # Process each node
    for node in workflow.get('nodes', []):
        # Only process HTTP Request nodes
        if node.get('type') == 'n8n-nodes-base.httpRequest':
            params = node.get('parameters', {})
            url = params.get('url', '')
            
            # Replace URL ports if they match the original API
            if 'http://host.docker.internal:5001/' in url:
                # Update to use enhanced API port (5003)
                params['url'] = url.replace('http://host.docker.internal:5001/', 'http://host.docker.internal:5003/')
                replacements += 1
                print(f"Updated URL in node '{node.get('name')}': {params['url']}")
                
            # Update URL for the video generator service if present
            elif 'http://host.docker.internal:5000/' in url:
                # Update to use enhanced video generator port (5004) if it's the video generator
                if '/video/' in url:
                    params['url'] = url.replace('http://host.docker.internal:5000/', 'http://host.docker.internal:5004/')
                    replacements += 1
                    print(f"Updated video generator URL in node '{node.get('name')}': {params['url']}")
    
    # Save the modified workflow
    if output_path is None:
        # Default output path is the input path with '-enhanced' suffix
        workflow_path_obj = Path(workflow_path)
        output_path = workflow_path_obj.parent / f"{workflow_path_obj.stem}-enhanced{workflow_path_obj.suffix}"
    
    with open(output_path, 'w') as f:
        json.dump(workflow, f, indent=2)
    
    print(f"Updated {replacements} URL(s) in the workflow")
    print(f"Saved enhanced workflow to: {output_path}")
    
    return output_path, replacements

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_workflow_urls.py <workflow_json_path> [output_path]")
        sys.exit(1)
    
    workflow_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    update_workflow_urls(workflow_path, output_path)
