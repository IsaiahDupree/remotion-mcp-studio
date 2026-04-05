#!/usr/bin/env python3
"""
Deep Research Pipeline — Generate documentary-grade scripts on ANY topic.

Enhanced with:
  - Multi-round reasoning (research → reason → ask more questions → deeper research)
  - Perplexity web search (grounded facts)
  - Reddit community insights (real discussions, debates, expert takes)
  - Claude synthesis (narrative structure, script writing)
  - Self-questioning loop (identifies knowledge gaps and fills them)

Takes a topic and produces:
  1. Deep multi-source research (web + Reddit + synthesis)
  2. Reasoning pass that identifies gaps and generates follow-up questions
  3. Second research pass to fill those gaps
  4. Structured chapter outline with chronological/thematic flow
  5. Full narration script with facts, dates, quotes, transitions
  6. Chapter metadata (titles, eras, colors, scene descriptions)
  7. Ready-to-feed into the documentary pipeline

Usage:
    python3 research_topic.py "The History of Artificial Intelligence"
    python3 research_topic.py "The Rise and Fall of Crypto" --chapters 8
    python3 research_topic.py "How Social Media Changed Politics" --depth deep
    python3 research_topic.py --from-file topic_brief.md

Output: research/{topic_slug}/
    ├── research_raw.json       # Raw research findings
    ├── research_round2.json    # Follow-up research after reasoning
    ├── reddit_insights.json    # Reddit community data
    ├── reasoning_log.json      # Reasoning chain + follow-up questions
    ├── outline.json            # Chapter structure
    ├── script.md               # Full narration script
    ├── chapter_meta.json       # Titles, eras, colors, image prompts
    └── generate_config.json    # Config to feed into the pipeline
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from textwrap import dedent

SCRIPT_DIR = Path(__file__).parent

PROJECT_DIR = Path(str(SCRIPT_DIR))
RESEARCH_DIR = PROJECT_DIR / "research"

# ─── API Keys ────────────────────────────────────────────────────────────────
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
RAPIDAPI_KEY = os.getenv(
    "RAPIDAPI_KEY",
    "a87cab3052mshf494034b3141e1ep1aacb0jsn580589e4be0b",
)

# Colors for chapter accent theming
CHAPTER_COLORS = [
    "#00ff88", "#ff6b35", "#4285f4", "#ea4335", "#fbbc04",
    "#34a853", "#9c27b0", "#00bcd4", "#ff4081", "#ff9800",
    "#00ff88", "#e91e63", "#3f51b5", "#009688", "#ff5722",
]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:60]


# ─── API Callers ─────────────────────────────────────────────────────────────

def api_call_claude(prompt: str, system: str = "", max_tokens: int = 8000) -> str:
    """Call AI API for script generation — tries Anthropic → OpenAI → Perplexity."""
    # Try Anthropic first
    if ANTHROPIC_API_KEY:
        try:
            payload = {
                "model": "claude-sonnet-4-6-20250131",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                payload["system"] = system
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
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            return data["content"][0]["text"]
        except Exception as e:
            print(f"    Anthropic failed: {e}")

    # Fallback to OpenAI
    if OPENAI_API_KEY:
        try:
            print("    Falling back to OpenAI...")
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            payload = {"model": "gpt-4o", "max_tokens": max_tokens, "messages": messages}
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"    OpenAI failed: {e}")

    # Fallback to Perplexity (web-grounded)
    if PERPLEXITY_API_KEY:
        try:
            print("    Falling back to Perplexity...")
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            payload = {"model": "sonar-pro", "max_tokens": min(max_tokens, 4000), "messages": messages}
            req = urllib.request.Request(
                "https://api.perplexity.ai/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"    Perplexity failed: {e}")

    raise ValueError("No AI API key available. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or PERPLEXITY_API_KEY.")


def api_call_perplexity(query: str) -> str:
    """Call Perplexity for web-grounded research."""
    if not PERPLEXITY_API_KEY:
        return ""

    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a research assistant for a documentary production. "
                    "Provide detailed, factual information with specific dates, names, "
                    "numbers, statistics, and sources. Be comprehensive and precise. "
                    "Include direct quotes from key figures when available."
                ),
            },
            {"role": "user", "content": query},
        ],
        "max_tokens": 4000,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"    Perplexity error: {e}")
        return ""


def api_call_reddit(endpoint: str, params: dict) -> dict | None:
    """
    Call Reddit3 RapidAPI endpoint.

    Working endpoints (base: /v1/reddit/):
      /v1/reddit/subreddit/comments?subreddit=X  → comments with body, ups, link_title
      /v1/reddit/subreddit/info?subreddit=X       → subreddit metadata
      /v1/reddit/subreddit/new?subreddit=X        → new subreddits
      /v1/reddit/subreddit/popular                 → popular subreddits
      /v1/reddit/user-stats?username=X             → user stats
      /v1/reddit/user-data?username=X              → user data
    """
    host = "reddit3.p.rapidapi.com"
    query = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    url = f"https://{host}{endpoint}?{query}" if query else f"https://{host}{endpoint}"

    req = urllib.request.Request(url)
    req.add_header("x-rapidapi-key", RAPIDAPI_KEY)
    req.add_header("x-rapidapi-host", host)
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"    Reddit API error: {e}")
        return None


# ─── Reddit Research ─────────────────────────────────────────────────────────

def research_reddit(topic: str, depth: str = "standard") -> list[dict]:
    """
    Pull relevant Reddit discussions about the topic.
    Searches multiple subreddits and extracts community insights.
    """
    print(f"  Reddit research: {topic}")
    findings = []

    # Generate search queries
    search_queries = [topic]
    if depth == "deep":
        # Generate more specific Reddit search queries
        extra = api_call_claude(
            f"Generate 4 specific Reddit search queries to find expert discussions about: {topic}\n"
            f"Target subreddits like r/AskHistorians, r/explainlikeimfive, r/TrueReddit, "
            f"or topic-specific subreddits.\n"
            f"Return ONLY a JSON array of query strings.",
            max_tokens=500,
        )
        try:
            match = re.search(r"\[.*\]", extra, re.DOTALL)
            if match:
                search_queries.extend(json.loads(match.group()))
        except (json.JSONDecodeError, AttributeError):
            pass

    # Pull comments from topic-specific subreddits (the working endpoint)
    topic_subs = _infer_subreddits(topic)
    for sub in topic_subs[:4]:
        print(f"    r/{sub} comments...")
        result = api_call_reddit("/v1/reddit/subreddit/comments", {"subreddit": sub})

        if result and isinstance(result, dict):
            comments = result.get("body", [])
            if isinstance(comments, list):
                for comment in comments[:10]:
                    body = comment.get("body", "")[:800]
                    author = comment.get("author", "")
                    ups = comment.get("ups", 0)
                    link_title = comment.get("link_title", "")
                    subreddit = comment.get("subreddit", sub)

                    if body and len(body) > 30:  # Skip very short comments
                        findings.append({
                            "source": "reddit",
                            "subreddit": subreddit,
                            "title": link_title,
                            "content": body,
                            "score": ups,
                            "author": author,
                            "query": f"r/{sub} comments",
                        })

        time.sleep(0.5)

    # Get subreddit info for context
    for sub in topic_subs[:2]:
        print(f"    r/{sub} info...")
        info = api_call_reddit("/v1/reddit/subreddit/info", {"subreddit": sub})
        if info and isinstance(info, dict):
            body = info.get("body", [])
            if isinstance(body, list) and body:
                sub_info = body[0]
                desc = sub_info.get("public_description", sub_info.get("description", ""))
                subscribers = sub_info.get("subscribers", 0)
                if desc:
                    findings.append({
                        "source": "reddit_meta",
                        "subreddit": sub,
                        "title": f"r/{sub} ({subscribers:,} subscribers)",
                        "content": desc[:500],
                        "score": subscribers,
                        "query": f"r/{sub} info",
                    })

        time.sleep(0.5)

    # Sort by score (most upvoted = most community agreement)
    findings.sort(key=lambda f: f.get("score", 0), reverse=True)
    return findings[:30]  # Top 30 most relevant


def _infer_subreddits(topic: str) -> list[str]:
    """Infer relevant subreddits for a topic."""
    topic_lower = topic.lower()

    # Common topic → subreddit mappings
    mappings = {
        "ai": ["artificial", "MachineLearning", "ChatGPT", "singularity"],
        "artificial intelligence": ["artificial", "MachineLearning", "ChatGPT", "singularity"],
        "crypto": ["CryptoCurrency", "Bitcoin", "ethereum", "CryptoMarkets"],
        "bitcoin": ["Bitcoin", "CryptoCurrency", "btc"],
        "seo": ["SEO", "bigseo", "TechSEO", "digital_marketing"],
        "social media": ["socialmedia", "marketing", "content_marketing"],
        "politics": ["politics", "PoliticalDiscussion", "NeutralPolitics"],
        "technology": ["technology", "Futurology", "gadgets"],
        "programming": ["programming", "learnprogramming", "coding"],
        "history": ["history", "AskHistorians", "HistoryMemes"],
        "space": ["space", "SpaceX", "astronomy"],
        "gaming": ["gaming", "Games", "pcgaming"],
        "finance": ["finance", "personalfinance", "investing"],
        "climate": ["climate", "environment", "ClimateActionPlan"],
        "music": ["Music", "LetsTalkMusic", "musictheory"],
    }

    found = []
    for keyword, subs in mappings.items():
        if keyword in topic_lower:
            found.extend(subs)

    if not found:
        # Default: use the topic as a subreddit name guess
        found = [slug(topic).replace("_", ""), "todayilearned", "explainlikeimfive"]

    return found[:5]


# ─── Multi-Round Reasoning ───────────────────────────────────────────────────

def reason_through_research(topic: str, findings: list[dict], reddit: list[dict]) -> dict:
    """
    Reasoning pass: analyze all research, identify gaps, generate follow-up questions.

    This is the "think harder" step — it reads everything gathered so far and asks:
    - What's missing?
    - What contradictions exist?
    - What would make this documentary unique?
    - What specific facts/dates/quotes are we lacking?
    """
    print(f"  Reasoning through {len(findings)} findings + {len(reddit)} Reddit insights...")

    research_summary = "\n\n".join(
        f"**[{f.get('source', 'web')}] {f.get('query', '')}**\n{f.get('content', '')[:1500]}"
        for f in findings[:10]
    )

    reddit_summary = "\n\n".join(
        f"**r/{r['subreddit']} ({r['score']} upvotes): {r['title']}**\n{r.get('content', '')[:500]}"
        for r in reddit[:10]
    )

    reasoning_prompt = f"""You are a documentary researcher analyzing gathered data about: "{topic}"

RESEARCH GATHERED:
{research_summary[:8000]}

REDDIT COMMUNITY INSIGHTS:
{reddit_summary[:4000]}

Now reason through this data carefully:

1. KNOWLEDGE GAPS: What critical information is MISSING that a great documentary needs?
   - Specific dates or timelines we don't have yet
   - Key figures whose stories we haven't found
   - Turning points that aren't well documented in our research
   - Statistics or data that would make arguments compelling

2. CONTRADICTIONS: Are any sources contradicting each other? What's the truth?

3. UNIQUE ANGLES: What surprising or counter-intuitive insights did the Reddit community reveal?
   What perspectives would make this documentary different from existing content?

4. EMOTIONAL HOOKS: What human stories, dramatic moments, or surprising facts would
   keep a viewer watching? What's the "Netflix hook" for each potential chapter?

5. FOLLOW-UP QUESTIONS: Generate 5-8 SPECIFIC research queries that would fill the gaps.
   These should be precise enough to get concrete answers (not vague).

Return ONLY valid JSON:
{{
    "gaps": ["gap 1", "gap 2", ...],
    "contradictions": ["contradiction 1", ...],
    "unique_angles": ["angle 1", "angle 2", ...],
    "emotional_hooks": ["hook 1", "hook 2", ...],
    "follow_up_questions": ["specific question 1", "specific question 2", ...],
    "confidence_score": 0.0-1.0,
    "reasoning_notes": "free-form analysis notes"
}}"""

    raw = api_call_claude(
        reasoning_prompt,
        system="You are an analytical documentary researcher. Be specific, not vague.",
        max_tokens=4000,
    )

    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        reasoning = json.loads(match.group()) if match else {}
    except (json.JSONDecodeError, AttributeError):
        reasoning = {
            "gaps": [],
            "follow_up_questions": [f"Detailed timeline of {topic}", f"Key controversies about {topic}"],
            "confidence_score": 0.5,
            "reasoning_notes": raw[:2000],
        }

    print(f"    Confidence: {reasoning.get('confidence_score', '?')}")
    print(f"    Gaps found: {len(reasoning.get('gaps', []))}")
    print(f"    Follow-ups: {len(reasoning.get('follow_up_questions', []))}")
    for q in reasoning.get("follow_up_questions", [])[:5]:
        print(f"      → {q[:70]}...")

    return reasoning


def research_follow_ups(questions: list[str], topic: str) -> list[dict]:
    """
    Second research pass: answer the follow-up questions identified by reasoning.
    Uses Perplexity for web-grounded answers and Reddit for community perspectives.
    """
    print(f"\n  Follow-up research: {len(questions)} questions...")
    findings = []

    for i, question in enumerate(questions[:8]):
        print(f"    [{i+1}/{min(len(questions), 8)}] {question[:60]}...")

        # Perplexity for factual answers
        answer = api_call_perplexity(question)
        if answer:
            findings.append({
                "query": question,
                "content": answer,
                "source": "perplexity_followup",
                "round": 2,
            })

        # Reddit for community perspective on the same question
        reddit_result = api_call_reddit("/search", {"query": question[:100], "sort": "relevance"})
        if reddit_result and isinstance(reddit_result, dict):
            posts = reddit_result.get("data", reddit_result.get("posts", []))
            if isinstance(posts, list):
                for post in posts[:2]:
                    title = post.get("title", "")
                    content = post.get("selftext", post.get("body", ""))[:600]
                    if title:
                        findings.append({
                            "query": question,
                            "content": f"[Reddit] {title}: {content}",
                            "source": "reddit_followup",
                            "round": 2,
                        })

        time.sleep(1)

    return findings


# ─── Research Phase ──────────────────────────────────────────────────────────

def research_topic(topic: str, depth: str = "standard") -> dict:
    """
    Conduct multi-round, multi-source research on a topic.

    Round 1: Perplexity web search + Reddit community insights
    Reasoning: Analyze gaps, contradictions, follow-up questions
    Round 2: Targeted follow-up research to fill gaps
    """
    print(f"  Researching: {topic}")
    research = {"topic": topic, "queries": [], "findings": [], "reddit": [], "reasoning": {}}

    # Step 1: Generate research queries
    num_queries = {"quick": 4, "standard": 6, "deep": 10}[depth]
    query_prompt = f"""Generate {num_queries} specific research queries for a documentary about:
"{topic}"

Each query should target a different aspect:
1. Origin/history — when and how did this begin?
2. Key figures — who were the most important people?
3. Major turning points — what events changed everything?
4. Controversies — what went wrong or was debated?
5. Technical details — how does the core technology/system work?
{"6. Cultural impact — how did this change society?" if depth in ("standard", "deep") else ""}
{"7. Current state — where does this stand today?" if depth in ("standard", "deep") else ""}
{"8. Economic impact — what are the numbers/statistics?" if depth == "deep" else ""}
{"9. Expert predictions — what do authorities predict?" if depth == "deep" else ""}
{"10. Counter-narratives — what do critics say?" if depth == "deep" else ""}

Return ONLY a JSON array of query strings, no other text."""

    queries_raw = api_call_claude(query_prompt, max_tokens=1500)
    try:
        match = re.search(r"\[.*\]", queries_raw, re.DOTALL)
        queries = json.loads(match.group()) if match else [topic]
    except (json.JSONDecodeError, AttributeError):
        queries = [
            f"Complete history and timeline of {topic}",
            f"Key people and figures in {topic}",
            f"Major turning points in {topic}",
            f"Controversies and debates about {topic}",
            f"Current state and future of {topic}",
        ]

    research["queries"] = queries

    # Step 2: Round 1 — Perplexity web search
    print(f"\n  Round 1: Web research ({len(queries)} queries)...")
    for i, query in enumerate(queries):
        print(f"    [{i+1}/{len(queries)}] {query[:60]}...")
        finding = api_call_perplexity(query)
        if finding:
            research["findings"].append({
                "query": query,
                "content": finding,
                "source": "perplexity",
                "round": 1,
            })
        else:
            # Fallback to Claude
            finding = api_call_claude(
                f"Research this thoroughly with specific facts, dates, and names:\n{query}",
                system="You are a documentary researcher. Provide detailed, factual information.",
                max_tokens=3000,
            )
            research["findings"].append({
                "query": query,
                "content": finding,
                "source": "claude",
                "round": 1,
            })
        time.sleep(1)

    print(f"    ✓ {len(research['findings'])} findings from web research")

    # Step 3: Reddit community insights
    print(f"\n  Round 1: Reddit community research...")
    research["reddit"] = research_reddit(topic, depth)
    print(f"    ✓ {len(research['reddit'])} Reddit insights")

    # Step 4: Reasoning pass — analyze gaps and generate follow-ups
    print(f"\n  Reasoning pass...")
    research["reasoning"] = reason_through_research(
        topic, research["findings"], research["reddit"]
    )

    # Step 5: Round 2 — Follow-up research
    follow_ups = research["reasoning"].get("follow_up_questions", [])
    if follow_ups:
        print(f"\n  Round 2: Follow-up research...")
        round2 = research_follow_ups(follow_ups, topic)
        research["findings"].extend(round2)
        print(f"    ✓ {len(round2)} additional findings")

    # Step 6: Final confidence check
    total = len(research["findings"])
    reddit_total = len(research["reddit"])
    confidence = research["reasoning"].get("confidence_score", 0.5)

    print(f"\n  Research complete:")
    print(f"    Web findings: {total}")
    print(f"    Reddit insights: {reddit_total}")
    print(f"    Confidence: {confidence:.0%}")
    print(f"    Unique angles: {len(research['reasoning'].get('unique_angles', []))}")

    return research


# ─── Outline Phase ───────────────────────────────────────────────────────────

def generate_outline(topic: str, research: dict, num_chapters: int = 11) -> dict:
    """Generate a structured chapter outline from all research sources."""
    print(f"\n  Generating {num_chapters}-chapter outline...")

    # Combine all research into a rich context
    web_text = "\n\n---\n\n".join(
        f"**{f['query']}** (source: {f['source']})\n{f['content']}"
        for f in research["findings"][:15]
    )

    reddit_text = "\n\n".join(
        f"**r/{r['subreddit']} ({r['score']}↑): {r['title']}**\n{r.get('content', '')[:300]}"
        for r in research.get("reddit", [])[:10]
    )

    reasoning = research.get("reasoning", {})
    angles = reasoning.get("unique_angles", [])
    hooks = reasoning.get("emotional_hooks", [])

    outline_prompt = f"""Based on extensive research about "{topic}", create a {num_chapters}-chapter documentary outline.

WEB RESEARCH:
{web_text[:10000]}

REDDIT COMMUNITY INSIGHTS:
{reddit_text[:3000]}

UNIQUE ANGLES IDENTIFIED:
{json.dumps(angles[:5])}

EMOTIONAL HOOKS:
{json.dumps(hooks[:5])}

Requirements:
- Each chapter covers a distinct era, theme, or turning point
- Chronological or thematic flow (first = intro/hook, last = conclusion/future)
- Each chapter: title, era/time period, 4-6 key points with SPECIFIC facts
- Include specific dates, full names, real numbers from the research
- Incorporate the unique angles and emotional hooks identified
- Include at least one "surprising fact" per chapter that would hook a viewer
- Target: each chapter ≈ 2-3 minutes of narration (200-400 words)

Return ONLY valid JSON:
{{
  "title": "Documentary Title — Compelling Subtitle",
  "chapters": [
    {{
      "id": "00_intro",
      "title": "Chapter Title",
      "era": "Time Period",
      "key_points": ["specific point 1", "specific point 2", ...],
      "hook": "Opening line that grabs attention",
      "surprising_fact": "A fact that would make someone stop scrolling",
      "tone": "dramatic | reflective | urgent | hopeful",
      "reddit_insight": "What the community uniquely contributed to this chapter"
    }}
  ]
}}"""

    outline_raw = api_call_claude(outline_prompt, max_tokens=6000)

    try:
        match = re.search(r"\{.*\}", outline_raw, re.DOTALL)
        outline = json.loads(match.group()) if match else {}
    except (json.JSONDecodeError, AttributeError):
        raise ValueError(f"Failed to parse outline JSON. Raw: {outline_raw[:500]}")

    # Ensure chapter IDs are properly formatted
    for i, ch in enumerate(outline.get("chapters", [])):
        if not ch.get("id"):
            ch["id"] = f"{i:02d}_{slug(ch.get('title', f'chapter_{i}'))}"

    return outline


# ─── Script Phase ────────────────────────────────────────────────────────────

def generate_script(topic: str, outline: dict, research: dict) -> str:
    """Generate the full narration script, chapter by chapter, with rich research context."""
    print(f"\n  Writing narration script...")

    # Build a research index by topic for targeted context
    all_research = "\n\n".join(f['content'][:1500] for f in research["findings"])
    reddit_insights = "\n".join(
        f"- r/{r['subreddit']}: {r['title']}" for r in research.get("reddit", [])[:15]
    )
    reasoning_notes = research.get("reasoning", {}).get("reasoning_notes", "")

    full_script = f"# {outline.get('title', topic)}\n\n"

    for i, chapter in enumerate(outline["chapters"]):
        print(f"    [{i+1}/{len(outline['chapters'])}] {chapter['title']}...")

        script_prompt = f"""Write the narration script for Chapter {i+1} of a documentary about "{topic}".

CHAPTER: {chapter['title']}
ERA: {chapter.get('era', '')}
KEY POINTS: {json.dumps(chapter.get('key_points', []))}
HOOK: {chapter.get('hook', '')}
SURPRISING FACT: {chapter.get('surprising_fact', '')}
TONE: {chapter.get('tone', 'dramatic')}
REDDIT INSIGHT: {chapter.get('reddit_insight', '')}

RESEARCH CONTEXT (use specific facts from this):
{all_research[:5000]}

COMMUNITY PERSPECTIVES:
{reddit_insights[:1500]}

ANALYSIS NOTES:
{reasoning_notes[:1000]}

PREVIOUS CHAPTERS WRITTEN:
{full_script[-2000:] if len(full_script) > 100 else "(This is the first chapter)"}

Requirements:
- Write 250-450 words of narration (2.5-3.5 minutes when spoken)
- Start with the hook — immediately grab attention
- Include AT LEAST 3 specific facts: exact dates, full names, real numbers
- Include the surprising fact naturally — frame it as a revelation
- Use vivid, cinematic language suitable for a Netflix-quality documentary
- If Reddit discussions revealed a unique perspective, weave it in naturally
- End with a transition that creates anticipation for the next chapter
- Write in second person where powerful ("Imagine..." "Think about that...")
- NO stage directions, NO [brackets], NO metadata — ONLY narration text
- Sound like an award-winning documentary narrator: authoritative, dramatic, human

Write ONLY the narration text."""

        chapter_script = api_call_claude(
            script_prompt,
            system=(
                "You are an award-winning documentary scriptwriter. "
                "Your narration is factual, engaging, and cinematic. "
                "You write like the narrator of a Netflix/HBO documentary — "
                "authoritative but accessible, dramatic but honest. "
                "Every sentence should make the viewer want to hear the next one."
            ),
            max_tokens=2500,
        )

        full_script += f"\n## {chapter['title']}\n\n{chapter_script.strip()}\n"
        time.sleep(0.5)

    return full_script


# ─── Metadata Phase ─────────────────────────────────────────────────────────

def generate_chapter_meta(outline: dict) -> dict:
    """Generate chapter metadata for the rendering pipeline."""
    chapters = outline.get("chapters", [])
    meta = {}

    for i, ch in enumerate(chapters):
        chapter_id = ch["id"]
        color = CHAPTER_COLORS[i % len(CHAPTER_COLORS)]

        meta[chapter_id] = {
            "title": ch["title"],
            "era": ch.get("era", ""),
            "color": color,
            "tone": ch.get("tone", "dramatic"),
            "surprising_fact": ch.get("surprising_fact", ""),
            "image_style_hints": ch.get("key_points", [])[:3],
        }

    return meta


def generate_pipeline_config(
    topic: str,
    outline: dict,
    meta: dict,
    output_dir: Path,
) -> dict:
    """Generate the config needed to run the full documentary pipeline."""
    chapter_ids = [ch["id"] for ch in outline["chapters"]]

    config = {
        "topic": topic,
        "title": outline.get("title", topic),
        "chapter_ids": chapter_ids,
        "chapter_meta": meta,
        "script_file": str(output_dir / "script.md"),
        "audio_dir": str(PROJECT_DIR / "audio"),
        "characters_dir": str(PROJECT_DIR / "characters"),
        "scene_images_dir": str(PROJECT_DIR / "scene_images"),
        "output_dir": str(PROJECT_DIR / "output"),
        "pipeline_steps": [
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
        ],
    }

    return config


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Deep Research → Documentary Script Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("topic", nargs="?", help="Documentary topic")
    parser.add_argument("--from-file", help="Read topic brief from a file")
    parser.add_argument("--chapters", type=int, default=11, help="Number of chapters (default: 11)")
    parser.add_argument("--depth", choices=["quick", "standard", "deep"], default="standard",
                        help="Research depth (default: standard)")
    parser.add_argument("--skip-research", action="store_true",
                        help="Skip research, use cached data")
    parser.add_argument("--skip-reddit", action="store_true",
                        help="Skip Reddit research")
    args = parser.parse_args()

    # Get topic
    if args.from_file:
        topic = Path(args.from_file).read_text().strip()
    elif args.topic:
        topic = args.topic
    else:
        parser.print_help()
        sys.exit(1)

    topic_slug = slug(topic)
    output_dir = RESEARCH_DIR / topic_slug
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"  Documentary Research Pipeline (Enhanced)")
    print(f"  Topic: {topic}")
    print(f"  Chapters: {args.chapters} | Depth: {args.depth}")
    print(f"  Sources: Perplexity + Reddit + Claude reasoning")
    print(f"  Output: {output_dir}/")
    print("=" * 60)

    # Step 1: Research (multi-round)
    research_path = output_dir / "research_raw.json"
    if args.skip_research and research_path.exists():
        print("\n1. Loading cached research...")
        research = json.loads(research_path.read_text())
    else:
        print("\n1. Multi-round deep research...")
        research = research_topic(topic, depth=args.depth)
        research_path.write_text(json.dumps(research, indent=2))

        # Save sub-components
        if research.get("reddit"):
            (output_dir / "reddit_insights.json").write_text(
                json.dumps(research["reddit"], indent=2)
            )
        if research.get("reasoning"):
            (output_dir / "reasoning_log.json").write_text(
                json.dumps(research["reasoning"], indent=2)
            )
        # Save round 2 separately
        round2 = [f for f in research["findings"] if f.get("round") == 2]
        if round2:
            (output_dir / "research_round2.json").write_text(
                json.dumps(round2, indent=2)
            )

        web_count = len([f for f in research["findings"] if f.get("round") == 1])
        r2_count = len(round2)
        reddit_count = len(research.get("reddit", []))
        print(f"\n   ✓ Round 1: {web_count} web findings")
        print(f"   ✓ Reddit: {reddit_count} community insights")
        print(f"   ✓ Round 2: {r2_count} follow-up findings")

    # Step 2: Outline
    print("\n2. Chapter outline generation...")
    outline = generate_outline(topic, research, num_chapters=args.chapters)
    (output_dir / "outline.json").write_text(json.dumps(outline, indent=2))
    print(f"   ✓ {len(outline.get('chapters', []))} chapters outlined")
    for ch in outline.get("chapters", []):
        print(f"     {ch['id']}: {ch['title']} ({ch.get('era', '')})")

    # Step 3: Full script
    print("\n3. Narration script writing...")
    script = generate_script(topic, outline, research)
    (output_dir / "script.md").write_text(script)
    word_count = len(script.split())
    est_minutes = word_count / 150
    print(f"   ✓ {word_count} words (~{est_minutes:.0f} minutes)")

    # Step 4: Chapter metadata
    print("\n4. Generating pipeline metadata...")
    meta = generate_chapter_meta(outline)
    (output_dir / "chapter_meta.json").write_text(json.dumps(meta, indent=2))

    # Step 5: Pipeline config
    config = generate_pipeline_config(topic, outline, meta, output_dir)
    (output_dir / "generate_config.json").write_text(json.dumps(config, indent=2))

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  Research & script complete!")
    print(f"  Title: {outline.get('title', topic)}")
    print(f"  Chapters: {len(outline.get('chapters', []))}")
    print(f"  Script: {word_count} words (~{est_minutes:.0f} min)")
    print(f"  Sources: Perplexity + Reddit + Claude (2 rounds)")
    print(f"  Output: {output_dir}/")
    print(f"\n  Next steps:")
    print(f"    1. Review script:  cat {output_dir}/script.md")
    print(f"    2. Generate audio: python3 generate_voiceover.py --config {output_dir}/generate_config.json")
    print(f"    3. QA gate:        python3 voice_qa_gate.py --auto-fix")
    print(f"    4. Run pipeline:   bash render_and_upload.sh")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
