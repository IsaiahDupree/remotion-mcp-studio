# Smart Text-on-Video Overlay Tool

A Python-based application that automatically analyzes videos and intelligently places context-aware text overlays. The tool analyzes transcript content, visual elements, and user prompts to generate compelling text that is positioned in uncluttered regions of the video.

## Features

- **Intelligent Text Generation**: Combines transcript analysis (30%), visual context (30%), and user prompts (40%) to create compelling overlays
- **Smart Placement Algorithm**: Automatically finds uncluttered regions by avoiding faces, UI elements, and visually important areas
- **Batch Processing**: Process multiple videos with a single command
- **Detailed Logging**: Comprehensive logs and mapping files for each processing run
- **Font Presets**: Multiple font styles with automatic sizing based on video resolution
- **Customizable**: Extensive configuration options via YAML file
- **GPU Acceleration**: Optimized performance with CUDA-capable GPUs and NVENC hardware encoding
- **Webhook Integration**: Send notifications to external services like Make.com or Zapier
- **Graphical User Interface**: Easy-to-use GUI wrapper for non-technical users
- **Docker Support**: Containerized deployment for cloud environments

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/smart-text-overlay.git
   cd smart-text-overlay
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Download required fonts automatically:
   ```
   python -m utils.font_downloader
   ```
   
   Or manually add your preferred fonts to the `fonts` directory. The default configuration looks for:
   - `fonts/Inter-Bold.ttf`
   - `fonts/Roboto-Light.ttf`
   - `fonts/Montserrat-ExtraBold.ttf`
   - `fonts/OpenSans-SemiBold.ttf`

4. Set up your OpenAI API key:
   ```
   export OPENAI_KEY="your-api-key-here"
   ```

## Usage

### Command Line Interface

#### Basic Usage

```bash
python smart_overlay.py \
  --input_dir ./input_videos \
  --prompt "5 ways to automate your business now" \
  --openai_key $OPENAI_KEY
```

#### Advanced Options

```bash
python smart_overlay.py \
  --input_dir ./input_videos \
  --prompt "5 ways to automate your business now" \
  --font_path "./fonts/Inter-Bold.ttf" \
  --preset 'TechMeStuff' \
  --output_dir ./custom_outputs \
  --config ./custom_config.yaml \
  --webhook_url "https://hooks.zapier.com/hooks/catch/your-webhook-id" \
  --openai_key $OPENAI_KEY
```

#### GPU Acceleration Options

```bash
python smart_overlay.py \
  --input_dir ./input_videos \
  --prompt "5 ways to automate your business now" \
  --half_precision \
  --openai_key $OPENAI_KEY
```

To force CPU-only mode even if a GPU is available:

```bash
python smart_overlay.py \
  --input_dir ./input_videos \
  --prompt "5 ways to automate your business now" \
  --cpu_only \
  --openai_key $OPENAI_KEY
```

#### Batch Processing with Multiple Prompts

Create a text file with one prompt per line:

```
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
  --openai_key $OPENAI_KEY
```

### Graphical User Interface

For a more user-friendly experience, you can use the GUI wrapper:

```bash
python gui.py
```

This will open a window where you can configure all options and process videos with a simple click.

### Docker

You can also run the tool using Docker:

```bash
# Build the Docker image
docker build -t smart-overlay .

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

## Configuration

The `config.yaml` file contains all customizable settings:

```yaml
video:
  min_font_size: 38
  max_font_size: 72
  fade_in_sec: 0.35
  safe_caption_height_pct: 15
overlay:
  font: "./fonts/Inter-Bold.ttf"
  color: "white"
  stroke: 
    width: 2
    color: "black"
models:
  whisper_model: "medium"
  clip_model: "ViT-B/32"
  gpt_model: "gpt-4o-mini"
  yolo_model: "yolov8n"
weights:
  transcript: 0.30
  vision: 0.30
  prompt: 0.40
sampling:
  short_interval_sec: 10
  long_interval_sec: 30
thresholds:
  min_mask_area_pct: 5
gpu:
  use_gpu: true  # Set to false to force CPU-only mode
  half_precision: true  # Use half precision (FP16) for models if supported
  batch_size: 2  # Batch size for processing multiple frames
  use_nvenc: true  # Use NVIDIA hardware encoding if available
webhook:
  enabled: false  # Set to true to enable webhook notifications
  url: ""  # URL to send webhook notifications to
```

## Output Structure

Each processing run creates a timestamped directory with:

```
outputs/
└── 2025-05-16_23-05_run/
    ├── edited/
    │   └── <new_name>.mp4
    ├── mapping.csv
    └── run.log
```

The `mapping.csv` file contains detailed information about each processed video:
- `original_name`: Original video filename
- `new_name`: New video filename
- `overlay_text`: The generated text overlay
- `start_sec`: Start time of the overlay
- `duration`: Duration of the overlay
- `position_x`, `position_y`: Position coordinates
- `font_style`: Font used
- `prompt`: Original prompt used

## Font Presets

The tool includes four built-in font presets:

1. **TechMeStuff** (default): Bold, modern look with strong contrast
2. **Minimalist**: Clean, light font with subtle stroke
3. **Dramatic**: Extra bold font with heavy stroke for maximum impact
4. **Professional**: Semi-bold font with balanced stroke for business content

## Requirements

- Python 3.8+
- OpenAI API key
- CUDA-capable GPU recommended for faster processing (optional)
- FFmpeg for video processing (automatically installed via requirements)

## Testing

Run the unit tests to ensure everything is working correctly:

```bash
python -m unittest discover tests
```

## Webhook Integration

The tool can send webhook notifications when videos are processed, making it easy to integrate with automation platforms like Make.com or Zapier. Webhooks are sent in the following format:

### Video Processed Event

```json
{
  "event": "video_processed",
  "timestamp": "2025-05-16T23:15:30.123456",
  "video": {
    "original_name": "input.mp4",
    "new_name": "5-ways-to-automate-your-business_input.mp4",
    "overlay_text": "Automate your business with these 5 game-changing strategies",
    "prompt": "5 ways to automate your business now",
    "position": {
      "x": 120,
      "y": 80
    },
    "duration": 180.5,
    "font_style": "./fonts/Inter-Bold.ttf"
  }
}
```

### Batch Complete Event

```json
{
  "event": "batch_complete",
  "timestamp": "2025-05-16T23:20:45.123456",
  "batch": {
    "total_videos": 5,
    "successful_videos": 5,
    "failed_videos": 0,
    "output_directory": "./outputs/2025-05-16_23-05_run",
    "mapping_file": "./outputs/2025-05-16_23-05_run/mapping.csv",
    "prompt": "5 ways to automate your business now"
  }
}
```

## Performance Optimization

The tool includes several performance optimizations:

- **GPU Acceleration**: Automatically uses CUDA for model inference if available
- **NVENC Hardware Encoding**: Uses NVIDIA's hardware encoder for faster video rendering
- **Half Precision**: Reduces memory usage and improves performance with FP16 computation
- **Batch Processing**: Processes multiple frames in parallel for faster analysis

## Project Structure

```
project_root/
├── config.yaml           # Configuration file
├── smart_overlay.py      # Main script
├── gui.py               # GUI wrapper
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
├── requirements.txt     # Python dependencies
├── input_videos/        # Input video directory
├── fonts/               # Font files
├── outputs/             # Output directory
├── tests/               # Unit tests
└── utils/               # Utility modules
    ├── font_downloader.py  # Font download utility
    ├── gpu_utils.py        # GPU acceleration utilities
    └── webhook.py          # Webhook notification utilities
```

## License

MIT License
