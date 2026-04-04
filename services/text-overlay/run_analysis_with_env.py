#!/usr/bin/env python
"""
Script to run the frame analysis with environment variables from .env file
"""
import os
import sys
import subprocess
from dotenv import load_dotenv
from pathlib import Path

def main():
    """Load environment variables and run the frame analysis script"""
    
    # Load environment variables from .env file
    env_path = Path(os.path.dirname(os.path.abspath(__file__))) / '.env'
    load_dotenv(dotenv_path=env_path)
    
    # Check if the OpenAI API key was loaded
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY not found in .env file.")
        return
        
    print(f"Successfully loaded OPENAI_API_KEY from .env file")
    
    # Set up the command to run the frame analysis script
    input_video = r"C:\Users\Isaia\Documents\N8N\shared_data\IMG_2401.MP4"
    
    # Build the command
    cmd = [
        sys.executable,
        r"C:\Users\Isaia\Documents\WordsOnText\frame_analysis_text_overlay.py",
        "--input", input_video,
        "--position", "TOP",
        "--interval", "5",
        "--font-scale", "1.2"
    ]
    
    # Run the command
    print(f"Running frame analysis with command: {' '.join(cmd)}")
    try:
        # Pass the current environment with the loaded variables
        process = subprocess.Popen(cmd, env=os.environ)
        print("Process started. Please wait while the video is analyzed...")
        process.wait()
        
        if process.returncode == 0:
            print("Frame analysis completed successfully!")
        else:
            print(f"Frame analysis failed with return code: {process.returncode}")
            
    except Exception as e:
        print(f"Error running frame analysis: {str(e)}")
        
if __name__ == "__main__":
    main()
