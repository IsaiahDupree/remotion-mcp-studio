#!/usr/bin/env python3
"""
Build Whisper-synced scene timings for SEO Documentary V2.

Reads word-level Whisper transcripts → finds natural sentence/phrase
boundaries → generates scene cut points (2.5–5s) aligned to speech pauses.

Output: scenes_synced.json — scene config per chapter with real timestamps.

Usage:
    python3 build_scene_timings.py
"""

import json
import re
from pathlib import Path

TRANSCRIPT_DIR = SCRIPT_DIR / "transcripts")
OUTPUT_FILE    = SCRIPT_DIR / "scenes_synced.json")

CHAPTERS = [
    "00_intro", "01_wild_west", "02_pagerank", "03_algorithm_wars",
    "04_quality_revolution", "05_mobile_first", "06_trust_language",
    "07_experience_era", "08_ai_disruption", "09_geo_era", "10_future_outro"
]

# Scene types cycle in order, repeating to fill chapter
SCENE_TYPE_CYCLE = [
    "title_card", "quote", "fact_reveal", "character",
    "quote", "timeline", "character", "quote", "fact_reveal",
]

MIN_SCENE_SECS = 2.5
MAX_SCENE_SECS = 5.0

# Sentence-ending punctuation patterns
SENTENCE_END = re.compile(r'[.!?]$')
CLAUSE_END   = re.compile(r'[,;:]$')


def find_cut_points(words: list, total_duration: float) -> list[float]:
    """
    Find natural cut points from word timestamps.
    Rules:
    1. Cut at sentence-ending words (period, !, ?) if 2.5–5s since last cut
    2. Cut at clause-ending words (comma, ;) if >3s since last cut
    3. Cut at natural pauses (gap > 0.3s between words) if >2.5s since last cut
    4. Force cut if > 5s since last cut
    Returns list of cut timestamps (start of each scene).
    """
    if not words:
        # No words — evenly space cuts every 3.5s
        cuts = []
        t = 0.0
        while t < total_duration:
            cuts.append(round(t, 3))
            t += 3.5
        return cuts

    cuts = [0.0]
    last_cut = 0.0

    for i, word in enumerate(words):
        t = word.get("start", 0)
        since_last = t - last_cut
        word_text = word.get("word", "").strip()

        # Gap detection: pause between this word end and next word start
        gap = 0.0
        if i < len(words) - 1:
            gap = words[i + 1].get("start", t) - word.get("end", t)

        is_sentence_end = bool(SENTENCE_END.search(word_text))
        is_clause_end   = bool(CLAUSE_END.search(word_text))

        should_cut = False

        if since_last >= MAX_SCENE_SECS:
            # Force cut — never let a scene go > 5s
            should_cut = True
        elif since_last >= MIN_SCENE_SECS:
            if is_sentence_end:
                should_cut = True
            elif is_clause_end and since_last >= 3.0:
                should_cut = True
            elif gap >= 0.3 and since_last >= 2.5:
                # Natural pause
                should_cut = True

        if should_cut:
            cut_time = word.get("end", t)
            cuts.append(round(cut_time, 3))
            last_cut = cut_time

    return cuts


def cuts_to_scenes(cuts: list[float], total_duration: float, chapter_id: str,
                   segments: list, chapter_color: str) -> list[dict]:
    """Convert cut points to scene dicts with type/content/duration."""
    scenes = []
    scene_type_idx = 0

    # Build a quick text lookup: for each scene window, grab the narration text
    def get_text_for_window(start: float, end: float) -> str:
        relevant = [
            s.get("text", "").strip()
            for s in segments
            if s.get("start", 0) < end and s.get("end", 0) > start
        ]
        text = " ".join(relevant).strip()
        # Truncate to reasonable length for display
        if len(text) > 120:
            text = text[:117] + "..."
        return text

    for i, cut_start in enumerate(cuts):
        cut_end = cuts[i + 1] if i + 1 < len(cuts) else total_duration
        duration_secs = round(cut_end - cut_start, 3)

        # Clamp duration
        duration_secs = max(MIN_SCENE_SECS, min(MAX_SCENE_SECS, duration_secs))

        scene_type = SCENE_TYPE_CYCLE[scene_type_idx % len(SCENE_TYPE_CYCLE)]
        scene_type_idx += 1

        # Get narration text for this window
        content = get_text_for_window(cut_start, cut_end)

        scene = {
            "type": scene_type,
            "durationSecs": duration_secs,
            "startSecs": cut_start,
            "endSecs": cut_end,
            "content": content,
            "subContent": "",
            "accentColor": chapter_color,
        }

        scenes.append(scene)

    return scenes


# Chapter colors matching V2
CHAPTER_COLORS = {
    "00_intro":             "#00ff88",
    "01_wild_west":         "#ff6b35",
    "02_pagerank":          "#4285f4",
    "03_algorithm_wars":    "#ea4335",
    "04_quality_revolution":"#fbbc04",
    "05_mobile_first":      "#34a853",
    "06_trust_language":    "#9c27b0",
    "07_experience_era":    "#00bcd4",
    "08_ai_disruption":     "#ff4081",
    "09_geo_era":           "#ff9800",
    "10_future_outro":      "#00ff88",
}


def process_chapter(chapter_id: str) -> dict | None:
    transcript_path = TRANSCRIPT_DIR / f"{chapter_id}.json"
    if not transcript_path.exists():
        print(f"  [MISSING] {chapter_id} — no transcript yet")
        return None

    data = json.loads(transcript_path.read_text())
    words    = data.get("words", [])
    segments = data.get("segments", [])
    duration = data.get("duration", 0)

    if not duration and words:
        duration = words[-1].get("end", 0) + 0.5

    cuts = find_cut_points(words, duration)
    scenes = cuts_to_scenes(cuts, duration, chapter_id, segments, CHAPTER_COLORS[chapter_id])

    print(f"  {chapter_id}: {len(scenes)} scenes, {duration:.1f}s ({duration/60:.1f}min)")

    return {
        "id": chapter_id,
        "audioDurationSecs": round(duration, 1),
        "sceneCount": len(scenes),
        "scenes": scenes,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build scene timings from Whisper transcripts")
    parser.add_argument("--config", help="Path to generate_config.json for custom chapters")
    parser.add_argument("--transcript-dir", help="Override transcript directory")
    parser.add_argument("--output", help="Override output file path")
    args = parser.parse_args()

    global TRANSCRIPT_DIR, OUTPUT_FILE, CHAPTER_COLORS

    chapters = CHAPTERS
    if args.config:
        config = json.loads(Path(args.config).read_text())
        chapters = config.get("chapter_ids", CHAPTERS)
        meta = config.get("chapter_meta", {})
        # Build colors from config meta
        for cid in chapters:
            if cid in meta and cid not in CHAPTER_COLORS:
                CHAPTER_COLORS[cid] = meta[cid].get("color", "#00ff88")
    if args.transcript_dir:
        TRANSCRIPT_DIR = Path(args.transcript_dir)
    if args.output:
        OUTPUT_FILE = Path(args.output)

    print("Building Whisper-synced scene timings...")
    print()

    results = {}
    for ch in chapters:
        if ch not in CHAPTER_COLORS:
            CHAPTER_COLORS[ch] = "#00ff88"  # Default color
        result = process_chapter(ch)
        if result:
            results[ch] = result

    OUTPUT_FILE.write_text(json.dumps(results, indent=2))
    print()
    print(f"Written: {OUTPUT_FILE}")
    print(f"Chapters processed: {len(results)}/{len(chapters)}")

    if results:
        total_scenes = sum(r["sceneCount"] for r in results.values())
        total_secs   = sum(r["audioDurationSecs"] for r in results.values())
        print(f"Total scenes: {total_scenes} across {total_secs/60:.1f} minutes")
        avg_scene = total_secs / total_scenes if total_scenes else 0
        print(f"Avg scene duration: {avg_scene:.1f}s")


if __name__ == "__main__":
    main()
