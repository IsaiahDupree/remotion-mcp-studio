#!/usr/bin/env python3
"""
Apply Whisper-synced scene timings to SEODocumentaryV2.tsx.
Replaces the scenes[] arrays with Whisper-timed cuts.

Usage:
    python3 apply_synced_scenes.py
"""

import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

SCENES_FILE     = SCRIPT_DIR / "scenes_synced.json")
COMPOSITION_V2  = SCRIPT_DIR / ".." / ".." / "src/compositions/SEODocumentaryV2.tsx")

CHAPTERS = [
    "00_intro", "01_wild_west", "02_pagerank", "03_algorithm_wars",
    "04_quality_revolution", "05_mobile_first", "06_trust_language",
    "07_experience_era", "08_ai_disruption", "09_geo_era", "10_future_outro"
]

# Existing curated key scenes per chapter (title card + key facts)
# These override the first few Whisper-generated scenes for better visual impact
CHAPTER_OPENERS = {
    "00_intro": [
        {"type": "title_card", "content": "The Complete History of SEO", "subContent": "From AltaVista to AI Overviews — 1991 to 2030"},
    ],
    "01_wild_west": [
        {"type": "title_card", "content": "The Wild West", "subContent": "Before Google, there was chaos."},
    ],
    "02_pagerank": [
        {"type": "title_card", "content": "The PageRank Revolution", "subContent": "Two Stanford students changed the internet forever."},
    ],
    "03_algorithm_wars": [
        {"type": "title_card", "content": "The Algorithm Wars", "subContent": "Black Hat vs. Google — the arms race begins."},
    ],
    "04_quality_revolution": [
        {"type": "title_card", "content": "The Quality Revolution", "subContent": "Panda. Penguin. The end of spam."},
    ],
    "05_mobile_first": [
        {"type": "title_card", "content": "Mobile First", "subContent": "The smartphone changes everything."},
    ],
    "06_trust_language": [
        {"type": "title_card", "content": "Trust & Language", "subContent": "RankBrain. BERT. AI starts reading."},
    ],
    "07_experience_era": [
        {"type": "title_card", "content": "The Experience Era", "subContent": "Core Web Vitals. UX becomes SEO."},
    ],
    "08_ai_disruption": [
        {"type": "title_card", "content": "AI Disruption", "subContent": "ChatGPT. Helpful Content. The rules rewrite."},
    ],
    "09_geo_era": [
        {"type": "title_card", "content": "The GEO Era", "subContent": "Generative Engine Optimization."},
    ],
    "10_future_outro": [
        {"type": "title_card", "content": "The Future of SEO", "subContent": "2026 – 2030: What comes next."},
    ],
}

SCENE_TYPE_CYCLE = [
    "title_card", "quote", "fact_reveal", "character",
    "quote", "timeline", "character", "quote", "fact_reveal", "character", "quote",
]


def scene_to_tsx(scene: dict, idx: int) -> str:
    """Convert a scene dict to TSX object literal."""
    t        = scene.get("type", "quote")
    dur      = scene.get("durationSecs", 3.5)
    content  = scene.get("content", "").replace("'", "\\'").replace('"', '\\"')
    sub      = scene.get("subContent", "").replace("'", "\\'").replace('"', '\\"')
    color    = scene.get("accentColor", "")

    parts = [
        f"type: '{t}'",
        f"durationSecs: {dur}",
        f"content: \"{content}\"",
    ]
    if sub:
        parts.append(f"subContent: \"{sub}\"")
    if color:
        parts.append(f"accentColor: '{color}'")

    return "        { " + ", ".join(parts) + " },"


def build_chapter_scenes_tsx(chapter_id: str, synced_data: dict) -> str:
    """Build the full scenes: [...] TSX block for a chapter."""
    scenes_list = synced_data.get("scenes", [])
    dur = synced_data.get("audioDurationSecs", 60)

    # Use opener as first scene, then flow into Whisper-timed scenes
    opener = CHAPTER_OPENERS.get(chapter_id, [])
    opener_dur = 4.0  # title card is 4 seconds

    # Skip whisper scenes that overlap with opener window
    remaining = [s for s in scenes_list if s.get("startSecs", 0) >= opener_dur]

    lines = ["      scenes: ["]

    # Opener(s) — curated title card
    for o in opener:
        o_scene = {**o, "durationSecs": opener_dur, "accentColor": scenes_list[0].get("accentColor", "") if scenes_list else ""}
        lines.append(scene_to_tsx(o_scene, 0))

    # Whisper-synced scenes (skip first N seconds covered by opener)
    for i, scene in enumerate(remaining):
        # Remap scene type from cycle for visual variety
        scene_copy = dict(scene)
        if scene_copy.get("type") == "title_card" and i > 0:
            scene_copy["type"] = SCENE_TYPE_CYCLE[(i + 1) % len(SCENE_TYPE_CYCLE)]
        lines.append(scene_to_tsx(scene_copy, i + len(opener)))

    lines.append("      ],")
    return "\n".join(lines)


def apply_to_composition(synced: dict):
    """Update SEODocumentaryV2.tsx scenes[] and audioDurationSecs for each chapter."""
    content = COMPOSITION_V2.read_text()

    for chapter_id in CHAPTERS:
        if chapter_id not in synced:
            print(f"  [SKIP] {chapter_id} — no synced data")
            continue

        data = synced[chapter_id]
        actual_dur = data.get("audioDurationSecs", 0)

        # Update audioDurationSecs
        content = re.sub(
            rf"(id: '{chapter_id}'.*?audioDurationSecs: )\d+",
            rf"\g<1>{round(actual_dur)}",
            content,
            flags=re.DOTALL,
            count=1
        )

        # Build new scenes block
        new_scenes_block = build_chapter_scenes_tsx(chapter_id, data)

        # Replace scenes: [ ... ], for this chapter
        # Find the chapter's scenes block by context
        # Pattern: after characterImageFile for this chapter, replace scenes: [...],
        pattern = (
            rf"(characterImageFile: 'seo_characters/{chapter_id}_character\.png',\s*"
            rf"audioDurationSecs: \d+,\s*)"
            rf"scenes: \[.*?\],"
        )
        replacement = r"\g<1>" + new_scenes_block.replace("\\", "\\\\")
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL, count=1)

        if new_content != content:
            content = new_content
            print(f"  ✓ {chapter_id}: {len(data['scenes'])} scenes, {actual_dur:.1f}s")
        else:
            print(f"  ✗ {chapter_id}: pattern not matched — scenes not updated")

    COMPOSITION_V2.write_text(content)
    print(f"\n  Updated: {COMPOSITION_V2}")


def main():
    if not SCENES_FILE.exists():
        print(f"ERROR: {SCENES_FILE} not found. Run transcribe_whisper.py + build_scene_timings.py first.")
        return

    synced = json.loads(SCENES_FILE.read_text())
    print(f"Applying synced timings for {len(synced)} chapters...")
    print()
    apply_to_composition(synced)
    print()
    print("Done. Re-render with:")
    print("  cd .")
    print("  npx remotion render SEODocumentaryV2 services/documentary-pipeline/output/seo_documentary_v3.mp4 --codec=h264 --concurrency=4")


if __name__ == "__main__":
    main()
