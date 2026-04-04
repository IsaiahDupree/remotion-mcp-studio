# Smart Text-on-Video Overlay Tool Examples

This directory contains example scripts and files that demonstrate how to use the Smart Text-on-Video Overlay Tool in various scenarios.

## Batch Processing Example

The `batch_process.py` script demonstrates how to process multiple videos with different prompts using a CSV mapping file.

### Usage

```bash
python batch_process.py \
  --input-dir ../input_videos \
  --output-dir ../outputs \
  --mapping-file sample_video_prompts.csv \
  --openai-key "your-api-key-here"
```

### Sample CSV Format

The CSV file should have the following format:

```csv
video_file,prompt
business_meeting.mp4,5 strategies to improve team collaboration and productivity
technology_typing.mp4,How to boost your typing speed and efficiency in 3 simple steps
```

Each row maps a video file to a specific prompt. The script will process each video with its corresponding prompt.

### Advanced Options

You can specify additional options:

```bash
python batch_process.py \
  --input-dir ../input_videos \
  --output-dir ../outputs \
  --mapping-file sample_video_prompts.csv \
  --config ../config.yaml \
  --preset "Professional" \
  --webhook-url "https://hooks.zapier.com/hooks/catch/your-webhook-id" \
  --openai-key "your-api-key-here"
```

## Integration Examples

### Automating with Cron Jobs

You can set up a cron job to process videos automatically:

```bash
# Process videos every day at 2 AM
0 2 * * * cd /path/to/smart-text-overlay && python examples/batch_process.py --input-dir /path/to/videos --mapping-file /path/to/prompts.csv --openai-key "your-api-key-here"
```

### Integration with Content Workflows

The webhook functionality allows you to integrate the tool with content management systems and automation platforms:

1. Set up a webhook URL in Make.com, Zapier, or similar platform
2. Use the `--webhook-url` parameter when running the tool
3. Configure your automation platform to trigger actions when it receives the webhook

For example, you could set up a workflow that:
- Uploads processed videos to YouTube
- Sends notifications when processing is complete
- Updates a content calendar in your CMS

## Performance Optimization

For large batch processing jobs, consider using GPU acceleration:

```bash
# Ensure your config.yaml has GPU settings enabled
python batch_process.py \
  --input-dir ../input_videos \
  --output-dir ../outputs \
  --mapping-file sample_video_prompts.csv \
  --openai-key "your-api-key-here"
```

This will leverage CUDA for model inference and NVENC for hardware encoding if available.

## Creating Your Own Examples

Feel free to modify these examples or create your own to fit your specific workflow. The modular design of the tool makes it easy to integrate with existing systems and customize for your needs.
