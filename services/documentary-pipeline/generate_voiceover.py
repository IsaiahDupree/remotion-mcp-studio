#!/usr/bin/env python3
"""
Generate SEO Documentary voiceover via ElevenLabs API
Splits script into segments and generates MP3 files per chapter
"""
import os
import json
import time
import requests
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "k0HDiJKO5QdXkGN6NSLI"  # Isaiah's cloned voice
OUTPUT_DIR = SCRIPT_DIR / "audio")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Documentary chapters with their scripts
CHAPTERS = {
    "00_intro": """Imagine a world where the internet was brand new. Where nobody knew the rules. Where you could rank number one on the entire web just by typing the same word one hundred times at the bottom of a page in white text on a white background. Nobody would see it. But the machines would.

That was the birth of SEO.

And over the next thirty years, the game would change so dramatically, so completely, that what worked in 1995 would get you banned in 2015. And what works in 2026 would have been science fiction in 2010.

This is the complete history of Search Engine Optimization — from the first website ever published, to the age of AI that is rewriting every rule we thought we knew.

I'm going to take you decade by decade, algorithm by algorithm, through every major shift that changed how the internet works and how businesses fight for visibility.

Whether you're an SEO veteran who lived through the Panda and Penguin updates, or you're just starting out in the age of AI Overviews — this documentary is for you.

Because understanding where SEO came from is the only way to understand where it's going.

Let's start at the very beginning.""",

    "01_wild_west": """Chapter One. The Wild West. Before Google, there was chaos.

August 6th, 1991. A physicist named Tim Berners-Lee published the world's first website on a NeXT computer at CERN in Switzerland. It was a simple page explaining what the World Wide Web was. There were no ads. No rankings. No SEO. There was barely an internet.

But within a few years, everything changed.

By 1994, people were building websites like crazy — businesses, academics, hobbyists. And nobody could find anything.

This is when the first search engines appeared. Not Google. Not even close.

In 1990, a researcher named Alan Emtage created Archie — the world's first search engine. It indexed FTP file archives. Then came Gopher, WAIS, and Veronica.

But the real explosion happened in 1994. That's when Yahoo launched — not as a search engine, but as a human-curated directory. Real people were literally sitting in offices, visiting websites, and deciding whether they were worth listing. If Yahoo included your site, you were set. If they didn't, you basically didn't exist.

The same year, AltaVista and Lycos launched. Infoseek, Excite. These were the early search engines — crawling the web with automated bots and trying to figure out which pages were relevant to which searches.

And this is where SEO was born.

The very first SEO tactic ever documented? A manager at Jefferson Starship — yes, the rock band — discovered their website ranked on page four of search results. Frustrated, he told his web team: just put our name on the page as many times as possible. Repeat it over and over.

It worked.

That's it. That's the origin of search engine optimization. Keyword stuffing.

And from 1994 to 1997, this is all SEO really was. Keyword stuffing. Repeating your target keywords hundreds of times on a page — sometimes in normal text, sometimes hidden. White text on a white background. Meta tag manipulation. Search engines heavily relied on the meta keywords tag — a hidden section of HTML where you could declare what your page was about. The trick? Stuff it with every keyword imaginable. Doorway pages. Build hundreds of nearly identical pages, each optimized for a slightly different keyword, all funneling to your main site.

The search engines of this era were incredibly naive. They essentially trusted whatever you told them.

In 1997, a man named Danny Sullivan launched Search Engine Watch — the first major publication dedicated to helping people navigate these new search tools. SEO was becoming a real profession.

But the chaos couldn't last. Someone was about to change everything.""",

    "02_pagerank": """Chapter Two. The PageRank Revolution. Two Stanford students changed the internet forever.

1996. Two Stanford PhD students — Larry Page and Sergey Brin — had a theory.

What if instead of ranking websites based on what they said about themselves, you ranked them based on what other people said about them?

What if a link from one website to another was essentially a vote of confidence? And what if some votes counted more than others — based on how many votes that voter had received?

They called it PageRank, named after Larry Page. And it was brilliant.

Think about it like academic citations. If a paper is cited by hundreds of respected researchers, it's probably important. If a random blog nobody reads cites it, that doesn't mean as much. PageRank applied the same logic to web links.

Their project, initially called BackRub, became Google. The company launched on September 27th, 1998.

And in the first few years, Google was remarkable. The results were clean. Relevant. Better than anything else on the market. Within three years, Google had captured the majority of search traffic. Yahoo, AltaVista, Lycos — they were fading.

For SEO practitioners in 1998 to 2002, the playbook completely changed.

On-page keywords still mattered. But now, off-page links were the real currency.

If you could get the New York Times to link to your website, your rankings would explode. Backlink building became an industry. People were cold-emailing webmasters, writing guest posts, creating resource pages just to attract links.

The concept of "link juice" emerged — the idea that when a high-authority page linked to you, it passed some of its ranking power to your site.

Google also introduced the Google Toolbar PageRank score — a visible zero-to-ten number showing any site's authority. This became obsessively tracked. Websites with PageRank eight or nine were internet royalty.

The year-by-year SEO strategy in this era was simple. Get as many links as possible from authoritative sources. Directory submissions, press releases, partnerships.

Google launched AdWords in 2000, proving they could monetize search. And by 2002, the age of Google was firmly established.

The question was: could the spam artists keep up?""",

    "03_algorithm_wars": """Chapter Three. The Algorithm Wars. Black Hat versus Google — the arms race begins.

Once SEOs figured out that links equal rankings, the obvious next step was: manufacture links. As many as possible.

And so began one of the most creative, chaotic, and ultimately unsustainable periods in internet history.

Link farms. Private Blog Networks. Comment spam. Forum spam. Article spinning. Link wheels. Three-way link exchanges. Hidden redirects.

The black hat SEO industry exploded. Companies were selling links openly. Buy ten thousand links for ninety-nine dollars. Entire networks of fake websites existed only to pass link juice around. It worked shockingly well.

Then came November 2003.

Google launched an algorithm update so significant that SEOs named it Florida. Hundreds of thousands of websites lost their rankings overnight. Google had cracked down on keyword stuffing and blatant link manipulation. Businesses that had been living off black hat tactics were suddenly invisible.

The Florida update set a pattern that would define the next decade: build a spam tactic, watch it work, watch Google kill it, adapt, repeat.

2003 to 2010 was a constant arms race.

Exact match domains were still king. If you owned insurance dot com or loans dot com, you had a massive advantage. Article spinning software generated thousands of variations of a single piece of content, each submitted to article directories for links.

Private Blog Networks emerged. Sophisticated operators bought expired domains with existing authority, built fake content sites on them, and used them to link to their money sites.

Link wheels and pyramids. Build tier-one links from legitimate sources, then build tier-two links pointing to those tier-one sources to boost their power.

Google wasn't sitting still. They launched the Caffeine update in 2010 — a complete overhaul of their crawling infrastructure. But the biggest reckoning was coming. And it had a name: Panda.""",

    "04_quality_revolution": """Chapter Four. The Quality Revolution. Content farms die, and semantic search is born.

By 2010, Google had a problem.

Search results were full of garbage.

Content farms — companies like Demand Media's eHow — had figured out a formula. Take a keyword. Write a three-hundred-word article. Publish it. Repeat ten thousand times. The articles answered the technical question of whether this page has content about this topic, but they were useless to real humans. Thin. Shallow. Nobody actually benefitted from reading them.

Demand Media alone was publishing four thousand articles a day. Their entire business model was gaming Google's content signals.

On February 24th, 2011, Google deployed what they internally called the Farmer update. The world called it Panda.

The impact was seismic.

Sites like Mahalo, eHow, HubPages, Ezine Articles — they lost 40%, 50%, sometimes 80% of their traffic overnight. If you had a legitimate content business built on quality, you were fine or even gained. If you were a content farm, you were finished.

Then on April 24th, 2012 came the Penguin update.

If Panda targeted bad content, Penguin targeted bad links.

Penguin specifically went after unnatural link patterns — the exact tactics that had worked so well for the previous decade. Keyword-heavy anchor text in backlinks? Penguin flagged it. Links from link farms and private blog networks? Penguin caught them.

Overnight, the black hat link building industry collapsed. Thousands of legitimate businesses that had hired dodgy SEO agencies found themselves penalized.

But the most intellectually interesting update came in August 2013: Hummingbird.

Before Hummingbird, Google essentially took your search query, broke it into individual keywords, and tried to match those keywords to pages. But language doesn't work that way.

Hummingbird introduced semantic understanding. Google now tried to understand the intent behind a query — not just the words.

This had massive implications. Topical authority emerged as a concept. A site that comprehensively covered a topic was seen as more authoritative than a site with one great article surrounded by thin filler.

The SEO industry was forced to grow up. The era of user intent had begun.""",

    "05_mobile_first": """Chapter Five. Mobile Goes First. The world fits in your pocket.

In 2014, something unprecedented happened in digital history.

For the first time ever, more people accessed the internet from mobile devices than from desktop computers.

Google had been watching this shift for years. And they knew they had a problem. Most websites in 2014 were built for desktop. They loaded slowly on mobile, had tiny text, required pinching and zooming, and often crashed mobile browsers entirely.

Users were searching on their phones and getting terrible experiences.

April 21st, 2015. The SEO community called it Mobilegeddon. Google officially started using mobile-friendliness as a ranking signal for mobile searches. Sites that weren't mobile-optimized lost rankings. The panic was immediate. Web developers worldwide scrambled to implement responsive design.

But mobile optimization was just the beginning.

In 2015, Google also announced something that would reshape the entire future of search: RankBrain.

RankBrain was Google's first major deployment of artificial intelligence — specifically machine learning — into its core ranking algorithm. It became the third most important ranking factor after content and links.

What did RankBrain do? It learned.

It analyzed patterns in search queries it had never seen before and figured out what kind of result users actually wanted. It also optimized for user behavior signals — particularly click-through rates and dwell time. If users clicked on your result and stayed on your page for a long time, that was a strong positive signal.

For SEO practitioners, the 2014 to 2016 playbook became: mobile first. User experience matters. Local SEO explodes. Rich snippets emerge as a battleground through schema markup.

Voice search appeared on the horizon. Siri, Cortana, Google Now. Voice queries are different from typed queries. More conversational. More question-based. Practitioners started thinking about question-based content.

2016 also brought Accelerated Mobile Pages — AMP. Near-instant loading mobile web pages. Publishers rushed to implement it. The world had moved to mobile. SEO had to move with it.""",

    "06_trust_language": """Chapter Six. Trust, Expertise, and Language. The Quality Rater Guidelines become law.

By 2017, Google was fighting a new enemy: misinformation.

The 2016 election cycle had exposed a problem. Fake news sites, conspiracy pages, and low-credibility content were ranking high. Google was surfacing health misinformation. Financial scams. Sites that looked professional but had no real credentials were outranking legitimate experts.

In 2015, Google had expanded their Quality Rater Guidelines — a document given to thousands of human contractors who manually evaluated search quality. Inside this document was a concept called E-A-T: Expertise, Authoritativeness, and Trustworthiness.

E-A-T wasn't technically an algorithm — no one could see it in the code. But it represented what Google's algorithms were trying to measure.

YMYL: Your Money or Your Life. Content about health, finance, legal matters, safety — domains where bad information could literally harm people — was held to a higher E-A-T standard.

For SEO practitioners, this was a fundamental shift. It wasn't enough to have great content. You needed to demonstrate who was behind that content.

Author bios became critical. Who wrote this? What are their credentials? Are they a doctor writing about medicine? A certified financial planner writing about investing?

Reviews and reputation management became SEO disciplines. What people said about you on Yelp, Trustpilot, Google Reviews — this fed into how Google perceived your trustworthiness.

Then in October 2019, Google deployed BERT. And this changed everything about how language was processed.

BERT — Bidirectional Encoder Representations from Transformers — was a natural language processing model that understood context within sentences bidirectionally.

For practitioners, the message was clear: write for humans. Stop optimizing for keyword density. Use synonyms. Use related terms. Explain concepts fully. Don't repeat your keyword awkwardly fifteen times.

The year-by-year strategy: build author profiles, establish credentials, build topical depth, optimize for featured snippets, prepare for BERT by auditing all content for natural language quality.

By the end of 2020, SEO had professionalized enormously. It was a billion-dollar industry. There were specialized practitioners for technical SEO, content strategy, link building, local SEO, international SEO, and e-commerce SEO.""",

    "07_experience_era": """Chapter Seven. The Experience Era. Speed, stability, and the Helpful Content Revolution.

2021 was the year Google officially told the world: user experience is a ranking factor.

Not indirectly through behavioral signals. Not theoretically through quality guidelines. Officially. Measurably. With specific metrics.

Core Web Vitals.

Google introduced three key measurements.

Largest Contentful Paint. How quickly does the main content of your page appear? Google said: under two and a half seconds is good. Over four seconds is poor.

First Input Delay. How quickly does your page respond when a user tries to interact with it? Under one hundred milliseconds is good.

Cumulative Layout Shift. Does your page layout jump around as it loads? Images pushing text down. Ads appearing and moving content. A score under zero point one is good.

In May 2021, Core Web Vitals became an official ranking signal as part of the Page Experience update.

This was a massive deal for developers. Suddenly, my site works wasn't enough. You needed to pass three specific performance benchmarks.

Technical SEO had a new frontier. The best practitioners weren't just optimizing title tags and building links — they were digging into render-blocking JavaScript, lazy loading strategies, image compression, and CDN configurations.

But perhaps the most consequential development of 2021 to 2022 wasn't about speed. It was about intent.

The Helpful Content Update launched in August 2022 specifically targeted what Google called search engine-first content. If your content strategy was built around finding keywords and producing content to capture them — without genuine value for real readers — you were in the crosshairs.

Google said to ask yourself: if Google search didn't exist, would you still create this content? Is there a real audience for this outside of search traffic?

For practitioners navigating 2021 and 2022, the winning strategy was clear. Optimize your Core Web Vitals aggressively. Build genuine topical authority. Create first-hand content. And build your brand.""",

    "08_ai_disruption": """Chapter Eight. The AI Disruption. ChatGPT broke everything we knew.

November 30th, 2022. OpenAI launched ChatGPT.

Within two months, it had one hundred million users. The fastest product adoption in history.

And for the SEO industry, the questions came fast and loud.

If people can ask an AI anything and get an instant, synthesized answer — why would they use Google?

If AI can generate unlimited content in seconds — what happens to the content creation industry?

The anxiety was real. And justified.

In 2023, Google responded with the Search Generative Experience — SGE — a direct response to the AI search threat. SGE placed an AI-generated response at the very top of Google's search results. Above the organic listings. Above the ads.

Testing showed that when SGE appeared, click-through rates to organic results dropped significantly — sometimes by thirty to forty percent.

But here's what's fascinating about the 2023 to 2024 era: Google search was still dominant. Despite all the AI hype, ChatGPT and other AI tools were sending a tiny fraction of Google's traffic to websites. Google was still sending roughly three hundred and forty-five times more website traffic than all AI tools combined.

However, the traffic from AI tools had a different quality. People who clicked through from an AI tool's response were converting at four to twenty-three times the rate of people from traditional search. They came in highly informed, already pre-sold on a solution.

The content industry had its own reckoning. AI could generate plausible content at scale. The Helpful Content Update expanded and intensified. The March 2024 core update was one of the most disruptive in Google's history.

For practitioners in 2023 and 2024, the strategy split into two tracks. Track one: Win in traditional Google search with genuine expertise and original research. Track two: Build presence in AI systems. Get your brand and content cited by ChatGPT, Claude, and Perplexity.

New job titles appeared: AI SEO Specialist. Generative Engine Optimization Consultant. The rulebook wasn't being thrown out — it was being doubled in size.""",

    "09_geo_era": """Chapter Nine. The GEO Era. Generative Engine Optimization — the new SEO.

Here we are.

2025 and 2026. The most complex, fragmented, and fascinating era in the history of search engine optimization.

Between January 2022 and early 2026, Google deployed more than thirty-three major algorithm updates. More updates in four years than in the previous decade combined. The pace of change has become relentless.

Meanwhile, AI search has gone from experiment to mainstream.

Google's AI Overviews now appear on a significant percentage of all searches. Perplexity AI has grown to hundreds of millions of users. ChatGPT has integrated search. People are increasingly starting their research journey in an AI chatbot rather than a traditional search engine.

This has given birth to a new discipline: Generative Engine Optimization. GEO.

The core insight of GEO is simple but profound: instead of optimizing to rank on a page of ten blue links, you're optimizing to be cited, referenced, or included in an AI-generated response.

The tactics are different.

Citation density. Use specific statistics, named studies, and quotable facts that AI systems can extract and reference.

Structured information. FAQ formats, clear definitions, numbered lists, data tables — these are highly extractable for AI systems building composite answers.

Brand authority in AI training data. Being mentioned in Wikipedia, authoritative publications, and primary sources affects whether AI systems associate your brand with your topic.

First-hand expertise. Create content that could only have been written by someone with direct experience.

But here's the nuanced reality of 2026: traditional SEO is not dead. Not even close. For purchase intent queries, people still click through. Traditional search behavior persists for commercial and navigational queries.

The winning strategy in 2025 and 2026 is dual-track integration. Maintain elite traditional SEO and build parallel GEO presence simultaneously.

The content that wins in 2026 has three properties: human expertise, structural clarity, and genuine novelty. Something AI can't generate from existing training data.""",

    "10_future_outro": """Chapter Ten. The Future. What comes after search?

Let me make some predictions. Not guesses — informed projections based on the trajectory of everything we've covered.

By 2027 to 2030, the nature of search itself will change.

AI agents — autonomous software that can browse the web, compare options, and make decisions on behalf of users — are already here in early form. Within the next few years, a meaningful percentage of searches won't be performed by humans at all. Your AI assistant will search for you.

When AI agents do research, the optimization target changes again. It's not about what a human will click. It's about what information architecture will allow an agent to extract, compare, and conclude.

Structured data becomes more critical than ever.

Entities over keywords. Google's Knowledge Graph already represents the internet as a network of named entities — things, not strings. Being a recognized entity with clear attributes, relationships, and factual claims will matter more than keyword optimization.

Brand becomes the ultimate moat. When AI summarizes a space, the brands it mentions are the ones with the strongest signal density in its training data.

The zero-click economy deepens. For a huge swath of informational queries, users will never visit a website. The information will come from an AI. The survivors will be those who built something beyond rankings — community, tools, products, subscriptions.

But here's what I want you to hold onto.

In 1994, the SEO trick was: repeat your keywords.
In 2002, the SEO trick was: get links from everywhere.
In 2012, the SEO trick was: create good content and earn quality links.
In 2020, the SEO trick was: create expert content with excellent user experience.
In 2026, the SEO trick is: create genuinely original, expert-led content that serves humans and can be cited by AI.

See the pattern?

Every single era, the core of what SEO rewards moves closer to: actually be good. Actually provide value. Actually have expertise. Actually create something worth citing.

The search engines started naive and manipulable. They're ending up as extraordinarily sophisticated judges of whether you deserve to be found.

The practitioners who've won over multiple decades — through Florida and Panda and Penguin and BERT and AI Overviews — are the ones who built for the permanent principle behind every algorithm: help people find what they're actually looking for.

The internet is thirty-five years old. SEO is thirty years old. And despite every disruption, the fundamental truth has never changed.

If you create something genuinely, demonstrably valuable to the people you're trying to reach — the algorithm will find a way to reward you. That's always been true. That will always be true.

Subscribe if you found this valuable — I'll be documenting the future of SEO as it unfolds in real time. And if you want to know exactly how to apply these principles to your business in 2026, the link in the description will take you to my SEO audit and build program.

The game keeps changing. But the winners are always the ones who understand the history.

See you in the next one."""
}

def generate_segment(segment_name: str, text: str) -> bool:
    """Generate voiceover for a single segment via ElevenLabs API"""
    output_file = OUTPUT_DIR / f"{segment_name}.mp3"

    if output_file.exists() and output_file.stat().st_size > 10000:
        print(f"  ✓ Skipping (exists): {segment_name}")
        return True

    print(f"  Generating: {segment_name}...")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.85,
            "style": 0.3,
            "use_speaker_boost": True
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)

        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            size_kb = output_file.stat().st_size / 1024
            print(f"  ✓ Saved: {segment_name} ({size_kb:.0f} KB)")
            return True
        else:
            print(f"  ✗ Error {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return False


def check_api_quota():
    """Check remaining ElevenLabs character quota"""
    url = "https://api.elevenlabs.io/v1/user"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            sub = data.get("subscription", {})
            used = sub.get("character_count", 0)
            limit = sub.get("character_limit", 0)
            remaining = limit - used
            print(f"\n📊 ElevenLabs Quota: {used:,} used / {limit:,} limit ({remaining:,} remaining)")
            return remaining
        else:
            print(f"Could not check quota: {response.status_code}")
            return None
    except Exception as e:
        print(f"Quota check error: {e}")
        return None


def load_chapters_from_config(config_path: str) -> dict:
    """Load chapters from a generate_config.json + script.md pair."""
    import re as _re

    config = json.loads(Path(config_path).read_text())
    script_file = Path(config.get("script_file", ""))
    if not script_file.exists():
        # Try relative to config dir
        script_file = Path(config_path).parent / "script.md"

    if not script_file.exists():
        raise FileNotFoundError(f"Script file not found: {script_file}")

    script_text = script_file.read_text()
    chapter_ids = config.get("chapter_ids", [])

    # Split script by ## headings (each chapter starts with ##)
    # Section 0 is the title/preamble, sections 1+ are chapters
    sections = _re.split(r'\n## ', script_text)
    chapters = {}

    # Map chapter_ids to sections (skip section 0 which is the title)
    content_sections = sections[1:] if len(sections) > 1 else sections

    for i, chapter_id in enumerate(chapter_ids):
        if i < len(content_sections):
            section = content_sections[i]
            lines = section.strip().split('\n')
            # First line is the heading text (already split off ##), skip it
            body = '\n'.join(lines[1:]).strip()
            # Clean up markdown formatting for narration
            body = _re.sub(r'\*\*([^*]+)\*\*', r'\1', body)  # Remove bold
            body = _re.sub(r'\*([^*]+)\*', r'\1', body)  # Remove italic
            body = _re.sub(r'#{1,3}\s+', '', body)  # Remove any remaining headings
            body = body.replace('---', '').replace('```', '')
            body = _re.sub(r'\n{3,}', '\n\n', body)  # Collapse excess newlines
            if body:
                chapters[chapter_id] = body

    return chapters, config


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate voiceover via ElevenLabs")
    parser.add_argument("--config", help="Path to generate_config.json (for new documentaries)")
    parser.add_argument("--output-dir", help="Override output directory for audio files")
    parser.add_argument("--skip-existing", action="store_true", default=True,
                        help="Skip chapters that already have audio (default: true)")
    parser.add_argument("--force", action="store_true", help="Regenerate all chapters")
    args = parser.parse_args()

    # Load chapters from config or use built-in
    if args.config:
        chapters, config = load_chapters_from_config(args.config)
        output_dir = Path(args.output_dir) if args.output_dir else Path(config.get("audio_dir", str(OUTPUT_DIR)))
        print(f"SEO Documentary — ElevenLabs Voiceover Generation")
        print(f"  Config: {args.config}")
        print(f"  Chapters: {len(chapters)}")
    else:
        chapters = CHAPTERS
        output_dir = Path(args.output_dir) if args.output_dir else OUTPUT_DIR
        print(f"SEO Documentary — ElevenLabs Voiceover Generation (built-in script)")

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Voice ID: {VOICE_ID}")
    print(f"  Output: {output_dir}")

    if args.force:
        # Remove existing files for regeneration
        for chapter_id in chapters:
            existing = output_dir / f"{chapter_id}.mp3"
            if existing.exists():
                existing.unlink()

    # Check quota first
    total_chars = sum(len(t) for t in chapters.values())
    print(f"\n  Total script characters: {total_chars:,}")

    remaining = check_api_quota()
    if remaining is not None and remaining < total_chars:
        print(f"\n  WARNING: Only {remaining:,} chars remaining but need {total_chars:,}")
        print("  Will generate as many chapters as possible.")

    print(f"\n  Starting generation...\n")

    # Temporarily override OUTPUT_DIR for generate_segment
    original_output = OUTPUT_DIR
    success = 0
    failed = []

    for segment_name, text in chapters.items():
        char_count = len(text)
        print(f"  [{segment_name}] ({char_count:,} chars)")

        output_file = output_dir / f"{segment_name}.mp3"
        if output_file.exists() and output_file.stat().st_size > 10000 and not args.force:
            print(f"    Skipping (exists): {segment_name}")
            success += 1
            continue

        # Generate directly to the target output_dir
        print(f"    Generating: {segment_name}...")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.85,
                "style": 0.3,
                "use_speaker_boost": True
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=300)
            if response.status_code == 200:
                output_file.write_bytes(response.content)
                size_kb = output_file.stat().st_size / 1024
                print(f"    Saved: {segment_name} ({size_kb:.0f} KB)")
                success += 1
            else:
                print(f"    Error {response.status_code}: {response.text[:200]}")
                failed.append(segment_name)
        except Exception as e:
            print(f"    Exception: {e}")
            failed.append(segment_name)

        time.sleep(1)

    print(f"\n  Complete: {success}/{len(chapters)} segments generated")
    if failed:
        print(f"  Failed: {failed}")

    # List output files
    print(f"\n  Generated audio files:")
    total_size = 0
    for f in sorted(output_dir.glob("*.mp3")):
        size_kb = f.stat().st_size / 1024
        total_size += size_kb
        print(f"    {f.name} ({size_kb:.0f} KB)")
    print(f"    Total: {total_size / 1024:.1f} MB")
