#!/usr/bin/env python3
"""
SEO Documentary — YouTube Upload
Uses Google OAuth2 (client_id + client_secret + refresh_token from ~/.env)

Usage:
    python3 upload_youtube.py output/seo_documentary.mp4
    python3 upload_youtube.py output/video.mp4 --config generate_config.json
    python3 upload_youtube.py output/video.mp4 --config generate_config.json --privacy public
    python3 upload_youtube.py output/video.mp4 --title "Custom Title" --privacy public
"""

import argparse
import os
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path

# ─── Credentials ─────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

# ─── Video Metadata ───────────────────────────────────────────────────────────
VIDEO_TITLE = "SEO and GEO in 2030: What Actually Works, What's Changing | Full Documentary"
VIDEO_DESCRIPTION = """The rules of search have been rewritten. AI Overviews, Generative Engine Optimization, and answer engines are replacing the blue links we've relied on for decades.

This 30-minute documentary covers the full landscape of SEO and GEO from 2026 to 2030 — from the origins of search engine optimization, through every major algorithm shift, to the emerging strategies that will define the next era of digital visibility.

Whether you're an SEO professional adapting to AI search, a founder building organic presence, or a marketer preparing for what's next — this is the most comprehensive guide to where search is headed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱ CHAPTERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
00:00 Navigating the New Digital Landscape — The search world has fundamentally changed. Here's what you need to know.
02:38 The Stone Age of SEO — How keyword stuffing and meta tag manipulation built (and broke) the early web.
05:58 The Era of Major Breakthroughs — PageRank, Panda, Penguin, and the algorithm updates that reshaped the internet.
09:09 Pioneers Paving the Path — The experts and innovators who defined modern search optimization.
12:17 The SEO and GEO Evolution — From mobile-first to AI-first: how the discipline transformed.
15:12 2026: The Year That Shaped the Future — AI Overviews, zero-click results, and the new reality of search.
18:04 Peering into the Horizon: 2030 and Beyond — Agentic AI, spatial computing, and the future of findability.
21:06 Home Ground Advantage: Local SEO — Why local search is the last stronghold of traditional SEO.
24:15 Schema Markup and Programmatic SEO — The technical foundations that power AI-era visibility.
27:24 Navigating Tomorrow: Strategy and Success — The playbook for thriving in the next decade of search.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 KEY TOPICS COVERED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Generative Engine Optimization (GEO) — what it is and how to implement it
• AI Overviews and zero-click search: impact and strategy
• E-E-A-T in the age of AI-generated content
• Local SEO as the last defensible moat
• Schema markup and structured data for AI citation
• Programmatic SEO at scale in 2026
• How to get cited by ChatGPT, Perplexity, and AI answer engines
• The dual-track strategy: traditional SEO + GEO simultaneously
• What agentic AI search means for content creators

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 WHO THIS IS FOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• SEO professionals adapting to AI-driven search
• Content marketers building long-term organic strategies
• Business owners who want to understand the new rules of visibility
• Digital marketing students learning modern search optimization
• Founders building AI-era search presence from scratch

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏷 TAGS & SEARCH TERMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEO 2026, GEO, generative engine optimization, AI overviews, SEO documentary, search engine optimization, Google algorithm updates, AI search, zero-click search, E-E-A-T, local SEO, schema markup, programmatic SEO, digital marketing 2026, content strategy, ChatGPT search, Perplexity SEO, SEO strategy, agentic AI, answer engine optimization, SEO future, search visibility

#SEO #GEO #GenerativeEngineOptimization #AIOverviews #DigitalMarketing #SEO2026 #SearchOptimization #ContentMarketing #LocalSEO #SchemaMarkup #AISearch #SEODocumentary #SEOStrategy

⚠️ Disclosure: This video contains AI-generated imagery. All narration is performed by a real human voice.
"""
VIDEO_TAGS = [
    "SEO", "GEO", "generative engine optimization", "AI overviews",
    "search engine optimization", "SEO 2026", "SEO documentary",
    "Google algorithm", "AI search", "zero-click search", "E-E-A-T",
    "local SEO", "schema markup", "programmatic SEO", "digital marketing",
    "content strategy", "ChatGPT search", "Perplexity SEO", "agentic AI",
    "answer engine optimization", "SEO future"
]
VIDEO_CATEGORY_ID = "27"  # Education
VIDEO_PRIVACY = "unlisted"  # Start unlisted for review, then switch to public


def get_access_token() -> str:
    """Exchange refresh token for access token."""
    url = "https://oauth2.googleapis.com/token"
    data = urllib.parse.urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": GOOGLE_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }).encode()

    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        if "access_token" not in result:
            raise ValueError(f"Token refresh failed: {result}")
        return result["access_token"]


def load_meta_from_config(config_path: str) -> dict:
    """Load youtube_meta from a generate_config.json file."""
    config_path = Path(config_path)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)
    with open(config_path, "r") as f:
        config = json.load(f)
    meta = config.get("youtube_meta")
    if not meta:
        print(f"Error: No 'youtube_meta' key found in {config_path}")
        sys.exit(1)
    return meta


def resolve_metadata(args) -> dict:
    """Resolve final metadata from config file, hardcoded defaults, and CLI overrides.

    Priority: CLI flags > config file > hardcoded defaults.
    Returns dict with keys: title, description, tags, category_id, privacy.
    """
    # Start with hardcoded defaults
    meta = {
        "title": VIDEO_TITLE,
        "description": VIDEO_DESCRIPTION,
        "tags": VIDEO_TAGS,
        "category_id": VIDEO_CATEGORY_ID,
        "privacy": VIDEO_PRIVACY,
    }

    # Layer config file values on top
    if args.config:
        cfg = load_meta_from_config(args.config)
        if "title" in cfg:
            meta["title"] = cfg["title"]
        if "description" in cfg:
            meta["description"] = cfg["description"]
        if "tags" in cfg:
            meta["tags"] = cfg["tags"]
        if "category_id" in cfg:
            meta["category_id"] = cfg["category_id"]

    # CLI overrides take highest precedence
    if args.title:
        meta["title"] = args.title
    if args.description:
        meta["description"] = args.description
    if args.privacy:
        meta["privacy"] = args.privacy

    return meta


def upload_video(video_path: str, access_token: str, meta: dict) -> str:
    """Upload video to YouTube via resumable upload. Returns video ID."""
    video_path = Path(video_path)
    file_size = video_path.stat().st_size

    print(f"  File: {video_path.name} ({file_size / 1024 / 1024:.1f}MB)")
    print(f"  Title: {meta['title']}")
    print(f"  Privacy: {meta['privacy']}")

    # Step 1: Initiate resumable upload
    metadata = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": meta["category_id"],
        },
        "status": {
            "privacyStatus": meta["privacy"],
            "selfDeclaredMadeForKids": False,
        }
    }

    init_url = (
        "https://www.googleapis.com/upload/youtube/v3/videos"
        "?uploadType=resumable&part=snippet,status"
    )
    init_data = json.dumps(metadata).encode()
    init_req = urllib.request.Request(init_url, data=init_data, method="POST")
    init_req.add_header("Authorization", f"Bearer {access_token}")
    init_req.add_header("Content-Type", "application/json")
    init_req.add_header("X-Upload-Content-Length", str(file_size))
    init_req.add_header("X-Upload-Content-Type", "video/mp4")

    with urllib.request.urlopen(init_req) as resp:
        upload_url = resp.headers.get("Location")
        if not upload_url:
            raise ValueError("No Location header in initiation response")

    print(f"  Upload URL obtained. Starting upload...")

    # Step 2: Upload in chunks
    chunk_size = 10 * 1024 * 1024  # 10MB chunks
    uploaded = 0

    with open(video_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            end_byte = uploaded + len(chunk) - 1
            content_range = f"bytes {uploaded}-{end_byte}/{file_size}"

            chunk_req = urllib.request.Request(upload_url, data=chunk, method="PUT")
            chunk_req.add_header("Authorization", f"Bearer {access_token}")
            chunk_req.add_header("Content-Type", "video/mp4")
            chunk_req.add_header("Content-Range", content_range)

            try:
                with urllib.request.urlopen(chunk_req) as resp:
                    if resp.status in (200, 201):
                        result = json.loads(resp.read())
                        video_id = result.get("id", "unknown")
                        print(f"  ✓ Upload complete! Video ID: {video_id}")
                        return video_id
                    uploaded += len(chunk)
                    pct = int(uploaded / file_size * 100)
                    print(f"  Progress: {pct}% ({uploaded // 1024 // 1024}MB / {file_size // 1024 // 1024}MB)")
            except urllib.error.HTTPError as e:
                if e.code == 308:  # Resume Incomplete — continue
                    uploaded += len(chunk)
                    pct = int(uploaded / file_size * 100)
                    print(f"  Progress: {pct}% ({uploaded // 1024 // 1024}MB / {file_size // 1024 // 1024}MB)")
                else:
                    raise

    return "upload_error"


def main():
    parser = argparse.ArgumentParser(
        description="Upload video to YouTube with metadata from config or CLI flags."
    )
    parser.add_argument("video_file", help="Path to the video file (e.g. output/video.mp4)")
    parser.add_argument("--config", help="Path to generate_config.json (reads youtube_meta)")
    parser.add_argument("--title", help="Override video title")
    parser.add_argument("--description", help="Override video description")
    parser.add_argument("--privacy", help="Privacy status (default: unlisted)",
                        choices=["public", "unlisted", "private"])
    args = parser.parse_args()

    if not Path(args.video_file).exists():
        print(f"Error: File not found: {args.video_file}")
        sys.exit(1)

    meta = resolve_metadata(args)

    print("Getting YouTube access token...")
    access_token = get_access_token()
    print("  ✓ Access token obtained")

    print("Uploading to YouTube...")
    video_id = upload_video(args.video_file, access_token, meta)

    print()
    print(f"YouTube URL: https://www.youtube.com/watch?v={video_id}")
    print(f"Studio URL:  https://studio.youtube.com/video/{video_id}/edit")


if __name__ == "__main__":
    main()
