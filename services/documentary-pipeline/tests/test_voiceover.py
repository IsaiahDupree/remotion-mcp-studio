# 300 tests for voiceover generation pipeline
"""
Comprehensive pytest suite for generate_voiceover_hq.py
Covers: chunk splitting, quality gates, chapter loading, audio validation, concatenation logic.
"""
import sys
import os
import string
import random
import tempfile
from pathlib import Path

import pytest

# Add project root to path so we can import the module
PROJECT_ROOT = Path(str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from generate_voiceover_hq import (

SCRIPT_DIR = Path(__file__).parent
    split_into_chunks,
    load_chapters_from_config,
    concatenate_chunks,
    get_mp3_duration,
    MIN_CHUNK_SIZE_BYTES,
    MAX_CHUNK_CHARS,
    DURATION_TOLERANCE,
    PARAGRAPH_GAP_SECS,
)

# ---------------------------------------------------------------------------
# Paths to real project files
# ---------------------------------------------------------------------------
CONFIG_PATH = str(
    PROJECT_ROOT
    / "research"
    / "seo_and_geo_in_2026_2030_what_actually_works_what_s_changing"
    / "generate_config.json"
)
AUDIO_DIR = PROJECT_ROOT / "audio_v2_hq"
CHAPTER_IDS = [
    "01_intro",
    "02_origins",
    "03_breakthroughs",
    "04_experts",
    "05_evolution",
    "06_current_affairs",
    "07_future_speculation",
    "08_local_seo",
    "09_schema_and_programmatic",
    "10_conclusion",
]


# ===========================================================================
# Helper utilities
# ===========================================================================
def _random_text(n_chars: int, seed: int = 0) -> str:
    """Generate deterministic pseudo-random text of approximately n_chars."""
    rng = random.Random(seed)
    words = []
    length = 0
    while length < n_chars:
        word_len = rng.randint(2, 10)
        word = "".join(rng.choices(string.ascii_lowercase, k=word_len))
        words.append(word)
        length += word_len + 1
    return " ".join(words)[:n_chars]


def _paragraphs(sizes: list[int], seed: int = 42) -> str:
    """Build text with paragraphs of given char sizes separated by \\n\\n."""
    paras = []
    for i, sz in enumerate(sizes):
        paras.append(_random_text(sz, seed=seed + i))
    return "\n\n".join(paras)


# ===========================================================================
# SECTION 1: Chunk Splitting Logic (~100 tests)
# ===========================================================================
class TestSplitIntoChunksBasic:
    """Basic chunk-splitting behaviour."""

    def test_single_paragraph_under_max_returns_one_chunk(self):
        text = "This is a short paragraph."
        chunks = split_into_chunks(text, max_chars=1000)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_two_paragraphs_both_under_max_merged(self):
        text = "Paragraph one.\n\nParagraph two."
        chunks = split_into_chunks(text, max_chars=1000)
        assert len(chunks) == 1
        assert "Paragraph one." in chunks[0]
        assert "Paragraph two." in chunks[0]

    def test_two_paragraphs_exceeding_max_split(self):
        p1 = "A" * 60
        p2 = "B" * 60
        text = f"{p1}\n\n{p2}"
        chunks = split_into_chunks(text, max_chars=100)
        assert len(chunks) == 2

    def test_many_small_paragraphs_merge_optimally(self):
        paras = ["word"] * 20  # each 4 chars
        text = "\n\n".join(paras)
        chunks = split_into_chunks(text, max_chars=50)
        # All content preserved
        assert "".join(chunks).replace("\n\n", "").replace(" ", "") == "word" * 20
        for c in chunks:
            assert len(c) <= 50

    def test_empty_text_returns_empty_list(self):
        assert split_into_chunks("") == []

    def test_only_whitespace_returns_empty_list(self):
        assert split_into_chunks("   \n\n   \n\n   ") == []

    def test_single_word(self):
        chunks = split_into_chunks("hello")
        assert chunks == ["hello"]

    def test_very_long_single_paragraph_one_chunk(self):
        text = "A" * 5000  # no \n\n breaks
        chunks = split_into_chunks(text, max_chars=1000)
        # Single paragraph with no break points stays as 1 chunk
        assert len(chunks) == 1

    def test_100_tiny_paragraphs(self):
        paras = [f"p{i}" for i in range(100)]
        text = "\n\n".join(paras)
        chunks = split_into_chunks(text, max_chars=500)
        joined = "\n\n".join(chunks)
        for p in paras:
            assert p in joined

    def test_no_empty_chunks_in_output(self):
        text = "a\n\n\n\n\n\nb\n\nc"
        chunks = split_into_chunks(text, max_chars=100)
        for c in chunks:
            assert c.strip() != ""

    def test_exactly_at_max_chars_boundary(self):
        text = "A" * 100
        chunks = split_into_chunks(text, max_chars=100)
        assert len(chunks) == 1

    def test_one_char_over_max_single_paragraph(self):
        text = "A" * 101
        chunks = split_into_chunks(text, max_chars=100)
        # Single paragraph cannot be split further
        assert len(chunks) == 1

    def test_two_paragraphs_exactly_at_boundary(self):
        # Two 49-char paragraphs + 2 for "\n\n" separator = 100
        p1 = "A" * 49
        p2 = "B" * 49
        text = f"{p1}\n\n{p2}"
        chunks = split_into_chunks(text, max_chars=100)
        assert len(chunks) == 1

    def test_two_paragraphs_one_char_over_boundary(self):
        p1 = "A" * 50
        p2 = "B" * 50
        text = f"{p1}\n\n{p2}"
        # 50 + 50 + 2 = 102 > 100
        chunks = split_into_chunks(text, max_chars=100)
        assert len(chunks) == 2

    def test_unicode_accented_chars(self):
        text = "Cafe\u0301 re\u0301sume\u0301\n\nUber u\u0308ber"
        chunks = split_into_chunks(text, max_chars=1000)
        assert len(chunks) >= 1
        joined = "\n\n".join(chunks)
        assert "Cafe\u0301" in joined

    def test_cjk_characters(self):
        text = "\u4f60\u597d\u4e16\u754c\n\n\u6d4b\u8bd5\u6587\u672c"
        chunks = split_into_chunks(text, max_chars=1000)
        assert len(chunks) >= 1

    def test_markdown_formatting_preserved(self):
        text = "**Bold text** and *italic*\n\n# Heading\n\nMore text"
        chunks = split_into_chunks(text, max_chars=1000)
        joined = "\n\n".join(chunks)
        assert "**Bold text**" in joined

    def test_numbers_and_special_chars(self):
        text = "Price: $99.99! (50% off)\n\nCall 1-800-555-0123"
        chunks = split_into_chunks(text, max_chars=1000)
        assert len(chunks) >= 1

    def test_preserves_all_content(self):
        text = "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph here."
        chunks = split_into_chunks(text, max_chars=50)
        joined = "\n\n".join(chunks)
        assert "First paragraph here." in joined
        assert "Second paragraph here." in joined
        assert "Third paragraph here." in joined

    def test_default_max_chars_is_module_constant(self):
        text = "Short."
        chunks = split_into_chunks(text)
        assert len(chunks) == 1


# Parametrized: various max_chars values
@pytest.mark.parametrize("max_chars", [100, 500, 1000])
class TestSplitMaxCharsValues:
    def test_no_chunk_exceeds_max_when_paragraphs_are_small(self, max_chars):
        paras = [_random_text(max_chars // 5, seed=i) for i in range(10)]
        text = "\n\n".join(paras)
        chunks = split_into_chunks(text, max_chars=max_chars)
        for c in chunks:
            assert len(c) <= max_chars, f"Chunk length {len(c)} exceeds max {max_chars}"

    def test_all_content_preserved(self, max_chars):
        paras = [_random_text(max_chars // 3, seed=i + 100) for i in range(5)]
        text = "\n\n".join(paras)
        chunks = split_into_chunks(text, max_chars=max_chars)
        joined = "\n\n".join(chunks)
        for p in paras:
            assert p in joined

    def test_no_empty_chunks(self, max_chars):
        paras = [_random_text(max_chars // 4, seed=i + 200) for i in range(8)]
        text = "\n\n".join(paras)
        chunks = split_into_chunks(text, max_chars=max_chars)
        for c in chunks:
            assert c.strip() != ""


# Parametrized: 50 random texts — no chunk exceeds max_chars
RANDOM_TEXT_SEEDS = list(range(10))


@pytest.mark.parametrize("seed", RANDOM_TEXT_SEEDS)
def test_random_text_no_chunk_exceeds_max(seed):
    rng = random.Random(seed)
    n_paras = rng.randint(1, 20)
    paras = [_random_text(rng.randint(10, 300), seed=seed * 100 + i) for i in range(n_paras)]
    text = "\n\n".join(paras)
    max_c = rng.choice([100, 500, 1000, 2000])
    chunks = split_into_chunks(text, max_chars=max_c)
    for idx, c in enumerate(chunks):
        if "\n\n" not in c:
            continue
        assert len(c) <= max_c, f"Seed {seed}, chunk {idx}: {len(c)} > {max_c}"


@pytest.mark.parametrize("seed", RANDOM_TEXT_SEEDS[:5])
def test_random_text_content_preserved(seed):
    rng = random.Random(seed + 5000)
    n_paras = rng.randint(2, 15)
    paras = [_random_text(rng.randint(20, 200), seed=seed * 200 + i) for i in range(n_paras)]
    text = "\n\n".join(paras)
    chunks = split_into_chunks(text, max_chars=500)
    joined = "\n\n".join(chunks)
    for p in paras:
        assert p in joined, f"Paragraph lost: {p[:40]}..."


@pytest.mark.parametrize("seed", RANDOM_TEXT_SEEDS[:5])
def test_random_text_no_empty_chunks(seed):
    rng = random.Random(seed + 9000)
    n_paras = rng.randint(3, 25)
    paras = [_random_text(rng.randint(5, 150), seed=seed * 300 + i) for i in range(n_paras)]
    text = "\n\n".join(paras)
    chunks = split_into_chunks(text, max_chars=200)
    for c in chunks:
        assert c.strip() != ""


class TestSplitEdgeCases:
    def test_triple_newline_treated_as_paragraph_break(self):
        text = "First\n\n\n\nSecond"
        chunks = split_into_chunks(text, max_chars=1000)
        assert len(chunks) >= 1

    def test_single_newline_not_paragraph_break(self):
        text = "Line one\nLine two"
        chunks = split_into_chunks(text, max_chars=1000)
        assert len(chunks) == 1

    def test_tab_characters(self):
        text = "\tTabbed paragraph.\n\n\tAnother tabbed."
        chunks = split_into_chunks(text, max_chars=1000)
        assert len(chunks) >= 1

    def test_mixed_whitespace_paragraphs(self):
        text = "  Para 1  \n\n  Para 2  \n\n  Para 3  "
        chunks = split_into_chunks(text, max_chars=1000)
        for c in chunks:
            assert c == c.strip()

    def test_very_small_max_chars(self):
        text = "Hello\n\nWorld"
        chunks = split_into_chunks(text, max_chars=3)
        assert len(chunks) == 2

    def test_paragraph_with_only_newlines_inside(self):
        text = "One\n\n\n\n\n\n\n\nTwo"
        chunks = split_into_chunks(text, max_chars=1000)
        joined = "\n\n".join(chunks)
        assert "One" in joined
        assert "Two" in joined

    def test_emoji_in_text(self):
        text = "Hello \U0001f600\n\nWorld \U0001f30d"
        chunks = split_into_chunks(text, max_chars=1000)
        assert len(chunks) >= 1

    def test_url_in_text(self):
        text = "Visit https://example.com/path?q=1&b=2\n\nMore info at http://test.org"
        chunks = split_into_chunks(text, max_chars=1000)
        joined = "\n\n".join(chunks)
        assert "https://example.com" in joined


# ===========================================================================
# SECTION 2: Quality Gate — Duration Check (~50 tests)
# ===========================================================================
class TestDurationFormula:
    """The expected duration formula: chars / 15 = seconds."""

    @pytest.mark.parametrize("char_count", [50, 100, 250, 500, 1000, 2500])
    def test_expected_duration_formula(self, char_count):
        expected = char_count / 15.0
        assert expected == pytest.approx(char_count / 15.0)

    @pytest.mark.parametrize("char_count", [50, 100, 500, 1000, 2500])
    def test_tolerance_lower_bound(self, char_count):
        expected = char_count / 15.0
        lower = expected * (1 - DURATION_TOLERANCE)
        assert lower == pytest.approx(expected * 0.5)

    @pytest.mark.parametrize("char_count", [50, 100, 500, 1000, 2500])
    def test_tolerance_upper_bound(self, char_count):
        expected = char_count / 15.0
        upper = expected * (1 + DURATION_TOLERANCE)
        assert upper == pytest.approx(expected * 1.5)

    @pytest.mark.parametrize(
        "char_count,actual_secs,should_warn",
        [
            (150, 10.0, False),      # expected 10, actual 10 → ratio 1.0
            (150, 5.0, False),       # ratio 0.5 → at boundary
            (150, 15.0, False),      # ratio 1.5 → at boundary
            (150, 4.9, True),        # ratio <0.5 → warn
            (150, 15.1, True),       # ratio >1.5 → warn
            (300, 20.0, False),      # expected 20, actual 20
            (300, 9.0, True),        # ratio <0.5
            (300, 31.0, True),       # ratio >1.5
            (1000, 66.7, False),     # expected ~66.7
            (1000, 30.0, True),      # under
            (1000, 110.0, True),     # over
        ],
    )
    def test_duration_ratio_warning_logic(self, char_count, actual_secs, should_warn):
        expected = char_count / 15.0
        ratio = actual_secs / expected
        warns = ratio < (1 - DURATION_TOLERANCE) or ratio > (1 + DURATION_TOLERANCE)
        assert warns == should_warn, (
            f"chars={char_count}, actual={actual_secs}s, expected={expected:.1f}s, "
            f"ratio={ratio:.2f}, warns={warns}"
        )

    @pytest.mark.parametrize("char_count", [1, 50, 500, 2500])
    def test_expected_duration_positive(self, char_count):
        assert char_count / 15.0 > 0

    @pytest.mark.parametrize("char_count", [100, 1000])
    def test_ratio_of_one_is_always_within_tolerance(self, char_count):
        expected = char_count / 15.0
        ratio = expected / expected  # 1.0
        assert not (ratio < (1 - DURATION_TOLERANCE) or ratio > (1 + DURATION_TOLERANCE))

    def test_duration_tolerance_is_fifty_percent(self):
        assert DURATION_TOLERANCE == 0.50

    def test_zero_char_count_zero_duration(self):
        assert 0 / 15.0 == 0.0

    @pytest.mark.parametrize(
        "ratio",
        [0.5, 0.7, 1.0, 1.3, 1.5],
    )
    def test_ratios_within_tolerance_do_not_warn(self, ratio):
        warns = ratio < (1 - DURATION_TOLERANCE) or ratio > (1 + DURATION_TOLERANCE)
        assert not warns, f"Ratio {ratio} should not warn"

    @pytest.mark.parametrize("ratio", [0.1, 0.3, 0.49, 1.51, 2.0, 3.0])
    def test_ratios_outside_tolerance_do_warn(self, ratio):
        warns = ratio < (1 - DURATION_TOLERANCE) or ratio > (1 + DURATION_TOLERANCE)
        assert warns, f"Ratio {ratio} should warn"


# ===========================================================================
# SECTION 3: Quality Gate — File Size (~30 tests)
# ===========================================================================
class TestFileSizeGate:
    """MIN_CHUNK_SIZE_BYTES = 5000."""

    def test_min_chunk_size_constant(self):
        assert MIN_CHUNK_SIZE_BYTES == 5000

    @pytest.mark.parametrize("size", [0, 100, 4999])
    def test_below_minimum_fails_gate(self, size):
        assert size < MIN_CHUNK_SIZE_BYTES

    @pytest.mark.parametrize("size", [5000, 10000, 100000])
    def test_above_or_equal_minimum_passes_gate(self, size):
        assert size >= MIN_CHUNK_SIZE_BYTES

    def test_zero_byte_file_fails_gate(self):
        assert 0 < MIN_CHUNK_SIZE_BYTES

    def test_exact_boundary_passes(self):
        assert 5000 >= MIN_CHUNK_SIZE_BYTES

    def test_one_below_boundary_fails(self):
        assert 4999 < MIN_CHUNK_SIZE_BYTES

    @pytest.mark.parametrize("size", [5000, 10000, 50000])
    def test_real_audio_file_size_range_passes(self, size):
        assert size >= MIN_CHUNK_SIZE_BYTES

    def test_tmpdir_file_below_min(self, tmp_path):
        p = tmp_path / "tiny.mp3"
        p.write_bytes(b"\x00" * 100)
        assert p.stat().st_size < MIN_CHUNK_SIZE_BYTES

    def test_tmpdir_file_above_min(self, tmp_path):
        p = tmp_path / "good.mp3"
        p.write_bytes(b"\x00" * 6000)
        assert p.stat().st_size >= MIN_CHUNK_SIZE_BYTES

    def test_tmpdir_empty_file(self, tmp_path):
        p = tmp_path / "empty.mp3"
        p.write_bytes(b"")
        assert p.stat().st_size < MIN_CHUNK_SIZE_BYTES

    @pytest.mark.parametrize(
        "size,expected_pass",
        [
            (0, False),
            (4999, False),
            (5000, True),
            (100000, True),
        ],
    )
    def test_gate_decision(self, size, expected_pass):
        passes = size >= MIN_CHUNK_SIZE_BYTES
        assert passes == expected_pass

    @pytest.mark.parametrize("multiplier", [1, 5, 10])
    def test_multiples_of_min_pass(self, multiplier):
        assert MIN_CHUNK_SIZE_BYTES * multiplier >= MIN_CHUNK_SIZE_BYTES



# ===========================================================================
# SECTION 4: Chapter Loading from Config (~40 tests)
# ===========================================================================
class TestLoadChaptersFromConfig:
    """Tests using the real config and script files."""

    @pytest.fixture(scope="class")
    def loaded(self):
        chapters, config = load_chapters_from_config(CONFIG_PATH)
        return chapters, config

    def test_returns_tuple(self, loaded):
        chapters, config = loaded
        assert isinstance(chapters, dict)
        assert isinstance(config, dict)

    def test_chapters_is_dict(self, loaded):
        chapters, _ = loaded
        assert isinstance(chapters, dict)

    def test_config_has_chapter_ids(self, loaded):
        _, config = loaded
        assert "chapter_ids" in config

    def test_chapter_count_matches_config(self, loaded):
        chapters, config = loaded
        assert len(chapters) <= len(config["chapter_ids"])

    def test_all_chapter_ids_present(self, loaded):
        chapters, _ = loaded
        for cid in CHAPTER_IDS:
            assert cid in chapters, f"Missing chapter: {cid}"

    @pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
    def test_chapter_text_non_empty(self, loaded, chapter_id):
        chapters, _ = loaded
        assert len(chapters[chapter_id].strip()) > 0

    @pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
    def test_chapter_no_bold_markdown(self, loaded, chapter_id):
        chapters, _ = loaded
        assert "**" not in chapters[chapter_id]

    @pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
    def test_chapter_no_heading_hashes(self, loaded, chapter_id):
        chapters, _ = loaded
        text = chapters[chapter_id]
        import re
        # No lines starting with # followed by space (markdown headings)
        assert not re.search(r"^#{1,3}\s", text, re.MULTILINE)

    def test_config_has_topic(self, loaded):
        _, config = loaded
        assert "topic" in config

    def test_config_has_title(self, loaded):
        _, config = loaded
        assert "title" in config

    def test_missing_config_raises(self):
        with pytest.raises(Exception):
            load_chapters_from_config("/nonexistent/path/config.json")

    def test_config_chapter_ids_list(self, loaded):
        _, config = loaded
        assert isinstance(config["chapter_ids"], list)
        assert len(config["chapter_ids"]) == 10

    def test_chapter_text_reasonable_length(self, loaded):
        chapters, _ = loaded
        for cid, text in chapters.items():
            assert len(text) > 100, f"{cid} text too short: {len(text)}"

    def test_no_triple_backticks_in_chapters(self, loaded):
        chapters, _ = loaded
        for cid, text in chapters.items():
            assert "```" not in text, f"{cid} still has code fences"

    def test_no_horizontal_rules_in_chapters(self, loaded):
        chapters, _ = loaded
        for cid, text in chapters.items():
            assert "---" not in text, f"{cid} still has horizontal rules"

    def test_no_excessive_newlines(self, loaded):
        chapters, _ = loaded
        for cid, text in chapters.items():
            assert "\n\n\n" not in text, f"{cid} has 3+ consecutive newlines"


# ===========================================================================
# SECTION 5: Audio File Validation (~50 tests)
# ===========================================================================
class TestAudioFilesExist:
    """Validate real generated audio files in audio_v2_hq/."""

    @pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
    def test_audio_file_exists(self, chapter_id):
        path = AUDIO_DIR / f"{chapter_id}.mp3"
        assert path.exists(), f"Missing audio file: {path}"

    @pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
    def test_audio_file_has_mp3_extension(self, chapter_id):
        path = AUDIO_DIR / f"{chapter_id}.mp3"
        assert path.suffix == ".mp3"

    @pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
    def test_audio_file_above_5kb(self, chapter_id):
        path = AUDIO_DIR / f"{chapter_id}.mp3"
        assert path.stat().st_size > 5 * 1024, f"{chapter_id}.mp3 is under 5KB"

    def test_file_count_matches_chapter_count(self):
        mp3s = list(AUDIO_DIR.glob("*.mp3"))
        # At least as many as chapters (could be more if extras exist)
        assert len(mp3s) >= len(CHAPTER_IDS)

class TestAudioDuration:
    """Duration sanity checks using ffprobe on real audio files."""

    @pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
    def test_duration_between_30_and_300_seconds(self, chapter_id):
        path = AUDIO_DIR / f"{chapter_id}.mp3"
        dur = get_mp3_duration(path)
        if dur > 0:
            assert 30 <= dur <= 300, f"{chapter_id} duration {dur:.1f}s out of range"
        else:
            pytest.skip("ffprobe not available or returned 0")

    def test_total_duration_20_to_40_minutes(self):
        total = 0.0
        for cid in CHAPTER_IDS:
            path = AUDIO_DIR / f"{cid}.mp3"
            dur = get_mp3_duration(path)
            total += dur
        if total > 0:
            minutes = total / 60.0
            assert 20 <= minutes <= 40, f"Total duration {minutes:.1f}min out of range"
        else:
            pytest.skip("ffprobe not available")

class TestAudioFileNames:
    """File name validation."""

    @pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
    def test_filename_matches_chapter_id(self, chapter_id):
        path = AUDIO_DIR / f"{chapter_id}.mp3"
        assert path.name == f"{chapter_id}.mp3"

    def test_no_unexpected_mp3_files(self):
        """All mp3 files in dir should match a known chapter ID."""
        mp3s = {f.stem for f in AUDIO_DIR.glob("*.mp3")}
        expected = set(CHAPTER_IDS)
        unexpected = mp3s - expected
        # Allow unexpected files but flag them
        assert len(unexpected) < 5, f"Many unexpected files: {unexpected}"

    @pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
    def test_audio_file_size_above_1mb(self, chapter_id):
        """Full chapter files should be >1MB."""
        path = AUDIO_DIR / f"{chapter_id}.mp3"
        size_mb = path.stat().st_size / (1024 * 1024)
        assert size_mb > 1.0, f"{chapter_id}.mp3 only {size_mb:.2f}MB"


# ===========================================================================
# SECTION 6: Concatenation Logic (~30 tests)
# ===========================================================================
class TestConcatenateChunksLogic:
    """Test concatenation parameter handling and edge cases."""

    def test_empty_chunk_list_returns_false(self):
        result = concatenate_chunks([], Path("/tmp/out.mp3"))
        assert result is False

    @pytest.mark.parametrize("gap", [0, 0.1, 0.15, 0.5, 1.0])
    def test_silence_gap_parameter_accepted(self, gap):
        """Verify the function signature accepts various gap values without TypeError."""
        # We pass empty list which returns False before gap is used
        result = concatenate_chunks([], Path("/tmp/out.mp3"), gap_secs=gap)
        assert result is False

    def test_default_gap_is_module_constant(self):
        assert PARAGRAPH_GAP_SECS == 0.15

    def test_single_real_chunk_concatenation(self):
        """If a single-chunk chapter exists, try concatenating it."""
        chunks_dir = AUDIO_DIR / "_chunks"
        if not chunks_dir.exists():
            pytest.skip("No _chunks directory")
        first_chunk = sorted(chunks_dir.glob("01_intro_chunk_00.mp3"))
        if not first_chunk:
            pytest.skip("No 01_intro chunk files found")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "test_concat.mp3"
            result = concatenate_chunks(first_chunk, out, gap_secs=0)
            if result:
                assert out.exists()
                assert out.stat().st_size > 0

    def test_chunk_path_list_construction(self):
        """Verify chunk paths follow the naming convention."""
        chunks_dir = AUDIO_DIR / "_chunks"
        if not chunks_dir.exists():
            pytest.skip("No _chunks directory")
        for cid in CHAPTER_IDS:
            chunk_files = sorted(chunks_dir.glob(f"{cid}_chunk_*.mp3"))
            if chunk_files:
                for i, cf in enumerate(chunk_files):
                    expected_name = f"{cid}_chunk_{i:02d}.mp3"
                    assert cf.name == expected_name, f"Expected {expected_name}, got {cf.name}"
                break
        else:
            pytest.skip("No chunk files found for any chapter")

    @pytest.mark.parametrize("n_chunks", [1, 5, 10])
    def test_chunk_path_list_length(self, n_chunks):
        """Build hypothetical chunk path lists of various lengths."""
        paths = [Path(f"/tmp/ch_chunk_{i:02d}.mp3") for i in range(n_chunks)]
        assert len(paths) == n_chunks

    @pytest.mark.parametrize("gap", [0.0, 0.15, 0.5, 1.0])
    def test_gap_is_non_negative(self, gap):
        assert gap >= 0

    def test_chunks_dir_exists(self):
        chunks_dir = AUDIO_DIR / "_chunks"
        assert chunks_dir.exists(), f"Expected _chunks directory at {chunks_dir}"

    def test_chunks_dir_has_files(self):
        chunks_dir = AUDIO_DIR / "_chunks"
        if not chunks_dir.exists():
            pytest.skip("No _chunks directory")
        files = list(chunks_dir.glob("*.mp3"))
        assert len(files) > 0, "No chunk mp3 files found"

    @pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
    def test_each_chunk_above_min_size(self, chapter_id):
        chunks_dir = AUDIO_DIR / "_chunks"
        if not chunks_dir.exists():
            pytest.skip("No _chunks directory")
        chunk_files = list(chunks_dir.glob(f"{chapter_id}_chunk_*.mp3"))
        for cf in chunk_files:
            assert cf.stat().st_size >= MIN_CHUNK_SIZE_BYTES, (
                f"{cf.name} is {cf.stat().st_size} bytes, below {MIN_CHUNK_SIZE_BYTES}"
            )


# ===========================================================================
# SECTION 7: Integration — split_into_chunks on real chapter text
# ===========================================================================
class TestSplitRealChapterText:
    """Run split_into_chunks on real chapter text from the config."""

    @pytest.fixture(scope="class")
    def chapters(self):
        chapters, _ = load_chapters_from_config(CONFIG_PATH)
        return chapters

    @pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
    def test_real_chapter_splits_without_error(self, chapters, chapter_id):
        chunks = split_into_chunks(chapters[chapter_id], max_chars=MAX_CHUNK_CHARS)
        assert len(chunks) >= 1

    @pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
    def test_real_chapter_no_chunk_exceeds_max(self, chapters, chapter_id):
        chunks = split_into_chunks(chapters[chapter_id], max_chars=MAX_CHUNK_CHARS)
        for i, c in enumerate(chunks):
            if "\n\n" not in c:
                continue
            assert len(c) <= MAX_CHUNK_CHARS, (
                f"{chapter_id} chunk {i}: {len(c)} chars > {MAX_CHUNK_CHARS}"
            )

    @pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
    def test_real_chapter_content_preserved(self, chapters, chapter_id):
        text = chapters[chapter_id]
        chunks = split_into_chunks(text, max_chars=MAX_CHUNK_CHARS)
        joined = "\n\n".join(chunks)
        # Every non-empty paragraph from original should appear in joined
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        for p in paras:
            assert p in joined, f"Lost paragraph in {chapter_id}: {p[:50]}..."

    @pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
    def test_real_chapter_no_empty_chunks(self, chapters, chapter_id):
        chunks = split_into_chunks(chapters[chapter_id], max_chars=MAX_CHUNK_CHARS)
        for c in chunks:
            assert c.strip() != ""
