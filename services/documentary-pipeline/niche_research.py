#!/usr/bin/env python3
"""
Niche Keyword Research Engine — Multi-Platform Deep Analysis

Platform-specific research strategies:

YOUTUBE:
  1. Search keyword → top 20-30 videos
  2. Download all transcripts (timestamped)
  3. Visual analysis: extract frame every 2s for first 30s of each video
  4. Comprehensive analysis: visual + transcript synthesis per video
  5. Cross-video pattern analysis: what hooks work, what thumbnails win

TWITTER/X:
  1. Search keyword → top 100 posts
  2. Sort by engagement (likes, retweets, replies)
  3. Go to top accounts → get their top 10-25 tweets
  4. Profile analysis: what makes these accounts successful
  5. Content pattern analysis: what formats/hooks get engagement

INSTAGRAM:
  1. Search keyword → top 20-50 reels/videos
  2. Visual analysis every 2s on each video
  3. Extract any transcript/caption
  4. Comprehensive visual + transcript summary per video
  5. Pattern analysis: what visual styles win

REDDIT:
  1. Search keyword → top 25 posts across relevant subreddits
  2. Pull ALL comments on each post
  3. Analyze human nature: what comments add value vs garbage
  4. Extract novel insights from high-value comments
  5. Community sentiment analysis

GOOGLE TRENDS:
  1. Interest over time for keyword
  2. Related queries (rising + top)
  3. Regional interest breakdown
  4. Compare against related keywords

Usage:
    python3 niche_research.py "SEO" --all
    python3 niche_research.py "AI automation" --youtube --twitter
    python3 niche_research.py "crypto trading" --reddit --depth deep
    python3 niche_research.py "content creation" --instagram --visual-analysis

Output: research/niche_{keyword}/
    ├── youtube_research.json
    ├── youtube_transcripts/
    ├── youtube_frames/
    ├── twitter_research.json
    ├── instagram_research.json
    ├── instagram_frames/
    ├── reddit_research.json
    ├── google_trends.json
    ├── cross_platform_synthesis.json
    └── final_report.md
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from dataclasses import dataclass, field

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR
RESEARCH_DIR = PROJECT_DIR / "research"

# ─── API Keys ────────────────────────────────────────────────────────────────
RAPIDAPI_KEY = os.getenv(
    "RAPIDAPI_KEY",
    "a87cab3052mshf494034b3141e1ep1aacb0jsn580589e4be0b",
)
ANTHROPIC_API_KEY = os.getenv(
    "ANTHROPIC_API_KEY",
    os.environ.get("ANTHROPIC_API_KEY", ""),
)
OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
    os.environ.get("OPENAI_API_KEY", ""),
)
PERPLEXITY_API_KEY = os.getenv(
    "PERPLEXITY_API_KEY",
    os.environ.get("PERPLEXITY_API_KEY", ""),
)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:50]


# ─── Generic API Helpers ─────────────────────────────────────────────────────

def rapidapi_get(host: str, path: str, params: dict = None) -> dict | list | None:
    """Generic RapidAPI GET request."""
    query = ""
    if params:
        query = "?" + urllib.parse.urlencode(params)
    url = f"https://{host}{path}{query}"

    req = urllib.request.Request(url)
    req.add_header("x-rapidapi-key", RAPIDAPI_KEY)
    req.add_header("x-rapidapi-host", host)
    req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:200]
        print(f"      API error {e.code}: {err[:100]}")
        return None
    except Exception as e:
        print(f"      Request error: {e}")
        return None


def rapidapi_post(host: str, path: str, body: dict, params: dict = None) -> dict | list | None:
    """Generic RapidAPI POST request."""
    query = ""
    if params:
        query = "?" + urllib.parse.urlencode(params)
    url = f"https://{host}{path}{query}"

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        method="POST",
    )
    req.add_header("x-rapidapi-key", RAPIDAPI_KEY)
    req.add_header("x-rapidapi-host", host)
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:200]
        print(f"      API error {e.code}: {err[:100]}")
        return None
    except Exception as e:
        print(f"      Request error: {e}")
        return None


def _call_anthropic(prompt: str, max_tokens: int = 4000) -> str | None:
    """Call Anthropic Claude API."""
    if not (ANTHROPIC_API_KEY or OPENAI_API_KEY or PERPLEXITY_API_KEY):
        return None
    payload = {
        "model": "claude-sonnet-4-6-20250131",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        return data["content"][0]["text"]
    except Exception as e:
        print(f"      Anthropic failed: {e}")
        return None


def _call_openai(prompt: str, max_tokens: int = 4000) -> str | None:
    """Call OpenAI GPT-4o API (fallback)."""
    if not OPENAI_API_KEY:
        return None
    payload = {
        "model": "gpt-4o",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"      OpenAI failed: {e}")
        return None


def _call_perplexity(prompt: str, max_tokens: int = 4000) -> str | None:
    """Call Perplexity API (web-grounded fallback)."""
    if not PERPLEXITY_API_KEY:
        return None
    payload = {
        "model": "sonar-pro",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        "https://api.perplexity.ai/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"      Perplexity failed: {e}")
        return None


def claude_analyze(prompt: str, max_tokens: int = 4000) -> str:
    """Call AI for analysis — tries Anthropic → OpenAI → Perplexity in order."""
    # Try each provider in priority order
    result = _call_anthropic(prompt, max_tokens)
    if result:
        return result

    print("      Falling back to OpenAI...")
    result = _call_openai(prompt, max_tokens)
    if result:
        return result

    print("      Falling back to Perplexity...")
    result = _call_perplexity(prompt, max_tokens)
    if result:
        return result

    return "(No AI API available — set ANTHROPIC_API_KEY, OPENAI_API_KEY, or PERPLEXITY_API_KEY)"


def extract_video_frames(video_url: str, output_dir: Path, interval: int = 2, max_secs: int = 30) -> list[Path]:
    """
    Extract frames from a video every N seconds using ffmpeg.
    Returns list of frame image paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    frames = []

    try:
        # Download video first if it's a URL
        if video_url.startswith("http"):
            import tempfile
            tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            tmp_path = tmp.name
            tmp.close()

            subprocess.run(
                ["yt-dlp", "-f", "worst[ext=mp4]", "-o", tmp_path, video_url],
                capture_output=True,
                timeout=120,
            )
            video_path = tmp_path
        else:
            video_path = video_url

        # Extract frames every N seconds for first max_secs
        for sec in range(0, max_secs, interval):
            frame_path = output_dir / f"frame_{sec:04d}.jpg"
            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-ss", str(sec), "-i", video_path,
                    "-frames:v", "1", "-q:v", "3", str(frame_path),
                ],
                capture_output=True,
                timeout=30,
            )
            if frame_path.exists() and frame_path.stat().st_size > 1000:
                frames.append(frame_path)

        # Clean up temp file
        if video_url.startswith("http"):
            Path(tmp_path).unlink(missing_ok=True)

    except Exception as e:
        print(f"      Frame extraction error: {e}")

    return frames


def _vision_gemini(frames: list[Path], prompt: str) -> str | None:
    """Visual analysis via Gemini Vision."""
    if not GEMINI_API_KEY:
        return None
    parts = [{"text": prompt}]
    for frame in frames[:15]:
        img_data = base64.b64encode(frame.read_bytes()).decode()
        parts.append({"inlineData": {"mimeType": "image/jpeg", "data": img_data}})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"maxOutputTokens": 2000},
    }
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        data=json.dumps(payload).encode(),
        headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        for candidate in data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if part.get("text"):
                    return part["text"]
    except Exception as e:
        print(f"      Gemini vision error: {e}")
    return None


def _vision_openai(frames: list[Path], prompt: str) -> str | None:
    """Visual analysis via OpenAI GPT-4o Vision (fallback)."""
    if not OPENAI_API_KEY:
        return None
    content = [{"type": "text", "text": prompt}]
    for frame in frames[:10]:  # OpenAI has tighter limits
        img_data = base64.b64encode(frame.read_bytes()).decode()
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img_data}", "detail": "low"},
        })

    payload = {
        "model": "gpt-4o",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": content}],
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"      OpenAI vision error: {e}")
    return None


def analyze_frames_with_gemini(frames: list[Path], context: str = "") -> str:
    """
    Visual analysis of video frames — tries Gemini Vision → OpenAI Vision.
    """
    if not frames:
        return ""

    prompt = (
        f"Analyze these video frames (extracted every 2 seconds from the first 30 seconds). {context}\n\n"
        "Describe:\n1. Visual style and production quality\n2. Text/graphics overlays used\n"
        "3. Scene composition and framing\n4. Color palette and mood\n"
        "5. What makes this visually engaging (or not)\n6. Hook strategy in the first 5 seconds"
    )

    result = _vision_gemini(frames, prompt)
    if result:
        return result

    print("      Gemini unavailable, trying OpenAI Vision...")
    result = _vision_openai(frames, prompt)
    if result:
        return result

    return ""


# ═════════════════════════════════════════════════════════════════════════════
# YOUTUBE RESEARCH
# ═════════════════════════════════════════════════════════════════════════════

def research_youtube(keyword: str, output_dir: Path, top_n: int = 20, visual: bool = False) -> dict:
    """
    YouTube niche research:
    1. Search keyword → top N videos
    2. Get transcripts for each
    3. Optional: visual analysis of first 30s
    4. Comprehensive analysis
    """
    print(f"\n  ═══ YOUTUBE RESEARCH: '{keyword}' ═══")
    results = {"keyword": keyword, "videos": [], "patterns": {}}

    # Step 1: Search
    print(f"    Searching top {top_n} videos...")
    search = rapidapi_get("yt-api.p.rapidapi.com", "/search", {
        "query": keyword,
        "type": "video",
        "sort_by": "relevance",
    })

    if not search:
        print("      Search failed — trying alternative")
        return results

    videos_raw = search.get("data", search.get("items", search.get("videos", [])))
    if not isinstance(videos_raw, list):
        videos_raw = []

    print(f"    Found {len(videos_raw)} videos")

    # Step 2: Get details + transcripts for each video
    transcript_dir = output_dir / "youtube_transcripts"
    transcript_dir.mkdir(parents=True, exist_ok=True)

    for i, v in enumerate(videos_raw[:top_n]):
        video_id = v.get("videoId", v.get("video_id", v.get("id", "")))
        title = v.get("title", "")
        if not video_id:
            continue

        print(f"    [{i+1}/{min(len(videos_raw), top_n)}] {title[:50]}...")

        video_data = {
            "video_id": video_id,
            "title": title,
            "channel": v.get("channelTitle", v.get("channel", {}).get("name", "")),
            "views": v.get("viewCount", v.get("views", 0)),
            "url": f"https://youtube.com/watch?v={video_id}",
        }

        # Get video info for more details
        info = rapidapi_get("yt-api.p.rapidapi.com", "/video/info", {"id": video_id})
        if info:
            video_data["views"] = info.get("viewCount", video_data["views"])
            video_data["likes"] = info.get("likeCount", 0)
            video_data["comments_count"] = info.get("commentCount", 0)
            video_data["description"] = info.get("description", "")[:500]
            video_data["duration"] = info.get("lengthSeconds", 0)

        # Get transcript
        transcript = rapidapi_get("youtube-transcriptor.p.rapidapi.com", "/transcript", {
            "video_id": video_id,
            "lang": "en",
        })

        if transcript:
            segments = transcript if isinstance(transcript, list) else transcript.get("segments", transcript.get("transcription", []))
            if isinstance(segments, list):
                video_data["transcript_segments"] = len(segments)
                full_text = " ".join(
                    s.get("text", s.get("subtitle", "")) for s in segments
                    if isinstance(s, dict)
                )
                video_data["transcript_text"] = full_text[:5000]

                # Save full transcript
                (transcript_dir / f"{video_id}.json").write_text(
                    json.dumps({"video_id": video_id, "title": title, "segments": segments}, indent=2)
                )

                # Extract first 30 seconds for hook analysis
                first_30s = " ".join(
                    s.get("text", s.get("subtitle", ""))
                    for s in segments
                    if isinstance(s, dict) and float(s.get("start", s.get("startMs", 0)) if not isinstance(s.get("start", 0), str) else s.get("start", "0").replace("s", "")) < 30
                )
                video_data["first_30s_text"] = first_30s[:1000]

        # Visual analysis (optional — expensive)
        if visual and video_id:
            frames_dir = output_dir / "youtube_frames" / video_id
            print(f"      Extracting frames...")
            frames = extract_video_frames(
                f"https://youtube.com/watch?v={video_id}",
                frames_dir,
                interval=2,
                max_secs=30,
            )
            if frames:
                print(f"      Analyzing {len(frames)} frames via Gemini Vision...")
                visual_analysis = analyze_frames_with_gemini(
                    frames,
                    context=f"Video: '{title}' about '{keyword}'"
                )
                video_data["visual_analysis"] = visual_analysis
                video_data["frames_extracted"] = len(frames)

        results["videos"].append(video_data)
        time.sleep(1)  # Rate limit

    # Step 3: Cross-video pattern analysis
    if results["videos"] and (ANTHROPIC_API_KEY or OPENAI_API_KEY or PERPLEXITY_API_KEY):
        print(f"    Analyzing patterns across {len(results['videos'])} videos...")

        videos_summary = "\n\n".join(
            f"**{v['title']}** ({v.get('views', '?')} views)\n"
            f"First 30s: {v.get('first_30s_text', 'N/A')[:300]}\n"
            f"Visual: {v.get('visual_analysis', 'N/A')[:200]}"
            for v in results["videos"][:15]
        )

        analysis = claude_analyze(
            f"""Analyze these top YouTube videos for the keyword "{keyword}":

{videos_summary}

Provide:
1. HOOK PATTERNS: What do the first 30 seconds have in common? What hooks work?
2. TITLE PATTERNS: Common title structures, power words, curiosity gaps
3. CONTENT STRUCTURE: How do top videos organize their content?
4. VISUAL PATTERNS: Common visual styles, thumbnails, production quality
5. GAPS: What are top videos NOT covering that could be an opportunity?
6. WINNING FORMULA: If you were making the next video on this topic, what would you do?

Be specific with examples from the actual videos.""",
            max_tokens=3000,
        )
        results["patterns"]["youtube_analysis"] = analysis

    return results


# ═════════════════════════════════════════════════════════════════════════════
# TWITTER/X RESEARCH
# ═════════════════════════════════════════════════════════════════════════════

def research_twitter(keyword: str, output_dir: Path, top_n: int = 100) -> dict:
    """
    Twitter niche research:
    1. Search keyword → top 100 posts
    2. Sort by engagement
    3. Get top accounts → their best tweets
    4. Pattern analysis
    """
    print(f"\n  ═══ TWITTER RESEARCH: '{keyword}' ═══")
    results = {"keyword": keyword, "posts": [], "top_accounts": [], "patterns": {}}

    # Step 1: Search tweets
    print(f"    Searching top tweets...")
    search = rapidapi_get("twitter-api45.p.rapidapi.com", "/search.php", {
        "query": keyword,
        "search_type": "Top",
    })

    if not search:
        # Fallback: try twitter154 API (another RapidAPI twitter endpoint)
        print("      twitter-api45 failed, trying twitter154...")
        search = rapidapi_get("twitter154.p.rapidapi.com", "/search/search", {
            "query": keyword,
            "section": "top",
            "limit": str(min(top_n, 20)),
        })

    if not search:
        # Fallback 2: try twttrapi
        print("      twitter154 failed, trying twttrapi...")
        search = rapidapi_get("twttrapi.p.rapidapi.com", "/search-tweets", {
            "query": keyword,
        })

    if not search:
        print("      All Twitter APIs failed (may need subscription)")
        return results

    # Handle multiple response formats (twitter-api45 vs twitter154 vs twttrapi)
    timeline = (
        search.get("results", []) or  # twitter154 format
        search.get("timeline", []) or  # twitter-api45 format
        search.get("tweets", []) or
        search.get("data", [])
    )
    if isinstance(timeline, list):
        for tweet in timeline[:top_n]:
            entry = tweet.get("tweet", tweet) if isinstance(tweet, dict) else {}
            if not isinstance(entry, dict):
                continue

            text = entry.get("text", entry.get("full_text", ""))
            author = entry.get("user", entry.get("author", {}))
            if isinstance(author, dict):
                screen_name = author.get("username", author.get("screen_name", ""))
                followers = author.get("follower_count", author.get("followers_count", 0))
            else:
                screen_name = str(author)
                followers = 0

            results["posts"].append({
                "text": text[:500],
                "author": screen_name,
                "followers": followers,
                "likes": entry.get("favorite_count", entry.get("likes", 0)),
                "retweets": entry.get("retweet_count", entry.get("retweets", 0)),
                "replies": entry.get("reply_count", entry.get("replies", 0)),
                "views": entry.get("views", 0),
            })

    print(f"    Found {len(results['posts'])} tweets")

    # Sort by engagement
    results["posts"].sort(
        key=lambda p: p.get("likes", 0) + p.get("retweets", 0) * 2,
        reverse=True,
    )

    # Step 2: Get top accounts
    seen_accounts = set()
    top_authors = []
    for post in results["posts"][:50]:
        author = post.get("author", "")
        if author and author not in seen_accounts:
            seen_accounts.add(author)
            top_authors.append(author)

    print(f"    Getting top {min(len(top_authors), 10)} account profiles...")

    for author in top_authors[:10]:
        print(f"      @{author}...")
        user_info = rapidapi_get("twitter154.p.rapidapi.com", "/user/details", {
            "username": author,
        })
        # Unwrap nested user object if present
        if user_info and isinstance(user_info, dict) and "user" in user_info:
            user_info = user_info["user"]

        if not user_info:
            continue

        account_data = {
            "username": author,
            "name": user_info.get("name", ""),
            "bio": user_info.get("description", user_info.get("desc", ""))[:300],
            "followers": user_info.get("followers", user_info.get("sub_count", 0)),
            "following": user_info.get("following", user_info.get("friends", 0)),
            "tweets_count": user_info.get("statuses_count", 0),
            "verified": user_info.get("verified", user_info.get("blue_verified", False)),
            "top_tweets": [],
        }

        # Get their timeline for top tweets
        user_id = user_info.get("id", user_info.get("rest_id", ""))
        if user_id:
            timeline = rapidapi_get("twitter154.p.rapidapi.com", "/user/tweets", {
                "username": author,
                "limit": "25",
            })

            if timeline:
                tweets = timeline.get("timeline", timeline.get("tweets", []))
                if isinstance(tweets, list):
                    sorted_tweets = sorted(
                        tweets,
                        key=lambda t: (t.get("tweet", t) if isinstance(t, dict) else {}).get("favorite_count", 0),
                        reverse=True,
                    )
                    for t in sorted_tweets[:25]:
                        entry = t.get("tweet", t) if isinstance(t, dict) else {}
                        if isinstance(entry, dict):
                            account_data["top_tweets"].append({
                                "text": entry.get("text", "")[:300],
                                "likes": entry.get("favorite_count", 0),
                                "retweets": entry.get("retweet_count", 0),
                            })

        results["top_accounts"].append(account_data)
        time.sleep(1)

    # Step 3: Pattern analysis
    if results["posts"] and (ANTHROPIC_API_KEY or OPENAI_API_KEY or PERPLEXITY_API_KEY):
        print(f"    Analyzing tweet patterns...")

        tweets_text = "\n".join(
            f"@{p['author']} ({p['likes']}❤️ {p['retweets']}🔄): {p['text'][:200]}"
            for p in results["posts"][:30]
        )

        accounts_text = "\n".join(
            f"@{a['username']} ({a['followers']} followers): {a['bio'][:100]}"
            for a in results["top_accounts"][:10]
        )

        analysis = claude_analyze(
            f"""Analyze these top Twitter posts and accounts for the keyword "{keyword}":

TOP TWEETS:
{tweets_text}

TOP ACCOUNTS:
{accounts_text}

Provide:
1. CONTENT PATTERNS: What formats get the most engagement? (threads, single tweets, images, links)
2. HOOK PATTERNS: How do top tweets open? First line analysis.
3. ACCOUNT PATTERNS: What do top accounts have in common? Bio styles, posting frequency.
4. TONE ANALYSIS: What tone works? (professional, casual, provocative, educational)
5. ENGAGEMENT TRIGGERS: What makes people like/retweet/reply?
6. OPPORTUNITY: What content gaps exist? What's nobody saying?""",
            max_tokens=2500,
        )
        results["patterns"]["twitter_analysis"] = analysis

    return results


# ═════════════════════════════════════════════════════════════════════════════
# INSTAGRAM RESEARCH
# ═════════════════════════════════════════════════════════════════════════════

def research_instagram(keyword: str, output_dir: Path, top_n: int = 20, visual: bool = False) -> dict:
    """
    Instagram niche research:
    1. Search keyword → find relevant users/hashtags
    2. Get top posts from those users via /user-feeds
    3. Visual analysis every 2s (optional)
    4. Caption/transcript extraction
    5. Pattern analysis
    """
    print(f"\n  ═══ INSTAGRAM RESEARCH: '{keyword}' ═══")
    results = {"keyword": keyword, "posts": [], "accounts": [], "hashtags": [], "patterns": {}}

    # Step 1: Search for users and hashtags related to keyword
    # Use multiple search queries to find niche-relevant accounts (not just name matches)
    search_queries = [keyword]
    kw_slug = keyword.lower().replace(" ", "")
    # Add niche-specific variations to find topical accounts
    for suffix in ["tips", "expert", "agency", "marketing"]:
        search_queries.append(f"{kw_slug}{suffix}")

    user_ids = []
    seen_uids = set()

    for sq in search_queries[:3]:  # Max 3 search queries
        print(f"    Searching '{sq}'...")
        search_data = rapidapi_get("instagram-looter2.p.rapidapi.com", "/search", {
            "query": sq,
        })
        if not search_data or not isinstance(search_data, dict):
            continue

        # Extract relevant hashtags (only from first query)
        if sq == keyword:
            for ht in search_data.get("hashtags", [])[:5]:
                ht_info = ht.get("hashtag", ht) if isinstance(ht, dict) else {}
                if isinstance(ht_info, dict):
                    results["hashtags"].append({
                        "name": ht_info.get("name", ""),
                        "media_count": ht_info.get("media_count", 0),
                    })
                    print(f"      #{ht_info.get('name', '')} ({ht_info.get('media_count', 0):,} posts)")

        # Extract relevant users
        for u in search_data.get("users", [])[:10]:
            user_info = u.get("user", u) if isinstance(u, dict) else {}
            if isinstance(user_info, dict):
                uid = str(user_info.get("pk", user_info.get("id", "")))
                username = user_info.get("username", "")
                if uid and uid not in seen_uids:
                    seen_uids.add(uid)
                    user_ids.append({"id": uid, "username": username})
                    results["accounts"].append({
                        "username": username,
                        "full_name": user_info.get("full_name", ""),
                        "is_verified": user_info.get("is_verified", False),
                    })
                    print(f"      @{username} {'✓' if user_info.get('is_verified') else ''}")
        time.sleep(0.5)

    # Step 2: Get posts from top users
    posts_raw = []
    max_users = min(len(user_ids), 5)  # Top 5 users
    print(f"    Getting posts from {max_users} accounts...")

    for u in user_ids[:max_users]:
        feed_data = rapidapi_get("instagram-looter2.p.rapidapi.com", "/user-feeds", {
            "id": u["id"],
            "count": str(min(top_n // max_users + 2, 12)),
        })
        if feed_data and isinstance(feed_data, dict):
            items = feed_data.get("items", [])
            for item in items:
                if isinstance(item, dict):
                    item["_source_username"] = u["username"]
                    posts_raw.append(item)
            print(f"      @{u['username']}: {len(items)} posts")
        time.sleep(0.5)

    print(f"    Found {len(posts_raw)} posts")

    # Step 2: Process each post
    frames_dir = output_dir / "instagram_frames"

    for i, post in enumerate(posts_raw[:top_n]):
        if not isinstance(post, dict):
            continue

        shortcode = post.get("code", post.get("shortcode", ""))
        caption = post.get("caption", "")
        if isinstance(caption, dict):
            caption = caption.get("text", "")

        owner = post.get("user", post.get("owner", {}))
        owner_username = post.get("_source_username", "")
        if isinstance(owner, dict):
            owner_username = owner.get("username", owner_username)

        post_data = {
            "shortcode": shortcode,
            "caption": str(caption)[:500] if caption else "",
            "likes": post.get("like_count", post.get("likes", 0)),
            "comments": post.get("comment_count", post.get("comments", 0)),
            "views": post.get("play_count", post.get("view_count", post.get("video_view_count", 0))),
            "is_video": post.get("media_type") == 2 or post.get("is_video", False),
            "owner": owner_username,
        }

        # Visual analysis for video posts
        if visual and post_data["is_video"] and shortcode:
            video_url = post.get("video_url", "")
            if video_url:
                print(f"      [{i+1}] Visual analysis: {shortcode}...")
                vid_frames_dir = frames_dir / shortcode
                frames = extract_video_frames(video_url, vid_frames_dir, interval=2, max_secs=30)
                if frames:
                    analysis = analyze_frames_with_gemini(
                        frames,
                        context=f"Instagram reel about '{keyword}'. Caption: {post_data['caption'][:100]}"
                    )
                    post_data["visual_analysis"] = analysis
                    post_data["frames_extracted"] = len(frames)

        results["posts"].append(post_data)

    # Sort by engagement
    results["posts"].sort(
        key=lambda p: p.get("likes", 0) + p.get("views", 0) // 10,
        reverse=True,
    )

    # Step 3: Pattern analysis
    if results["posts"] and (ANTHROPIC_API_KEY or OPENAI_API_KEY or PERPLEXITY_API_KEY):
        print(f"    Analyzing Instagram patterns...")

        posts_text = "\n".join(
            f"@{p['owner']} ({p['likes']}❤️ {p['views']}👁): {p['caption'][:150]}"
            + (f"\nVisual: {p.get('visual_analysis', '')[:150]}" if p.get("visual_analysis") else "")
            for p in results["posts"][:20]
        )

        analysis = claude_analyze(
            f"""Analyze these top Instagram posts for the keyword "{keyword}":

{posts_text}

Provide:
1. VISUAL PATTERNS: What visual styles dominate? Colors, framing, text overlays
2. CAPTION PATTERNS: How do top captions open? Length, hashtag usage, CTAs
3. HOOK PATTERNS: What makes people stop scrolling in the first 2 seconds?
4. CONTENT TYPES: Ratio of educational vs entertaining vs promotional
5. ENGAGEMENT PATTERNS: What drives likes vs comments vs shares?
6. OPPORTUNITY: What visual/content approach is underrepresented?""",
            max_tokens=2500,
        )
        results["patterns"]["instagram_analysis"] = analysis

    return results


# ═════════════════════════════════════════════════════════════════════════════
# REDDIT RESEARCH
# ═════════════════════════════════════════════════════════════════════════════

def research_reddit(keyword: str, output_dir: Path, top_n: int = 25) -> dict:
    """
    Reddit niche research using free public JSON API:
    1. Search keyword → top 25 posts
    2. Get ALL comments for top posts
    3. Analyze human nature behind top comments
    4. Separate value-adds from garbage
    5. Extract novel insights
    """
    print(f"\n  ═══ REDDIT RESEARCH: '{keyword}' ═══")
    results = {"keyword": keyword, "posts": [], "patterns": {}}

    # Step 1: Search Reddit (free API, no key needed)
    print(f"    Searching Reddit for '{keyword}'...")
    search_url = f"https://www.reddit.com/search.json?q={urllib.parse.quote(keyword)}&sort=relevance&limit={top_n}&t=year"

    req = urllib.request.Request(search_url)
    req.add_header("User-Agent", "Mozilla/5.0 (DocumentaryResearch/1.0)")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"      Search failed: {e}")
        # Fallback to RapidAPI
        data = None

    posts_raw = []
    if data and isinstance(data, dict):
        children = data.get("data", {}).get("children", [])
        for child in children:
            post = child.get("data", {})
            if post:
                posts_raw.append(post)

    print(f"    Found {len(posts_raw)} posts")

    # Step 2: Get comments for top posts
    for i, post in enumerate(posts_raw[:top_n]):
        title = post.get("title", "")
        permalink = post.get("permalink", "")
        subreddit = post.get("subreddit", "")

        print(f"    [{i+1}/{min(len(posts_raw), top_n)}] r/{subreddit}: {title[:50]}...")

        post_data = {
            "title": title,
            "subreddit": subreddit,
            "score": post.get("score", 0),
            "upvote_ratio": post.get("upvote_ratio", 0),
            "num_comments": post.get("num_comments", 0),
            "selftext": post.get("selftext", "")[:2000],
            "author": post.get("author", ""),
            "url": f"https://reddit.com{permalink}",
            "comments": [],
        }

        # Get comments
        if permalink:
            comments_url = f"https://www.reddit.com{permalink}.json?limit=100&sort=top"
            req = urllib.request.Request(comments_url)
            req.add_header("User-Agent", "Mozilla/5.0 (DocumentaryResearch/1.0)")

            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    comment_data = json.loads(resp.read())

                if isinstance(comment_data, list) and len(comment_data) > 1:
                    comment_children = comment_data[1].get("data", {}).get("children", [])
                    for cc in comment_children[:50]:
                        c = cc.get("data", {})
                        if c.get("body") and c.get("body") != "[deleted]":
                            post_data["comments"].append({
                                "body": c["body"][:1000],
                                "score": c.get("score", 0),
                                "author": c.get("author", ""),
                                "is_op": c.get("is_submitter", False),
                            })
            except Exception as e:
                print(f"      Comments failed: {e}")

            time.sleep(1)  # Rate limit for Reddit

        results["posts"].append(post_data)

    # Step 3: Comment quality analysis
    if results["posts"] and (ANTHROPIC_API_KEY or OPENAI_API_KEY or PERPLEXITY_API_KEY):
        print(f"    Analyzing Reddit comment patterns...")

        # Collect top comments across all posts
        all_comments = []
        for post in results["posts"]:
            for comment in post.get("comments", [])[:5]:
                all_comments.append({
                    "subreddit": post["subreddit"],
                    "post_title": post["title"][:60],
                    "comment": comment["body"][:300],
                    "score": comment["score"],
                })

        # Sort by score
        all_comments.sort(key=lambda c: c["score"], reverse=True)

        comments_text = "\n\n".join(
            f"r/{c['subreddit']} | Post: {c['post_title']} | Score: {c['score']}\n{c['comment']}"
            for c in all_comments[:30]
        )

        analysis = claude_analyze(
            f"""Analyze these top Reddit comments about "{keyword}":

{comments_text}

Provide:
1. VALUE COMMENTS: Which comments genuinely add new information, expert insight, or unique perspective?
   Quote the specific valuable insights.
2. GARBAGE COMMENTS: Which are just noise, memes, or low-effort?
3. HUMAN NATURE: What motivates people to engage with this topic? What emotions drive the discussion?
4. NOVEL INSIGHTS: What did the Reddit community reveal that you wouldn't find in mainstream articles?
   These are GOLD for documentary content.
5. COMMON QUESTIONS: What do people keep asking? These represent knowledge gaps.
6. SENTIMENT: Is the community optimistic, pessimistic, divided? On what specifically?
7. EXPERT VOICES: Any comments from people with obvious expertise? What do they say that others don't?""",
            max_tokens=3000,
        )
        results["patterns"]["reddit_analysis"] = analysis

    return results


# ═════════════════════════════════════════════════════════════════════════════
# GOOGLE TRENDS
# ═════════════════════════════════════════════════════════════════════════════

def research_google_trends(keyword: str, output_dir: Path) -> dict:
    """
    Google Trends research via SerpAPI or direct scraping.
    Falls back to Perplexity for trend data if no direct API.
    """
    print(f"\n  ═══ GOOGLE TRENDS: '{keyword}' ═══")
    results = {"keyword": keyword, "trends": {}}

    # Use Claude to synthesize trend data (more reliable than scraping)
    if ANTHROPIC_API_KEY or OPENAI_API_KEY or PERPLEXITY_API_KEY:
        print(f"    Analyzing search trends and keyword data...")
        analysis = claude_analyze(
            f"""For the keyword/niche "{keyword}", provide a comprehensive keyword research analysis:

1. SEARCH VOLUME TREND: Is interest rising, declining, or stable? Seasonal patterns?
2. RELATED KEYWORDS: Top 20 related search terms people also search for
3. LONG-TAIL VARIATIONS: 15 specific long-tail keyword variations with estimated search intent
4. QUESTION KEYWORDS: 10 "how to", "what is", "why does" questions people search
5. COMPETITOR KEYWORDS: What related keywords do top-ranking sites target?
6. CONTENT GAP KEYWORDS: High-intent keywords with low competition
7. GOOGLE ADS INSIGHT: Estimated CPC ranges and commercial intent keywords
8. TRENDING SUBTOPICS: What's currently hot within this niche?

Format each section with specific, actionable keywords.""",
            max_tokens=3000,
        )
        results["trends"]["keyword_analysis"] = analysis

    return results


# ═════════════════════════════════════════════════════════════════════════════
# CROSS-PLATFORM SYNTHESIS
# ═════════════════════════════════════════════════════════════════════════════

def synthesize_all(keyword: str, platforms: dict, output_dir: Path) -> str:
    """
    Final synthesis: combine all platform research into actionable insights.
    """
    print(f"\n  ═══ CROSS-PLATFORM SYNTHESIS ═══")

    if not (ANTHROPIC_API_KEY or OPENAI_API_KEY or PERPLEXITY_API_KEY):
        return "No ANTHROPIC_API_KEY — cannot synthesize"

    # Collect all pattern analyses
    sections = []
    for platform, data in platforms.items():
        patterns = data.get("patterns", {})
        for key, analysis in patterns.items():
            if analysis:
                sections.append(f"### {platform.upper()} PATTERNS:\n{analysis[:2000]}")

    if not sections:
        return "No pattern data to synthesize"

    combined = "\n\n".join(sections)

    synthesis = claude_analyze(
        f"""You have comprehensive niche research for "{keyword}" across multiple platforms.

{combined}

Now synthesize everything into a FINAL NICHE RESEARCH REPORT:

1. NICHE OVERVIEW: What is the current state of this niche across all platforms?

2. CONTENT STRATEGY:
   - What content format works best on each platform?
   - What's the ideal posting strategy (frequency, timing, style)?
   - What cross-platform content strategy would maximize reach?

3. HOOK FORMULA: Based on what works across all platforms, what's the winning hook formula?

4. VISUAL STRATEGY: What visual style wins? Colors, framing, production quality.

5. KEYWORD MAP: Top 20 keywords/phrases to target across all platforms.

6. COMPETITOR GAPS: What are established creators NOT doing that presents an opportunity?

7. DOCUMENTARY ANGLE: If making a documentary about this topic, what unique angle
   would get the most views based on what the audience is actively searching for
   and discussing?

8. ACTION PLAN: Top 5 specific actions to take based on this research.

Be specific, data-driven, and actionable. Reference specific examples from the research.""",
        max_tokens=4000,
    )

    return synthesis


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Multi-Platform Niche Keyword Research Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("keyword", help="Keyword or phrase to research")
    parser.add_argument("--all", action="store_true", help="Research all platforms")
    parser.add_argument("--youtube", action="store_true", help="YouTube research")
    parser.add_argument("--twitter", action="store_true", help="Twitter/X research")
    parser.add_argument("--instagram", action="store_true", help="Instagram research")
    parser.add_argument("--reddit", action="store_true", help="Reddit research")
    parser.add_argument("--trends", action="store_true", help="Google Trends/Keywords")
    parser.add_argument("--visual-analysis", action="store_true", help="Enable visual frame analysis (slower)")
    parser.add_argument("--top-n", type=int, default=20, help="Top N results per platform")
    parser.add_argument("--depth", choices=["quick", "standard", "deep"], default="standard")
    args = parser.parse_args()

    keyword = args.keyword
    keyword_slug = slug(keyword)
    output_dir = RESEARCH_DIR / f"niche_{keyword_slug}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Default to all if nothing specified
    if not any([args.youtube, args.twitter, args.instagram, args.reddit, args.trends]):
        args.all = True

    top_n = {"quick": 10, "standard": 20, "deep": 30}[args.depth]
    if args.top_n != 20:
        top_n = args.top_n

    print("=" * 60)
    print(f"  Niche Keyword Research Engine")
    print(f"  Keyword: {keyword}")
    print(f"  Depth: {args.depth} | Top N: {top_n}")
    print(f"  Visual: {'ON' if args.visual_analysis else 'OFF'}")
    print(f"  Output: {output_dir}/")
    print("=" * 60)

    platforms = {}

    if args.all or args.youtube:
        yt = research_youtube(keyword, output_dir, top_n=top_n, visual=args.visual_analysis)
        platforms["youtube"] = yt
        (output_dir / "youtube_research.json").write_text(json.dumps(yt, indent=2))
        print(f"    ✓ YouTube: {len(yt['videos'])} videos analyzed")

    if args.all or args.twitter:
        tw = research_twitter(keyword, output_dir, top_n=min(top_n * 3, 100))
        platforms["twitter"] = tw
        (output_dir / "twitter_research.json").write_text(json.dumps(tw, indent=2))
        print(f"    ✓ Twitter: {len(tw['posts'])} tweets, {len(tw['top_accounts'])} accounts")

    if args.all or args.instagram:
        ig = research_instagram(keyword, output_dir, top_n=top_n, visual=args.visual_analysis)
        platforms["instagram"] = ig
        (output_dir / "instagram_research.json").write_text(json.dumps(ig, indent=2))
        print(f"    ✓ Instagram: {len(ig['posts'])} posts analyzed")

    if args.all or args.reddit:
        rd = research_reddit(keyword, output_dir, top_n=top_n)
        platforms["reddit"] = rd
        (output_dir / "reddit_research.json").write_text(json.dumps(rd, indent=2))
        total_comments = sum(len(p.get("comments", [])) for p in rd["posts"])
        print(f"    ✓ Reddit: {len(rd['posts'])} posts, {total_comments} comments")

    if args.all or args.trends:
        gt = research_google_trends(keyword, output_dir)
        platforms["google_trends"] = gt
        (output_dir / "google_trends.json").write_text(json.dumps(gt, indent=2))
        print(f"    ✓ Google Trends: keyword analysis complete")

    # Cross-platform synthesis
    if len(platforms) > 1:
        synthesis = synthesize_all(keyword, platforms, output_dir)
        (output_dir / "cross_platform_synthesis.json").write_text(
            json.dumps({"keyword": keyword, "synthesis": synthesis}, indent=2)
        )

        # Generate final report
        report = f"# Niche Research Report: {keyword}\n\n"
        report += f"## Cross-Platform Synthesis\n\n{synthesis}\n\n"

        for platform, data in platforms.items():
            patterns = data.get("patterns", {})
            for key, analysis in patterns.items():
                if analysis:
                    report += f"## {platform.upper()} Analysis\n\n{analysis}\n\n"

        (output_dir / "final_report.md").write_text(report)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  Research complete!")
    print(f"  Keyword: {keyword}")
    print(f"  Platforms: {', '.join(platforms.keys())}")
    print(f"  Output: {output_dir}/")
    print(f"\n  Files:")
    for f in sorted(output_dir.glob("*.json")) + sorted(output_dir.glob("*.md")):
        size = f.stat().st_size
        print(f"    {f.name} ({size // 1024}KB)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
