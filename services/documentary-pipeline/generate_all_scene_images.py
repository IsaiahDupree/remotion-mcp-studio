#!/usr/bin/env python3
"""
Generate a unique cinematic image for EVERY scene in the documentary.
Uses narrative prompt engineering based on top Nano Banana research:
- awesome-nano-banana-pro-prompts (9.9K stars)
- gemini-image-prompting-handbook (JSON schema approach)
- Video_Agent_v2 (8-field shot recipe)
- Max Woolf's gemimg findings (Markdown + "award-winning" measurably improves)

Output: scene_images/{chapter_id}_scene_{index:03d}.png
"""

import os
import base64
import json
import time
import argparse
from pathlib import Path

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PROPS_FILE   = SCRIPT_DIR / "render_props_v3.json")
OUTPUT_DIR   = SCRIPT_DIR / "scene_images")
REMOTION_DIR = SCRIPT_DIR / ".." / ".." / "public/seo_scene_images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REMOTION_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "gemini-2.5-flash-image"

# Fallback for any chapter without a visual_style in config or hardcoded recipes
DEFAULT_RECIPE = {
    "camera": "35mm anamorphic lens, shallow depth of field",
    "lighting": "dramatic cinematic side lighting with warm key and cool fill",
    "film": "modern digital cinema, clean rendering",
    "env": "abstract documentary setting",
    "palette": "dark moody tones with selective color accents",
}

# Legacy hardcoded recipes for backwards compatibility (used when --config is not provided)
_HARDCODED_ERA_RECIPES = {
    "01_intro": {
        "camera": "35mm anamorphic lens, shallow depth of field",
        "lighting": "dramatic volumetric lighting with neon blue and green accents cutting through digital particles",
        "film": "modern digital cinema, clean sharp rendering",
        "env": "futuristic command center with holographic search interfaces and floating data streams",
        "palette": "#00ff88 green and #4285f4 blue neon highlights against deep blacks",
    },
    "02_origins": {
        "camera": "85mm f/1.4 portrait lens, soft bokeh background",
        "lighting": "warm tungsten bulb lighting from overhead desk lamp, CRT monitor phosphor glow on faces",
        "film": "Kodak Portra 400, warm nostalgic grain, slightly desaturated",
        "env": "cramped 1990s office cubicle with beige CRT monitors, floppy disks, dial-up modems, stacked tech manuals",
        "palette": "warm amber #D4A574, cool CRT green #33CC33, beige #C4B09C",
    },
    "03_breakthroughs": {
        "camera": "wide-angle 24mm lens from low angle, dramatic perspective",
        "lighting": "golden hour sunlight streaming through campus windows, warm academic glow",
        "film": "Kodachrome, rich saturated colors with golden warmth",
        "env": "Stanford-style campus computer lab transitioning to early Google-era garage office, whiteboards with network diagrams",
        "palette": "#4285f4 Google blue, warm golden #FFD700, Stanford red #8C1515",
    },
    "04_experts": {
        "camera": "50mm lens, classic documentary framing, rule of thirds",
        "lighting": "professional three-point softbox setup, clean key light with subtle fill",
        "film": "modern digital cinema, clean and sharp",
        "env": "modern studio interview setting with subtle tech displays, professional and authoritative",
        "palette": "#ea4335 red accents, warm neutral backgrounds, professional tones",
    },
    "05_evolution": {
        "camera": "35mm lens, dynamic handheld documentary feel",
        "lighting": "mixed natural and artificial, transitioning from warm indoor to cool blue screen glow",
        "film": "digital cinema with slight grain, evolving color temperature",
        "env": "timeline of evolving workspaces — from desktop offices to mobile-first open-plan tech hubs",
        "palette": "#fbbc04 golden evolution, transitioning blues and greens",
    },
    "06_current_affairs": {
        "camera": "anamorphic 40mm, slight lens flare, urgent documentary feel",
        "lighting": "harsh overhead fluorescents mixed with urgent red warning indicators, breaking-news energy",
        "film": "modern digital, high contrast, news-room sharpness",
        "env": "data war room with multiple screens showing traffic graphs crashing, urgent atmosphere",
        "palette": "#34a853 green dashboards, #ea4335 red warnings, high contrast",
    },
    "07_future_speculation": {
        "camera": "wide 24mm anamorphic, epic establishing shots",
        "lighting": "ethereal purple and blue atmospheric glow, dawn-light optimism",
        "film": "sci-fi cinema, clean with subtle chromatic aberration",
        "env": "futuristic cityscape with holographic AR overlays, next-generation search interfaces",
        "palette": "#9c27b0 deep purple, #E040FB bright magenta, celestial blue #7B68EE",
    },
    "08_local_seo": {
        "camera": "35mm street photography lens, authentic documentary",
        "lighting": "natural storefront lighting, golden hour on main street, warm and inviting",
        "film": "Kodak Portra 400, warm skin tones, organic grain",
        "env": "vibrant local business district with Google Maps pins, storefronts with reviews visible, real community",
        "palette": "#00bcd4 cyan maps, warm #FF8C00 storefronts, natural greens",
    },
    "09_schema_and_programmatic": {
        "camera": "macro 100mm for code detail, pulling back to 35mm for context",
        "lighting": "cool blue monitor glow in dark room, matrix-style code reflections on surfaces",
        "film": "digital cinema, ultra-sharp, technical precision",
        "env": "developer workspace with structured data visualizations, schema markup floating as 3D holographic JSON trees",
        "palette": "#ff4081 hot pink accents, #00E5FF cyan code, deep navy #0D1B2A",
    },
    "10_conclusion": {
        "camera": "wide 24mm anamorphic, sweeping horizon shot",
        "lighting": "warm golden sunrise from the horizon, hopeful volumetric rays, lens flare",
        "film": "Kodachrome warmth, rich and optimistic",
        "env": "figure standing at the edge of a digital horizon where the old internet meets the new, roads stretching forward",
        "palette": "#ff9800 warm orange sunrise, #00ff88 hopeful green, golden #FFD700",
    },
}

# Active ERA_RECIPES — starts as hardcoded, overwritten by build_era_recipes_from_config()
ERA_RECIPES = dict(_HARDCODED_ERA_RECIPES)


def build_era_recipes_from_config(config_path: str) -> dict:
    """
    Build ERA_RECIPES dynamically from generate_config.json.

    Reads chapter_meta[chapter_id].visual_style fields (camera, lighting, film, env, palette).
    Chapters without a visual_style fall back to DEFAULT_RECIPE.
    """
    config = json.loads(Path(config_path).read_text())
    chapter_meta = config.get("chapter_meta", {})
    recipes = {}

    for chapter_id, meta in chapter_meta.items():
        vs = meta.get("visual_style")
        if vs and isinstance(vs, dict):
            recipe = dict(DEFAULT_RECIPE)  # start from defaults
            for key in ("camera", "lighting", "film", "env", "palette"):
                if key in vs:
                    recipe[key] = vs[key]
            recipes[chapter_id] = recipe

    return recipes

# Scene type -> camera angle/composition guidance
SCENE_TYPE_SHOTS = {
    "image_reveal": "wide establishing shot capturing the full environment",
    "character":    "medium close-up portrait framing, subject fills 40% of frame",
    "quote":        "tight close-up with shallow depth of field, intimate feel",
    "fact_reveal":  "dynamic angle, slight Dutch tilt for impact, data visualization elements",
    "timeline":     "sweeping panoramic view showing progression and change over time",
}

import urllib.request
import urllib.error

SCRIPT_DIR = Path(__file__).parent


def content_to_image_prompt(content: str, chapter_id: str, scene_type: str) -> str:
    """
    Convert scene narration into a cinematic narrative prompt.
    Uses the 5-part formula: Subject + Action/Context + Environment + Lighting & Style + Technical.
    """
    recipe = ERA_RECIPES.get(chapter_id, DEFAULT_RECIPE)
    shot_guidance = SCENE_TYPE_SHOTS.get(scene_type, "medium shot, balanced composition")

    text = content[:200].strip()
    if not text:
        text = "An abstract visual metaphor for this moment in the documentary"

    prompt = (
        f"Generate a cinematic documentary photograph for an award-winning documentary film. "
        f"{shot_guidance}. "
        f"\n\n"
        f"Scene: {text}\n\n"
        f"Environment: {recipe['env']}. "
        f"Shot with a {recipe['camera']}. "
        f"{recipe['lighting']}. "
        f"Color palette: {recipe['palette']}. "
        f"Rendered in the style of {recipe['film']}. "
        f"\n\n"
        f"MUST be photorealistic, hyperdetailed, high production value. "
        f"MUST use 16:9 cinematic composition with strong depth and dimensionality. "
        f"NEVER include any text, watermarks, logos, writing, letters, words, or UI elements in the image."
    )

    return prompt


def generate_image(prompt: str, output_path: Path, max_retries: int = 2) -> bool:
    """Generate image with retry and prompt reinforcement on failure."""
    if output_path.exists():
        return True

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

    for attempt in range(max_retries + 1):
        # On retry, reinforce the image generation intent
        actual_prompt = prompt if attempt == 0 else f"Generate a photorealistic image. {prompt}"

        payload = {
            "contents": [{"parts": [{"text": actual_prompt}]}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "imageConfig": {
                    "aspectRatio": "16:9",
                    "imageSize": "2K",
                },
            },
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={
                "x-goog-api-key": GEMINI_API_KEY,
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            err = e.read().decode()[:200]
            print(f"      ✗ HTTP {e.code}: {err}")
            if e.code == 429:
                wait = 10 * (attempt + 1)
                print(f"      Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            return False
        except Exception as e:
            print(f"      ✗ Error: {e}")
            return False

        for candidate in data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                inline = part.get("inlineData") or part.get("inline_data")
                if inline:
                    img_bytes = base64.b64decode(inline["data"])
                    output_path.write_bytes(img_bytes)
                    remotion_path = REMOTION_DIR / output_path.name
                    remotion_path.write_bytes(img_bytes)
                    return True

        # Text-only response — retry with reinforced prompt
        if attempt < max_retries:
            print(f"      Text-only response, retrying ({attempt + 1}/{max_retries})...")
            time.sleep(3)

    return False


def main():
    parser = argparse.ArgumentParser(description="Generate per-scene images")
    parser.add_argument("--props-file", help="Override render props JSON path")
    parser.add_argument("--output-dir", help="Override output directory")
    parser.add_argument("--chapter", help="Generate for a single chapter only")
    parser.add_argument("--force", action="store_true", help="Regenerate even if images exist")
    parser.add_argument("--config", help="Path to generate_config.json — builds visual styles from chapter_meta")
    args = parser.parse_args()

    global OUTPUT_DIR, REMOTION_DIR, PROPS_FILE, ERA_RECIPES
    if args.props_file:
        PROPS_FILE = Path(args.props_file)
    if args.output_dir:
        OUTPUT_DIR = Path(args.output_dir)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build ERA_RECIPES from config if provided, otherwise use hardcoded legacy recipes
    if args.config:
        config_recipes = build_era_recipes_from_config(args.config)
        if config_recipes:
            ERA_RECIPES = config_recipes
            print(f"  Loaded visual styles from config for {len(config_recipes)} chapters")
        else:
            print(f"  Warning: no visual_style entries found in config, using defaults")

    props = json.loads(PROPS_FILE.read_text())

    print("Generating per-scene cinematic images (optimized prompts)...")
    print(f"  Model: {MODEL}")
    print(f"  Prompt style: Narrative + camera/lens + film stock + MUST/NEVER")
    print()

    total_needed = 0
    total_done = 0
    total_failed = 0

    for ch in props["chapters"]:
        chapter_id = ch["id"]

        if args.chapter and chapter_id != args.chapter:
            continue

        scenes = ch["scenes"]

        needs_image = []
        for i, scene in enumerate(scenes):
            if scene["type"] == "title_card":
                continue
            fname = f"{chapter_id}_scene_{i:03d}.png"
            fpath = OUTPUT_DIR / fname
            if args.force and fpath.exists():
                fpath.unlink()
            needs_image.append((i, scene, fpath, fname))

        total_needed += len(needs_image)
        already = sum(1 for _, _, fp, _ in needs_image if fp.exists())

        print(f"  {chapter_id}: {len(needs_image)} scenes ({already} cached, {len(needs_image) - already} to generate)")

        for idx, scene, fpath, fname in needs_image:
            if fpath.exists():
                total_done += 1
                continue

            prompt = content_to_image_prompt(
                scene.get("content", ""),
                chapter_id,
                scene.get("type", "image_reveal"),
            )
            success = generate_image(prompt, fpath)
            if success:
                total_done += 1
                print(f"    ✓ {fname}")
            else:
                total_failed += 1
                print(f"    ✗ {fname}")

            # Rate limit: 2s between requests (safe for paid tier ~10 IPM)
            time.sleep(2)

    print()
    print(f"Done: {total_done}/{total_needed} scene images ({total_failed} failed)")
    print(f"Output: {OUTPUT_DIR}/")
    print(f"Remotion: {REMOTION_DIR}/")


if __name__ == "__main__":
    main()
