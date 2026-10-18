#!/usr/bin/env python3
"""
Generate concept images for SEO Documentary scene_images/ pool.
Uses Gemini (Nano Banana) to generate 3-4 images per chapter.
These power the image_reveal scene type in the documentary.

Output: scene_images/{chapter_id}_{index}.png
        Remotion/public/seo_scene_images/{chapter_id}_{index}.png
"""

import os
import base64
import json
import time
from pathlib import Path

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OUTPUT_DIR  = Path(os.getenv("SCENE_IMAGES_DIR", "scene_images"))
REMOTION_DIR = Path(os.getenv("REMOTION_PUBLIC_DIR", "../../public/seo_scene_images"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REMOTION_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "gemini-2.5-flash-image"

STYLE = (
    "cinematic documentary photography, 16:9 composition, "
    "dark moody color grading, high production value, "
    "no text or watermarks, photorealistic"
)

# 3-4 concept images per chapter — visual metaphors for the era/topic
CHAPTER_SCENES = {
    "00_intro": [
        f"aerial view of a glowing interconnected web of nodes representing the internet, deep space aesthetic, vibrant green and blue lights, {STYLE}",
        f"close-up of a person's hands typing on a keyboard, search bar glowing on screen with the word SEO, dramatic side lighting, {STYLE}",
        f"timeline visualization stretching across a dark screen, years 1991 to 2030 glowing, futuristic UI, {STYLE}",
    ],
    "01_wild_west": [
        f"vintage 1990s computer lab with CRT monitors showing early web browsers, warm tungsten lighting, film grain, {STYLE}",
        f"old AltaVista or Yahoo search engine result page on a CRT monitor, retro green phosphor glow, cluttered early internet aesthetic, {STYLE}",
        f"digital wild west — lone computer in a dark desert with code scrolling down the screen like a waterfall, {STYLE}",
        f"white text hidden on a white background concept art — invisible ink reveal, metaphor for early SEO spam tactics, {STYLE}",
    ],
    "02_pagerank": [
        f"glowing network graph of interconnected websites, nodes of different sizes representing PageRank authority, dark background, blue tones, {STYLE}",
        f"Stanford University campus at golden hour, two young computer scientists with laptops and diagrams, warm academic atmosphere, {STYLE}",
        f"abstract visualization of links between websites forming a hierarchy, some nodes glowing brighter, representing link authority, {STYLE}",
    ],
    "03_algorithm_wars": [
        f"underground server room with red warning lights, hackers in shadows representing black hat SEO, dramatic contrast, {STYLE}",
        f"battlefield metaphor — two armies of robots facing each other across a digital landscape, one side labeled black hat, epic scale, {STYLE}",
        f"Google search algorithm update notification on screen, site rankings collapsing in a graph, chaos visual, {STYLE}",
        f"link farm visualization — thousands of fake websites as a spider web of deceit, dark gothic aesthetic, {STYLE}",
    ],
    "04_quality_revolution": [
        f"panda bear sitting calmly in front of server racks, symbolic, cinematic, soft backlighting, {STYLE}",
        f"penguin standing guard in front of a wall of spam content being deleted, content quality metaphor, {STYLE}",
        f"before and after — left side shows spam-filled website rubble, right side shows clean beautiful content, split composition, {STYLE}",
        f"quality content creation — writer at a desk surrounded by glowing manuscripts, warm library atmosphere, {STYLE}",
    ],
    "05_mobile_first": [
        f"smartphone held up showing Google search results, city street background blurred, modern urban setting, {STYLE}",
        f"the moment mobile searches surpassed desktop — split screen of phone vs computer with tipping scale, dramatic lighting, {STYLE}",
        f"mobilegeddon concept — websites falling off a cliff into darkness, mobile-friendly sites standing tall, {STYLE}",
        f"responsive web design grid adapting across phone tablet laptop, clean tech visualization, {STYLE}",
    ],
    "06_trust_language": [
        f"AI neural network brain processing language and understanding meaning, purple and blue tones, {STYLE}",
        f"RankBrain visualization — machine learning layer above traditional search results, geometric patterns, {STYLE}",
        f"BERT language model concept — words and sentences being understood by an AI, natural language processing visual, {STYLE}",
        f"E-A-T concept — three pillars of expertise authoritativeness trustworthiness glowing, editorial authority visual, {STYLE}",
    ],
    "07_experience_era": [
        f"Core Web Vitals dashboard on screen — LCP FID CLS metrics with green indicators, clean tech UI, {STYLE}",
        f"website speed test visualization — fast loading page with dynamic swoosh motion, performance metric art, {STYLE}",
        f"user experience journey — person on phone smoothly navigating a beautiful fast website, satisfaction visible, {STYLE}",
    ],
    "08_ai_disruption": [
        f"ChatGPT interface on screen with an AI assistant answering questions, disruption metaphor, dramatic glow, {STYLE}",
        f"Google search being disrupted by AI — traditional blue links fading, AI overview replacing them, seismic shift visual, {STYLE}",
        f"robot and human writer side by side at desks, collaboration and competition metaphor, cinematic, {STYLE}",
        f"helpful content concept — authentic human experience glowing vs AI slop fading to grey, contrast visual, {STYLE}",
    ],
    "09_geo_era": [
        f"generative AI search overview with sources cited, future interface design, clean and authoritative, {STYLE}",
        f"brand mentions floating across AI responses — GEO optimization visualization, interconnected citations, {STYLE}",
        f"AI chatbot answering a complex query with cited sources glowing, trustworthy information ecosystem, {STYLE}",
    ],
    "10_future_outro": [
        f"futuristic search interface — holographic augmented reality search overlaid on city skyline 2030, {STYLE}",
        f"human expertise glowing in the age of AI — person surrounded by knowledge with AI tools as assistants, hopeful, {STYLE}",
        f"the future of SEO — a road stretching into a bright horizon with digital infrastructure on both sides, {STYLE}",
        f"person looking at a holographic display of the complete SEO timeline 1991 to 2030, documentary conclusion visual, {STYLE}",
    ],
}

import urllib.request
import urllib.error


def generate_image(prompt: str, output_path: Path) -> bool:
    if output_path.exists():
        print(f"    [SKIP] {output_path.name}")
        return True

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
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
        print(f"    ✗ HTTP {e.code}: {e.read().decode()[:200]}")
        return False

    # Extract image from response (API returns camelCase: inlineData)
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline:
                img_bytes = base64.b64decode(inline["data"])
                output_path.write_bytes(img_bytes)
                remotion_path = REMOTION_DIR / output_path.name
                remotion_path.write_bytes(img_bytes)
                return True

    print(f"    ✗ No image in response: {json.dumps(data)[:200]}")
    return False


def build_scenes_from_config(config_path: str) -> dict:
    """Build CHAPTER_SCENES from generate_config.json image_style_hints."""
    config = json.loads(Path(config_path).read_text())
    chapters = config.get("chapter_ids", [])
    meta = config.get("chapter_meta", {})
    scenes = {}
    for cid in chapters:
        m = meta.get(cid, {})
        hints = m.get("image_style_hints", [])
        prompts = [f"{hint}, {STYLE}" for hint in hints]
        if not prompts:
            prompts = [f"Documentary establishing shot for {m.get('title', cid)}, {m.get('era', '')}, {STYLE}"]
        scenes[cid] = prompts
    return scenes


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate scene concept images")
    parser.add_argument("--config", help="Path to generate_config.json for custom chapters")
    parser.add_argument("--output-dir", help="Override output directory")
    args = parser.parse_args()

    global OUTPUT_DIR, REMOTION_DIR

    chapter_scenes = CHAPTER_SCENES
    if args.config:
        chapter_scenes = build_scenes_from_config(args.config)
    if args.output_dir:
        OUTPUT_DIR = Path(args.output_dir)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating scene concept images via Gemini (Nano Banana)...")
    print(f"Output: {OUTPUT_DIR}/")
    print()

    total = sum(len(v) for v in chapter_scenes.values())
    done = 0
    failed = 0

    for chapter_id, prompts in chapter_scenes.items():
        print(f"  {chapter_id} ({len(prompts)} images):")
        for i, prompt in enumerate(prompts):
            output_path = OUTPUT_DIR / f"{chapter_id}_{i:02d}.png"
            success = generate_image(prompt, output_path)
            if success:
                done += 1
                print(f"    ✓ {output_path.name}")
            else:
                failed += 1
            time.sleep(1.5)

    print()
    print(f"Done: {done}/{total} images generated, {failed} failed")
    print(f"Remotion public: {REMOTION_DIR}/")


if __name__ == "__main__":
    main()
