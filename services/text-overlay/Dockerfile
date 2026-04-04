# Multi-stage build for Flask Video Enhancement API
FROM python:3.9-slim as base

# Install system dependencies for video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libgomp1 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/enhanced_videos /app/temp /shared_data

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p fonts input_videos outputs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
ENTRYPOINT ["python", "smart_overlay.py"]

# Default arguments (can be overridden)
CMD ["--help"]
