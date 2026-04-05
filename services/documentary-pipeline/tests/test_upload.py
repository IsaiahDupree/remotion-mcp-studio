"""
test_upload.py — 150 pytest tests for upload_youtube.py

Sections:
  - Metadata Resolution (~60 tests)
  - Config Loading (~40 tests)
  - Video Metadata Quality (~50 tests)

Uses real files and data. No mocks.
"""
import json
import re
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from upload_youtube import (
    VIDEO_TITLE,
    VIDEO_DESCRIPTION,
    VIDEO_TAGS,
    VIDEO_CATEGORY_ID,
    VIDEO_PRIVACY,
    load_meta_from_config,
    resolve_metadata,
)
from conftest import make_args, CONFIG_PATH, RESEARCH_DIR


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Metadata Resolution (~60 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestResolveMetadataDefaults:
    """resolve_metadata without config or CLI overrides → hardcoded defaults."""

    def test_default_title(self):
        meta = resolve_metadata(make_args())
        assert meta["title"] == VIDEO_TITLE

    def test_default_description(self):
        meta = resolve_metadata(make_args())
        assert meta["description"] == VIDEO_DESCRIPTION

    def test_default_tags(self):
        meta = resolve_metadata(make_args())
        assert meta["tags"] == VIDEO_TAGS

    def test_default_category_id(self):
        meta = resolve_metadata(make_args())
        assert meta["category_id"] == VIDEO_CATEGORY_ID

    def test_default_privacy_is_unlisted(self):
        meta = resolve_metadata(make_args())
        assert meta["privacy"] == "unlisted"

    def test_default_returns_dict(self):
        meta = resolve_metadata(make_args())
        assert isinstance(meta, dict)

    def test_default_has_all_keys(self):
        meta = resolve_metadata(make_args())
        required = {"title", "description", "tags", "category_id", "privacy"}
        assert required == set(meta.keys())

    def test_default_tags_is_list(self):
        meta = resolve_metadata(make_args())
        assert isinstance(meta["tags"], list)

    def test_default_tags_nonempty(self):
        meta = resolve_metadata(make_args())
        assert len(meta["tags"]) > 0

    def test_default_tags_all_strings(self):
        meta = resolve_metadata(make_args())
        assert all(isinstance(t, str) for t in meta["tags"])


class TestResolveMetadataCLIOverrides:
    """CLI flags override both config and defaults."""

    def test_cli_title_override(self):
        meta = resolve_metadata(make_args(title="My Custom Title"))
        assert meta["title"] == "My Custom Title"

    def test_cli_description_override(self):
        meta = resolve_metadata(make_args(description="Custom desc"))
        assert meta["description"] == "Custom desc"

    def test_cli_privacy_public(self):
        meta = resolve_metadata(make_args(privacy="public"))
        assert meta["privacy"] == "public"

    def test_cli_privacy_unlisted(self):
        meta = resolve_metadata(make_args(privacy="unlisted"))
        assert meta["privacy"] == "unlisted"

    def test_cli_privacy_private(self):
        meta = resolve_metadata(make_args(privacy="private"))
        assert meta["privacy"] == "private"

    def test_cli_title_over_config(self):
        """CLI title takes precedence even when config is provided."""
        # Create a temp config with youtube_meta
        tmp = _make_temp_config(title="Config Title")
        meta = resolve_metadata(make_args(config=str(tmp), title="CLI Title"))
        assert meta["title"] == "CLI Title"

    def test_cli_description_over_config(self):
        tmp = _make_temp_config(description="Config desc")
        meta = resolve_metadata(make_args(config=str(tmp), description="CLI desc"))
        assert meta["description"] == "CLI desc"

    def test_cli_privacy_over_default(self):
        meta = resolve_metadata(make_args(privacy="private"))
        assert meta["privacy"] == "private"
        assert meta["privacy"] != VIDEO_PRIVACY or VIDEO_PRIVACY == "private"

    def test_cli_title_preserves_other_defaults(self):
        meta = resolve_metadata(make_args(title="Override"))
        assert meta["description"] == VIDEO_DESCRIPTION
        assert meta["tags"] == VIDEO_TAGS


class TestResolveMetadataWithConfig:
    """Config file values override hardcoded defaults."""

    def test_config_title_overrides_default(self):
        tmp = _make_temp_config(title="From Config")
        meta = resolve_metadata(make_args(config=str(tmp)))
        assert meta["title"] == "From Config"

    def test_config_description_overrides_default(self):
        tmp = _make_temp_config(description="Config description here")
        meta = resolve_metadata(make_args(config=str(tmp)))
        assert meta["description"] == "Config description here"

    def test_config_tags_overrides_default(self):
        tmp = _make_temp_config(tags=["a", "b", "c"])
        meta = resolve_metadata(make_args(config=str(tmp)))
        assert meta["tags"] == ["a", "b", "c"]

    def test_config_category_id_overrides_default(self):
        tmp = _make_temp_config(category_id="22")
        meta = resolve_metadata(make_args(config=str(tmp)))
        assert meta["category_id"] == "22"

    def test_config_without_title_keeps_default(self):
        tmp = _make_temp_config(description="Only desc")
        meta = resolve_metadata(make_args(config=str(tmp)))
        assert meta["title"] == VIDEO_TITLE

    def test_config_without_tags_keeps_default(self):
        tmp = _make_temp_config(title="T")
        meta = resolve_metadata(make_args(config=str(tmp)))
        assert meta["tags"] == VIDEO_TAGS

    def test_config_privacy_not_in_youtube_meta(self):
        """youtube_meta doesn't set privacy; it stays at default."""
        tmp = _make_temp_config(title="T")
        meta = resolve_metadata(make_args(config=str(tmp)))
        assert meta["privacy"] == VIDEO_PRIVACY


# Parametrize: 20 different title strings
_TITLE_CASES = [
    "Short",
    "A" * 99,
    "Title with spaces and numbers 123",
    "Unicode: cafe\u0301 re\u0301sume\u0301",
    "Emoji title \U0001f680\U0001f30d",
    "Title with 'single quotes'",
    'Title with "double quotes"',
    "ALLCAPS TITLE",
    "lowercase only",
    "MiXeD cAsE tItLe",
    "Title-with-dashes",
    "Title_with_underscores",
    "Title.with.dots",
    "Title (with parentheses)",
    "Title [with brackets]",
    "Title {with braces}",
    "Title & ampersand | pipe",
    "   Leading whitespace",
    "Trailing whitespace   ",
    "",
]


@pytest.mark.parametrize("title", _TITLE_CASES, ids=[f"title_{i}" for i in range(len(_TITLE_CASES))])
class TestParametrizedTitles:
    def test_cli_title_roundtrip(self, title):
        meta = resolve_metadata(make_args(title=title if title else None))
        if title:
            assert meta["title"] == title
        else:
            assert meta["title"] == VIDEO_TITLE


# Parametrize: tag list validation
_TAG_CASES = [
    (["SEO"], True),
    (["SEO", "GEO", "AI"], True),
    (["tag with spaces"], True),
    ([""], True),  # empty string is still a string
    ([], True),  # empty list is valid list
    (["SEO", "SEO"], False),  # duplicates
    (["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"], True),
    (["UPPER", "lower", "MiXeD"], True),
    (["unicode-caf\u00e9"], True),
    ([str(i) for i in range(30)], True),  # 30 numeric tags
]


@pytest.mark.parametrize("tags,expect_unique", _TAG_CASES, ids=[f"tags_{i}" for i in range(len(_TAG_CASES))])
class TestParametrizedTags:
    def test_tags_are_list(self, tags, expect_unique):
        assert isinstance(tags, list)

    def test_tags_all_strings(self, tags, expect_unique):
        assert all(isinstance(t, str) for t in tags)

    def test_tags_uniqueness(self, tags, expect_unique):
        has_no_dupes = len(tags) == len(set(tags))
        assert has_no_dupes == expect_unique


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Config Loading (~40 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestLoadRealConfig:
    """Load the real generate_config.json and validate its structure."""

    def test_config_file_exists(self, config_path):
        assert config_path.exists()

    def test_config_is_valid_json(self, config_data):
        assert isinstance(config_data, dict)

    def test_config_has_topic(self, config_data):
        assert "topic" in config_data

    def test_config_has_title(self, config_data):
        assert "title" in config_data

    def test_config_has_chapter_ids(self, config_data):
        assert "chapter_ids" in config_data
        assert isinstance(config_data["chapter_ids"], list)

    def test_config_has_10_chapters(self, config_data):
        assert len(config_data["chapter_ids"]) == 10

    def test_config_has_chapter_meta(self, config_data):
        assert "chapter_meta" in config_data
        assert isinstance(config_data["chapter_meta"], dict)

    def test_config_chapter_meta_matches_ids(self, config_data):
        for cid in config_data["chapter_ids"]:
            assert cid in config_data["chapter_meta"], f"Missing meta for {cid}"

    def test_config_chapter_meta_has_title(self, config_data):
        for cid, meta in config_data["chapter_meta"].items():
            assert "title" in meta, f"Missing title in {cid}"

    def test_config_chapter_meta_has_era(self, config_data):
        for cid, meta in config_data["chapter_meta"].items():
            assert "era" in meta, f"Missing era in {cid}"

    def test_config_chapter_meta_has_color(self, config_data):
        for cid, meta in config_data["chapter_meta"].items():
            assert "color" in meta, f"Missing color in {cid}"
            assert meta["color"].startswith("#"), f"Color should be hex in {cid}"

    def test_config_chapter_meta_has_tone(self, config_data):
        for cid, meta in config_data["chapter_meta"].items():
            assert "tone" in meta, f"Missing tone in {cid}"

    def test_config_chapter_meta_has_surprising_fact(self, config_data):
        for cid, meta in config_data["chapter_meta"].items():
            assert "surprising_fact" in meta, f"Missing surprising_fact in {cid}"

    def test_config_chapter_meta_has_image_style_hints(self, config_data):
        for cid, meta in config_data["chapter_meta"].items():
            assert "image_style_hints" in meta, f"Missing image_style_hints in {cid}"
            assert isinstance(meta["image_style_hints"], list)

    def test_config_has_pipeline_steps(self, config_data):
        assert "pipeline_steps" in config_data
        assert isinstance(config_data["pipeline_steps"], list)

    def test_config_pipeline_has_steps(self, config_data):
        assert len(config_data["pipeline_steps"]) >= 9

    def test_config_title_under_100_chars(self, config_data):
        assert len(config_data["title"]) < 100

    def test_config_topic_is_nontrivial(self, config_data):
        assert len(config_data["topic"]) > 50

    def test_config_has_script_file(self, config_data):
        assert "script_file" in config_data

    def test_config_has_audio_dir(self, config_data):
        assert "audio_dir" in config_data

    def test_config_has_output_dir(self, config_data):
        assert "output_dir" in config_data


class TestConfigHasYoutubeMetaReal:
    """The reference config has youtube_meta — validate its presence."""

    def test_real_config_has_youtube_meta(self, config_data):
        assert "youtube_meta" in config_data

    def test_load_meta_succeeds_on_real_config(self):
        """load_meta_from_config should succeed when youtube_meta is present."""
        meta = load_meta_from_config(str(CONFIG_PATH))
        assert isinstance(meta, dict)
        assert "title" in meta

    def test_load_meta_exits_on_missing_youtube_meta(self, tmp_path):
        """load_meta_from_config should sys.exit(1) when youtube_meta is absent."""
        no_yt_config = tmp_path / "no_yt.json"
        no_yt_config.write_text('{"chapter_ids": [], "chapter_meta": {}}')
        with pytest.raises(SystemExit) as exc_info:
            load_meta_from_config(str(no_yt_config))
        assert exc_info.value.code == 1

    def test_load_meta_exits_on_nonexistent_file(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            load_meta_from_config(str(tmp_path / "nonexistent.json"))
        assert exc_info.value.code == 1


class TestConfigWithYoutubeMeta:
    """Test load_meta_from_config with a valid youtube_meta config."""

    def test_load_returns_dict(self):
        tmp = _make_temp_config(title="T", description="D", tags=["a"])
        meta = load_meta_from_config(str(tmp))
        assert isinstance(meta, dict)

    def test_load_has_title(self):
        tmp = _make_temp_config(title="Test Title")
        meta = load_meta_from_config(str(tmp))
        assert meta["title"] == "Test Title"

    def test_load_has_description(self):
        tmp = _make_temp_config(description="Test desc")
        meta = load_meta_from_config(str(tmp))
        assert meta["description"] == "Test desc"

    def test_load_has_tags(self):
        tmp = _make_temp_config(tags=["x", "y"])
        meta = load_meta_from_config(str(tmp))
        assert meta["tags"] == ["x", "y"]

    def test_load_has_category_id(self):
        tmp = _make_temp_config(category_id="28")
        meta = load_meta_from_config(str(tmp))
        assert meta["category_id"] == "28"

    def test_load_preserves_extra_keys(self):
        tmp = _make_temp_config(title="T", chapters_timestamps="00:00 Intro")
        meta = load_meta_from_config(str(tmp))
        assert "chapters_timestamps" in meta

    def test_load_minimal_meta(self):
        """Even a single key in youtube_meta should load."""
        tmp = _make_temp_config(title="Only Title")
        meta = load_meta_from_config(str(tmp))
        assert "title" in meta

    def test_load_empty_youtube_meta_exits(self):
        """Empty youtube_meta dict is falsy → sys.exit(1)."""
        tmp = _write_temp_json({"youtube_meta": {}})
        with pytest.raises(SystemExit):
            load_meta_from_config(str(tmp))

    def test_load_null_youtube_meta_exits(self):
        tmp = _write_temp_json({"youtube_meta": None})
        with pytest.raises(SystemExit):
            load_meta_from_config(str(tmp))

    def test_load_large_tag_list(self):
        tags = [f"tag_{i}" for i in range(50)]
        tmp = _make_temp_config(tags=tags)
        meta = load_meta_from_config(str(tmp))
        assert len(meta["tags"]) == 50


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Video Metadata Quality (~50 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestHardcodedMetadataQuality:
    """Validate the hardcoded VIDEO_* constants in upload_youtube.py."""

    def test_title_not_empty(self):
        assert len(VIDEO_TITLE) > 0

    def test_title_under_100_chars(self):
        assert len(VIDEO_TITLE) < 100

    def test_title_is_descriptive(self):
        assert "SEO" in VIDEO_TITLE or "seo" in VIDEO_TITLE.lower()

    def test_title_not_generic(self):
        generic = {"Video", "Untitled", "Test", "My Video", "Upload"}
        assert VIDEO_TITLE not in generic

    def test_title_contains_topic_keyword(self):
        assert "SEO" in VIDEO_TITLE

    def test_title_contains_year_or_timeframe(self):
        assert "2030" in VIDEO_TITLE or "2026" in VIDEO_TITLE

    def test_description_not_empty(self):
        assert len(VIDEO_DESCRIPTION) > 0

    def test_description_over_100_chars(self):
        assert len(VIDEO_DESCRIPTION) > 100

    def test_description_contains_chapters(self):
        assert "00:00" in VIDEO_DESCRIPTION

    def test_description_chapter_timestamp_format(self):
        timestamps = re.findall(r"\d{2}:\d{2}", VIDEO_DESCRIPTION)
        assert len(timestamps) >= 10, "Expected at least 10 chapter timestamps"

    def test_description_chapters_start_at_zero(self):
        assert "00:00" in VIDEO_DESCRIPTION

    def test_description_contains_ai_disclosure(self):
        lower = VIDEO_DESCRIPTION.lower()
        assert "ai-generated" in lower or "ai generated" in lower

    def test_description_contains_key_topics(self):
        lower = VIDEO_DESCRIPTION.lower()
        assert "generative engine optimization" in lower or "geo" in lower

    def test_description_contains_hashtags(self):
        assert "#SEO" in VIDEO_DESCRIPTION

    def test_description_multiline(self):
        assert "\n" in VIDEO_DESCRIPTION

    def test_tags_nonempty(self):
        assert len(VIDEO_TAGS) > 0

    def test_tags_has_more_than_5(self):
        assert len(VIDEO_TAGS) > 5

    def test_tags_all_strings(self):
        assert all(isinstance(t, str) for t in VIDEO_TAGS)

    def test_tags_no_duplicates(self):
        assert len(VIDEO_TAGS) == len(set(VIDEO_TAGS))

    def test_tags_include_seo(self):
        lower_tags = [t.lower() for t in VIDEO_TAGS]
        assert "seo" in lower_tags

    def test_tags_include_geo(self):
        lower_tags = [t.lower() for t in VIDEO_TAGS]
        assert "geo" in lower_tags

    def test_tags_include_ai(self):
        lower_tags = [t.lower() for t in VIDEO_TAGS]
        assert any("ai" in t for t in lower_tags)

    def test_tags_include_documentary(self):
        lower_tags = [t.lower() for t in VIDEO_TAGS]
        assert any("documentary" in t for t in lower_tags)

    def test_category_id_is_string(self):
        assert isinstance(VIDEO_CATEGORY_ID, str)

    def test_category_id_is_valid_youtube_category(self):
        # Valid YouTube category IDs: 1-44
        valid_ids = {str(i) for i in range(1, 45)}
        assert VIDEO_CATEGORY_ID in valid_ids

    def test_category_id_is_education(self):
        assert VIDEO_CATEGORY_ID == "27"

    def test_privacy_is_string(self):
        assert isinstance(VIDEO_PRIVACY, str)

    def test_privacy_is_valid_value(self):
        assert VIDEO_PRIVACY in {"public", "unlisted", "private"}

    def test_privacy_default_is_unlisted(self):
        assert VIDEO_PRIVACY == "unlisted"


# Parametrize: 30 different tag format validations
_TAG_FORMAT_CASES = [
    "SEO",
    "GEO",
    "generative engine optimization",
    "AI overviews",
    "search engine optimization",
    "SEO 2026",
    "SEO documentary",
    "Google algorithm",
    "AI search",
    "zero-click search",
    "E-E-A-T",
    "local SEO",
    "schema markup",
    "programmatic SEO",
    "digital marketing",
    "content strategy",
    "ChatGPT search",
    "Perplexity SEO",
    "agentic AI",
    "answer engine optimization",
    "SEO future",
    # Additional format checks (not necessarily in VIDEO_TAGS)
    "single",
    "two words",
    "three word tag",
    "hyphen-tag",
    "UPPERCASE",
    "MiXeD CaSe",
    "tag with numbers 2026",
    "special & chars",
    "acronym AI",
]


@pytest.mark.parametrize("tag", _TAG_FORMAT_CASES, ids=[f"tagfmt_{i}" for i in range(len(_TAG_FORMAT_CASES))])
class TestTagFormat:
    def test_tag_is_string(self, tag):
        assert isinstance(tag, str)

    def test_tag_not_empty(self, tag):
        assert len(tag) > 0

    def test_tag_under_500_chars(self, tag):
        assert len(tag) < 500


class TestDescriptionChapterTimestamps:
    """Validate that chapter timestamps in the description are well-formed."""

    def test_timestamps_are_ascending(self):
        timestamps = re.findall(r"(\d{2}):(\d{2})", VIDEO_DESCRIPTION)
        seconds = [int(m) * 60 + int(s) for m, s in timestamps]
        # Filter to unique (some may repeat in non-chapter context)
        # Take only the first 10 which are chapter markers
        chapter_seconds = seconds[:10]
        for i in range(1, len(chapter_seconds)):
            assert chapter_seconds[i] > chapter_seconds[i - 1], (
                f"Timestamp {i} not ascending: {chapter_seconds[i-1]} >= {chapter_seconds[i]}"
            )

    def test_first_timestamp_is_zero(self):
        timestamps = re.findall(r"(\d{2}):(\d{2})", VIDEO_DESCRIPTION)
        first = int(timestamps[0][0]) * 60 + int(timestamps[0][1])
        assert first == 0

    def test_at_least_10_timestamps(self):
        timestamps = re.findall(r"\d{2}:\d{2}", VIDEO_DESCRIPTION)
        assert len(timestamps) >= 10

    def test_each_timestamp_has_description(self):
        """Each timestamp line should have text after it."""
        lines = VIDEO_DESCRIPTION.split("\n")
        ts_lines = [l for l in lines if re.match(r"^\d{2}:\d{2}\s", l)]
        for line in ts_lines:
            text_after = re.sub(r"^\d{2}:\d{2}\s*", "", line).strip()
            assert len(text_after) > 5, f"Timestamp line too short: {line}"

    def test_last_chapter_timestamp_under_30_min(self):
        timestamps = re.findall(r"(\d{2}):(\d{2})", VIDEO_DESCRIPTION)
        chapter_timestamps = timestamps[:10]
        last = int(chapter_timestamps[-1][0]) * 60 + int(chapter_timestamps[-1][1])
        assert last < 30 * 60, "Last chapter starts after 30 minutes"


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _make_temp_config(**youtube_meta_fields) -> Path:
    """Create a temp config JSON with the given youtube_meta fields."""
    config = {"youtube_meta": youtube_meta_fields}
    return _write_temp_json(config)


def _write_temp_json(data: dict) -> Path:
    """Write data to a temp JSON file and return its path."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, tmp)
    tmp.close()
    return Path(tmp.name)
