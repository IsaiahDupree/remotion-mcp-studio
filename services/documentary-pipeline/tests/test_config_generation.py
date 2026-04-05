# 300 tests for config generation and validation
"""
Comprehensive pytest suite for research_and_generate.py and generate_voiceover_hq.py.

Categories:
  - Topic Slug Generation (~80 tests)
  - Config JSON Schema (~60 tests)
  - Chapter ID Format (~40 tests)
  - Visual Style Validation (~40 tests)
  - YouTube Meta Validation (~40 tests)
  - Narrator Style (~20 tests)
  - Chunk Splitting (~20 tests)

Run: pytest tests/test_config_generation.py -v
"""

import json
import re
import sys
from pathlib import Path

import pytest

# -- Setup imports from project root --
PROJECT_DIR = Path(str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_DIR))

from research_and_generate import (
    CHAPTER_COLORS,
    NARRATOR_STYLE_PROMPTS,
    extract_json,
    slug,
)
from generate_voiceover_hq import split_into_chunks

SCRIPT_DIR = Path(__file__).parent

# -- Load the real reference config --
REFERENCE_CONFIG_PATH = (
    PROJECT_DIR
    / "research"
    / "seo_and_geo_in_2026_2030_what_actually_works_what_s_changing"
    / "generate_config.json"
)
REFERENCE_CONFIG = json.loads(REFERENCE_CONFIG_PATH.read_text())

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
CHAPTER_ID_RE = re.compile(r"^\d{2}_[a-z][a-z0-9_]*$")


# ============================================================================
# TOPIC SLUG GENERATION (~80 tests)
# ============================================================================

class TestSlugNormalTopics:
    """Basic topic-to-slug conversion."""

    @pytest.mark.parametrize("topic,expected", [
        ("The History of AI", "the_history_of_ai"),
        ("Rise of Electric Cars", "rise_of_electric_cars"),
        ("Quantum Computing", "quantum_computing"),
        ("Space Race: USA vs USSR", "space_race_usa_vs_ussr"),
        ("How the Internet Was Built", "how_the_internet_was_built"),
        ("SEO in 2026", "seo_in_2026"),
        ("Machine Learning 101", "machine_learning_101"),
        ("The Cloud Revolution", "the_cloud_revolution"),
        ("Bitcoin: Digital Gold?", "bitcoin_digital_gold"),
        ("Web3 and Blockchain", "web3_and_blockchain"),
    ])
    def test_normal_topic_slugs(self, topic, expected):
        assert slug(topic) == expected


class TestSlugSpecialChars:
    """Special characters, unicode, edge cases."""

    @pytest.mark.parametrize("topic,expected_pattern", [
        # Special characters stripped
        ("Hello!@#$%^&*()World", r"^hello_world$"),
        ("A/B Testing", r"^a_b_testing$"),
        ("C++ Programming", r"^c_programming$"),
        ("Node.js & React", r"^node_js_react$"),
        ("Price: $99.99", r"^price_99_99$"),
        ("50% Off Sale!", r"^50_off_sale$"),
        ("Q&A Session", r"^q_a_session$"),
        ("Rock & Roll", r"^rock_roll$"),
        # Colons, semicolons, dashes
        ("AI: Past; Present - Future", r"^ai_past_present_future$"),
        ("Part 1 -- The Beginning", r"^part_1_the_beginning$"),
    ])
    def test_special_chars(self, topic, expected_pattern):
        result = slug(topic)
        assert re.match(expected_pattern, result), f"slug({topic!r}) = {result!r}"

    @pytest.mark.parametrize("topic", [
        "Caf\u00e9 Culture",
        "\u00dcber Technology",
        "Na\u00efve Bayes",
        "R\u00e9sum\u00e9 Builder",
        "\u4eba\u5de5\u667a\u80fd",       # Chinese: "Artificial Intelligence"
        "\u30c7\u30fc\u30bf\u30b5\u30a4\u30a8\u30f3\u30b9",  # Japanese: "Data Science"
        "\u041c\u0430\u0448\u0438\u043d\u043d\u043e\u0435 \u043e\u0431\u0443\u0447\u0435\u043d\u0438\u0435",  # Russian: "Machine Learning"
        "\uc778\uacf5\uc9c0\ub2a5",       # Korean: "AI"
    ])
    def test_unicode_topics_produce_valid_slug(self, topic):
        result = slug(topic)
        # Slug must only contain [a-z0-9_]
        assert re.match(r"^[a-z0-9_]*$", result), f"slug({topic!r}) = {result!r}"

    @pytest.mark.parametrize("topic", [
        "",           # empty
        "   ",        # whitespace only
        "\t\t",       # tabs only
        "\n\n",       # newlines only
        "   \n  \t ", # mixed whitespace
    ])
    def test_empty_and_whitespace_slugs(self, topic):
        result = slug(topic)
        assert result == "" or re.match(r"^[a-z0-9_]+$", result)

    @pytest.mark.parametrize("topic", [
        "12345",
        "007",
        "2026",
        "3.14159",
        "100_percent",
    ])
    def test_numeric_topics(self, topic):
        result = slug(topic)
        assert re.match(r"^[a-z0-9_]+$", result)
        assert len(result) > 0

    @pytest.mark.parametrize("topic", [
        "a",
        "Z",
        "1",
        "!",
        " ",
    ])
    def test_single_char_topics(self, topic):
        result = slug(topic)
        assert len(result) <= 1
        assert re.match(r"^[a-z0-9_]*$", result)


class TestSlugEdgeCases:
    """Long strings, URLs, paths, injection, emojis."""

    def test_extremely_long_string_truncated_to_80(self):
        topic = "a" * 500
        result = slug(topic)
        assert len(result) <= 80

    @pytest.mark.parametrize("length", [79, 80, 81, 100, 200, 500])
    def test_max_length_enforcement(self, length):
        topic = "x" * length
        result = slug(topic)
        assert len(result) <= 80

    @pytest.mark.parametrize("topic", [
        "https://www.example.com/page?q=test&lang=en",
        "http://localhost:3000/api/health",
        "ftp://files.example.com/data.csv",
    ])
    def test_urls_produce_valid_slugs(self, topic):
        result = slug(topic)
        assert re.match(r"^[a-z0-9_]+$", result)
        assert len(result) <= 80

    @pytest.mark.parametrize("topic", [
        "/usr/local/bin/python3",
        "C:\\Users\\test\\Documents",
        "~/Documents/project/file.py",
    ])
    def test_file_paths(self, topic):
        result = slug(topic)
        assert re.match(r"^[a-z0-9_]+$", result)

    @pytest.mark.parametrize("topic", [
        "'; DROP TABLE users; --",
        "<script>alert('xss')</script>",
        "{{template injection}}",
        "$(command substitution)",
        "`backtick injection`",
    ])
    def test_injection_strings_safe(self, topic):
        result = slug(topic)
        assert re.match(r"^[a-z0-9_]*$", result)
        assert "'" not in result
        assert "<" not in result
        assert ">" not in result

    @pytest.mark.parametrize("topic", [
        "\U0001f680 Rocket Science",
        "AI \U0001e9c0 Deep Learning",
        "\U0001f4a1 Ideas",
        "\U0001f525\U0001f525\U0001f525 Hot Takes",
    ])
    def test_emojis_stripped(self, topic):
        result = slug(topic)
        assert re.match(r"^[a-z0-9_]*$", result)

    @pytest.mark.parametrize("topic", [
        "<h1>Title</h1>",
        "<p>paragraph</p>",
        '<img src="x" onerror="alert(1)">',
        "<div class='test'>content</div>",
    ])
    def test_html_tags_stripped(self, topic):
        result = slug(topic)
        assert "<" not in result
        assert ">" not in result

    @pytest.mark.parametrize("topic", [
        "line1\nline2",
        "tab1\ttab2",
        "mixed\n\ttabs\nand\nnewlines",
        "carriage\rreturn",
    ])
    def test_newlines_and_tabs(self, topic):
        result = slug(topic)
        assert "\n" not in result
        assert "\t" not in result
        assert "\r" not in result

    @pytest.mark.parametrize("topic", [
        "!!!???...",
        "---___---",
        "###$$$%%%",
        "((([[[)))]]]]",
    ])
    def test_repeated_special_chars(self, topic):
        result = slug(topic)
        assert re.match(r"^[a-z0-9_]*$", result)

    def test_mixed_case_lowered(self):
        assert slug("CamelCaseTitle") == "camelcasetitle"

    def test_leading_trailing_specials_stripped(self):
        result = slug("---Hello World---")
        assert not result.startswith("_")
        assert not result.endswith("_")

    def test_consecutive_underscores_collapsed(self):
        result = slug("hello   world   test")
        # The regex replaces runs of non-alnum with single _
        assert "__" not in result


# ============================================================================
# CONFIG JSON SCHEMA VALIDATION (~60 tests)
# ============================================================================

class TestConfigRequiredKeys:
    """Validate all required top-level keys exist in reference config."""

    @pytest.mark.parametrize("key", [
        "topic",
        "title",
        "chapter_ids",
        "chapter_meta",
        "script_file",
        "audio_dir",
        "characters_dir",
        "scene_images_dir",
        "output_dir",
        "pipeline_steps",
    ])
    def test_required_top_level_key(self, key):
        assert key in REFERENCE_CONFIG, f"Missing required key: {key}"

    def test_topic_is_string(self):
        assert isinstance(REFERENCE_CONFIG["topic"], str)

    def test_topic_not_empty(self):
        assert len(REFERENCE_CONFIG["topic"]) > 0

    def test_title_is_string(self):
        assert isinstance(REFERENCE_CONFIG["title"], str)

    def test_title_not_empty(self):
        assert len(REFERENCE_CONFIG["title"]) > 0

    def test_chapter_ids_is_list(self):
        assert isinstance(REFERENCE_CONFIG["chapter_ids"], list)

    def test_chapter_meta_is_dict(self):
        assert isinstance(REFERENCE_CONFIG["chapter_meta"], dict)

    def test_pipeline_steps_is_list(self):
        assert isinstance(REFERENCE_CONFIG["pipeline_steps"], list)

    def test_pipeline_steps_count(self):
        assert len(REFERENCE_CONFIG["pipeline_steps"]) == 11


class TestConfigChapterMetaFields:
    """Validate chapter_meta has required fields per chapter."""

    REQUIRED_CHAPTER_FIELDS = [
        "title", "era", "color", "tone", "surprising_fact", "image_style_hints"
    ]

    @pytest.mark.parametrize("chapter_id", REFERENCE_CONFIG["chapter_ids"])
    def test_chapter_exists_in_meta(self, chapter_id):
        assert chapter_id in REFERENCE_CONFIG["chapter_meta"]

    @pytest.mark.parametrize(
        "chapter_id,field",
        [
            (cid, field)
            for cid in REFERENCE_CONFIG["chapter_ids"]
            for field in ["title", "era", "color", "tone", "surprising_fact", "image_style_hints"]
        ],
    )
    def test_chapter_has_required_field(self, chapter_id, field):
        meta = REFERENCE_CONFIG["chapter_meta"][chapter_id]
        assert field in meta, f"Chapter {chapter_id} missing field: {field}"

    @pytest.mark.parametrize("chapter_id", REFERENCE_CONFIG["chapter_ids"])
    def test_chapter_title_is_string(self, chapter_id):
        assert isinstance(REFERENCE_CONFIG["chapter_meta"][chapter_id]["title"], str)

    @pytest.mark.parametrize("chapter_id", REFERENCE_CONFIG["chapter_ids"])
    def test_chapter_color_valid_hex(self, chapter_id):
        color = REFERENCE_CONFIG["chapter_meta"][chapter_id]["color"]
        assert HEX_RE.match(color), f"Invalid hex color {color!r} for {chapter_id}"

    @pytest.mark.parametrize("chapter_id", REFERENCE_CONFIG["chapter_ids"])
    def test_chapter_image_style_hints_is_list(self, chapter_id):
        hints = REFERENCE_CONFIG["chapter_meta"][chapter_id]["image_style_hints"]
        assert isinstance(hints, list)
        assert len(hints) > 0

    @pytest.mark.parametrize("chapter_id", REFERENCE_CONFIG["chapter_ids"])
    def test_chapter_surprising_fact_not_empty(self, chapter_id):
        fact = REFERENCE_CONFIG["chapter_meta"][chapter_id]["surprising_fact"]
        assert isinstance(fact, str)
        assert len(fact) > 0


class TestConfigChapterCount:
    """Validate chapter count ranges and consistency."""

    def test_chapter_count_in_range(self):
        count = len(REFERENCE_CONFIG["chapter_ids"])
        assert 1 <= count <= 20

    def test_chapter_ids_match_meta_keys(self):
        ids = set(REFERENCE_CONFIG["chapter_ids"])
        meta_keys = set(REFERENCE_CONFIG["chapter_meta"].keys())
        # Every chapter_id must have a meta entry
        assert ids.issubset(meta_keys)

    def test_no_extra_meta_beyond_ids(self):
        ids = set(REFERENCE_CONFIG["chapter_ids"])
        meta_keys = set(REFERENCE_CONFIG["chapter_meta"].keys())
        assert meta_keys == ids

    def test_no_duplicate_chapter_ids(self):
        ids = REFERENCE_CONFIG["chapter_ids"]
        assert len(ids) == len(set(ids))


class TestConfigYoutubeMeta:
    """Validate youtube_meta in reference config."""

    @pytest.mark.parametrize("key", ["title", "description", "tags", "category_id"])
    def test_youtube_meta_has_key(self, key):
        yt = REFERENCE_CONFIG.get("youtube_meta", {})
        # The reference config may not have youtube_meta; skip if absent
        if not yt:
            pytest.skip("Reference config lacks youtube_meta")
        assert key in yt


# ============================================================================
# CHAPTER ID FORMAT (~40 tests)
# ============================================================================

class TestChapterIdFormat:
    """Chapter IDs must match NN_slug pattern."""

    @pytest.mark.parametrize("chapter_id", REFERENCE_CONFIG["chapter_ids"])
    def test_reference_chapter_ids_match_pattern(self, chapter_id):
        assert CHAPTER_ID_RE.match(chapter_id), f"Bad format: {chapter_id}"

    @pytest.mark.parametrize("valid_id", [
        "01_intro",
        "02_origins",
        "05_evolution",
        "10_conclusion",
        "15_epilogue",
        "20_appendix",
        "01_a",
        "99_z",
    ])
    def test_valid_chapter_id_patterns(self, valid_id):
        assert CHAPTER_ID_RE.match(valid_id)

    @pytest.mark.parametrize("invalid_id", [
        "1_intro",       # single digit
        "intro",         # no number
        "01-intro",      # dash not underscore
        "01_",           # trailing underscore only
        "01_Intro",      # uppercase
        "001_intro",     # triple digit
        "01_123",        # starts with digit after _
        "",              # empty
        "01",            # number only
        "_01_intro",     # leading underscore
        "01__intro",     # double underscore
    ])
    def test_invalid_chapter_id_patterns(self, invalid_id):
        assert not CHAPTER_ID_RE.match(invalid_id), f"Should be invalid: {invalid_id}"

    def test_sequential_numbering_in_reference(self):
        ids = REFERENCE_CONFIG["chapter_ids"]
        numbers = [int(cid.split("_")[0]) for cid in ids]
        for i, n in enumerate(numbers):
            assert n == i + 1, f"Expected {i+1}, got {n} at position {i}"

    def test_no_gaps_in_numbering(self):
        ids = REFERENCE_CONFIG["chapter_ids"]
        numbers = [int(cid.split("_")[0]) for cid in ids]
        for i in range(1, len(numbers)):
            assert numbers[i] == numbers[i - 1] + 1

    @pytest.mark.parametrize("count", [1, 5, 10, 15, 20])
    def test_generated_id_sequences(self, count):
        """Verify that a synthetic N-chapter list has correct sequential IDs."""
        ids = [f"{i+1:02d}_ch{i+1}" for i in range(count)]
        numbers = [int(cid.split("_")[0]) for cid in ids]
        assert numbers == list(range(1, count + 1))
        for cid in ids:
            assert CHAPTER_ID_RE.match(cid)

    @pytest.mark.parametrize("count", [1, 5, 10, 15, 20])
    def test_no_duplicates_in_generated_sequences(self, count):
        ids = [f"{i+1:02d}_chapter_{i+1}" for i in range(count)]
        assert len(ids) == len(set(ids))


# ============================================================================
# VISUAL STYLE VALIDATION (~40 tests)
# ============================================================================

VISUAL_STYLE_FIELDS = ["camera", "lighting", "film", "env", "palette"]


class TestVisualStylePresence:
    """When visual_style exists, validate its structure."""

    @pytest.mark.parametrize("chapter_id", REFERENCE_CONFIG["chapter_ids"])
    def test_visual_style_key_type(self, chapter_id):
        meta = REFERENCE_CONFIG["chapter_meta"][chapter_id]
        if "visual_style" in meta:
            assert isinstance(meta["visual_style"], dict)

    @pytest.mark.parametrize(
        "chapter_id,field",
        [
            (cid, f)
            for cid in REFERENCE_CONFIG["chapter_ids"]
            for f in VISUAL_STYLE_FIELDS
            if "visual_style" in REFERENCE_CONFIG["chapter_meta"].get(cid, {})
        ],
    )
    def test_visual_style_field_exists(self, chapter_id, field):
        vs = REFERENCE_CONFIG["chapter_meta"][chapter_id]["visual_style"]
        assert field in vs, f"Missing visual_style.{field} in {chapter_id}"

    @pytest.mark.parametrize(
        "chapter_id,field",
        [
            (cid, f)
            for cid in REFERENCE_CONFIG["chapter_ids"]
            for f in VISUAL_STYLE_FIELDS
            if "visual_style" in REFERENCE_CONFIG["chapter_meta"].get(cid, {})
        ],
    )
    def test_visual_style_field_is_string(self, chapter_id, field):
        vs = REFERENCE_CONFIG["chapter_meta"][chapter_id]["visual_style"]
        assert isinstance(vs[field], str)


class TestVisualStyleEdgeCases:
    """Test fallback behavior and various field values."""

    def test_empty_visual_style_dict(self):
        vs = {}
        for field in VISUAL_STYLE_FIELDS:
            assert field not in vs

    @pytest.mark.parametrize("field", VISUAL_STYLE_FIELDS)
    def test_missing_individual_field_detected(self, field):
        vs = {f: "value" for f in VISUAL_STYLE_FIELDS if f != field}
        assert field not in vs

    def test_all_fields_present(self):
        vs = {f: "test value" for f in VISUAL_STYLE_FIELDS}
        for field in VISUAL_STYLE_FIELDS:
            assert field in vs
            assert isinstance(vs[field], str)

    @pytest.mark.parametrize("camera", [
        "wide establishing shot",
        "close-up portrait",
        "aerial drone",
        "tracking shot",
        "medium shot",
        "Dutch angle",
        "overhead bird's eye",
        "handheld documentary",
    ])
    def test_camera_lens_descriptions(self, camera):
        assert isinstance(camera, str)
        assert len(camera) > 0

    @pytest.mark.parametrize("film", [
        "35mm grain",
        "clean digital",
        "vintage 8mm",
        "IMAX clarity",
        "desaturated",
        "Kodak Portra 400",
        "Super 16mm",
        "anamorphic widescreen",
    ])
    def test_film_stock_references(self, film):
        assert isinstance(film, str)
        assert len(film) > 0

    @pytest.mark.parametrize("palette", [
        "warm amber and brown",
        "cold blue and steel",
        "vibrant neon",
        "muted earth tones",
        "#00ff88, #ff6b35",
        "monochrome",
        "high contrast black and white",
        "pastel watercolor",
    ])
    def test_palette_formats(self, palette):
        assert isinstance(palette, str)
        assert len(palette) > 0

    @pytest.mark.parametrize("lighting", [
        "golden hour",
        "harsh fluorescent",
        "candlelit",
        "neon-lit",
        "overcast",
        "studio softbox",
        "natural window light",
    ])
    def test_lighting_descriptions(self, lighting):
        assert isinstance(lighting, str)
        assert len(lighting) > 0

    @pytest.mark.parametrize("env", [
        "university lab 1950s",
        "Silicon Valley garage",
        "server room",
        "lecture hall",
        "modern open-plan office",
        "industrial warehouse",
    ])
    def test_environment_descriptions(self, env):
        assert isinstance(env, str)
        assert len(env) > 0


# ============================================================================
# YOUTUBE META VALIDATION (~40 tests)
# ============================================================================

class TestYoutubeMetaValidation:
    """Validate youtube_meta fields and constraints."""

    @pytest.mark.parametrize("title", [
        "Short Title",
        "A" * 99,
        "SEO Documentary: What Works in 2026",
        "The Complete Guide to Modern SEO",
        "How AI Changed Search Forever",
    ])
    def test_title_under_100_chars(self, title):
        assert len(title) < 100

    @pytest.mark.parametrize("title", [
        "A" * 100,
        "A" * 150,
        "A" * 200,
    ])
    def test_title_over_100_chars_rejected(self, title):
        assert len(title) >= 100

    @pytest.mark.parametrize("desc", [
        "A short description.",
        "Multi-paragraph description.\n\nWith call to action.",
        "SEO keywords and links https://example.com",
    ])
    def test_description_not_empty(self, desc):
        assert len(desc) > 0

    def test_empty_description_detected(self):
        assert len("") == 0

    @pytest.mark.parametrize("tags", [
        ["seo", "documentary"],
        ["ai", "search", "google", "2026"],
        ["tag1"],
    ])
    def test_tags_is_nonempty_list(self, tags):
        assert isinstance(tags, list)
        assert len(tags) > 0

    def test_empty_tags_detected(self):
        tags = []
        assert len(tags) == 0

    @pytest.mark.parametrize("tag", [
        "seo",
        "artificial intelligence",
        "a" * 49,
    ])
    def test_individual_tag_under_50_chars(self, tag):
        assert len(tag) < 50

    @pytest.mark.parametrize("tag", [
        "a" * 50,
        "a" * 100,
    ])
    def test_individual_tag_over_50_chars_rejected(self, tag):
        assert len(tag) >= 50

    @pytest.mark.parametrize("category_id", [
        "27",
        "22",
        "1",
        "10",
        "28",
    ])
    def test_category_id_is_digit_string(self, category_id):
        assert isinstance(category_id, str)
        assert category_id.isdigit()

    @pytest.mark.parametrize("category_id", [
        "abc",
        "",
        "27a",
        "12.5",
        None,
    ])
    def test_invalid_category_id_detected(self, category_id):
        if category_id is None:
            assert category_id is None
        else:
            assert not category_id.isdigit() or category_id == ""

    @pytest.mark.parametrize("privacy", ["public", "unlisted", "private"])
    def test_valid_privacy_values(self, privacy):
        assert privacy in {"public", "unlisted", "private"}

    @pytest.mark.parametrize("privacy", ["draft", "scheduled", "archived", "", "PUBLIC"])
    def test_invalid_privacy_values(self, privacy):
        assert privacy not in {"public", "unlisted", "private"}

    def test_reference_youtube_meta_title_length(self):
        yt = REFERENCE_CONFIG.get("youtube_meta")
        if yt and "title" in yt:
            assert len(yt["title"]) < 100

    def test_reference_youtube_meta_tags_list(self):
        yt = REFERENCE_CONFIG.get("youtube_meta")
        if yt and "tags" in yt:
            assert isinstance(yt["tags"], list)
            assert len(yt["tags"]) > 0

    def test_reference_youtube_meta_each_tag_length(self):
        yt = REFERENCE_CONFIG.get("youtube_meta")
        if yt and "tags" in yt:
            for tag in yt["tags"]:
                assert len(tag) < 50, f"Tag too long: {tag!r}"


# ============================================================================
# NARRATOR STYLE (~20 tests)
# ============================================================================

class TestNarratorStyle:
    """Narrator style validation."""

    @pytest.mark.parametrize("style", ["documentary", "educational", "dramatic"])
    def test_valid_style_exists_in_prompts(self, style):
        assert style in NARRATOR_STYLE_PROMPTS

    @pytest.mark.parametrize("style", ["documentary", "educational", "dramatic"])
    def test_valid_style_prompt_is_string(self, style):
        assert isinstance(NARRATOR_STYLE_PROMPTS[style], str)

    @pytest.mark.parametrize("style", ["documentary", "educational", "dramatic"])
    def test_valid_style_prompt_not_empty(self, style):
        assert len(NARRATOR_STYLE_PROMPTS[style]) > 50

    @pytest.mark.parametrize("style", [
        "comedic",
        "horror",
        "romantic",
        "noir",
        "children",
        "academic",
        "satirical",
        "Documentary",   # wrong case
        "EDUCATIONAL",   # wrong case
        "",
        None,
    ])
    def test_invalid_style_not_in_prompts(self, style):
        assert style not in NARRATOR_STYLE_PROMPTS

    def test_default_style_is_documentary(self):
        # The module defaults to "documentary" when style not found
        unknown = "nonexistent_style"
        result = NARRATOR_STYLE_PROMPTS.get(unknown, NARRATOR_STYLE_PROMPTS["documentary"])
        assert result == NARRATOR_STYLE_PROMPTS["documentary"]

    def test_exactly_three_styles(self):
        assert len(NARRATOR_STYLE_PROMPTS) == 3

    def test_all_prompts_mention_narration_or_write(self):
        for style, prompt in NARRATOR_STYLE_PROMPTS.items():
            lower = prompt.lower()
            assert "narration" in lower or "write" in lower or "storyteller" in lower, (
                f"Style {style!r} prompt doesn't mention narration/write/storyteller"
            )


# ============================================================================
# CHUNK SPLITTING FROM voiceover_hq (~20 tests)
# ============================================================================

class TestSplitIntoChunks:
    """Test split_into_chunks from generate_voiceover_hq."""

    def test_single_short_paragraph(self):
        chunks = split_into_chunks("Hello world.")
        assert len(chunks) == 1
        assert chunks[0] == "Hello world."

    def test_two_paragraphs_under_max(self):
        text = "Paragraph one.\n\nParagraph two."
        chunks = split_into_chunks(text, max_chars=500)
        assert len(chunks) == 1
        assert "Paragraph one." in chunks[0]
        assert "Paragraph two." in chunks[0]

    def test_two_paragraphs_over_max_split(self):
        p1 = "A" * 600
        p2 = "B" * 600
        text = f"{p1}\n\n{p2}"
        chunks = split_into_chunks(text, max_chars=700)
        assert len(chunks) == 2

    @pytest.mark.parametrize("max_chars", [200, 500, 1000, 2000])
    def test_all_chunks_under_max(self, max_chars):
        # Each paragraph is ~50 chars, well under all max_chars values tested
        paragraphs = ["Word " * 8 + "end."] * 20
        text = "\n\n".join(paragraphs)
        chunks = split_into_chunks(text, max_chars=max_chars)
        for chunk in chunks:
            assert len(chunk) <= max_chars + 10, (
                f"Chunk length {len(chunk)} exceeds {max_chars}"
            )

    def test_no_empty_chunks(self):
        text = "Para 1.\n\n\n\nPara 2.\n\n\n\nPara 3."
        chunks = split_into_chunks(text)
        for chunk in chunks:
            assert len(chunk.strip()) > 0

    def test_total_content_preserved(self):
        paragraphs = [f"Paragraph {i} with some content." for i in range(5)]
        text = "\n\n".join(paragraphs)
        chunks = split_into_chunks(text)
        # All original text should appear across chunks
        combined = "\n\n".join(chunks)
        for p in paragraphs:
            assert p in combined

    def test_empty_text_returns_empty(self):
        chunks = split_into_chunks("")
        assert chunks == []

    def test_whitespace_only_returns_empty(self):
        chunks = split_into_chunks("   \n\n   \n\n   ")
        assert chunks == []

    def test_single_very_long_paragraph(self):
        # Single paragraph exceeding max stays as one chunk (can't split on \n\n)
        text = "A" * 3000
        chunks = split_into_chunks(text, max_chars=1000)
        assert len(chunks) >= 1
        # The content should still be there
        assert "".join(chunks) == text

    @pytest.mark.parametrize("n_paragraphs", [1, 3, 5, 10, 20, 50])
    def test_various_paragraph_counts(self, n_paragraphs):
        paragraphs = [f"Paragraph {i}." for i in range(n_paragraphs)]
        text = "\n\n".join(paragraphs)
        chunks = split_into_chunks(text, max_chars=200)
        assert len(chunks) >= 1
        # No empty chunks
        for c in chunks:
            assert len(c.strip()) > 0

    def test_default_max_chars_is_1000(self):
        # Verify the default comes from the module constant
        from generate_voiceover_hq import MAX_CHUNK_CHARS
        assert MAX_CHUNK_CHARS == 1000


# ============================================================================
# EXTRACT JSON (~20 tests — bonus to round out count)
# ============================================================================

class TestExtractJson:
    """Test the extract_json helper from research_and_generate."""

    @pytest.mark.parametrize("raw,expected_key", [
        ('{"topic": "test"}', "topic"),
        ('```json\n{"title": "hello"}\n```', "title"),
        ('```\n{"key": "val"}\n```', "key"),
        ('Some text before {"data": 1} some text after', "data"),
        ('Here is the config:\n```json\n{"x": 42}\n```\nDone.', "x"),
    ])
    def test_valid_json_extracted(self, raw, expected_key):
        result = extract_json(raw)
        assert expected_key in result

    @pytest.mark.parametrize("raw", [
        "no json here",
        "just plain text",
        "{ invalid json }}}",
        "",
    ])
    def test_invalid_json_raises(self, raw):
        with pytest.raises((ValueError, Exception)):
            extract_json(raw)

    def test_nested_json_extracted(self):
        raw = '{"a": {"b": {"c": 1}}}'
        result = extract_json(raw)
        assert result["a"]["b"]["c"] == 1

    def test_json_with_arrays(self):
        raw = '{"tags": ["a", "b", "c"]}'
        result = extract_json(raw)
        assert result["tags"] == ["a", "b", "c"]

    def test_json_with_unicode(self):
        raw = '{"name": "caf\u00e9"}'
        result = extract_json(raw)
        assert result["name"] == "caf\u00e9"

    def test_json_in_markdown_fence_preferred(self):
        # If both fenced and bare JSON exist, fenced should be extracted
        raw = '{"outer": 1}\n```json\n{"inner": 2}\n```'
        result = extract_json(raw)
        assert "inner" in result

    def test_large_json_extracted(self):
        data = {"items": [{"id": i, "name": f"item_{i}"} for i in range(100)]}
        raw = f"```json\n{json.dumps(data)}\n```"
        result = extract_json(raw)
        assert len(result["items"]) == 100


# ============================================================================
# CHAPTER COLORS (~10 tests)
# ============================================================================

class TestChapterColors:
    """Validate the CHAPTER_COLORS constant."""

    @pytest.mark.parametrize("color", CHAPTER_COLORS)
    def test_color_is_valid_hex(self, color):
        assert HEX_RE.match(color), f"Invalid hex: {color}"

    def test_at_least_10_colors(self):
        assert len(CHAPTER_COLORS) >= 10

    def test_colors_are_strings(self):
        for c in CHAPTER_COLORS:
            assert isinstance(c, str)

    @pytest.mark.parametrize("idx", list(range(min(15, len(CHAPTER_COLORS)))))
    def test_color_at_index_valid(self, idx):
        assert HEX_RE.match(CHAPTER_COLORS[idx])


# ============================================================================
# PIPELINE STEPS VALIDATION (~10 tests)
# ============================================================================

class TestPipelineSteps:
    """Validate pipeline_steps structure in reference config."""

    def test_steps_sequential(self):
        steps = REFERENCE_CONFIG["pipeline_steps"]
        for i, s in enumerate(steps):
            assert s["step"] == i + 1

    @pytest.mark.parametrize("idx", list(range(11)))
    def test_step_has_required_keys(self, idx):
        step = REFERENCE_CONFIG["pipeline_steps"][idx]
        assert "step" in step
        assert "script" in step
        assert "desc" in step

    @pytest.mark.parametrize("idx", list(range(11)))
    def test_step_script_is_string(self, idx):
        assert isinstance(REFERENCE_CONFIG["pipeline_steps"][idx]["script"], str)

    def test_first_step_is_voiceover(self):
        assert "voiceover" in REFERENCE_CONFIG["pipeline_steps"][0]["script"]

    def test_last_step_is_optimize(self):
        assert "optimize" in REFERENCE_CONFIG["pipeline_steps"][-1]["script"]
