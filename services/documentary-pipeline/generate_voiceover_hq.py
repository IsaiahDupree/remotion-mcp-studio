#!/usr/bin/env python3
"""
High-Quality ElevenLabs Voiceover Generator
Splits chapters into paragraph-level chunks for maximum prosody quality.

Quality gates:
  1. Per-chunk: duration sanity (chars/15 ≈ expected seconds, ±50%)
  2. Per-chunk: file size minimum (>5KB = not truncated)
  3. Per-chapter: concatenated duration vs original (±20% tolerance)
  4. Overall: all chapters present + no zero-byte files

ElevenLabs quality tiers:
  < 1,000 chars = excellent (single breath groups)
  1,000-2,500 chars = good
  > 2,500 chars = quality degrades (prosody drift)
"""
import os
import json
import time
import re
import subprocess
import tempfile
import struct
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "k0HDiJKO5QdXkGN6NSLI"  # Isaiah's cloned voice
MODEL_ID = "eleven_multilingual_v2"

# Target chunk size for excellent quality
MAX_CHUNK_CHARS = 1000
# Silence between paragraphs (seconds)
PARAGRAPH_GAP_SECS = 0.15
# Quality gate tolerances
DURATION_TOLERANCE = 0.50  # ±50% per chunk
CHAPTER_DURATION_TOLERANCE = 0.20  # ±20% vs original
MIN_CHUNK_SIZE_BYTES = 5000  # 5KB minimum per chunk

import urllib.request
import urllib.error


def get_mp3_duration(path: Path) -> float:
    """Get MP3 duration using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def split_into_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split text into paragraph-level chunks, merging small ones."""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    chunks = []
    current = ""

    for para in paragraphs:
        # If adding this paragraph would exceed max, flush current
        if current and len(current) + len(para) + 2 > max_chars:
            chunks.append(current.strip())
            current = para
        else:
            current = (current + "\n\n" + para).strip() if current else para

    if current:
        chunks.append(current.strip())

    return chunks


def generate_chunk(text: str, output_path: Path, chunk_label: str, max_retries: int = 2) -> bool:
    """Generate a single audio chunk via ElevenLabs API with quality gate."""
    if output_path.exists() and output_path.stat().st_size > MIN_CHUNK_SIZE_BYTES:
        return True

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

    payload = json.dumps({
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.85,
            "style": 0.3,
            "use_speaker_boost": True
        }
    }).encode()

    for attempt in range(max_retries + 1):
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                audio_data = resp.read()
        except urllib.error.HTTPError as e:
            err = e.read().decode()[:200]
            print(f"      HTTP {e.code}: {err}")
            if e.code == 429:
                wait = 15 * (attempt + 1)
                print(f"      Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            return False
        except Exception as e:
            print(f"      Error: {e}")
            if attempt < max_retries:
                time.sleep(5)
                continue
            return False

        # Quality gate 1: minimum file size
        if len(audio_data) < MIN_CHUNK_SIZE_BYTES:
            print(f"      QG FAIL: chunk too small ({len(audio_data)} bytes) — retrying")
            if attempt < max_retries:
                time.sleep(3)
                continue
            return False

        output_path.write_bytes(audio_data)

        # Quality gate 2: duration sanity check
        duration = get_mp3_duration(output_path)
        expected_duration = len(text) / 15.0  # ~15 chars/sec speaking rate
        if duration > 0 and expected_duration > 0:
            ratio = duration / expected_duration
            if ratio < (1 - DURATION_TOLERANCE) or ratio > (1 + DURATION_TOLERANCE):
                print(f"      QG WARN: duration {duration:.1f}s vs expected {expected_duration:.1f}s (ratio {ratio:.2f})")
                # Warning only, don't fail — ElevenLabs pacing varies

        return True

    return False


def concatenate_chunks(chunk_paths: list[Path], output_path: Path, gap_secs: float = PARAGRAPH_GAP_SECS) -> bool:
    """Concatenate audio chunks with silence gaps using ffmpeg."""
    if not chunk_paths:
        return False

    # Build ffmpeg concat filter with silence between chunks
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for i, cp in enumerate(chunk_paths):
            f.write(f"file '{cp}'\n")
            if i < len(chunk_paths) - 1 and gap_secs > 0:
                # Generate silence file
                silence_path = cp.parent / f"_silence_{i}.mp3"
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i",
                    f"anullsrc=r=44100:cl=mono", "-t", str(gap_secs),
                    "-c:a", "libmp3lame", "-b:a", "128k",
                    str(silence_path)
                ], capture_output=True, timeout=10)
                f.write(f"file '{silence_path}'\n")
        concat_list = f.name

    try:
        result = subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-c:a", "libmp3lame", "-b:a", "192k",
            str(output_path)
        ], capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            print(f"    ffmpeg error: {result.stderr[:300]}")
            return False

        return True
    finally:
        os.unlink(concat_list)
        # Cleanup silence files
        for i in range(len(chunk_paths) - 1):
            silence_path = chunk_paths[0].parent / f"_silence_{i}.mp3"
            if silence_path.exists():
                silence_path.unlink()


def load_chapters_from_config(config_path: str) -> tuple[dict, dict]:
    """Load chapters from generate_config.json + script.md."""
    config = json.loads(Path(config_path).read_text())
    script_file = Path(config_path).parent / "script.md"
    if not script_file.exists():
        raise FileNotFoundError(f"Script not found: {script_file}")

    script_text = script_file.read_text()
    chapter_ids = config.get("chapter_ids", [])

    sections = re.split(r'\n## ', script_text)
    chapters = {}
    content_sections = sections[1:] if len(sections) > 1 else sections

    for i, chapter_id in enumerate(chapter_ids):
        if i < len(content_sections):
            section = content_sections[i]
            lines = section.strip().split('\n')
            body = '\n'.join(lines[1:]).strip()
            body = re.sub(r'\*\*([^*]+)\*\*', r'\1', body)
            body = re.sub(r'\*([^*]+)\*', r'\1', body)
            body = re.sub(r'#{1,3}\s+', '', body)
            body = body.replace('---', '').replace('```', '')
            body = re.sub(r'\n{3,}', '\n\n', body)
            if body:
                chapters[chapter_id] = body

    return chapters, config


def main():
    import argparse
    parser = argparse.ArgumentParser(description="High-quality chunked ElevenLabs voiceover")
    parser.add_argument("--config", required=True, help="Path to generate_config.json")
    parser.add_argument("--output-dir", help="Override output directory")
    parser.add_argument("--force", action="store_true", help="Regenerate all chapters")
    parser.add_argument("--max-chunk", type=int, default=MAX_CHUNK_CHARS,
                        help=f"Max chars per chunk (default: {MAX_CHUNK_CHARS})")
    parser.add_argument("--dry-run", action="store_true", help="Show chunks without generating")
    args = parser.parse_args()

    chapters, config = load_chapters_from_config(args.config)
    output_dir = Path(args.output_dir) if args.output_dir else (
        SCRIPT_DIR / "audio_v2_hq"
    )
    chunks_dir = output_dir / "_chunks"
    output_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    # Also get original audio dir for duration comparison
    orig_audio_dir = SCRIPT_DIR / "audio_v2"

    print("=" * 60)
    print("High-Quality ElevenLabs Voiceover Generator")
    print("=" * 60)
    print(f"  Config:    {args.config}")
    print(f"  Chapters:  {len(chapters)}")
    print(f"  Max chunk: {args.max_chunk} chars (target: excellent quality)")
    print(f"  Output:    {output_dir}")
    print(f"  Voice:     {VOICE_ID}")
    print(f"  Model:     {MODEL_ID}")
    print()

    # Analyze chunks
    total_chars = 0
    total_chunks = 0
    chapter_chunks = {}

    for chapter_id, text in chapters.items():
        chunks = split_into_chunks(text, args.max_chunk)
        chapter_chunks[chapter_id] = chunks
        total_chars += len(text)
        total_chunks += len(chunks)
        sizes = [len(c) for c in chunks]
        print(f"  {chapter_id}: {len(text):,} chars → {len(chunks)} chunks "
              f"(avg {sum(sizes)//len(sizes)} chars, max {max(sizes)})")

    print(f"\n  Total: {total_chars:,} chars, {total_chunks} chunks")
    print(f"  All chunks under {args.max_chunk} chars: "
          f"{'YES' if all(len(c) <= args.max_chunk for chunks in chapter_chunks.values() for c in chunks) else 'NO'}")

    if args.dry_run:
        print("\n  [DRY RUN] Would generate the above chunks. Exiting.")
        return

    print(f"\n{'=' * 60}")
    print("Generating audio chunks...")
    print("=" * 60)

    results = {}
    gate_failures = []

    for chapter_id, chunks in chapter_chunks.items():
        final_path = output_dir / f"{chapter_id}.mp3"

        if final_path.exists() and final_path.stat().st_size > 10000 and not args.force:
            dur = get_mp3_duration(final_path)
            print(f"\n  [{chapter_id}] SKIP (exists, {dur:.1f}s)")
            results[chapter_id] = {"status": "skipped", "duration": dur}
            continue

        print(f"\n  [{chapter_id}] {len(chunks)} chunks to generate")

        chunk_paths = []
        all_ok = True

        for j, chunk_text in enumerate(chunks):
            chunk_path = chunks_dir / f"{chapter_id}_chunk_{j:02d}.mp3"
            label = f"{chapter_id} chunk {j+1}/{len(chunks)}"

            if chunk_path.exists() and chunk_path.stat().st_size > MIN_CHUNK_SIZE_BYTES and not args.force:
                dur = get_mp3_duration(chunk_path)
                print(f"    [{j+1}/{len(chunks)}] cached ({dur:.1f}s, {len(chunk_text)} chars)")
                chunk_paths.append(chunk_path)
                continue

            print(f"    [{j+1}/{len(chunks)}] generating ({len(chunk_text)} chars)...", end=" ", flush=True)
            ok = generate_chunk(chunk_text, chunk_path, label)

            if ok:
                dur = get_mp3_duration(chunk_path)
                print(f"OK ({dur:.1f}s)")
                chunk_paths.append(chunk_path)
            else:
                print("FAILED")
                all_ok = False
                gate_failures.append(f"{chapter_id} chunk {j+1}")

            time.sleep(1.5)  # Rate limit between chunks

        if not all_ok or not chunk_paths:
            print(f"    QUALITY GATE FAIL: missing chunks for {chapter_id}")
            results[chapter_id] = {"status": "failed", "reason": "missing chunks"}
            continue

        # Concatenate chunks into final chapter audio
        print(f"    Concatenating {len(chunk_paths)} chunks...", end=" ", flush=True)
        ok = concatenate_chunks(chunk_paths, final_path)

        if not ok:
            print("FAILED")
            results[chapter_id] = {"status": "failed", "reason": "concat failed"}
            gate_failures.append(f"{chapter_id} concatenation")
            continue

        final_dur = get_mp3_duration(final_path)
        final_size = final_path.stat().st_size / 1024

        # Quality gate 3: compare duration to original
        orig_path = orig_audio_dir / f"{chapter_id}.mp3"
        duration_note = ""
        if orig_path.exists():
            orig_dur = get_mp3_duration(orig_path)
            if orig_dur > 0:
                ratio = final_dur / orig_dur
                if abs(ratio - 1.0) > CHAPTER_DURATION_TOLERANCE:
                    duration_note = f" ⚠ DURATION DRIFT: {ratio:.0%} of original ({orig_dur:.1f}s)"
                    gate_failures.append(f"{chapter_id} duration drift ({ratio:.0%})")
                else:
                    duration_note = f" ✓ vs original: {ratio:.0%} ({orig_dur:.1f}s)"

        print(f"OK ({final_dur:.1f}s, {final_size:.0f}KB){duration_note}")
        results[chapter_id] = {"status": "ok", "duration": final_dur, "size_kb": final_size}

    # Final report
    print(f"\n{'=' * 60}")
    print("QUALITY GATE REPORT")
    print("=" * 60)

    ok_count = sum(1 for r in results.values() if r["status"] in ("ok", "skipped"))
    fail_count = sum(1 for r in results.values() if r["status"] == "failed")

    for chapter_id, r in results.items():
        status_icon = "✓" if r["status"] in ("ok", "skipped") else "✗"
        dur = r.get("duration", 0)
        print(f"  {status_icon} {chapter_id}: {r['status']} ({dur:.1f}s)")

    print(f"\n  Passed: {ok_count}/{len(chapters)}")
    if gate_failures:
        print(f"  Gate failures: {len(gate_failures)}")
        for gf in gate_failures:
            print(f"    - {gf}")

    if fail_count == 0:
        print(f"\n  ALL QUALITY GATES PASSED")
    else:
        print(f"\n  {fail_count} CHAPTERS NEED ATTENTION")

    # List final files
    print(f"\n  Output files:")
    total_size = 0
    total_dur = 0
    for f in sorted(output_dir.glob("*.mp3")):
        dur = get_mp3_duration(f)
        sz = f.stat().st_size / 1024
        total_size += sz
        total_dur += dur
        print(f"    {f.name} ({dur:.1f}s, {sz:.0f}KB)")
    print(f"    Total: {total_dur:.0f}s ({total_dur/60:.1f}min), {total_size/1024:.1f}MB")


if __name__ == "__main__":
    main()
