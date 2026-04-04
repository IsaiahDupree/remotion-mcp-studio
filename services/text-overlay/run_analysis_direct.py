#!/usr/bin/env python
"""
Simple script to run frame analysis with API key read directly from .env file
"""
import os
import sys
import subprocess
from pathlib import Path

def read_env_file(env_path):
    """Read key=value pairs from .env file"""
    env_vars = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                key_value = line.split('=', 1)
                if len(key_value) == 2:
                    key, value = key_value
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        print(f"Error reading .env file: {str(e)}")
    return env_vars

def main():
    # Read API key from .env file
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    env_vars = read_env_file(env_path)
    
    openai_api_key = env_vars.get('OPENAI_API_KEY')
    if not openai_api_key:
        print("Error: OPENAI_API_KEY not found in .env file.")
        return
    
    print(f"Successfully read OpenAI API key from .env file")
    
    # Input video path
    input_video = r"C:\Users\Isaia\Documents\N8N\shared_data\IMG_2401.MP4"
    
    # Run the frame analysis script with the API key passed as a parameter
    cmd = [
        sys.executable,
        r"C:\Users\Isaia\Documents\WordsOnText\frame_analysis_text_overlay.py",
        "--input", input_video,
        "--position", "TOP",
        "--api-key", openai_api_key
    ]
    
    # Execute the command
    print("Running frame analysis script with API key...")
    process = subprocess.run(cmd)
    
    if process.returncode == 0:
        print("Frame analysis completed successfully!")
    else:
        print(f"Frame analysis failed with return code: {process.returncode}")

if __name__ == "__main__":
    main()
