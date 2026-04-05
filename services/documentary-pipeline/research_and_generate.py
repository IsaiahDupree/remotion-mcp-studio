#!/usr/bin/env python3
"""
Research & Generate — One-shot documentary config + script generator.

Takes a topic string and produces a complete generate_config.json + script.md
for ANY documentary topic using the Anthropic Claude API.

Usage:
    python3 research_and_generate.py --topic "The History of AI: From Turing to GPT"
    python3 research_and_generate.py --topic "The Rise of Electric Cars" --chapters 8
    python3 research_and_generate.py --topic "How the Internet Was Built" --narrator-style dramatic
    python3 research_and_generate.py --topic "Quantum Computing" --dry-run

Output: research/{topic_slug}/
    ├── generate_config.json   # Full pipeline config
    └── script.md              # Narration script
"""

import argparse
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

PROJECT_DIR = Path(str(SCRIPT_DIR))
RESEARCH_DIR = PROJECT_DIR / "research"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Try to load from Remotion .env.local if not in environment
if not OPENAI_API_KEY:
    _env_path = Path.home() / "Documents/Software/Remotion/.env.local"
    if _env_path.exists():
        for line in _env_path.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                OPENAI_API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

# Colors for chapter accent theming
CHAPTER_COLORS = [
    "#00ff88", "#ff6b35", "#4285f4", "#ea4335", "#fbbc04",
    "#34a853", "#9c27b0", "#00bcd4", "#ff4081", "#ff9800",
    "#00ff88", "#e91e63", "#3f51b5", "#009688", "#ff5722",
]

NARRATOR_STYLE_PROMPTS = {
    "documentary": (
        "You are an award-winning documentary scriptwriter. "
        "Your narration is factual, engaging, and cinematic. "
        "You write like the narrator of a Netflix/HBO documentary — "
        "authoritative but accessible, dramatic but honest. "
        "Every sentence should make the viewer want to hear the next one."
    ),
    "educational": (
        "You are a world-class educational content writer. "
        "Your narration is clear, informative, and engaging. "
        "You explain complex topics simply without dumbing them down. "
        "Think Kurzgesagt or Veritasium — visual, precise, wonder-inducing."
    ),
    "dramatic": (
        "You are a dramatic storyteller crafting a gripping narrative. "
        "Your narration builds tension, uses cliffhangers, and creates emotional peaks. "
        "Think true-crime documentary meets historical epic. "
        "Every chapter ends with a revelation that demands the next."
    ),
}


def slug(text: str) -> str:
    """Convert text to a URL/filename-safe slug."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:80]


def call_openai(prompt: str, system: str = "", max_tokens: int = 8000) -> str:
    """Call the OpenAI API using urllib (no SDK dependency)."""
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not available.", file=sys.stderr)
        sys.exit(1)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": "gpt-4o",
        "max_tokens": max_tokens,
        "messages": messages,
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    ctx = ssl.create_default_context()

    try:
        with urllib.request.urlopen(req, timeout=180, context=ctx) as resp:
            result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: OpenAI API returned HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: OpenAI API call failed: {e}", file=sys.stderr)
        sys.exit(1)


def call_claude(prompt: str, system: str = "", max_tokens: int = 8000) -> str:
    """Call Anthropic Claude API, falling back to OpenAI if no Anthropic key."""
    if not ANTHROPIC_API_KEY:
        if OPENAI_API_KEY:
            print("  (Using OpenAI GPT-4o — ANTHROPIC_API_KEY not set)")
            return call_openai(prompt, system, max_tokens)
        print("ERROR: Neither ANTHROPIC_API_KEY nor OPENAI_API_KEY is available.", file=sys.stderr)
        sys.exit(1)

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        payload["system"] = system

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )

    # Create SSL context for macOS compatibility
    ctx = ssl.create_default_context()

    try:
        with urllib.request.urlopen(req, timeout=180, context=ctx) as resp:
            result = json.loads(resp.read())
        return result["content"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: Claude API returned HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Claude API call failed: {e}", file=sys.stderr)
        sys.exit(1)


def extract_json(text: str) -> dict:
    """Extract a JSON object from Claude's response text."""
    # Try to find JSON block in markdown code fence first
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Fall back to finding the outermost { ... }
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract JSON from response. First 500 chars:\n{text[:500]}")


def generate_config_and_script(
    topic: str,
    num_chapters: int,
    narrator_style: str,
    output_dir: Path,
) -> tuple[dict, str]:
    """
    Generate both generate_config.json and script.md in two Claude calls.

    Call 1: generate_config.json (structured metadata)
    Call 2: script.md (narration text, chapter by chapter)
    """

    topic_slug = slug(topic)
    narrator_system = NARRATOR_STYLE_PROMPTS.get(narrator_style, NARRATOR_STYLE_PROMPTS["documentary"])

    # ── Call 1: Generate config ──────────────────────────────────────────────

    print("\n[1/2] Generating documentary config (chapters, metadata, visual styles)...")

    config_system = (
        "You are a documentary production planner. You create structured metadata "
        "for documentary video pipelines. You are precise with historical facts, dates, "
        "and visual descriptions. Return ONLY valid JSON, no other text."
    )

    config_prompt = f"""Create a complete documentary production config for the topic:

"{topic}"

Requirements:
- Generate exactly {num_chapters} chapters
- Each chapter covers a distinct era, theme, or turning point
- Chronological or thematic flow: first chapter = intro/hook, last = conclusion/future
- Chapter IDs follow the pattern: 01_slug, 02_slug, etc.
- Include rich visual style metadata that an AI image generator can use directly

Return ONLY this JSON structure (no markdown, no commentary):
{{
  "topic": "{topic}",
  "title": "A compelling documentary title (short, punchy)",
  "chapter_ids": ["01_intro", "02_slug", ...],
  "chapter_meta": {{
    "01_intro": {{
      "title": "Chapter Title",
      "era": "Time period or year range",
      "color": "#hex accent color",
      "tone": "dramatic | reflective | urgent | hopeful | suspenseful",
      "surprising_fact": "A specific, verifiable fact that would make someone stop scrolling",
      "image_style_hints": [
        "Visual description 1 for this chapter's key moment",
        "Visual description 2 for another key scene",
        "Visual description 3 for atmosphere/setting"
      ],
      "visual_style": {{
        "camera": "e.g. wide establishing shot, close-up portrait, aerial drone, tracking shot",
        "lighting": "e.g. golden hour, harsh fluorescent, candlelit, neon-lit, overcast",
        "film": "e.g. 35mm grain, clean digital, vintage 8mm, IMAX clarity, desaturated",
        "env": "e.g. university lab 1950s, Silicon Valley garage, server room, lecture hall",
        "palette": "e.g. warm amber and brown, cold blue and steel, vibrant neon, muted earth tones"
      }}
    }}
  }},
  "youtube_meta": {{
    "title": "YouTube video title (SEO-optimized, under 70 chars)",
    "description": "YouTube description (2-3 paragraphs, include keywords, call to action)",
    "tags": ["tag1", "tag2", "tag3", ...up to 15 tags],
    "category_id": "27",
    "chapters_timestamps": [
      {{"time": "0:00", "label": "Introduction"}},
      {{"time": "2:30", "label": "Chapter 2 Title"}},
      ...one per chapter, estimated ~2:30 apart
    ]
  }}
}}

Use these accent colors in order for chapters: {json.dumps(CHAPTER_COLORS[:num_chapters])}

IMPORTANT: Return ONLY the JSON object. No markdown fences, no explanation."""

    config_raw = call_claude(config_prompt, system=config_system, max_tokens=6000)
    config = extract_json(config_raw)

    # Validate and fix chapter structure
    chapter_ids = config.get("chapter_ids", [])
    chapter_meta = config.get("chapter_meta", {})

    if len(chapter_ids) < num_chapters:
        print(f"  Warning: Got {len(chapter_ids)} chapters instead of {num_chapters}, using what we got.")

    # Ensure all chapter_ids have matching meta entries
    for cid in chapter_ids:
        if cid not in chapter_meta:
            print(f"  Warning: Missing meta for chapter '{cid}', adding placeholder.")
            chapter_meta[cid] = {
                "title": cid.replace("_", " ").title(),
                "era": "",
                "color": CHAPTER_COLORS[chapter_ids.index(cid) % len(CHAPTER_COLORS)],
                "tone": "documentary",
                "surprising_fact": "",
                "image_style_hints": [],
                "visual_style": {
                    "camera": "medium shot",
                    "lighting": "natural",
                    "film": "clean digital",
                    "env": "modern setting",
                    "palette": "neutral tones",
                },
            }

    # Ensure visual_style fields exist in every chapter
    for cid, meta in chapter_meta.items():
        if "visual_style" not in meta:
            meta["visual_style"] = {
                "camera": "medium shot",
                "lighting": "natural",
                "film": "clean digital",
                "env": "contextual setting",
                "palette": "neutral tones",
            }
        else:
            for field in ("camera", "lighting", "film", "env", "palette"):
                if field not in meta["visual_style"]:
                    meta["visual_style"][field] = ""

    # Add pipeline paths and steps
    config["script_file"] = str(output_dir / "script.md")
    config["audio_dir"] = str(PROJECT_DIR / "audio")
    config["characters_dir"] = str(PROJECT_DIR / "characters")
    config["scene_images_dir"] = str(PROJECT_DIR / "scene_images")
    config["output_dir"] = str(PROJECT_DIR / "output")
    config["pipeline_steps"] = [
        {"step": 1, "script": "generate_voiceover.py", "desc": "Generate ElevenLabs narration"},
        {"step": 2, "script": "voice_qa_gate.py", "desc": "Voice artifact quality gate"},
        {"step": 3, "script": "transcribe_whisper.py", "desc": "Whisper word-level transcription"},
        {"step": 4, "script": "generate_characters.py", "desc": "Generate character images"},
        {"step": 5, "script": "build_scene_timings.py", "desc": "Build scene cut points"},
        {"step": 6, "script": "generate_render_props.py", "desc": "Build render props JSON"},
        {"step": 7, "script": "generate_scene_images.py", "desc": "Generate scene concept art"},
        {"step": 8, "script": "generate_all_scene_images.py", "desc": "Per-scene image generation"},
        {"step": 9, "script": "test_documentary.py", "desc": "Full pipeline validation"},
        {"step": 10, "script": "render_and_upload.sh", "desc": "Remotion render + YouTube upload"},
        {"step": 11, "script": "video_optimize_loop/optimize.py", "desc": "Retention optimization loop"},
    ]

    print(f"  Config generated: {len(chapter_ids)} chapters")
    for cid in chapter_ids:
        meta = chapter_meta.get(cid, {})
        print(f"    {cid}: {meta.get('title', '?')} ({meta.get('era', '?')})")

    # ── Call 2: Generate script ──────────────────────────────────────────────

    print(f"\n[2/2] Writing narration script ({narrator_style} style)...")

    # Build chapter list for the prompt
    chapters_desc = []
    for cid in chapter_ids:
        meta = chapter_meta.get(cid, {})
        chapters_desc.append(
            f"## {meta.get('title', cid)}\n"
            f"- Era: {meta.get('era', 'N/A')}\n"
            f"- Tone: {meta.get('tone', 'documentary')}\n"
            f"- Surprising fact to weave in: {meta.get('surprising_fact', 'N/A')}\n"
            f"- Key visuals: {', '.join(meta.get('image_style_hints', []))}\n"
        )

    script_prompt = f"""Write the complete narration script for a documentary titled:
"{config.get('title', topic)}"

Topic: {topic}

The documentary has {len(chapter_ids)} chapters. Write narration for EACH chapter.

CHAPTER STRUCTURE:
{"".join(chapters_desc)}

Requirements for EACH chapter:
- Write 300-500 words of narration text
- Start each chapter with a hook that grabs attention immediately
- Include at least 3 specific facts: exact dates, full names, real statistics
- Weave in the surprising fact naturally as a revelation moment
- Use vivid, cinematic language — paint pictures with words
- Use second person where powerful: "Imagine...", "Think about that..."
- End each chapter with a transition that creates anticipation for the next
- The final chapter should end with a powerful, memorable closing statement
- NO stage directions, NO [brackets], NO metadata — ONLY narration text

Format the output as markdown:
# {config.get('title', topic)}

## Chapter 1 Title

Narration text here...

## Chapter 2 Title

Narration text here...

(continue for all {len(chapter_ids)} chapters)

Write ONLY the narration markdown. No preamble, no commentary after."""

    script = call_claude(
        script_prompt,
        system=narrator_system,
        max_tokens=max(4000, num_chapters * 800),
    )

    # Clean up: ensure it starts with a markdown heading
    script = script.strip()
    if not script.startswith("#"):
        script = f"# {config.get('title', topic)}\n\n{script}"

    word_count = len(script.split())
    est_minutes = word_count / 150
    print(f"  Script written: {word_count} words (~{est_minutes:.0f} minutes of narration)")

    return config, script


def show_dry_run(topic: str, num_chapters: int, narrator_style: str, output_dir: Path) -> None:
    """Show what would be generated without calling the API."""
    topic_slug = slug(topic)

    print("\n" + "=" * 60)
    print("  DRY RUN — No API calls will be made")
    print("=" * 60)
    print(f"\n  Topic:          {topic}")
    print(f"  Slug:           {topic_slug}")
    print(f"  Chapters:       {num_chapters}")
    print(f"  Narrator style: {narrator_style}")
    print(f"  Output dir:     {output_dir}/")
    print(f"\n  Files that would be created:")
    print(f"    {output_dir}/generate_config.json")
    print(f"    {output_dir}/script.md")
    print(f"\n  generate_config.json would contain:")
    print(f"    - topic, title")
    print(f"    - chapter_ids: [{num_chapters} chapter IDs]")
    print(f"    - chapter_meta: {num_chapters} entries, each with:")
    print(f"        title, era, color, tone, surprising_fact,")
    print(f"        image_style_hints, visual_style (camera/lighting/film/env/palette)")
    print(f"    - youtube_meta: title, description, tags, category_id, chapters_timestamps")
    print(f"    - pipeline paths + 11 pipeline steps")
    print(f"\n  script.md would contain:")
    print(f"    - {num_chapters} chapters of narration")
    print(f"    - ~{num_chapters * 400} words estimated ({num_chapters * 400 / 150:.0f} min)")
    print(f"    - Style: {narrator_style}")
    print(f"\n  Narrator style prompt:")
    print(f"    {NARRATOR_STYLE_PROMPTS.get(narrator_style, 'custom')[:100]}...")
    print(f"\n  API: Anthropic Claude (claude-sonnet-4-20250514)")
    print(f"  API calls: 2 (1 for config, 1 for script)")

    api_key_set = bool(os.getenv("ANTHROPIC_API_KEY"))
    print(f"  ANTHROPIC_API_KEY: {'set' if api_key_set else 'NOT SET (required)'}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Generate documentary config + script for any topic using Claude API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 research_and_generate.py --topic "The History of AI: From Turing to GPT"
  python3 research_and_generate.py --topic "The Rise of Electric Cars" --chapters 8
  python3 research_and_generate.py --topic "Quantum Computing" --narrator-style educational
  python3 research_and_generate.py --topic "The Space Race" --dry-run
        """,
    )
    parser.add_argument("--topic", required=True, help="Documentary topic string")
    parser.add_argument("--chapters", type=int, default=10, help="Number of chapters (default: 10)")
    parser.add_argument(
        "--narrator-style",
        choices=["documentary", "educational", "dramatic"],
        default="documentary",
        help="Narration tone/style (default: documentary)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show plan without calling API")
    args = parser.parse_args()

    topic_slug = slug(args.topic)
    output_dir = RESEARCH_DIR / topic_slug
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        show_dry_run(args.topic, args.chapters, args.narrator_style, output_dir)
        return

    print("=" * 60)
    print("  Documentary Research & Generate")
    print(f"  Topic:    {args.topic}")
    print(f"  Chapters: {args.chapters}")
    print(f"  Style:    {args.narrator_style}")
    print(f"  Output:   {output_dir}/")
    print("=" * 60)

    config, script = generate_config_and_script(
        topic=args.topic,
        num_chapters=args.chapters,
        narrator_style=args.narrator_style,
        output_dir=output_dir,
    )

    # Save files
    config_path = output_dir / "generate_config.json"
    script_path = output_dir / "script.md"

    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))
    script_path.write_text(script, encoding="utf-8")

    # Summary
    word_count = len(script.split())
    est_minutes = word_count / 150
    chapter_count = len(config.get("chapter_ids", []))

    print(f"\n{'=' * 60}")
    print(f"  Generation complete!")
    print(f"  Title:    {config.get('title', args.topic)}")
    print(f"  Chapters: {chapter_count}")
    print(f"  Script:   {word_count} words (~{est_minutes:.0f} min)")
    print(f"\n  Generated files:")
    print(f"    {config_path}")
    print(f"    {script_path}")
    print(f"\n  Next steps:")
    print(f"    1. Review script:  cat {script_path}")
    print(f"    2. Generate audio: python3 generate_voiceover.py --config {config_path}")
    print(f"    3. QA gate:        python3 voice_qa_gate.py --auto-fix")
    print(f"    4. Run pipeline:   bash render_and_upload.sh")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
