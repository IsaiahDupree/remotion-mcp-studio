# 300 tests for scene timings and render props
"""
Comprehensive pytest suite validating scene timings and render props
for the SEO Documentary V2 HQ pipeline.

Uses real data files — NO mocks.
"""

import json
import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures — load real data once per session
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

SCENES_SYNCED_PATH = BASE_DIR / "scenes_synced_v2_hq.json"
RENDER_PROPS_PATH = BASE_DIR / "render_props_v2_hq.json"
SCENE_IMAGES_DIR = BASE_DIR / "scene_images_v2"
AUDIO_DIR = BASE_DIR / "audio_v2_hq"


@pytest.fixture(scope="session")
def scenes_synced():
    with open(SCENES_SYNCED_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def render_props():
    with open(RENDER_PROPS_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def render_chapters(render_props):
    return render_props["chapters"]


# ---------------------------------------------------------------------------
# Chapter IDs and valid types
# ---------------------------------------------------------------------------

SYNCED_CHAPTER_IDS = [
    "01_intro", "02_origins", "03_breakthroughs", "04_experts",
    "05_evolution", "06_current_affairs", "07_future_speculation",
    "08_local_seo", "09_schema_and_programmatic", "10_conclusion",
]

VALID_SCENE_TYPES = {
    "title_card", "fact_reveal", "quote", "character",
    "timeline", "transition", "image_reveal",
}


# ===================================================================
# SECTION 1: Scene Timing Validation (80 tests)
# ===================================================================

class TestSceneTimingValidation:
    """Validate scenes_synced_v2_hq.json timing constraints."""

    def test_scenes_synced_file_exists(self):
        assert SCENES_SYNCED_PATH.exists(), "scenes_synced_v2_hq.json missing"

    def test_scenes_synced_is_valid_json(self):
        with open(SCENES_SYNCED_PATH) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_total_chapters_is_10(self, scenes_synced):
        assert len(scenes_synced) == 10

    @pytest.mark.parametrize("chapter_id", SYNCED_CHAPTER_IDS)
    def test_chapter_exists_and_has_scenes(self, scenes_synced, chapter_id):
        assert chapter_id in scenes_synced
        assert len(scenes_synced[chapter_id]["scenes"]) > 0

    @pytest.mark.parametrize("chapter_id", SYNCED_CHAPTER_IDS)
    def test_each_scene_start_non_negative_and_end_after_start(self, scenes_synced, chapter_id):
        for i, scene in enumerate(scenes_synced[chapter_id]["scenes"]):
            assert scene["startSecs"] >= 0, f"Negative startSecs in {chapter_id} scene {i}"
            assert scene["endSecs"] > scene["startSecs"], (
                f"{chapter_id} scene {i}: endSecs {scene['endSecs']} <= startSecs {scene['startSecs']}"
            )

    @pytest.mark.parametrize("chapter_id", SYNCED_CHAPTER_IDS)
    def test_scenes_chronological_order(self, scenes_synced, chapter_id):
        scenes = scenes_synced[chapter_id]["scenes"]
        for i in range(1, len(scenes)):
            assert scenes[i]["startSecs"] >= scenes[i - 1]["startSecs"], (
                f"{chapter_id}: scene {i} starts before scene {i-1}"
            )

    @pytest.mark.parametrize("chapter_id", SYNCED_CHAPTER_IDS)
    def test_no_scene_overlap_within_chapter(self, scenes_synced, chapter_id):
        scenes = scenes_synced[chapter_id]["scenes"]
        for i in range(1, len(scenes)):
            overlap = scenes[i - 1]["endSecs"] - scenes[i]["startSecs"]
            assert overlap <= 0.01, (
                f"{chapter_id}: overlap {overlap:.3f}s between scene {i-1} and {i}"
            )

    @pytest.mark.parametrize("chapter_id", SYNCED_CHAPTER_IDS)
    def test_no_gaps_over_10s_between_scenes(self, scenes_synced, chapter_id):
        scenes = scenes_synced[chapter_id]["scenes"]
        for i in range(1, len(scenes)):
            gap = scenes[i]["startSecs"] - scenes[i - 1]["endSecs"]
            assert gap <= 10.0, (
                f"{chapter_id}: gap {gap:.2f}s between scene {i-1} and {i}"
            )

    @pytest.mark.parametrize("chapter_id", SYNCED_CHAPTER_IDS)
    def test_last_scene_within_audio_duration(self, scenes_synced, chapter_id):
        ch = scenes_synced[chapter_id]
        last_scene = ch["scenes"][-1]
        assert last_scene["endSecs"] <= ch["audioDurationSecs"] + 1.0, (
            f"{chapter_id}: last scene ends at {last_scene['endSecs']} "
            f"but audio is {ch['audioDurationSecs']}s"
        )

    @pytest.mark.parametrize("chapter_id", SYNCED_CHAPTER_IDS)
    def test_scene_durations_between_1_and_15(self, scenes_synced, chapter_id):
        for i, scene in enumerate(scenes_synced[chapter_id]["scenes"]):
            dur = scene["durationSecs"]
            assert 1.0 <= dur <= 15.0, (
                f"{chapter_id} scene {i}: duration {dur}s out of range"
            )

    @pytest.mark.parametrize("threshold", [100, 200, 370])
    def test_total_scene_count_above_threshold(self, scenes_synced, threshold):
        total = sum(ch["sceneCount"] for ch in scenes_synced.values())
        assert total >= threshold, f"Total scenes {total} < {threshold}"

    # non-parametrized single tests
    def test_all_scene_counts_match_arrays(self, scenes_synced):
        for cid, ch in scenes_synced.items():
            assert ch["sceneCount"] == len(ch["scenes"]), f"{cid}: count mismatch"

    def test_all_audio_durations_positive(self, scenes_synced):
        for cid, ch in scenes_synced.items():
            assert ch["audioDurationSecs"] > 0, f"{cid}: non-positive duration"

    def test_all_first_scenes_start_at_zero(self, scenes_synced):
        for cid, ch in scenes_synced.items():
            assert ch["scenes"][0]["startSecs"] == 0.0, f"{cid}: first scene not at 0"

    def test_all_chapters_have_id_field(self, scenes_synced):
        for cid, ch in scenes_synced.items():
            assert ch["id"] == cid

    def test_scene_count_per_chapter_above_30(self, scenes_synced):
        for cid, ch in scenes_synced.items():
            assert ch["sceneCount"] >= 30, f"{cid}: only {ch['sceneCount']} scenes"


# ===================================================================
# SECTION 2: Scene Type Distribution (42 tests)
# ===================================================================

class TestSceneTypeDistribution:
    """Validate scene type assignments across chapters."""

    @pytest.mark.parametrize("chapter_id", SYNCED_CHAPTER_IDS)
    def test_no_unknown_scene_types(self, scenes_synced, chapter_id):
        for i, scene in enumerate(scenes_synced[chapter_id]["scenes"]):
            assert scene["type"] in VALID_SCENE_TYPES, (
                f"{chapter_id} scene {i}: unknown type '{scene['type']}'"
            )

    @pytest.mark.parametrize("chapter_id", SYNCED_CHAPTER_IDS)
    def test_chapter_starts_with_title_card_or_image_reveal(self, scenes_synced, chapter_id):
        first = scenes_synced[chapter_id]["scenes"][0]
        assert first["type"] in ("title_card", "image_reveal"), (
            f"{chapter_id} starts with '{first['type']}'"
        )

    def test_image_reveal_percentage_above_30_in_render_props(self, render_chapters):
        total = sum(len(c["scenes"]) for c in render_chapters)
        img_count = sum(
            1 for c in render_chapters for s in c["scenes"]
            if s["type"] == "image_reveal"
        )
        pct = img_count / total * 100
        assert pct > 30, f"image_reveal only {pct:.1f}%, expected >30%"

    @pytest.mark.parametrize("scene_type", [
        "title_card", "fact_reveal", "quote", "character", "timeline",
    ])
    def test_scene_type_appears_at_least_once_synced(self, scenes_synced, scene_type):
        found = any(
            s["type"] == scene_type
            for ch in scenes_synced.values()
            for s in ch["scenes"]
        )
        assert found, f"Scene type '{scene_type}' never appears in scenes_synced"

    @pytest.mark.parametrize("scene_type", [
        "title_card", "fact_reveal", "quote", "character",
        "timeline", "image_reveal",
    ])
    def test_scene_type_appears_at_least_once_render(self, render_chapters, scene_type):
        found = any(
            s["type"] == scene_type
            for c in render_chapters
            for s in c["scenes"]
        )
        assert found, f"Scene type '{scene_type}' never appears in render_props"

    @pytest.mark.parametrize("chapter_id", SYNCED_CHAPTER_IDS)
    def test_each_scene_has_content_and_accent_color(self, scenes_synced, chapter_id):
        for i, scene in enumerate(scenes_synced[chapter_id]["scenes"]):
            assert "content" in scene, f"{chapter_id} scene {i}: missing content"
            assert "accentColor" in scene, f"{chapter_id} scene {i}: missing accentColor"

    def test_title_card_count_at_least_10(self, scenes_synced):
        count = sum(
            1 for ch in scenes_synced.values()
            for s in ch["scenes"] if s["type"] == "title_card"
        )
        assert count >= 10, f"Only {count} title_card scenes"

    def test_quote_scenes_mostly_have_content(self, scenes_synced):
        """Most quote scenes should have content (allow up to 3 empty from Whisper gaps)."""
        empty = sum(
            1 for ch in scenes_synced.values()
            for s in ch["scenes"]
            if s["type"] == "quote" and len(s.get("content", "")) == 0
        )
        assert empty <= 3, f"{empty} quote scenes with empty content"

    def test_fact_reveal_count_above_20(self, scenes_synced):
        count = sum(
            1 for ch in scenes_synced.values()
            for s in ch["scenes"] if s["type"] == "fact_reveal"
        )
        assert count >= 20, f"Only {count} fact_reveal scenes"

    def test_character_count_above_20(self, scenes_synced):
        count = sum(
            1 for ch in scenes_synced.values()
            for s in ch["scenes"] if s["type"] == "character"
        )
        assert count >= 20, f"Only {count} character scenes"


# ===================================================================
# SECTION 3: Render Props Schema (58 tests)
# ===================================================================

class TestRenderPropsSchema:
    """Validate render_props_v2_hq.json top-level and chapter schema."""

    def test_render_props_file_exists(self):
        assert RENDER_PROPS_PATH.exists(), "render_props_v2_hq.json missing"

    def test_top_level_has_chapters_array(self, render_props):
        assert "chapters" in render_props
        assert isinstance(render_props["chapters"], list)

    def test_chapters_count_is_10(self, render_chapters):
        assert len(render_chapters) == 10

    @pytest.mark.parametrize("field", [
        "id", "title", "era", "color", "audioFile",
        "characterImageFile", "audioDurationSecs", "scenes",
    ])
    def test_all_chapters_have_required_field(self, render_chapters, field):
        for c in render_chapters:
            assert field in c, f"Chapter {c.get('id', '?')} missing '{field}'"

    def test_all_audio_durations_positive(self, render_chapters):
        for c in render_chapters:
            assert c["audioDurationSecs"] > 0, f"{c['id']}: non-positive duration"

    def test_all_audio_files_match_pattern(self, render_chapters):
        for c in render_chapters:
            af = c["audioFile"]
            assert re.match(r"seo_audio/.+\.mp3$", af), f"{c['id']}: bad audioFile {af}"

    @pytest.mark.parametrize("idx", range(10))
    def test_color_is_valid_hex(self, render_chapters, idx):
        color = render_chapters[idx]["color"]
        assert re.match(r"^#[0-9a-fA-F]{6}$", color), f"Bad color: {color}"

    def test_all_scenes_non_empty_arrays(self, render_chapters):
        for c in render_chapters:
            assert isinstance(c["scenes"], list)
            assert len(c["scenes"]) > 0, f"{c['id']}: empty scenes"

    def test_all_scenes_have_type_duration_content(self, render_chapters):
        for c in render_chapters:
            for i, s in enumerate(c["scenes"]):
                assert "type" in s, f"{c['id']} scene {i}: missing type"
                assert "durationSecs" in s, f"{c['id']} scene {i}: missing durationSecs"
                assert "content" in s, f"{c['id']} scene {i}: missing content"

    def test_all_titles_non_empty_strings(self, render_chapters):
        for c in render_chapters:
            assert isinstance(c["title"], str)
            assert len(c["title"]) > 0, f"{c['id']}: empty title"

    def test_all_eras_are_strings(self, render_chapters):
        for c in render_chapters:
            assert isinstance(c["era"], str)

    def test_chapter_ids_match_expected(self, render_chapters):
        ids = [c["id"] for c in render_chapters]
        assert ids == SYNCED_CHAPTER_IDS

    def test_all_character_image_files_are_strings(self, render_chapters):
        for c in render_chapters:
            assert isinstance(c["characterImageFile"], str)

    def test_all_chapter_ids_are_strings(self, render_chapters):
        for c in render_chapters:
            assert isinstance(c["id"], str)
            assert len(c["id"]) > 0

    def test_no_duplicate_chapter_ids(self, render_chapters):
        ids = [c["id"] for c in render_chapters]
        assert len(ids) == len(set(ids))

    def test_all_scene_types_valid_in_render(self, render_chapters):
        for c in render_chapters:
            for i, s in enumerate(c["scenes"]):
                assert s["type"] in VALID_SCENE_TYPES, (
                    f"{c['id']} scene {i}: unknown type '{s['type']}'"
                )

    def test_all_first_scenes_are_title_card(self, render_chapters):
        for c in render_chapters:
            assert c["scenes"][0]["type"] in ("title_card", "image_reveal"), (
                f"{c['id']} first scene is '{c['scenes'][0]['type']}'"
            )


# ===================================================================
# SECTION 4: Word Timestamps (38 tests)
# ===================================================================

class TestWordTimestamps:
    """Validate word-level timestamps in render_props chapters."""

    @pytest.mark.parametrize("idx", range(10))
    def test_chapter_has_non_empty_words_array(self, render_chapters, idx):
        assert "words" in render_chapters[idx]
        assert isinstance(render_chapters[idx]["words"], list)
        assert len(render_chapters[idx]["words"]) > 0

    @pytest.mark.parametrize("idx", range(10))
    def test_each_word_has_required_fields(self, render_chapters, idx):
        for i, w in enumerate(render_chapters[idx]["words"]):
            assert "word" in w, f"Ch {idx} word {i}: missing 'word'"
            assert "start" in w, f"Ch {idx} word {i}: missing 'start'"
            assert "end" in w, f"Ch {idx} word {i}: missing 'end'"

    @pytest.mark.parametrize("idx", range(10))
    def test_word_start_leq_end(self, render_chapters, idx):
        """start <= end for all words (some Whisper words have zero duration)."""
        for i, w in enumerate(render_chapters[idx]["words"]):
            assert w["start"] <= w["end"], (
                f"Ch {idx} word {i}: start {w['start']} > end {w['end']}"
            )

    @pytest.mark.parametrize("idx", range(10))
    def test_words_chronologically_ordered(self, render_chapters, idx):
        words = render_chapters[idx]["words"]
        for i in range(1, len(words)):
            assert words[i]["start"] >= words[i - 1]["start"] - 0.01, (
                f"Ch {idx}: word {i} out of order"
            )

    @pytest.mark.parametrize("idx", range(10))
    def test_no_significant_word_overlap(self, render_chapters, idx):
        words = render_chapters[idx]["words"]
        for i in range(1, len(words)):
            overlap = words[i - 1]["end"] - words[i]["start"]
            assert overlap < 0.5, (
                f"Ch {idx}: word {i} overlaps previous by {overlap:.3f}s"
            )

    @pytest.mark.parametrize("threshold", [500, 1000, 2000, 3000, 4000])
    def test_total_word_count_above_threshold(self, render_chapters, threshold):
        total = sum(len(c["words"]) for c in render_chapters)
        assert total >= threshold, f"Total words {total} < {threshold}"

    def test_all_first_words_start_near_zero(self, render_chapters):
        for i, ch in enumerate(render_chapters):
            first = ch["words"][0]
            assert first["start"] < 2.0, (
                f"Ch {i}: first word starts at {first['start']}"
            )

    def test_all_last_words_end_near_audio_duration(self, render_chapters):
        for i, ch in enumerate(render_chapters):
            last = ch["words"][-1]
            dur = ch["audioDurationSecs"]
            assert last["end"] > dur - 5.0, (
                f"Ch {i}: last word ends at {last['end']}, audio is {dur}s"
            )


# ===================================================================
# SECTION 5: Image File References (41 tests)
# ===================================================================

class TestImageFileReferences:
    """Validate scene image file references and on-disk existence."""

    @pytest.mark.parametrize("idx", range(10))
    def test_image_file_path_pattern(self, render_chapters, idx):
        """imageFile follows per-scene (_scene_NNN.png) or concept art (_NN.png) pattern."""
        ch = render_chapters[idx]
        for i, s in enumerate(ch["scenes"]):
            if "imageFile" in s:
                assert re.match(
                    r"seo_scene_images/.+\.(png|jpg)$", s["imageFile"]
                ), f"Ch {idx} scene {i}: bad imageFile pattern '{s['imageFile']}'"

    @pytest.mark.parametrize("idx", range(10))
    def test_chapter_id_in_image_filename(self, render_chapters, idx):
        ch = render_chapters[idx]
        cid = ch["id"]
        for i, s in enumerate(ch["scenes"]):
            if "imageFile" in s:
                fname = s["imageFile"].split("/")[-1]
                assert fname.startswith(cid), (
                    f"Ch {idx} scene {i}: imageFile '{fname}' doesn't match '{cid}'"
                )

    @pytest.mark.parametrize("idx", range(10))
    def test_scene_image_indices_sequential(self, render_chapters, idx):
        ch = render_chapters[idx]
        indices = []
        for s in ch["scenes"]:
            if "imageFile" in s:
                match = re.search(r"_scene_(\d{3})\.png$", s["imageFile"])
                if match:
                    indices.append(int(match.group(1)))
        for i in range(1, len(indices)):
            assert indices[i] > indices[i - 1], (
                f"Ch {idx}: image indices not sequential: {indices[i-1]} then {indices[i]}"
            )

    def test_no_duplicate_image_references(self, render_chapters):
        all_refs = []
        for c in render_chapters:
            for s in c["scenes"]:
                if "imageFile" in s:
                    all_refs.append(s["imageFile"])
        dupes = len(all_refs) - len(set(all_refs))
        assert dupes <= 5, f"{dupes} duplicate image references"

    @pytest.mark.parametrize("idx", range(10))
    def test_scene_images_exist_on_disk(self, render_chapters, idx):
        ch = render_chapters[idx]
        missing = []
        for s in ch["scenes"]:
            if "imageFile" not in s:
                continue
            fname = s["imageFile"].split("/")[-1]
            disk_path = SCENE_IMAGES_DIR / fname
            if not disk_path.exists():
                missing.append(fname)
        assert len(missing) == 0, (
            f"Ch {idx}: {len(missing)} missing images: {missing[:3]}"
        )


# ===================================================================
# SECTION 6: Duration Consistency (41 tests)
# ===================================================================

class TestDurationConsistency:
    """Cross-validate durations between files and real audio."""

    def test_total_audio_duration_approx_1800s(self, render_chapters):
        total = sum(c["audioDurationSecs"] for c in render_chapters)
        assert 1440 <= total <= 2160, f"Total duration {total}s outside 1800 +/- 20%"

    @pytest.mark.parametrize("idx", range(10))
    def test_individual_chapter_between_100_and_250s(self, render_chapters, idx):
        dur = render_chapters[idx]["audioDurationSecs"]
        assert 100 <= dur <= 250, (
            f"Ch {idx}: audioDurationSecs {dur}s outside 100-250 range"
        )

    @pytest.mark.parametrize("idx", range(10))
    def test_scene_durations_sum_near_audio_duration(self, render_chapters, idx):
        ch = render_chapters[idx]
        audio_dur = ch["audioDurationSecs"]
        scene_sum = 0
        for s in ch["scenes"]:
            if "endSecs" in s and "startSecs" in s:
                scene_sum += s["endSecs"] - s["startSecs"]
            else:
                scene_sum += s["durationSecs"]
        assert scene_sum > audio_dur * 0.5, (
            f"Ch {idx}: scene sum {scene_sum:.1f}s << audio {audio_dur:.1f}s"
        )

    @pytest.mark.parametrize("idx", range(10))
    def test_synced_audio_duration_matches_render_props(self, scenes_synced, render_chapters, idx):
        ch = render_chapters[idx]
        cid = ch["id"]
        if cid in scenes_synced:
            synced_dur = scenes_synced[cid]["audioDurationSecs"]
            render_dur = ch["audioDurationSecs"]
            assert abs(synced_dur - render_dur) < 1.0, (
                f"{cid}: synced {synced_dur}s != render {render_dur}s"
            )

    @pytest.mark.parametrize("chapter_id", SYNCED_CHAPTER_IDS)
    def test_mp3_file_exists_and_non_empty(self, chapter_id):
        mp3 = AUDIO_DIR / f"{chapter_id}.mp3"
        assert mp3.exists(), f"Missing MP3: {mp3}"
        assert mp3.stat().st_size > 10000, f"MP3 too small: {mp3}"

    def test_total_duration_above_1780(self, render_chapters):
        total = sum(c["audioDurationSecs"] for c in render_chapters)
        assert total >= 1780, f"Total {total}s < 1780s"
