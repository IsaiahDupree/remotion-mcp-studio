# Sample Video Instructions

To test the Video Context Extractor node, you'll need to place a sample video file in this directory.

## Obtaining a Sample Video

You can use any of the following methods to get a sample video:

1. **Download a sample video** from a public domain source like [Pexels](https://www.pexels.com/videos/) or [Pixabay](https://pixabay.com/videos/)

2. **Create a simple screen recording** using a tool like OBS Studio, Windows Game Bar, or QuickTime (Mac)

3. **Use a video from your own collection** that you'd like to analyze

## Naming Convention

For the workflow to automatically detect your video, name it:
- `sample-video.mp4`

If you use a different filename, you'll need to modify the workflow to point to your specific file.

## Video Requirements

For optimal results:
- **File size**: Keep under 25MB (Whisper API limit)
- **Duration**: 30 seconds to 2 minutes is ideal for testing
- **Format**: MP4 is recommended, but other formats should work
- **Content**: Videos with both visual action and spoken content will demonstrate the full capabilities

## After Adding Your Video

1. Restart the n8n container to ensure all configuration changes take effect:
   ```
   cd versions/1.87.0
   docker-compose down
   docker-compose up -d
   ```

2. Access the n8n interface at http://localhost:5678

3. Import and run the video analysis workflow

4. Check the output in the shared/videos directory (a JSON file with the analysis results)
