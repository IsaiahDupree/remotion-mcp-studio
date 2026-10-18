# Videos Directory for n8n

This directory is designed for storing video files that you want to process with n8n workflows.

## How to Use This Directory

1. Place your video files in this directory on your host computer
2. These videos will be automatically available inside the n8n Docker container at `/home/node/shared/videos/`
3. In your n8n workflows, reference videos using the path `/home/node/shared/videos/your-video-file.mp4`

## Example Workflow Usage

```javascript
// In a Read Binary File node
{
  "filePath": "/home/node/shared/videos/large-video.mp4"
}
```

## Important Notes

- This directory is suitable for large video files (up to ~1GB) thanks to our optimized n8n configuration
- Files placed here persist across different n8n versions
- The directory is shared between your host computer and the Docker container
- Changes made on either side (host or container) are immediately visible on the other

## Best Practices

1. **Organize your files**: Consider creating subdirectories for different projects or video types
2. **Clean up regularly**: Remove videos that are no longer needed to save disk space
3. **Use descriptive filenames**: This makes it easier to identify videos in your workflows
4. **Consider file formats**: n8n works best with standard video formats (MP4, MOV, AVI, etc.)

## For Very Large Files (>1GB)

For extremely large files, consider:

1. Using chunked uploads via the Execute Command node with `curl` or similar tools
2. Generating presigned URLs and handling the upload outside of n8n
3. Using a dedicated file transfer service and having n8n coordinate the process

See `docs/large-file-handling.md` for more details on handling large file transfers.
