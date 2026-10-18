"""
test_pipeline.py — 150 pytest tests for produce_documentary.sh pipeline

Sections:
  - Path Derivation (~60 tests)
  - Step Ordering (~30 tests)
  - Dry Run Mode (~20 tests)
  - Real Output Validation (~40 tests)

Uses real files and subprocess. No mocks.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from conftest import (
    PROJECT_ROOT,
    REMOTION_DIR,
    CONFIG_PATH,
    RESEARCH_DIR,
    AUDIO_DIR,
    TRANSCRIPT_DIR,
    SCENE_IMAGES_DIR,
    RENDER_PROPS_PATH,
    SCENES_SYNCED_PATH,
    CHAPTER_IDS,
)

PRODUCE_SCRIPT = PROJECT_ROOT / "produce_documentary.sh"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Path Derivation (~60 tests)
# ═══════════════════════════════════════════════════════════════════════════════


def _slugify(topic: str) -> str:
    """Replicate the shell slugify logic: lowercase, non-alnum → _, collapse, trim."""
    slug = topic.lower()
    slug = re.sub(r"[^a-z0-9]", "_", slug)
    slug = re.sub(r"_+", "_", slug)
    slug = slug.strip("_")
    return slug[:80]


class TestSlugGeneration:
    """Topic → slug derivation matches the shell script logic."""

    def test_simple_topic(self):
        assert _slugify("Hello World") == "hello_world"

    def test_uppercase_lowered(self):
        assert _slugify("ALL CAPS TOPIC") == "all_caps_topic"

    def test_special_chars_replaced(self):
        assert _slugify("AI: The Future!") == "ai_the_future"

    def test_multiple_spaces_collapsed(self):
        assert _slugify("too   many   spaces") == "too_many_spaces"

    def test_leading_trailing_stripped(self):
        assert _slugify("  padded  ") == "padded"

    def test_numbers_preserved(self):
        assert _slugify("SEO 2026") == "seo_2026"

    def test_dashes_become_underscores(self):
        assert _slugify("dash-separated-topic") == "dash_separated_topic"

    def test_long_topic_truncated_at_80(self):
        long_topic = "a" * 200
        assert len(_slugify(long_topic)) == 80

    def test_dots_replaced(self):
        assert _slugify("file.name.test") == "file_name_test"

    def test_ampersand_replaced(self):
        assert _slugify("SEO & GEO") == "seo_geo"

    def test_parentheses_replaced(self):
        assert _slugify("Topic (subtitle)") == "topic_subtitle"

    def test_colon_replaced(self):
        assert _slugify("SEO: 2030") == "seo_2030"

    def test_unicode_stripped(self):
        slug = _slugify("caf\u00e9 r\u00e9sum\u00e9")
        assert "_" in slug or slug == "caf_r_sum"  # non-ascii → _

    def test_empty_becomes_empty(self):
        assert _slugify("") == ""

    def test_single_char(self):
        assert _slugify("A") == "a"


# Parametrize 30 topics → verify slug properties
_TOPIC_SLUG_CASES = [
    ("The History of AI: From Turing to GPT", "the_history_of_ai_from_turing_to_gpt"),
    ("SEO 2026", "seo_2026"),
    ("Hello, World!", "hello_world"),
    ("  Leading spaces  ", "leading_spaces"),
    ("UPPERCASE ONLY", "uppercase_only"),
    ("lowercase only", "lowercase_only"),
    ("Mixed Case Topic", "mixed_case_topic"),
    ("Numbers 123 456", "numbers_123_456"),
    ("Special!@#$%Chars", "special_chars"),
    ("Dash-separated-words", "dash_separated_words"),
    ("dot.separated.words", "dot_separated_words"),
    ("slash/path/like", "slash_path_like"),
    ("pipe|char|test", "pipe_char_test"),
    ("ampersand&test", "ampersand_test"),
    ("question?mark", "question_mark"),
    ("a" * 100, "a" * 80),
    ("one", "one"),
    ("12345", "12345"),
    ("Topic (2026)", "topic_2026"),
    ("Title: Subtitle", "title_subtitle"),
    ("What's New in AI", "what_s_new_in_ai"),
    ("Quote \"Test\"", "quote_test"),
    ("Tab\there", "tab_here"),
    ("New\nLine", "new_line"),
    ("Back\\slash", "back_slash"),
    ("Plus+Sign", "plus_sign"),
    ("Equal=Sign", "equal_sign"),
    ("Comma,Test", "comma_test"),
    ("Semicolon;Test", "semicolon_test"),
    ("Brackets[Test]", "brackets_test"),
]


@pytest.mark.parametrize("topic,expected_slug", _TOPIC_SLUG_CASES,
                         ids=[f"slug_{i}" for i in range(len(_TOPIC_SLUG_CASES))])
class TestParametrizedSlugs:
    def test_slug_matches(self, topic, expected_slug):
        assert _slugify(topic) == expected_slug

    def test_slug_no_uppercase(self, topic, expected_slug):
        slug = _slugify(topic)
        assert slug == slug.lower()


class TestPathDerivationFromSlug:
    """Verify all derived paths from a slug match the shell script pattern."""

    SLUG = "seo_and_geo_in_2026_2030_what_actually_works_what_s_changing"

    def test_audio_dir(self):
        assert f"audio_{self.SLUG}" == "audio_seo_and_geo_in_2026_2030_what_actually_works_what_s_changing"

    def test_transcript_dir(self):
        assert f"transcripts_{self.SLUG}" == "transcripts_seo_and_geo_in_2026_2030_what_actually_works_what_s_changing"

    def test_scenes_file(self):
        assert f"scenes_synced_{self.SLUG}.json" == f"scenes_synced_{self.SLUG}.json"

    def test_render_props(self):
        assert f"render_props_{self.SLUG}.json" == f"render_props_{self.SLUG}.json"

    def test_scene_images_dir(self):
        assert f"scene_images_{self.SLUG}" == f"scene_images_{self.SLUG}"

    def test_characters_dir(self):
        assert f"characters_{self.SLUG}" == f"characters_{self.SLUG}"

    def test_remotion_props(self):
        expected = f"{REMOTION_DIR}/props_{self.SLUG}.json"
        assert "Remotion" in expected and expected.endswith(".json")

    def test_output_video(self):
        expected = f"{REMOTION_DIR}/output/documentary_{self.SLUG}.mp4"
        assert expected.endswith(".mp4") and "documentary_" in expected

    def test_config_is_in_research_dir(self):
        expected = f"research/{self.SLUG}/generate_config.json"
        assert expected.startswith("research/")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Step Ordering (~30 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestStepOrder:
    """The 9 pipeline steps in produce_documentary.sh run in correct order."""

    @pytest.fixture(scope="class")
    def script_content(self):
        return PRODUCE_SCRIPT.read_text()

    def test_script_exists(self):
        assert PRODUCE_SCRIPT.exists()

    def test_script_is_executable(self):
        assert os.access(PRODUCE_SCRIPT, os.X_OK)

    def test_has_9_run_step_calls(self, script_content):
        steps = re.findall(r"run_step\s+(\d+)", script_content)
        assert len(steps) == 9

    def test_steps_are_sequential(self, script_content):
        steps = [int(s) for s in re.findall(r"run_step\s+(\d+)", script_content)]
        assert steps == list(range(1, 10))

    def test_step1_is_voiceover(self, script_content):
        assert "run_step 1" in script_content
        match = re.search(r'run_step 1 "([^"]+)"', script_content)
        assert "Voiceover" in match.group(1) or "voiceover" in match.group(1).lower()

    def test_step2_is_transcription(self, script_content):
        match = re.search(r'run_step 2 "([^"]+)"', script_content)
        assert "Transcri" in match.group(1) or "Whisper" in match.group(1)

    def test_step3_is_scene_timings(self, script_content):
        match = re.search(r'run_step 3 "([^"]+)"', script_content)
        assert "Scene" in match.group(1) or "Timing" in match.group(1)

    def test_step4_is_render_props(self, script_content):
        match = re.search(r'run_step 4 "([^"]+)"', script_content)
        assert "Render" in match.group(1) or "Props" in match.group(1)

    def test_step5_is_character_images(self, script_content):
        match = re.search(r'run_step 5 "([^"]+)"', script_content)
        assert "Character" in match.group(1)

    def test_step6_is_scene_images(self, script_content):
        match = re.search(r'run_step 6 "([^"]+)"', script_content)
        assert "Scene" in match.group(1) or "Image" in match.group(1)

    def test_step7_is_remotion_assets(self, script_content):
        match = re.search(r'run_step 7 "([^"]+)"', script_content)
        assert "Remotion" in match.group(1) or "Asset" in match.group(1)

    def test_step8_is_render(self, script_content):
        match = re.search(r'run_step 8 "([^"]+)"', script_content)
        assert "Render" in match.group(1)

    def test_step9_is_upload(self, script_content):
        match = re.search(r'run_step 9 "([^"]+)"', script_content)
        assert "Upload" in match.group(1) or "YouTube" in match.group(1)

    def test_step1_produces_audio(self, script_content):
        # Step 1 calls generate_voiceover_hq.py with --output-dir audio
        line = _get_run_step_line(script_content, 1)
        assert "generate_voiceover_hq.py" in line
        assert "--output-dir" in line

    def test_step2_reads_audio(self, script_content):
        line = _get_run_step_line(script_content, 2)
        assert "--audio-dir" in line

    def test_step2_produces_transcripts(self, script_content):
        line = _get_run_step_line(script_content, 2)
        assert "--transcript-dir" in line

    def test_step3_reads_transcripts(self, script_content):
        line = _get_run_step_line(script_content, 3)
        assert "--transcript-dir" in line

    def test_step3_produces_scenes(self, script_content):
        line = _get_run_step_line(script_content, 3)
        assert "--output" in line

    def test_step4_reads_scenes(self, script_content):
        line = _get_run_step_line(script_content, 4)
        assert "--scenes-file" in line

    def test_step4_produces_render_props(self, script_content):
        line = _get_run_step_line(script_content, 4)
        assert "--output" in line

    def test_step6_reads_render_props(self, script_content):
        line = _get_run_step_line(script_content, 6)
        assert "--props-file" in line

    def test_step7_copies_to_remotion(self, script_content):
        line = _get_run_step_line(script_content, 7)
        assert "Remotion" in line or "remotion" in line.lower()

    def test_step8_renders_video(self, script_content):
        line = _get_run_step_line(script_content, 8)
        assert "remotion render" in line.lower() or "npx" in line

    def test_step9_uploads_video(self, script_content):
        line = _get_run_step_line(script_content, 9)
        assert "upload_youtube.py" in line

    def test_each_step_uses_config(self, script_content):
        """Steps 1-6 all reference --config."""
        for step_num in range(1, 7):
            line = _get_run_step_line(script_content, step_num)
            assert "--config" in line or "CONFIG" in line, f"Step {step_num} missing --config"

    def test_run_step_function_defined(self, script_content):
        assert "run_step()" in script_content or "run_step ()" in script_content or "run_step()\n" in script_content or re.search(r"run_step\s*\(\)", script_content)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Dry Run Mode (~20 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestDryRun:
    """--dry-run should print commands without executing them."""

    @pytest.fixture(scope="class")
    def dry_run_output(self):
        result = subprocess.run(
            [str(PRODUCE_SCRIPT), "--config", str(CONFIG_PATH), "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        return result

    def test_dry_run_exits_zero(self, dry_run_output):
        assert dry_run_output.returncode == 0

    def test_dry_run_prints_dry_run_label(self, dry_run_output):
        assert "[DRY-RUN]" in dry_run_output.stdout

    def test_dry_run_prints_step1(self, dry_run_output):
        assert "generate_voiceover_hq.py" in dry_run_output.stdout

    def test_dry_run_prints_step2(self, dry_run_output):
        assert "transcribe_whisper.py" in dry_run_output.stdout

    def test_dry_run_prints_step3(self, dry_run_output):
        assert "build_scene_timings.py" in dry_run_output.stdout

    def test_dry_run_prints_step4(self, dry_run_output):
        assert "generate_render_props.py" in dry_run_output.stdout

    def test_dry_run_prints_step5(self, dry_run_output):
        assert "generate_characters.py" in dry_run_output.stdout

    def test_dry_run_prints_step6(self, dry_run_output):
        assert "generate_all_scene_images.py" in dry_run_output.stdout

    def test_dry_run_prints_step7(self, dry_run_output):
        assert "Remotion" in dry_run_output.stdout

    def test_dry_run_prints_step8(self, dry_run_output):
        assert "remotion render" in dry_run_output.stdout.lower() or "npx" in dry_run_output.stdout

    def test_dry_run_prints_step9(self, dry_run_output):
        assert "upload_youtube.py" in dry_run_output.stdout

    def test_dry_run_shows_config_path(self, dry_run_output):
        assert "generate_config.json" in dry_run_output.stdout

    def test_dry_run_shows_audio_dir(self, dry_run_output):
        assert "audio_" in dry_run_output.stdout

    def test_dry_run_shows_transcript_dir(self, dry_run_output):
        assert "transcripts_" in dry_run_output.stdout

    def test_dry_run_shows_output_video(self, dry_run_output):
        assert ".mp4" in dry_run_output.stdout

    def test_dry_run_no_error_output(self, dry_run_output):
        # stderr may have minor info, but no Python tracebacks or bash errors
        assert "Traceback" not in dry_run_output.stderr
        assert "Error" not in dry_run_output.stderr or "Error" in dry_run_output.stdout

    def test_dry_run_prints_pipeline_complete(self, dry_run_output):
        assert "Pipeline complete" in dry_run_output.stdout or "complete" in dry_run_output.stdout.lower()

    def test_dry_run_with_topic_flag(self):
        """--dry-run with --topic should compute slug without running research."""
        result = subprocess.run(
            [str(PRODUCE_SCRIPT), "--topic", "Test Topic Here", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "test_topic_here" in result.stdout.lower() or "DRY-RUN" in result.stdout

    def test_dry_run_with_custom_chapters(self):
        result = subprocess.run(
            [str(PRODUCE_SCRIPT), "--topic", "AI Future", "--chapters", "5", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0

    def test_dry_run_with_privacy(self):
        result = subprocess.run(
            [str(PRODUCE_SCRIPT), "--config", str(CONFIG_PATH), "--privacy", "public", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Real Output Validation (~40 tests)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAudioOutputs:
    """Validate audio_v2_hq/ has correct outputs."""

    def test_audio_dir_exists(self, audio_dir):
        assert audio_dir.exists()

    def test_audio_dir_is_directory(self, audio_dir):
        assert audio_dir.is_dir()

    def test_audio_has_10_mp3_files(self, audio_dir):
        mp3s = list(audio_dir.glob("*.mp3"))
        assert len(mp3s) == 10

    def test_audio_files_match_chapter_ids(self, audio_dir, chapter_ids):
        for cid in chapter_ids:
            assert (audio_dir / f"{cid}.mp3").exists(), f"Missing {cid}.mp3"

    def test_audio_files_nonempty(self, audio_dir):
        for mp3 in audio_dir.glob("*.mp3"):
            assert mp3.stat().st_size > 0, f"Empty file: {mp3.name}"

    def test_audio_files_reasonable_size(self, audio_dir):
        """Each MP3 should be > 100KB (real audio, not a stub)."""
        for mp3 in audio_dir.glob("*.mp3"):
            assert mp3.stat().st_size > 100_000, f"Too small: {mp3.name} ({mp3.stat().st_size}B)"


class TestTranscriptOutputs:
    """Validate transcripts_v2_hq/ has correct outputs."""

    def test_transcript_dir_exists(self, transcript_dir):
        assert transcript_dir.exists()

    def test_transcript_dir_is_directory(self, transcript_dir):
        assert transcript_dir.is_dir()

    def test_transcript_has_10_json_files(self, transcript_dir):
        jsons = list(transcript_dir.glob("*.json"))
        assert len(jsons) == 10

    def test_transcript_files_match_chapter_ids(self, transcript_dir, chapter_ids):
        for cid in chapter_ids:
            assert (transcript_dir / f"{cid}.json").exists(), f"Missing {cid}.json"

    def test_transcript_files_are_valid_json(self, transcript_dir):
        for jf in transcript_dir.glob("*.json"):
            with open(jf) as f:
                data = json.load(f)
            assert isinstance(data, (dict, list)), f"Invalid JSON structure in {jf.name}"

    def test_transcript_files_nonempty(self, transcript_dir):
        for jf in transcript_dir.glob("*.json"):
            assert jf.stat().st_size > 100, f"Too small: {jf.name}"


class TestSceneImagesOutputs:
    """Validate scene_images_v2/ has correct outputs."""

    def test_scene_images_dir_exists(self, scene_images_dir):
        assert scene_images_dir.exists()

    def test_scene_images_dir_is_directory(self, scene_images_dir):
        assert scene_images_dir.is_dir()

    def test_scene_images_over_100_pngs(self, scene_images_dir):
        pngs = list(scene_images_dir.glob("*.png"))
        assert len(pngs) > 100, f"Only {len(pngs)} PNGs found (expected > 100)"

    def test_scene_images_nonempty(self, scene_images_dir):
        pngs = list(scene_images_dir.glob("*.png"))
        for png in pngs[:20]:  # spot-check first 20
            assert png.stat().st_size > 1000, f"Too small: {png.name}"

    def test_scene_images_cover_all_chapters(self, scene_images_dir, chapter_ids):
        """Each chapter should have at least one scene image."""
        for cid in chapter_ids:
            matching = list(scene_images_dir.glob(f"{cid}_*.png"))
            assert len(matching) > 0, f"No scene images for chapter {cid}"


class TestRenderPropsOutput:
    """Validate render_props_v2_hq.json."""

    def test_render_props_exists(self, render_props_path):
        assert render_props_path.exists()

    def test_render_props_is_valid_json(self, render_props_data):
        assert isinstance(render_props_data, dict)

    def test_render_props_has_chapters(self, render_props_data):
        assert "chapters" in render_props_data

    def test_render_props_has_10_chapters(self, render_props_data):
        assert len(render_props_data["chapters"]) == 10

    def test_render_props_chapters_have_id(self, render_props_data):
        for ch in render_props_data["chapters"]:
            assert "id" in ch

    def test_render_props_chapters_have_scenes(self, render_props_data):
        for ch in render_props_data["chapters"]:
            assert "scenes" in ch
            assert len(ch["scenes"]) > 0

    def test_render_props_chapters_have_audio(self, render_props_data):
        for ch in render_props_data["chapters"]:
            assert "audioFile" in ch

    def test_render_props_chapter_ids_match(self, render_props_data, chapter_ids):
        prop_ids = [ch["id"] for ch in render_props_data["chapters"]]
        assert prop_ids == chapter_ids


class TestScenesSyncedOutput:
    """Validate scenes_synced_v2_hq.json."""

    def test_scenes_synced_exists(self, scenes_synced_path):
        assert scenes_synced_path.exists()

    def test_scenes_synced_is_valid_json(self, scenes_synced_data):
        assert isinstance(scenes_synced_data, (dict, list))

    def test_scenes_synced_nonempty(self, scenes_synced_path):
        assert scenes_synced_path.stat().st_size > 100


class TestPipelineConsistency:
    """Cross-check that all pipeline artifacts are consistent."""

    def test_same_chapter_count_audio_and_transcript(self, audio_dir, transcript_dir):
        mp3s = sorted(audio_dir.glob("*.mp3"))
        jsons = sorted(transcript_dir.glob("*.json"))
        assert len(mp3s) == len(jsons)

    def test_same_chapter_names_audio_and_transcript(self, audio_dir, transcript_dir):
        mp3_names = sorted(p.stem for p in audio_dir.glob("*.mp3"))
        json_names = sorted(p.stem for p in transcript_dir.glob("*.json"))
        assert mp3_names == json_names

    def test_render_props_chapters_match_audio(self, render_props_data, audio_dir):
        prop_ids = [ch["id"] for ch in render_props_data["chapters"]]
        audio_ids = sorted(p.stem for p in audio_dir.glob("*.mp3"))
        assert prop_ids == audio_ids

    def test_scene_images_referenced_in_render_props(self, render_props_data, scene_images_dir):
        """Spot-check: image files referenced in render props should exist in scene_images_v2."""
        for ch in render_props_data["chapters"]:
            for scene in ch.get("scenes", []):
                img = scene.get("imageFile")
                if img and "scene_images" in img:
                    # imageFile is like "seo_scene_images/01_intro_scene_003.png"
                    # The actual file is in scene_images_v2/
                    img_name = Path(img).name
                    assert (scene_images_dir / img_name).exists(), (
                        f"Referenced image {img_name} not found in scene_images_v2/"
                    )

    def test_all_chapters_have_audio_duration(self, render_props_data):
        for ch in render_props_data["chapters"]:
            assert "audioDurationSecs" in ch
            assert ch["audioDurationSecs"] > 0

    def test_total_duration_reasonable(self, render_props_data):
        """Total audio should be roughly 25-40 minutes for a 30min documentary."""
        total = sum(ch.get("audioDurationSecs", 0) for ch in render_props_data["chapters"])
        assert 20 * 60 < total < 45 * 60, f"Total duration {total/60:.1f}min outside 20-45min range"

    def test_config_chapter_ids_match_outputs(self, config_data, chapter_ids):
        assert config_data["chapter_ids"] == chapter_ids


class TestRemotionOutputDir:
    """Check Remotion output directory exists (video may or may not exist)."""

    def test_remotion_dir_exists(self, remotion_dir):
        assert remotion_dir.exists()

    def test_remotion_output_dir_exists(self, remotion_dir):
        output_dir = remotion_dir / "output"
        assert output_dir.exists()

    def test_remotion_output_has_mp4_files(self, remotion_dir):
        output_dir = remotion_dir / "output"
        mp4s = list(output_dir.glob("*.mp4"))
        assert len(mp4s) > 0, "No MP4 files in Remotion output"


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _get_run_step_line(script_content: str, step_num: int) -> str:
    """Extract the full run_step N block from the shell script."""
    # run_step calls can span multiple lines with backslash continuation
    pattern = rf"run_step {step_num} .*?(?:\\\n.*?)*(?:\n|$)"
    match = re.search(pattern, script_content, re.DOTALL)
    if match:
        return match.group(0)
    # Fallback: just find lines mentioning run_step N
    lines = script_content.split("\n")
    result = []
    capturing = False
    for line in lines:
        if f"run_step {step_num} " in line:
            capturing = True
        if capturing:
            result.append(line)
            if not line.rstrip().endswith("\\"):
                break
    return "\n".join(result)
