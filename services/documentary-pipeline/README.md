# Documentary Production Pipeline

Full automated pipeline: **Topic → Research → Script → Voiceover → Transcription → Scene Timing → Images → Render Props → Remotion Render → YouTube Upload**

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env and fill in API keys
cp .env.example .env

# Generate a full documentary
./produce_documentary.sh --topic "The History of AI: From Turing to GPT"

# Or resume from a specific step
./produce_documentary.sh --config research/my_topic/generate_config.json --step 5
```

## Pipeline Steps

| Step | Script | What It Does | API |
|------|--------|-------------|-----|
| 1 | `research_topic.py` | Multi-source research (web + Reddit + synthesis) | Perplexity, Reddit, Claude |
| 2 | `research_and_generate.py` | Generate chapter structure + narration script | Claude |
| 3 | `generate_voiceover_hq.py` | Chapter voiceover (paragraph-level chunks) | ElevenLabs |
| 4 | `transcribe_whisper.py` | Word-level timestamps | OpenAI Whisper |
| 5 | `build_scene_timings.py` | Natural scene cuts from speech | Local (no API) |
| 6 | `generate_render_props.py` | Build Remotion config JSON | Local |
| 7 | `generate_characters.py` | Consistent character images | Gemini |
| 8 | `generate_all_scene_images.py` | Per-scene concept images | Gemini |
| 9 | Remotion render | `npx remotion render SEODocumentaryV2` | Local |
| 10 | `upload_youtube.py` | Upload with metadata + chapters | YouTube API |

## Quality Assurance

```bash
# Voice quality check (detects clipping, artifacts, pacing issues)
python voice_qa_gate.py --auto-fix

# Pipeline sanity checks
python -m pytest tests/
```

## Renders Into

This pipeline generates `render_props_v3.json` which feeds into:
- `src/compositions/SEODocumentaryV2.tsx` — Scene-based with Whisper captions, Ken Burns, 7 scene types
- `src/compositions/SEODocumentary.tsx` — Simpler chapter-card format

## Environment Variables

See `.env.example` for all required API keys (ElevenLabs, Anthropic, OpenAI, Gemini, Perplexity, Google/YouTube).
