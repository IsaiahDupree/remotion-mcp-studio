#!/bin/zsh
# SEO Documentary — Render + YouTube Upload Pipeline

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REMOTION_DIR="$SCRIPT_DIR/../.."
OUTPUT_DIR="$SCRIPT_DIR/output"
OUTPUT_FILE="$OUTPUT_DIR/seo_documentary.mp4"

mkdir -p "$OUTPUT_DIR"

echo "=== SEO Documentary Render Pipeline ==="
echo ""

# Step 1: Render via Remotion
echo "[1/3] Rendering SEODocumentary composition..."
cd "$REMOTION_DIR"
npx remotion render SEODocumentary "$OUTPUT_FILE" \
  --codec=h264 \
  --jpeg-quality=90 \
  --concurrency=4

echo "  ✓ Rendered to $OUTPUT_FILE"
echo ""

# Step 2: Upload to YouTube via upload_youtube.py
echo "[2/3] Uploading to YouTube..."
cd "$SCRIPT_DIR"
python3 upload_youtube.py "$OUTPUT_FILE"

echo ""
echo "[3/3] Done! Check YouTube Studio for the upload."
