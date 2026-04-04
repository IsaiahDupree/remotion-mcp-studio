#!/usr/bin/env python3
"""
GPU Utilities for Smart Text-on-Video Overlay Tool

Provides functions to detect and utilize GPU acceleration for improved performance.
"""

import logging
import os
from typing import Tuple, Dict, Any, Optional

# Set up logging
log = logging.getLogger("smart_overlay.gpu")


def detect_gpu() -> Tuple[bool, Dict[str, Any]]:
    """Detect available GPU and its capabilities.
    
    Returns:
        Tuple[bool, Dict[str, Any]]: (gpu_available, gpu_info)
    """
    gpu_info = {
        "cuda_available": False,
        "device_count": 0,
        "device_names": [],
        "cuda_version": None,
        "cudnn_version": None,
        "nvenc_available": False
    }
    
    try:
        import torch
        
        # Check CUDA availability
        cuda_available = torch.cuda.is_available()
        gpu_info["cuda_available"] = cuda_available
        
        if cuda_available:
            # Get device count and names
            device_count = torch.cuda.device_count()
            gpu_info["device_count"] = device_count
            
            device_names = []
            for i in range(device_count):
                device_names.append(torch.cuda.get_device_name(i))
            gpu_info["device_names"] = device_names
            
            # Get CUDA version
            cuda_version = torch.version.cuda
            gpu_info["cuda_version"] = cuda_version
            
            # Get cuDNN version if available
            if hasattr(torch.backends, 'cudnn') and torch.backends.cudnn.is_available():
                cudnn_version = torch.backends.cudnn.version()
                gpu_info["cudnn_version"] = cudnn_version
            
            # Check for NVENC (NVIDIA encoder)
            try:
                import subprocess
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,encoder.stats", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                gpu_info["nvenc_available"] = "Encoder" in result.stdout
            except (subprocess.SubprocessError, FileNotFoundError):
                # Try alternative method
                gpu_info["nvenc_available"] = any("GeForce" in name or "Quadro" in name or "Tesla" in name for name in device_names)
            
            log.info(f"GPU detected: {device_names[0]} (CUDA {cuda_version})")
            return True, gpu_info
        
        log.info("No CUDA-capable GPU detected")
        return False, gpu_info
    
    except ImportError:
        log.warning("PyTorch not installed, cannot detect GPU")
        return False, gpu_info
    except Exception as e:
        log.error(f"Error detecting GPU: {e}")
        return False, gpu_info


def setup_gpu_acceleration(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Configure GPU acceleration based on available hardware.
    
    Args:
        config: Configuration dictionary (optional)
        
    Returns:
        Dict[str, Any]: GPU configuration
    """
    gpu_available, gpu_info = detect_gpu()
    
    gpu_config = {
        "use_gpu": False,
        "device": "cpu",
        "use_nvenc": False,
        "half_precision": False,
        "batch_size": 1
    }
    
    if not gpu_available:
        return gpu_config
    
    # GPU is available, configure settings
    gpu_config["use_gpu"] = True
    gpu_config["device"] = "cuda:0"
    
    # Configure NVENC for video encoding if available
    if gpu_info["nvenc_available"]:
        gpu_config["use_nvenc"] = True
        os.environ["IMAGEIO_FFMPEG_EXE"] = "ffmpeg"  # Ensure ffmpeg is used
        log.info("NVENC hardware encoding enabled")
    
    # Configure precision based on GPU capabilities
    # Modern GPUs benefit from half precision (FP16)
    if any(gpu_name in str(gpu_info["device_names"]) for gpu_name in ["RTX", "A100", "V100", "T4"]):
        gpu_config["half_precision"] = True
        log.info("Half precision (FP16) enabled")
    
    # Set batch size based on available VRAM
    # This is a simplified heuristic
    if gpu_info["device_count"] > 0:
        # Default conservative batch size
        gpu_config["batch_size"] = 2
        
        # Increase for higher-end GPUs
        if any(gpu_name in str(gpu_info["device_names"]) for gpu_name in ["RTX 3090", "RTX 4090", "A100", "V100"]):
            gpu_config["batch_size"] = 4
    
    # Override with user config if provided
    if config and "gpu" in config:
        user_gpu_config = config.get("gpu", {})
        for key in user_gpu_config:
            if key in gpu_config:
                gpu_config[key] = user_gpu_config[key]
    
    log.info(f"GPU acceleration configured: {gpu_config}")
    return gpu_config


def get_optimal_ffmpeg_args(gpu_config: Dict[str, Any]) -> Dict[str, Any]:
    """Get optimal ffmpeg arguments based on GPU configuration.
    
    Args:
        gpu_config: GPU configuration dictionary
        
    Returns:
        Dict[str, Any]: FFmpeg arguments
    """
    ffmpeg_args = {
        "codec": "libx264",
        "audio_codec": "aac",
        "preset": "medium",
        "threads": os.cpu_count()
    }
    
    if gpu_config["use_nvenc"]:
        ffmpeg_args["codec"] = "h264_nvenc"
        ffmpeg_args["preset"] = "p4"
        ffmpeg_args["extra_args"] = ["-tune", "hq"]
    
    return ffmpeg_args


if __name__ == "__main__":
    # Configure logging for standalone testing
    logging.basicConfig(level=logging.INFO)
    
    # Test GPU detection
    gpu_available, gpu_info = detect_gpu()
    print(f"GPU Available: {gpu_available}")
    print(f"GPU Info: {gpu_info}")
    
    # Test GPU configuration
    gpu_config = setup_gpu_acceleration()
    print(f"GPU Config: {gpu_config}")
    
    # Test FFmpeg arguments
    ffmpeg_args = get_optimal_ffmpeg_args(gpu_config)
    print(f"FFmpeg Args: {ffmpeg_args}")
