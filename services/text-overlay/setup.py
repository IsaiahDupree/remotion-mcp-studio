#!/usr/bin/env python3
"""
Setup script for Smart Text-on-Video Overlay Tool.
Installs dependencies and prepares the environment.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from setuptools import setup, find_packages

# Package metadata
NAME = "smart_text_overlay"
DESCRIPTION = "Smart Text-on-Video Overlay Tool"
URL = "https://github.com/yourusername/smart-text-overlay"
EMAIL = "your.email@example.com"
AUTHOR = "Your Name"
REQUIRES_PYTHON = ">=3.8.0"
VERSION = "1.0.0"

# Required packages
REQUIRED = [
    "faster-whisper>=0.10.0",
    "openai>=1.12.0",
    "opencv-python>=4.8.0",
    "ftfy>=6.1.3",
    "regex>=2023.10.3",
    "tqdm>=4.66.1",
    "torch>=2.1.0",
    "torchvision>=0.16.0",
    "clip @ git+https://github.com/openai/CLIP.git",
    "mediapipe>=0.10.8",
    "ultralytics>=8.0.0",
    "moviepy>=1.0.3",
    "ffmpeg-python>=0.2.0",
    "pydantic>=2.5.0",
    "rich>=13.6.0",
    "PyYAML>=6.0.1",
    "python-slugify>=8.0.1",
    "PyQt5>=5.15.0",
    "requests>=2.28.0",
]

# Optional packages
EXTRAS = {
    "dev": [
        "pytest>=7.0.0",
        "black>=23.0.0",
        "flake8>=6.0.0",
        "isort>=5.12.0",
    ],
    "gui": ["PyQt5>=5.15.0"],
}

# Create necessary directories
def create_directories():
    """Create necessary directories for the project."""
    directories = ["input_videos", "outputs", "fonts"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

# Download fonts
def download_fonts():
    """Download required fonts."""
    try:
        from utils.font_downloader import download_and_install_fonts
        print("Downloading fonts...")
        download_and_install_fonts()
    except ImportError:
        print("Font downloader not available. Skipping font download.")
        print("Please run 'python -m utils.font_downloader' after installation.")

# Check system compatibility
def check_compatibility():
    """Check system compatibility."""
    print("\nChecking system compatibility...")
    
    # Check Python version
    python_version = sys.version.split()[0]
    print(f"Python version: {python_version}")
    if sys.version_info < (3, 8):
        print("WARNING: Python 3.8 or higher is recommended.")
    
    # Check for CUDA
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            cuda_version = torch.version.cuda
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "N/A"
            print(f"CUDA available: Yes (version {cuda_version})")
            print(f"GPU: {device_name}")
        else:
            print("CUDA available: No (CPU-only mode)")
    except ImportError:
        print("CUDA check failed: PyTorch not installed")
    
    # Check for FFmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            capture_output=True, 
            text=True, 
            check=False
        )
        if result.returncode == 0:
            ffmpeg_version = result.stdout.split('\n')[0]
            print(f"FFmpeg: {ffmpeg_version}")
        else:
            print("FFmpeg: Not found (required for video processing)")
    except FileNotFoundError:
        print("FFmpeg: Not found (required for video processing)")
    
    # Check operating system
    system = platform.system()
    print(f"Operating System: {system} {platform.version()}")
    
    print("\nSetup complete!")
    print("To run the tool, use: python smart_overlay.py --help")
    print("For the GUI interface, use: python gui.py")

# Main setup function
if __name__ == "__main__":
    # Setup package
    setup(
        name=NAME,
        version=VERSION,
        description=DESCRIPTION,
        author=AUTHOR,
        author_email=EMAIL,
        python_requires=REQUIRES_PYTHON,
        url=URL,
        packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
        install_requires=REQUIRED,
        extras_require=EXTRAS,
        include_package_data=True,
        license="MIT",
        classifiers=[
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: Implementation :: CPython",
        ],
    )
    
    # Create directories and download fonts
    create_directories()
    
    # Check compatibility
    check_compatibility()
    
    # Prompt for font download
    download_fonts_input = input("\nDo you want to download required fonts now? (y/n): ")
    if download_fonts_input.lower() in ["y", "yes"]:
        download_fonts()
    else:
        print("Skipping font download. You can run 'python -m utils.font_downloader' later.")
    
    print("\nThank you for installing the Smart Text-on-Video Overlay Tool!")
    print("For more information, see the README.md file.")
