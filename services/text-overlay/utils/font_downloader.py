#!/usr/bin/env python3
"""
Font Downloader Utility

Downloads and installs the required fonts for the smart text-on-video overlay tool.
"""

import os
import sys
import requests
import zipfile
import shutil
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn

# Font URLs - using Google Fonts
FONT_URLS = {
    "Inter": "https://fonts.google.com/download?family=Inter",
    "Roboto": "https://fonts.google.com/download?family=Roboto",
    "Montserrat": "https://fonts.google.com/download?family=Montserrat",
    "OpenSans": "https://fonts.google.com/download?family=Open+Sans"
}

# Font files we need
REQUIRED_FONTS = [
    "Inter-Bold.ttf",
    "Roboto-Light.ttf",
    "Montserrat-ExtraBold.ttf",
    "OpenSans-SemiBold.ttf"
]

console = Console()


def download_file(url: str, target_path: str) -> bool:
    """Download a file from URL to target path with progress bar."""
    try:
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
        ) as progress:
            task = progress.add_task(f"Downloading {os.path.basename(target_path)}", total=None)
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Get content length if available
            total_size = int(response.headers.get('content-length', 0))
            if total_size:
                progress.update(task, total=total_size)
            
            # Download the file
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))
            
            return True
    except Exception as e:
        console.print(f"[bold red]Error downloading {url}: {e}[/bold red]")
        return False


def extract_font_zip(zip_path: str, extract_dir: str) -> None:
    """Extract font zip file to temporary directory."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)


def find_font_file(search_dir: str, font_name: str) -> str:
    """Find a specific font file in the extracted directory."""
    for root, _, files in os.walk(search_dir):
        for file in files:
            if file.lower() == font_name.lower():
                return os.path.join(root, file)
    return ""


def download_and_install_fonts(fonts_dir: str = "./fonts") -> None:
    """Download and install all required fonts."""
    console.print("[bold green]Font Downloader Utility[/bold green]")
    console.print(f"Installing fonts to: {fonts_dir}")
    
    # Create fonts directory if it doesn't exist
    os.makedirs(fonts_dir, exist_ok=True)
    
    # Create temporary directory for downloads
    temp_dir = os.path.join(os.path.dirname(fonts_dir), "temp_fonts")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        for font_family, url in FONT_URLS.items():
            console.print(f"\n[bold]Processing {font_family} font family...[/bold]")
            
            # Download zip file
            zip_path = os.path.join(temp_dir, f"{font_family}.zip")
            if download_file(url, zip_path):
                # Extract zip
                extract_dir = os.path.join(temp_dir, font_family)
                os.makedirs(extract_dir, exist_ok=True)
                extract_font_zip(zip_path, extract_dir)
                
                # Find and copy required font files
                for font_file in REQUIRED_FONTS:
                    if font_file.startswith(font_family):
                        font_path = find_font_file(extract_dir, font_file)
                        if font_path:
                            target_path = os.path.join(fonts_dir, font_file)
                            shutil.copy2(font_path, target_path)
                            console.print(f"[green]✓[/green] Installed {font_file}")
                        else:
                            console.print(f"[yellow]⚠[/yellow] Could not find {font_file}")
        
        console.print("\n[bold green]Font installation complete![/bold green]")
        
        # Verify all required fonts were installed
        missing_fonts = []
        for font_file in REQUIRED_FONTS:
            if not os.path.exists(os.path.join(fonts_dir, font_file)):
                missing_fonts.append(font_file)
        
        if missing_fonts:
            console.print(f"[bold yellow]Warning: The following fonts are missing: {', '.join(missing_fonts)}[/bold yellow]")
            console.print("You may need to download these fonts manually.")
        else:
            console.print("[bold green]All required fonts were successfully installed.[/bold green]")
    
    finally:
        # Clean up temporary files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            console.print("[dim]Cleaned up temporary files[/dim]")


if __name__ == "__main__":
    fonts_dir = "./fonts"
    if len(sys.argv) > 1:
        fonts_dir = sys.argv[1]
    
    download_and_install_fonts(fonts_dir)
