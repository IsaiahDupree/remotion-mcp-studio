#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# Documentary Factory — Topic-Agnostic Production Pipeline
#
# Creates a complete 30-minute documentary from any topic:
#   Research → Script → Voiceover → Transcription → Images → Render → Upload
#
# Usage:
#   ./produce_documentary.sh --topic "The History of AI: From Turing to GPT"
#   ./produce_documentary.sh --config path/to/generate_config.json
#   ./produce_documentary.sh --config path/to/config.json --step 5
#   ./produce_documentary.sh --topic "..." --chapters 8 --dry-run
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

REMOTION_DIR="$SCRIPT_DIR/../.."

# Defaults
TOPIC=""
CONFIG=""
START_STEP=1
DRY_RUN=false
CHAPTERS=10
NARRATOR_STYLE="documentary"
PRIVACY="unlisted"
FORCE=false

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --topic) TOPIC="$2"; shift 2;;
    --config) CONFIG="$2"; shift 2;;
    --step) START_STEP="$2"; shift 2;;
    --chapters) CHAPTERS="$2"; shift 2;;
    --narrator-style) NARRATOR_STYLE="$2"; shift 2;;
    --privacy) PRIVACY="$2"; shift 2;;
    --force) FORCE=true; shift;;
    --dry-run) DRY_RUN=true; shift;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

# Validate: need either --topic or --config
if [[ -z "$TOPIC" && -z "$CONFIG" ]]; then
  echo "Error: Provide --topic \"...\" for a new documentary or --config path/to/config.json for existing"
  echo ""
  echo "Usage:"
  echo "  ./produce_documentary.sh --topic \"The History of AI: From Turing to GPT\""
  echo "  ./produce_documentary.sh --config research/my_topic/generate_config.json"
  echo "  ./produce_documentary.sh --topic \"...\" --chapters 8 --narrator-style dramatic"
  echo ""
  echo "Options:"
  echo "  --topic TEXT        Documentary topic (triggers research + script generation)"
  echo "  --config PATH       Path to existing generate_config.json"
  echo "  --step N            Start from step N (skip earlier steps)"
  echo "  --chapters N        Number of chapters (default: 10)"
  echo "  --narrator-style    documentary|educational|dramatic (default: documentary)"
  echo "  --privacy           YouTube privacy: public|unlisted|private (default: unlisted)"
  echo "  --force             Regenerate even if files exist"
  echo "  --dry-run           Show what would run without executing"
  exit 1
fi

# ─── Step 0: Research & Generate Config (if --topic provided) ─────────────────
if [[ -n "$TOPIC" && -z "$CONFIG" ]]; then
  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "  Step 0: Research & Generate Config"
  echo "  Topic: $TOPIC"
  echo "═══════════════════════════════════════════════════════════════"

  if $DRY_RUN; then
    echo "  [DRY-RUN] python3 research_and_generate.py --topic \"$TOPIC\" --chapters $CHAPTERS --narrator-style $NARRATOR_STYLE"
    # Compute slug for dry-run display
    SLUG=$(echo "$TOPIC" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/_/g' | sed 's/__*/_/g' | sed 's/^_//;s/_$//' | cut -c1-80)
    CONFIG="research/${SLUG}/generate_config.json"
    echo "  [DRY-RUN] Config would be: $CONFIG"
  else
    python3 research_and_generate.py --topic "$TOPIC" --chapters "$CHAPTERS" --narrator-style "$NARRATOR_STYLE"

    # Find the generated config (most recently created)
    SLUG=$(echo "$TOPIC" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/_/g' | sed 's/__*/_/g' | sed 's/^_//;s/_$//' | cut -c1-80)
    CONFIG="research/${SLUG}/generate_config.json"

    if [[ ! -f "$CONFIG" ]]; then
      echo "Error: Expected config at $CONFIG but not found"
      exit 1
    fi
    echo "  ✓ Config generated: $CONFIG"
  fi
fi

# ─── Derive paths from config ────────────────────────────────────────────────
CONFIG_DIR="$(dirname "$CONFIG")"
TOPIC_SLUG="$(basename "$CONFIG_DIR")"

AUDIO_DIR="audio_${TOPIC_SLUG}"
TRANSCRIPT_DIR="transcripts_${TOPIC_SLUG}"
SCENES_FILE="scenes_synced_${TOPIC_SLUG}.json"
RENDER_PROPS="render_props_${TOPIC_SLUG}.json"
SCENE_IMAGES_DIR="scene_images_${TOPIC_SLUG}"
CHARACTERS_DIR="characters_${TOPIC_SLUG}"
REMOTION_PROPS="${REMOTION_DIR}/props_${TOPIC_SLUG}.json"
OUTPUT_VIDEO="${REMOTION_DIR}/output/documentary_${TOPIC_SLUG}.mp4"

FORCE_FLAG=""
if $FORCE; then FORCE_FLAG="--force"; fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Documentary Factory — Production Pipeline"
echo "═══════════════════════════════════════════════════════════════"
echo "  Config:     $CONFIG"
echo "  Audio:      $AUDIO_DIR"
echo "  Transcripts: $TRANSCRIPT_DIR"
echo "  Images:     $SCENE_IMAGES_DIR"
echo "  Output:     $OUTPUT_VIDEO"
echo "  Start step: $START_STEP"
echo "═══════════════════════════════════════════════════════════════"
echo ""

run_step() {
  local step=$1
  local desc=$2
  shift 2
  local cmd=("$@")

  if [[ $step -lt $START_STEP ]]; then
    echo "  [SKIP] Step $step: $desc"
    return
  fi

  echo ""
  echo "──── Step $step: $desc ────"
  if $DRY_RUN; then
    echo "  [DRY-RUN] ${cmd[*]}"
  else
    "${cmd[@]}"
    echo "  ✓ Step $step complete"
  fi
}

# Step 1: Generate HQ Voiceover (ElevenLabs — paragraph-level chunks)
run_step 1 "Generate HQ Voiceover (ElevenLabs)" \
  python3 generate_voiceover_hq.py --config "$CONFIG" --output-dir "$AUDIO_DIR" $FORCE_FLAG

# Step 2: Whisper Word-Level Transcription
run_step 2 "Whisper Transcription" \
  python3 transcribe_whisper.py --config "$CONFIG" --audio-dir "$AUDIO_DIR" --transcript-dir "$TRANSCRIPT_DIR"

# Step 3: Build Scene Timings
run_step 3 "Build Scene Timings" \
  python3 build_scene_timings.py --config "$CONFIG" --transcript-dir "$TRANSCRIPT_DIR" --output "$SCENES_FILE"

# Step 4: Generate Render Props
run_step 4 "Build Render Props" \
  python3 generate_render_props.py --config "$CONFIG" --transcript-dir "$TRANSCRIPT_DIR" --scenes-file "$SCENES_FILE" --scene-images-dir "$SCENE_IMAGES_DIR" --output "$RENDER_PROPS"

# Step 5: Generate Character Images (Gemini)
run_step 5 "Generate Character Images" \
  python3 generate_characters.py --config "$CONFIG" --output-dir "$CHARACTERS_DIR"

# Step 6: Generate Per-Scene Images (Gemini — config-driven visual styles)
run_step 6 "Generate Per-Scene Images" \
  python3 generate_all_scene_images.py --config "$CONFIG" --props-file "$RENDER_PROPS" --output-dir "$SCENE_IMAGES_DIR"

# Step 7: Copy assets to Remotion + build Remotion props
run_step 7 "Prepare Remotion Assets" \
  bash -c "
    mkdir -p '${REMOTION_DIR}/public/seo_audio' '${REMOTION_DIR}/public/seo_characters' '${REMOTION_DIR}/public/seo_scene_images'
    cp '${AUDIO_DIR}'/*.mp3 '${REMOTION_DIR}/public/seo_audio/' 2>/dev/null || true
    cp '${CHARACTERS_DIR}'/*.png '${REMOTION_DIR}/public/seo_characters/' 2>/dev/null || true
    cp '${SCENE_IMAGES_DIR}'/*.png '${REMOTION_DIR}/public/seo_scene_images/' 2>/dev/null || true
    cp '${RENDER_PROPS}' '${REMOTION_PROPS}'
    echo '    Assets copied to Remotion'
  "

# Step 8: Remotion Render
run_step 8 "Remotion Video Render" \
  bash -c "cd '${REMOTION_DIR}' && npx remotion render SEODocumentaryV2 '${OUTPUT_VIDEO}' --props='${REMOTION_PROPS}' --concurrency=4"

# Step 9: YouTube Upload
run_step 9 "YouTube Upload" \
  python3 upload_youtube.py "${OUTPUT_VIDEO}" --config "$CONFIG" --privacy "$PRIVACY"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Pipeline complete!"
echo "  Video: $OUTPUT_VIDEO"
echo "═══════════════════════════════════════════════════════════════"
