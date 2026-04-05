#!/usr/bin/env python3
"""
SEO Documentary — Nano Banana (Google Gemini Image) Character Generator
Generates consistent character images for each documentary chapter
using the Gemini API (gemini-2.5-flash-image / Nano Banana 2)

Character: "SEO Guide" — a tech-savvy narrator figure who appears
in each chapter dressed/styled for that era.

Usage:
    python3 generate_characters.py

Character consistency strategy:
- Session-based multi-turn chat (same chat session = latent anchor)
- Token locking: reuse exact descriptive phrases verbatim each prompt
- Reference image used after first generation
"""

import os
import base64
import json
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "characters"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Character anchor — reused verbatim in every prompt (token locking)
CHARACTER_ANCHOR = (
    "SEO Guide character, 30-year-old man, confident and sharp, "
    "dark styled short hair, intelligent dark brown eyes with glasses, "
    "tech-savvy appearance, clean jawline, warm medium skin tone, "
    "cinematic documentary style portrait"
)

# Chapter character prompts — anchor + era context
CHAPTER_CHARACTERS = [
    {
        "id": "00_intro",
        "era": "2026",
        "prompt": f"{CHARACTER_ANCHOR}, wearing a modern dark blazer, "
                  "standing in front of a futuristic holographic search interface, "
                  "looking directly at camera, documentary intro, 16:9 cinematic",
    },
    {
        "id": "01_wild_west",
        "era": "1991-1997",
        "prompt": f"{CHARACTER_ANCHOR}, wearing a 90s flannel shirt, "
                  "sitting at a vintage CRT computer terminal showing early AltaVista search, "
                  "retro office setting, warm tungsten lighting, 16:9 cinematic",
    },
    {
        "id": "02_pagerank",
        "era": "1998-2002",
        "prompt": f"{CHARACTER_ANCHOR}, wearing a late-90s casual button-down shirt, "
                  "holding a sheet of paper with a web diagram showing PageRank link structure, "
                  "Stanford University-style campus in background, golden hour lighting, 16:9 cinematic",
    },
    {
        "id": "03_algorithm_wars",
        "era": "2003-2010",
        "prompt": f"{CHARACTER_ANCHOR}, wearing a 2000s tech startup hoodie, "
                  "at a modern office desk with multiple monitors showing search analytics, "
                  "dramatic red and blue lighting representing the algorithm wars, 16:9 cinematic",
    },
    {
        "id": "04_quality_revolution",
        "era": "2011-2013",
        "prompt": f"{CHARACTER_ANCHOR}, wearing a Google-era casual blazer, "
                  "standing in front of a wall showing Panda and Penguin algorithm names, "
                  "clean modern tech office, bright daylight, 16:9 cinematic",
    },
    {
        "id": "05_mobile_first",
        "era": "2013-2016",
        "prompt": f"{CHARACTER_ANCHOR}, wearing a smart casual shirt, "
                  "holding an early smartphone showing mobile search results, "
                  "outdoor urban setting with people on phones, warm 2015 lighting, 16:9 cinematic",
    },
    {
        "id": "06_trust_language",
        "era": "2015-2019",
        "prompt": f"{CHARACTER_ANCHOR}, wearing a professional tech shirt, "
                  "at a whiteboard with E-A-T and RankBrain written in chalk, "
                  "bright modern office, confident teaching pose, 16:9 cinematic",
    },
    {
        "id": "07_experience_era",
        "era": "2019-2022",
        "prompt": f"{CHARACTER_ANCHOR}, wearing a modern minimalist outfit, "
                  "pointing at a monitor showing Core Web Vitals dashboard with green scores, "
                  "sleek design studio environment, 16:9 cinematic",
    },
    {
        "id": "08_ai_disruption",
        "era": "2022-2024",
        "prompt": f"{CHARACTER_ANCHOR}, wearing a dark tech jacket, "
                  "surrounded by floating AI chat interfaces and search result snippets, "
                  "dramatic blue and purple AI-era lighting, looking serious, 16:9 cinematic",
    },
    {
        "id": "09_geo_era",
        "era": "2024-2026",
        "prompt": f"{CHARACTER_ANCHOR}, wearing a cutting-edge tech blazer, "
                  "interacting with an AI Overview-style holographic search results panel, "
                  "futuristic search engine environment, cool cyan and white lighting, 16:9 cinematic",
    },
    {
        "id": "10_future_outro",
        "era": "2026-2030",
        "prompt": f"{CHARACTER_ANCHOR}, wearing a future-forward outfit, "
                  "standing at the edge of a digital horizon with evolving search interfaces, "
                  "inspiring futuristic setting, warm golden sunrise lighting, looking hopeful, 16:9 cinematic",
    },
]


def generate_image_gemini(prompt: str, model: str = "gemini-2.5-flash-image") -> bytes | None:
    """Generate an image via Gemini API (Nano Banana 2)."""
    import urllib.request
    import urllib.error

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {
                "aspectRatio": "16:9",
                "imageSize": "2K"
            }
        }
    }

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json"
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())

            # Extract image from response (API returns camelCase: inlineData)
            for candidate in result.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    img_block = part.get("inlineData") or part.get("inline_data")
                    if img_block:
                        return base64.b64decode(img_block["data"])

            print(f"  No image in response. Text: {result}")
            return None
    except Exception as e:
        print(f"  Error: {e}")
        # Try to print response body
        try:
            print(f"  Response: {e.read().decode()[:500]}")
        except Exception:
            pass
        return None


def generate_image_with_reference(
    prompt: str,
    reference_image_path: Path,
    model: str = "gemini-2.5-flash-image"
) -> bytes | None:
    """Generate a character image using a reference image for consistency."""
    import urllib.request

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    with open(reference_image_path, "rb") as f:
        ref_b64 = base64.b64encode(f.read()).decode()

    # Detect mime type
    suffix = reference_image_path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"

    payload = {
        "contents": [{
            "parts": [
                {
                    "inline_data": {
                        "mime_type": mime,
                        "data": ref_b64
                    }
                },
                {"text": f"Using the same character from the reference image exactly — same face, same {CHARACTER_ANCHOR} features. {prompt}"}
            ]
        }],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {
                "aspectRatio": "16:9",
                "imageSize": "2K"
            }
        }
    }

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json"
    }

    import json as j
    data = j.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = j.loads(resp.read())
            for candidate in result.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    img_block = part.get("inlineData") or part.get("inline_data")
                    if img_block:
                        return base64.b64decode(img_block["data"])
            print(f"  No image in response")
            return None
    except Exception as e:
        print(f"  Error with reference: {e}")
        return None


def build_characters_from_config(config_path: str) -> list[dict]:
    """Build CHAPTER_CHARACTERS list from generate_config.json."""
    config = json.loads(Path(config_path).read_text())
    chapters = config.get("chapter_ids", [])
    meta = config.get("chapter_meta", {})
    result = []
    for cid in chapters:
        m = meta.get(cid, {})
        era = m.get("era", "")
        hints = m.get("image_style_hints", [])
        hint_text = hints[0] if hints else m.get("title", cid)
        prompt = (
            f"{CHARACTER_ANCHOR}, in the era of {era}, "
            f"visual context: {hint_text}, "
            f"16:9 cinematic documentary style"
        )
        result.append({"id": cid, "era": era, "prompt": prompt})
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate character images")
    parser.add_argument("--config", help="Path to generate_config.json for custom chapters")
    parser.add_argument("--output-dir", help="Override output directory")
    args = parser.parse_args()

    global OUTPUT_DIR

    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY not set. Export it:")
        print("  export GEMINI_API_KEY=your_key_here")
        print("  Get key at: https://aistudio.google.com/apikey")
        return

    characters = CHAPTER_CHARACTERS
    if args.config:
        characters = build_characters_from_config(args.config)
    if args.output_dir:
        OUTPUT_DIR = Path(args.output_dir)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(characters)} character images via Nano Banana 2...")
    print(f"Output: {OUTPUT_DIR}")
    print()

    reference_path = None

    for i, chapter in enumerate(characters):
        output_path = OUTPUT_DIR / f"{chapter['id']}_character.png"

        if output_path.exists():
            print(f"  [SKIP] {chapter['id']} already exists")
            if reference_path is None:
                reference_path = output_path
            continue

        print(f"  [{i+1}/{len(characters)}] {chapter['id']} ({chapter['era']})...")

        if reference_path and reference_path.exists():
            image_bytes = generate_image_with_reference(chapter["prompt"], reference_path)
        else:
            image_bytes = generate_image_gemini(chapter["prompt"])

        if image_bytes:
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            print(f"    ✓ Saved {output_path.name} ({len(image_bytes) // 1024}KB)")
            if reference_path is None:
                reference_path = output_path
        else:
            print(f"    ✗ Failed to generate {chapter['id']}")

    print()
    print("Character generation complete.")
    generated = list(OUTPUT_DIR.glob("*_character.png"))
    print(f"Generated {len(generated)} character images in {OUTPUT_DIR}")

    # Copy to Remotion public folder
    remotion_chars = SCRIPT_DIR / ".." / ".." / "public" / "seo_characters"
    remotion_chars.mkdir(parents=True, exist_ok=True)
    import shutil
    for img in generated:
        shutil.copy(img, remotion_chars / img.name)
    print(f"Copied to Remotion: {remotion_chars}")


if __name__ == "__main__":
    main()
