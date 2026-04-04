# Getting Started with Smart Text-on-Video Overlay Tool

This guide will help you quickly get up and running with the Smart Text-on-Video Overlay Tool.

## Quick Start

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Download sample videos**:

   ```bash
   python download_samples.py
   ```

3. **Check system compatibility**:

   ```bash
   python check_system.py
   ```

4. **Process a video**:

   ```bash
   python smart_overlay.py --input_dir ./input_videos --prompt "5 ways to automate your business now" --openai_key "your-api-key-here"
   ```

5. **View the results** in the `outputs` directory.

## Step-by-Step Guide

### 1. Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/yourusername/smart-text-overlay.git
cd smart-text-overlay
pip install -r requirements.txt
```

Alternatively, you can use the setup script for a guided installation:

```bash
python setup.py install
```

### 2. Download Required Fonts

The tool requires specific fonts for the text overlays. You can download them automatically:

```bash
python -m utils.font_downloader
```

### 3. Download Sample Videos

For testing purposes, you can download sample public domain videos:

```bash
python download_samples.py
```

This will download 5 sample videos to the `input_videos` directory. You can specify a different number of videos:

```bash
python download_samples.py --count 3
```

### 4. Check System Compatibility

Before running the tool, check if your system meets all requirements:

```bash
python check_system.py
```

For detailed information, use the verbose flag:

```bash
python check_system.py --verbose
```

You can also export the results to a file:

```bash
python check_system.py --export system_check.json
```

### 5. Process Videos

#### Basic Usage

Process all videos in the input directory with a single prompt:

```bash
python smart_overlay.py --input_dir ./input_videos --prompt "5 ways to automate your business now" --openai_key "your-api-key-here"
```

#### Advanced Options

```bash
python smart_overlay.py \
  --input_dir ./input_videos \
  --prompt "5 ways to automate your business now" \
  --font_path "./fonts/Inter-Bold.ttf" \
  --preset 'TechMeStuff' \
  --output_dir ./custom_outputs \
  --config ./config.yaml \
  --webhook_url "https://hooks.zapier.com/hooks/catch/your-webhook-id" \
  --openai_key "your-api-key-here"
```

#### Batch Processing with Multiple Prompts

Create a file `prompts.txt` with one prompt per line:

```text
5 ways to automate your business now
Top 3 productivity hacks for entrepreneurs
Why every business needs AI in 2025
```

Then run:

```bash
python smart_overlay.py \
  --input_dir ./input_videos \
  --prompt "Default prompt" \
  --batch_prompts ./prompts.txt \
  --openai_key "your-api-key-here"
```

### 6. Using the GUI

For a more user-friendly experience, you can use the graphical interface:

```bash
python gui.py
```

This will open a window where you can:

- Select input videos
- Enter your prompt
- Choose font settings
- Configure output options
- Process videos with a single click

### 7. Using Docker

If you prefer to use Docker, you can build and run the tool in a container:

```bash
# Build the Docker image
docker build -t smart-overlay .
```

```bash
# Run with Docker
docker run -v ./input_videos:/app/input_videos \
           -v ./outputs:/app/outputs \
           -e OPENAI_KEY="your-api-key-here" \
           smart-overlay \
           --input_dir /app/input_videos \
           --prompt "5 ways to automate your business now"
```

Or use Docker Compose:

```bash
# Set environment variables
export OPENAI_KEY="your-api-key-here"
export PROMPT="5 ways to automate your business now"

# Run with Docker Compose
docker-compose up
```

## Common Issues and Troubleshooting

### Missing Dependencies

If you encounter errors about missing dependencies, try reinstalling them:

```bash
pip install -r requirements.txt --force-reinstall
```

### Font Issues

If you see errors related to fonts, make sure you've downloaded the required fonts:

```bash
python -m utils.font_downloader
```

Alternatively, you can specify a custom font path:

```bash
python smart_overlay.py --input_dir ./input_videos --prompt "Your prompt" --font_path "/path/to/your/font.ttf" --openai_key "your-api-key-here"
```

### GPU Acceleration Issues

If you're having problems with GPU acceleration, you can force CPU-only mode:

```bash
python smart_overlay.py --input_dir ./input_videos --prompt "Your prompt" --cpu_only --openai_key "your-api-key-here"
```

### OpenAI API Key Issues

Make sure your OpenAI API key is valid and has sufficient credits. You can check this on the OpenAI dashboard.

## Next Steps

- Try different prompts to see how they affect the generated text
- Experiment with different font presets
- Customize the configuration in `config.yaml`
- Integrate with your content workflow using webhooks

For more detailed information, refer to the [README.md](README.md) file.
