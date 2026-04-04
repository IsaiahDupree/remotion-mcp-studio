# Shared Folder

This folder is shared between your host computer and the n8n Docker container.

## Purpose

- Files placed in this folder on your host computer will be accessible inside the Docker container at `/home/node/shared`
- Files created by n8n inside the container in `/home/node/shared` will be accessible on your host computer in this folder

## Use Cases

- Share input files for n8n workflows
- Export data from n8n workflows
- Transfer files between your computer and n8n
- Store temporary files that need to be accessible by both systems

## Example

1. Place a CSV file in this folder on your host computer
2. In n8n, use the "Read Binary File" node to read the file from `/home/node/shared/your-file.csv`
3. Process the data in n8n
4. Use the "Write Binary File" node to write the output to `/home/node/shared/output.csv`
5. Access the output file on your host computer in this folder

## Note

This shared folder persists across different n8n versions, allowing you to maintain consistent access to your files regardless of which version you're currently running.
