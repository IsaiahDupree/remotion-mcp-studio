#!/usr/bin/env python3
"""
System Compatibility Checker for Smart Text-on-Video Overlay Tool

Checks if the system meets all requirements for running the tool.
"""

import os
import sys
import json
import subprocess
import platform
from typing import Dict, Any, List, Tuple, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def check_python_version() -> Tuple[bool, str]:
    """Check Python version."""
    python_version = sys.version.split()[0]
    is_compatible = sys.version_info >= (3, 8)
    message = f"{python_version} {'✓' if is_compatible else '✗'}"
    return is_compatible, message

def check_cuda() -> Tuple[bool, Dict[str, Any]]:
    """Check CUDA availability."""
    cuda_info = {
        "available": False,
        "version": "N/A",
        "device_count": 0,
        "device_name": "N/A",
    }
    
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        cuda_info["available"] = cuda_available
        
        if cuda_available:
            cuda_info["version"] = torch.version.cuda
            cuda_info["device_count"] = torch.cuda.device_count()
            if cuda_info["device_count"] > 0:
                cuda_info["device_name"] = torch.cuda.get_device_name(0)
        
        return cuda_available, cuda_info
    except ImportError:
        return False, cuda_info

def check_ffmpeg() -> Tuple[bool, str]:
    """Check FFmpeg installation."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            capture_output=True, 
            text=True, 
            check=False
        )
        if result.returncode == 0:
            ffmpeg_version = result.stdout.split('\n')[0]
            return True, ffmpeg_version
        else:
            return False, "Not found"
    except FileNotFoundError:
        return False, "Not found"

def check_dependencies() -> List[Tuple[str, bool, str]]:
    """Check required Python dependencies."""
    dependencies = [
        "openai",
        "opencv-python",
        "torch",
        "torchvision",
        "mediapipe",
        "ultralytics",
        "moviepy",
        "ffmpeg-python",
        "pydantic",
        "rich",
        "PyYAML",
        "python-slugify",
    ]
    
    results = []
    for dep in dependencies:
        try:
            if dep == "opencv-python":
                import cv2
                version = cv2.__version__
            elif dep == "torch":
                import torch
                version = torch.__version__
            elif dep == "torchvision":
                import torchvision
                version = torchvision.__version__
            elif dep == "openai":
                import openai
                version = openai.__version__
            elif dep == "mediapipe":
                import mediapipe
                version = mediapipe.__version__
            elif dep == "ultralytics":
                import ultralytics
                version = ultralytics.__version__
            elif dep == "moviepy":
                import moviepy
                version = moviepy.__version__
            elif dep == "ffmpeg-python":
                import ffmpeg
                version = "Installed"
            elif dep == "pydantic":
                import pydantic
                version = pydantic.__version__
            elif dep == "rich":
                import rich
                version = rich.__version__
            elif dep == "PyYAML":
                import yaml
                version = yaml.__version__
            elif dep == "python-slugify":
                import slugify
                version = slugify.__version__
            else:
                module = __import__(dep)
                version = getattr(module, "__version__", "Installed")
            
            results.append((dep, True, version))
        except (ImportError, AttributeError):
            results.append((dep, False, "Not installed"))
    
    return results

def check_directories() -> List[Tuple[str, bool]]:
    """Check if required directories exist."""
    directories = ["input_videos", "outputs", "fonts"]
    results = []
    
    for directory in directories:
        exists = os.path.isdir(directory)
        results.append((directory, exists))
    
    return results

def check_gpu_capabilities() -> Dict[str, Any]:
    """Check GPU capabilities for advanced features."""
    capabilities = {
        "cuda": False,
        "cudnn": False,
        "nvenc": False,
        "half_precision": False,
    }
    
    try:
        import torch
        if torch.cuda.is_available():
            capabilities["cuda"] = True
            
            # Check cuDNN
            if hasattr(torch.backends, 'cudnn') and torch.backends.cudnn.is_available():
                capabilities["cudnn"] = True
            
            # Check for half precision support
            device = torch.device("cuda:0")
            if torch.cuda.get_device_capability(0)[0] >= 7:  # Volta or newer
                capabilities["half_precision"] = True
            
            # Check for NVENC
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,encoder.stats", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                capabilities["nvenc"] = "Encoder" in result.stdout
            except (subprocess.SubprocessError, FileNotFoundError):
                # Try alternative method - check for GeForce/Quadro/Tesla GPUs which typically have NVENC
                device_name = torch.cuda.get_device_name(0).lower()
                capabilities["nvenc"] = any(name in device_name for name in ["geforce", "quadro", "tesla", "rtx", "gtx"])
    
    except ImportError:
        pass
    
    return capabilities

def main(verbose: bool = False, export_file: Optional[str] = None):
    """Run all system checks and display results.
    
    Args:
        verbose: Whether to show detailed information
        export_file: Path to export results to (json or txt)
    """
    console.print(Panel.fit("[bold]Smart Text-on-Video Overlay Tool - System Compatibility Check[/bold]"))
    
    # Check Python version
    python_compatible, python_version = check_python_version()
    console.print(f"Python version: {python_version}")
    
    # Check OS
    system = platform.system()
    console.print(f"Operating System: {system} {platform.version()}")
    
    # Check CUDA
    cuda_available, cuda_info = check_cuda()
    if cuda_available:
        console.print(f"CUDA: [green]Available[/green] (version {cuda_info['version']})")
        console.print(f"GPU: {cuda_info['device_name']}")
    else:
        console.print("CUDA: [yellow]Not available[/yellow] (CPU-only mode)")
    
    # Check FFmpeg
    ffmpeg_available, ffmpeg_version = check_ffmpeg()
    if ffmpeg_available:
        console.print(f"FFmpeg: [green]{ffmpeg_version}[/green]")
    else:
        console.print("FFmpeg: [red]Not found[/red] (required for video processing)")
    
    # Check directories
    console.print("\n[bold]Directory Check:[/bold]")
    dir_table = Table("Directory", "Status")
    for directory, exists in check_directories():
        status = "[green]✓ Exists[/green]" if exists else "[yellow]✗ Missing[/yellow]"
        dir_table.add_row(directory, status)
    console.print(dir_table)
    
    # Check dependencies
    console.print("\n[bold]Dependency Check:[/bold]")
    dep_table = Table("Package", "Status", "Version")
    for dep, installed, version in check_dependencies():
        status = "[green]✓ Installed[/green]" if installed else "[red]✗ Missing[/red]"
        dep_table.add_row(dep, status, version)
    console.print(dep_table)
    
    # Check GPU capabilities
    if cuda_available:
        console.print("\n[bold]GPU Capabilities:[/bold]")
        capabilities = check_gpu_capabilities()
        cap_table = Table("Feature", "Status")
        
        for feature, available in capabilities.items():
            status = "[green]✓ Available[/green]" if available else "[yellow]✗ Not available[/yellow]"
            feature_name = {
                "cuda": "CUDA Acceleration",
                "cudnn": "cuDNN (Deep Learning)",
                "nvenc": "NVENC (Hardware Encoding)",
                "half_precision": "Half Precision (FP16)",
            }.get(feature, feature)
            
            cap_table.add_row(feature_name, status)
        
        console.print(cap_table)
    
    # Overall assessment
    console.print("\n[bold]Overall Assessment:[/bold]")
    
    critical_requirements = python_compatible and ffmpeg_available
    
    if critical_requirements and cuda_available:
        console.print("[green]✓ Your system meets all requirements for optimal performance![/green]")
    elif critical_requirements:
        console.print("[yellow]✓ Your system meets the minimum requirements (CPU-only mode)[/yellow]")
        console.print("  For better performance, consider using a CUDA-capable GPU.")
    else:
        console.print("[red]✗ Your system does not meet all requirements.[/red]")
        if not python_compatible:
            console.print("  - Python 3.8 or higher is required")
        if not ffmpeg_available:
            console.print("  - FFmpeg is required for video processing")
    
    # Recommendations
    console.print("\n[bold]Recommendations:[/bold]")
    
    if not ffmpeg_available:
        console.print("- Install FFmpeg: https://ffmpeg.org/download.html")
    
    missing_deps = [dep for dep, installed, _ in check_dependencies() if not installed]
    if missing_deps:
        console.print(f"- Install missing dependencies: pip install {' '.join(missing_deps)}")
    
    missing_dirs = [directory for directory, exists in check_directories() if not exists]
    if missing_dirs:
        console.print(f"- Create missing directories: {', '.join(missing_dirs)}")
    
    if not cuda_available:
        console.print("- For better performance, consider using a CUDA-capable GPU")
        console.print("  https://developer.nvidia.com/cuda-downloads")
    
    # Export results if requested
    if export_file:
        export_results = {
            "python": {
                "compatible": python_compatible,
                "version": python_version
            },
            "os": {
                "system": system,
                "version": platform.version()
            },
            "cuda": cuda_info,
            "ffmpeg": {
                "available": ffmpeg_available,
                "version": ffmpeg_version
            },
            "directories": {dir_name: exists for dir_name, exists in check_directories()},
            "dependencies": {dep: {"installed": installed, "version": version} for dep, installed, version in check_dependencies()},
            "gpu_capabilities": check_gpu_capabilities() if cuda_available else {},
            "overall": {
                "meets_requirements": critical_requirements,
                "optimal_performance": critical_requirements and cuda_available
            }
        }
        
        # Export as JSON or text
        if export_file.endswith(".json"):
            with open(export_file, "w") as f:
                json.dump(export_results, f, indent=2)
            console.print(f"\nResults exported to [bold]{export_file}[/bold]")
        elif export_file.endswith(".txt"):
            with open(export_file, "w") as f:
                f.write("Smart Text-on-Video Overlay Tool - System Compatibility Check\n\n")
                f.write(f"Python version: {python_version}\n")
                f.write(f"Operating System: {system} {platform.version()}\n")
                f.write(f"CUDA: {'Available' if cuda_available else 'Not available'}")
                if cuda_available:
                    f.write(f" (version {cuda_info['version']})\n")
                    f.write(f"GPU: {cuda_info['device_name']}\n")
                else:
                    f.write(" (CPU-only mode)\n")
                f.write(f"FFmpeg: {ffmpeg_version if ffmpeg_available else 'Not found'}\n\n")
                
                f.write("Directory Check:\n")
                for directory, exists in check_directories():
                    f.write(f"- {directory}: {'Exists' if exists else 'Missing'}\n")
                
                f.write("\nDependency Check:\n")
                for dep, installed, version in check_dependencies():
                    f.write(f"- {dep}: {'Installed' if installed else 'Missing'} ({version})\n")
                
                if cuda_available:
                    f.write("\nGPU Capabilities:\n")
                    capabilities = check_gpu_capabilities()
                    for feature, available in capabilities.items():
                        feature_name = {
                            "cuda": "CUDA Acceleration",
                            "cudnn": "cuDNN (Deep Learning)",
                            "nvenc": "NVENC (Hardware Encoding)",
                            "half_precision": "Half Precision (FP16)",
                        }.get(feature, feature)
                        f.write(f"- {feature_name}: {'Available' if available else 'Not available'}\n")
                
                f.write("\nOverall Assessment:\n")
                if critical_requirements and cuda_available:
                    f.write("✓ Your system meets all requirements for optimal performance!\n")
                elif critical_requirements:
                    f.write("✓ Your system meets the minimum requirements (CPU-only mode)\n")
                    f.write("  For better performance, consider using a CUDA-capable GPU.\n")
                else:
                    f.write("✗ Your system does not meet all requirements.\n")
                    if not python_compatible:
                        f.write("  - Python 3.8 or higher is required\n")
                    if not ffmpeg_available:
                        f.write("  - FFmpeg is required for video processing\n")
            
            console.print(f"\nResults exported to [bold]{export_file}[/bold]")
        else:
            console.print(f"\n[yellow]Warning: Unknown export format. Use .json or .txt extension.[/yellow]")
    
    # Additional verbose output
    if verbose:
        console.print("\n[bold]Detailed System Information:[/bold]")
        
        # Python details
        console.print("\n[bold]Python Details:[/bold]")
        console.print(f"Python Implementation: {platform.python_implementation()}")
        console.print(f"Python Build: {platform.python_build()[0]} {platform.python_build()[1]}")
        console.print(f"Python Compiler: {platform.python_compiler()}")
        
        # System details
        console.print("\n[bold]System Details:[/bold]")
        console.print(f"Machine: {platform.machine()}")
        console.print(f"Processor: {platform.processor()}")
        
        # CUDA details if available
        if cuda_available:
            console.print("\n[bold]CUDA Details:[/bold]")
            import torch
            console.print(f"PyTorch Version: {torch.__version__}")
            console.print(f"CUDA Arch List: {torch.cuda.get_arch_list() if hasattr(torch.cuda, 'get_arch_list') else 'N/A'}")
            console.print(f"CUDA Device Count: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                console.print(f"  Device {i}: {torch.cuda.get_device_name(i)}")
                console.print(f"    Capability: {torch.cuda.get_device_capability(i)}")
                console.print(f"    Total Memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
            
            if hasattr(torch.backends, 'cudnn'):
                console.print(f"cuDNN Version: {torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else 'Not available'}")
                console.print(f"cuDNN Enabled: {torch.backends.cudnn.enabled}")
        
        # Dependency details
        console.print("\n[bold]Dependency Details:[/bold]")
        for dep, installed, version in check_dependencies():
            if installed:
                console.print(f"[green]{dep}[/green]: {version}")
            else:
                console.print(f"[red]{dep}[/red]: Not installed")

if __name__ == "__main__":
    main()
