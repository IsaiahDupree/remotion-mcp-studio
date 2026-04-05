#!/usr/bin/env python3
"""
Whisper word-level transcription for all SEO documentary chapters.
Outputs JSON with word timestamps for scene sync.

Usage:
    python3 transcribe_whisper.py
    python3 transcribe_whisper.py --chapter 00_intro  # single chapter
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

SCRIPT_DIR = Path(__file__).parent
AUDIO_DIR  = SCRIPT_DIR / "audio"
TRANSCRIPT_DIR = SCRIPT_DIR / "transcripts"
TRANSCRIPT_DIR.mkdir(exist_ok=True)

CHAPTERS = [
    "00_intro", "01_wild_west", "02_pagerank", "03_algorithm_wars",
    "04_quality_revolution", "05_mobile_first", "06_trust_language",
    "07_experience_era", "08_ai_disruption", "09_geo_era", "10_future_outro"
]


def transcribe_chapter(chapter_id: str) -> dict:
    """Transcribe one chapter with word-level timestamps via Whisper API."""
    audio_path = AUDIO_DIR / f"{chapter_id}.mp3"
    output_path = TRANSCRIPT_DIR / f"{chapter_id}.json"

    if output_path.exists():
        print(f"  [SKIP] {chapter_id} — already transcribed")
        return json.loads(output_path.read_text())

    print(f"  Transcribing {chapter_id} ({audio_path.stat().st_size // 1024}KB)...")

    # Build multipart/form-data manually
    boundary = "----FormBoundary" + str(int(time.time() * 1000))

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    def encode_field(name, value):
        return (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        ).encode()

    def encode_file(name, filename, data, content_type):
        header = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
        return header + data + b"\r\n"

    body = (
        encode_field("model", "whisper-1") +
        encode_field("response_format", "verbose_json") +
        encode_field("timestamp_granularities[]", "word") +
        encode_field("timestamp_granularities[]", "segment") +
        encode_field("language", "en") +
        encode_file("file", f"{chapter_id}.mp3", audio_data, "audio/mpeg") +
        f"--{boundary}--\r\n".encode()
    )

    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions",
        data=body,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read())
            output_path.write_text(json.dumps(result, indent=2))
            words = result.get("words", [])
            duration = result.get("duration", 0)
            print(f"    ✓ {chapter_id}: {len(words)} words, {duration:.1f}s")
            return result
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:300]
        print(f"    ✗ {chapter_id} failed: {err}")
        return {}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Whisper transcription")
    parser.add_argument("--chapter", help="Single chapter ID to transcribe")
    parser.add_argument("--config", help="Path to generate_config.json for custom chapter list")
    parser.add_argument("--audio-dir", help="Override audio directory")
    parser.add_argument("--transcript-dir", help="Override transcript output directory")
    args = parser.parse_args()

    global AUDIO_DIR, TRANSCRIPT_DIR

    chapters = CHAPTERS
    if args.config:
        config = json.loads(Path(args.config).read_text())
        chapters = config.get("chapter_ids", CHAPTERS)
        if not args.audio_dir:
            AUDIO_DIR = Path(config.get("audio_dir", str(AUDIO_DIR)))
    if args.chapter:
        chapters = [args.chapter]
    if args.audio_dir:
        AUDIO_DIR = Path(args.audio_dir)
    if args.transcript_dir:
        TRANSCRIPT_DIR = Path(args.transcript_dir)
        TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Transcribing {len(chapters)} chapter(s) with Whisper word-level timestamps...")
    print(f"Audio: {AUDIO_DIR}")
    print(f"Output: {TRANSCRIPT_DIR}")
    print()

    results = {}
    for ch in chapters:
        results[ch] = transcribe_chapter(ch)

    print()
    print(f"Done. Transcripts in {TRANSCRIPT_DIR}/")
    done = list(TRANSCRIPT_DIR.glob("*.json"))
    print(f"{len(done)} chapters transcribed.")


if __name__ == "__main__":
    main()
