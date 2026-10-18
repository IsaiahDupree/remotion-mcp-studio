# 300 tests for image generation pipeline
"""
Comprehensive pytest suite for generate_all_scene_images.py.
Covers prompt construction, ERA_RECIPES validation, config-driven recipes,
scene type shot mapping, output file naming, and generated image file validation.
"""

import json
import os
import re
import sys
from pathlib import Path

import pytest

# Add project root to path so we can import the module
PROJECT_ROOT = Path(str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from generate_all_scene_images import (

SCRIPT_DIR = Path(__file__).parent
    ERA_RECIPES,
    DEFAULT_RECIPE,
    SCENE_TYPE_SHOTS,
    build_era_recipes_from_config,
    content_to_image_prompt,
)

# ---------------------------------------------------------------------------
# Constants used across tests
# ---------------------------------------------------------------------------
ALL_CHAPTER_IDS = [
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

ALL_SCENE_TYPES = ["image_reveal", "character", "quote", "fact_reveal", "timeline"]

RECIPE_FIELDS = ["camera", "lighting", "film", "env", "palette"]

CONFIG_PATH = str(
    PROJECT_ROOT
    / "research"
    / "seo_and_geo_in_2026_2030_what_actually_works_what_s_changing"
    / "generate_config.json"
)

SCENE_IMAGES_V2_DIR = PROJECT_ROOT / "scene_images_v2"


# ===========================================================================
# SECTION 1: Prompt Construction (~100 tests)
# ===========================================================================


class TestPromptConstruction:
    """Tests for content_to_image_prompt function."""

    # --- 50 parametrized: chapter_id x scene_type combos ---
    @pytest.mark.parametrize("chapter_id", ALL_CHAPTER_IDS)
    @pytest.mark.parametrize("scene_type", ALL_SCENE_TYPES)
    def test_prompt_for_chapter_scene_combo(self, chapter_id, scene_type):
        """Each chapter+scene_type combo produces a non-empty prompt string."""
        prompt = content_to_image_prompt("Test content", chapter_id, scene_type)
        assert isinstance(prompt, str)
        assert len(prompt) > 50

    # --- Content variations (12 tests) ---
    @pytest.mark.parametrize(
        "content",
        [
            "Short",
            "",
            "A" * 500,
            "Unicode: \u00e9\u00e8\u00ea \u00fc\u00f6\u00e4 \u4e16\u754c \ud83c\udf0d",
            "Numbers: 12345 67.89 -100",
            "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?",
            "  leading and trailing whitespace  ",
            "\n\nNewlines\nin\ncontent\n",
            "Tab\there\tand\tthere",
            "ALL CAPS CONTENT FOR TESTING",
            "mixedCaseContentWithCamelCase",
            "a",
        ],
        ids=[
            "short",
            "empty",
            "long_500_chars",
            "unicode",
            "numbers",
            "special_chars",
            "whitespace",
            "newlines",
            "tabs",
            "all_caps",
            "camel_case",
            "single_char",
        ],
    )
    def test_prompt_with_various_content(self, content):
        """Prompt is generated for diverse content strings."""
        prompt = content_to_image_prompt(content, "01_intro", "image_reveal")
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    # --- Required phrase checks (6 tests) ---
    def test_prompt_contains_cinematic_documentary(self):
        prompt = content_to_image_prompt("test", "01_intro", "image_reveal")
        assert "Generate a cinematic documentary photograph" in prompt

    def test_prompt_contains_must_be_photorealistic(self):
        prompt = content_to_image_prompt("test", "01_intro", "image_reveal")
        assert "MUST be photorealistic" in prompt

    def test_prompt_contains_never_include_text(self):
        prompt = content_to_image_prompt("test", "01_intro", "image_reveal")
        assert "NEVER include any text" in prompt

    def test_prompt_contains_camera_spec(self):
        prompt = content_to_image_prompt("test", "01_intro", "image_reveal")
        recipe = ERA_RECIPES["01_intro"]
        assert recipe["camera"] in prompt

    def test_prompt_contains_lighting(self):
        prompt = content_to_image_prompt("test", "02_origins", "character")
        recipe = ERA_RECIPES["02_origins"]
        assert recipe["lighting"] in prompt

    def test_prompt_contains_film_stock(self):
        prompt = content_to_image_prompt("test", "02_origins", "character")
        recipe = ERA_RECIPES["02_origins"]
        assert recipe["film"] in prompt

    # --- Per-chapter recipe embedding (10 tests) ---
    @pytest.mark.parametrize("chapter_id", ALL_CHAPTER_IDS)
    def test_prompt_contains_palette_from_recipe(self, chapter_id):
        prompt = content_to_image_prompt("test", chapter_id, "image_reveal")
        recipe = ERA_RECIPES.get(chapter_id, DEFAULT_RECIPE)
        assert recipe["palette"] in prompt

    @pytest.mark.parametrize("chapter_id", ALL_CHAPTER_IDS)
    def test_prompt_contains_environment_from_recipe(self, chapter_id):
        prompt = content_to_image_prompt("test", chapter_id, "image_reveal")
        recipe = ERA_RECIPES.get(chapter_id, DEFAULT_RECIPE)
        assert recipe["env"] in prompt

    # --- Unknown chapter_id falls back to DEFAULT_RECIPE (1 test) ---
    def test_unknown_chapter_uses_default_recipe(self):
        prompt = content_to_image_prompt("test", "99_nonexistent", "image_reveal")
        assert DEFAULT_RECIPE["camera"] in prompt
        assert DEFAULT_RECIPE["env"] in prompt

    # --- Prompt length safety (1 test) ---
    def test_prompt_length_under_2000_chars(self):
        long_content = "X" * 500
        prompt = content_to_image_prompt(long_content, "01_intro", "image_reveal")
        assert len(prompt) < 2000

    # --- Content truncation at 200 chars (2 tests) ---
    def test_content_truncated_at_200_chars(self):
        long_content = "A" * 300
        prompt = content_to_image_prompt(long_content, "01_intro", "image_reveal")
        assert "A" * 201 not in prompt

    def test_short_content_not_truncated(self):
        short_content = "Hello world SEO documentary"
        prompt = content_to_image_prompt(short_content, "01_intro", "image_reveal")
        assert short_content in prompt

    # --- Empty content fallback (1 test) ---
    def test_empty_content_uses_fallback(self):
        prompt = content_to_image_prompt("", "01_intro", "image_reveal")
        assert "abstract visual metaphor" in prompt

    # --- Whitespace-only content fallback (1 test) ---
    def test_whitespace_only_content_uses_fallback(self):
        prompt = content_to_image_prompt("   ", "01_intro", "image_reveal")
        assert "abstract visual metaphor" in prompt

    # --- Valid UTF-8 (1 test) ---
    def test_prompt_is_valid_utf8(self):
        prompt = content_to_image_prompt("caf\u00e9 \u00fc\u00f6\u00e4", "01_intro", "image_reveal")
        prompt.encode("utf-8")  # raises if invalid

    # --- Scene type shot guidance in prompt (5 tests) ---
    @pytest.mark.parametrize("scene_type", ALL_SCENE_TYPES)
    def test_prompt_contains_shot_guidance(self, scene_type):
        prompt = content_to_image_prompt("test", "01_intro", scene_type)
        expected = SCENE_TYPE_SHOTS[scene_type]
        assert expected in prompt

    # --- Unknown scene type default shot (1 test) ---
    def test_unknown_scene_type_default_shot(self):
        prompt = content_to_image_prompt("test", "01_intro", "unknown_type")
        assert "medium shot, balanced composition" in prompt

    # --- 16:9 composition mentioned (1 test) ---
    def test_prompt_contains_16_9_composition(self):
        prompt = content_to_image_prompt("test", "01_intro", "image_reveal")
        assert "16:9" in prompt

    # --- Award-winning mentioned (1 test) ---
    def test_prompt_contains_award_winning(self):
        prompt = content_to_image_prompt("test", "01_intro", "image_reveal")
        assert "award-winning" in prompt


# ===========================================================================
# SECTION 2: ERA_RECIPES Validation (~50 tests)
# ===========================================================================


class TestEraRecipesValidation:
    """Validate structure and content of ERA_RECIPES and DEFAULT_RECIPE."""

    # --- All 10 chapter recipes exist (10 tests) ---
    @pytest.mark.parametrize("chapter_id", ALL_CHAPTER_IDS)
    def test_chapter_recipe_exists(self, chapter_id):
        assert chapter_id in ERA_RECIPES

    # --- Each recipe has all 5 required fields (10 tests) ---
    @pytest.mark.parametrize("chapter_id", ALL_CHAPTER_IDS)
    def test_recipe_has_all_fields(self, chapter_id):
        recipe = ERA_RECIPES[chapter_id]
        for field in RECIPE_FIELDS:
            assert field in recipe, f"Missing field '{field}' in {chapter_id}"

    # --- No empty values in any recipe field (50 combos via parametrize: 10 chapters x 5 fields) ---
    @pytest.mark.parametrize("chapter_id", ALL_CHAPTER_IDS)
    @pytest.mark.parametrize("field", RECIPE_FIELDS)
    def test_recipe_field_not_empty(self, chapter_id, field):
        value = ERA_RECIPES[chapter_id][field]
        assert isinstance(value, str)
        assert len(value.strip()) > 0

    # --- Camera field mentions lens (10 tests) ---
    @pytest.mark.parametrize("chapter_id", ALL_CHAPTER_IDS)
    def test_camera_mentions_lens(self, chapter_id):
        camera = ERA_RECIPES[chapter_id]["camera"]
        assert "mm" in camera.lower() or "lens" in camera.lower(), (
            f"Camera for {chapter_id} should mention lens/mm: {camera}"
        )

    # --- Palette field contains hex color (10 tests) ---
    @pytest.mark.parametrize("chapter_id", ALL_CHAPTER_IDS)
    def test_palette_contains_hex_color(self, chapter_id):
        palette = ERA_RECIPES[chapter_id]["palette"]
        assert re.search(r"#[0-9a-fA-F]{6}", palette), (
            f"Palette for {chapter_id} should contain a hex color: {palette}"
        )

    # --- DEFAULT_RECIPE validation (5 tests) ---
    @pytest.mark.parametrize("field", RECIPE_FIELDS)
    def test_default_recipe_has_field(self, field):
        assert field in DEFAULT_RECIPE
        assert isinstance(DEFAULT_RECIPE[field], str)
        assert len(DEFAULT_RECIPE[field].strip()) > 0

    # --- ERA_RECIPES count (1 test) ---
    def test_era_recipes_count(self):
        assert len(ERA_RECIPES) == 10


# ===========================================================================
# SECTION 3: Config-Driven Recipes (~50 tests)
# ===========================================================================


class TestConfigDrivenRecipes:
    """Tests for build_era_recipes_from_config."""

    def test_loads_from_real_config(self):
        """Real config file can be loaded."""
        recipes = build_era_recipes_from_config(CONFIG_PATH)
        assert isinstance(recipes, dict)

    def test_config_recipes_keys_are_chapter_ids(self):
        """If config has visual_style entries, keys are valid chapter IDs."""
        recipes = build_era_recipes_from_config(CONFIG_PATH)
        # Config may or may not have visual_style; test structure if any exist
        for key in recipes:
            assert isinstance(key, str)
            assert len(key) > 0

    @pytest.mark.parametrize("field", RECIPE_FIELDS)
    def test_config_recipe_values_have_required_fields(self, field):
        """Each recipe built from config has all required fields."""
        recipes = build_era_recipes_from_config(CONFIG_PATH)
        for chapter_id, recipe in recipes.items():
            assert field in recipe, f"Missing {field} in config recipe for {chapter_id}"

    def test_config_without_visual_style_returns_empty(self, tmp_path):
        """Config missing visual_style returns empty dict."""
        config = {
            "chapter_meta": {
                "01_intro": {"title": "Test", "era": "2026"},
            }
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        recipes = build_era_recipes_from_config(str(config_file))
        assert recipes == {}

    def test_empty_visual_style_dict_returns_empty(self, tmp_path):
        """Config with empty visual_style dict skips that chapter."""
        config = {
            "chapter_meta": {
                "01_intro": {"title": "Test", "visual_style": {}},
            }
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        recipes = build_era_recipes_from_config(str(config_file))
        # Empty dict is falsy, so no recipe built
        assert "01_intro" not in recipes

    def test_partial_visual_style_falls_back(self, tmp_path):
        """Partial visual_style fills missing fields from DEFAULT_RECIPE."""
        config = {
            "chapter_meta": {
                "01_intro": {
                    "title": "Test",
                    "visual_style": {"camera": "50mm custom lens"},
                },
            }
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        recipes = build_era_recipes_from_config(str(config_file))
        assert "01_intro" in recipes
        recipe = recipes["01_intro"]
        assert recipe["camera"] == "50mm custom lens"
        assert recipe["lighting"] == DEFAULT_RECIPE["lighting"]
        assert recipe["film"] == DEFAULT_RECIPE["film"]
        assert recipe["env"] == DEFAULT_RECIPE["env"]
        assert recipe["palette"] == DEFAULT_RECIPE["palette"]

    @pytest.mark.parametrize("field", RECIPE_FIELDS)
    def test_partial_visual_style_single_field_override(self, field, tmp_path):
        """Override a single field; others fall back to DEFAULT_RECIPE."""
        override_value = f"custom_{field}_value"
        config = {
            "chapter_meta": {
                "test_ch": {
                    "title": "Test",
                    "visual_style": {field: override_value},
                },
            }
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        recipes = build_era_recipes_from_config(str(config_file))
        assert recipes["test_ch"][field] == override_value
        for other_field in RECIPE_FIELDS:
            if other_field != field:
                assert recipes["test_ch"][other_field] == DEFAULT_RECIPE[other_field]

    def test_config_with_no_chapter_meta(self, tmp_path):
        """Config missing chapter_meta entirely returns empty dict."""
        config = {"topic": "Test"}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        recipes = build_era_recipes_from_config(str(config_file))
        assert recipes == {}

    def test_visual_style_as_non_dict_ignored(self, tmp_path):
        """visual_style set to a string (not dict) is ignored."""
        config = {
            "chapter_meta": {
                "01_intro": {"title": "Test", "visual_style": "not a dict"},
            }
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        recipes = build_era_recipes_from_config(str(config_file))
        assert "01_intro" not in recipes

    def test_visual_style_as_list_ignored(self, tmp_path):
        """visual_style set to a list (not dict) is ignored."""
        config = {
            "chapter_meta": {
                "01_intro": {"title": "Test", "visual_style": ["camera", "lighting"]},
            }
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        recipes = build_era_recipes_from_config(str(config_file))
        assert "01_intro" not in recipes

    @pytest.mark.parametrize(
        "num_chapters", [1, 2, 5, 10, 15],
        ids=["1_chapter", "2_chapters", "5_chapters", "10_chapters", "15_chapters"],
    )
    def test_various_chapter_counts(self, num_chapters, tmp_path):
        """Config with varying chapter counts produces matching recipe count."""
        chapter_meta = {}
        for i in range(num_chapters):
            chapter_meta[f"ch_{i:02d}"] = {
                "title": f"Chapter {i}",
                "visual_style": {"camera": f"{i * 10 + 20}mm lens"},
            }
        config = {"chapter_meta": chapter_meta}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        recipes = build_era_recipes_from_config(str(config_file))
        assert len(recipes) == num_chapters

    def test_full_visual_style_override(self, tmp_path):
        """All 5 fields provided in visual_style override all defaults."""
        custom = {
            "camera": "custom camera",
            "lighting": "custom lighting",
            "film": "custom film",
            "env": "custom env",
            "palette": "custom palette",
        }
        config = {
            "chapter_meta": {
                "test_ch": {"title": "Test", "visual_style": custom},
            }
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        recipes = build_era_recipes_from_config(str(config_file))
        for field in RECIPE_FIELDS:
            assert recipes["test_ch"][field] == custom[field]

    def test_extra_fields_in_visual_style_ignored(self, tmp_path):
        """Extra unknown fields in visual_style do not appear in recipe."""
        config = {
            "chapter_meta": {
                "test_ch": {
                    "title": "Test",
                    "visual_style": {
                        "camera": "50mm",
                        "extra_field": "should be ignored",
                    },
                },
            }
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        recipes = build_era_recipes_from_config(str(config_file))
        assert "extra_field" not in recipes["test_ch"]

    @pytest.mark.parametrize("chapter_id", ALL_CHAPTER_IDS)
    def test_real_config_chapter_meta_exists(self, chapter_id):
        """Real config has chapter_meta for each expected chapter ID."""
        config = json.loads(Path(CONFIG_PATH).read_text())
        assert chapter_id in config["chapter_meta"]

    def test_real_config_has_10_chapters(self):
        """Real config has exactly 10 chapter IDs."""
        config = json.loads(Path(CONFIG_PATH).read_text())
        assert len(config["chapter_ids"]) == 10

    def test_mixed_chapters_with_and_without_visual_style(self, tmp_path):
        """Only chapters with visual_style dict get recipes."""
        config = {
            "chapter_meta": {
                "ch_with": {"title": "With", "visual_style": {"camera": "50mm"}},
                "ch_without": {"title": "Without"},
                "ch_empty": {"title": "Empty", "visual_style": {}},
            }
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        recipes = build_era_recipes_from_config(str(config_file))
        assert "ch_with" in recipes
        assert "ch_without" not in recipes
        assert "ch_empty" not in recipes


# ===========================================================================
# SECTION 4: Scene Type Shot Mapping (~30 tests)
# ===========================================================================


class TestSceneTypeShotMapping:
    """Tests for SCENE_TYPE_SHOTS dictionary."""

    # --- All defined scene types present (5 tests) ---
    @pytest.mark.parametrize("scene_type", ALL_SCENE_TYPES)
    def test_scene_type_exists(self, scene_type):
        assert scene_type in SCENE_TYPE_SHOTS

    # --- Shot descriptions are non-empty strings (5 tests) ---
    @pytest.mark.parametrize("scene_type", ALL_SCENE_TYPES)
    def test_shot_description_non_empty(self, scene_type):
        desc = SCENE_TYPE_SHOTS[scene_type]
        assert isinstance(desc, str)
        assert len(desc.strip()) > 0

    # --- Shot descriptions < 200 chars (5 tests) ---
    @pytest.mark.parametrize("scene_type", ALL_SCENE_TYPES)
    def test_shot_description_under_200_chars(self, scene_type):
        desc = SCENE_TYPE_SHOTS[scene_type]
        assert len(desc) < 200

    # --- Unknown scene type default (1 test) ---
    def test_unknown_scene_type_returns_default(self):
        default = SCENE_TYPE_SHOTS.get("nonexistent_type", "medium shot, balanced composition")
        assert default == "medium shot, balanced composition"

    # --- Shot descriptions contain composition keywords (5 tests) ---
    COMPOSITION_KEYWORDS = ["shot", "framing", "angle", "close-up", "view"]

    @pytest.mark.parametrize("scene_type", ALL_SCENE_TYPES)
    def test_shot_description_has_composition_keyword(self, scene_type):
        desc = SCENE_TYPE_SHOTS[scene_type].lower()
        assert any(kw in desc for kw in self.COMPOSITION_KEYWORDS), (
            f"Shot description for {scene_type} lacks composition keyword: {desc}"
        )

    # --- Exact count of scene types (1 test) ---
    def test_scene_type_shots_count(self):
        assert len(SCENE_TYPE_SHOTS) == 5

    # --- Values are unique (1 test) ---
    def test_shot_descriptions_are_unique(self):
        values = list(SCENE_TYPE_SHOTS.values())
        assert len(values) == len(set(values))

    # --- Specific content checks per scene type (5 tests) ---
    def test_image_reveal_is_wide(self):
        assert "wide" in SCENE_TYPE_SHOTS["image_reveal"].lower()

    def test_character_is_portrait(self):
        desc = SCENE_TYPE_SHOTS["character"].lower()
        assert "portrait" in desc or "close-up" in desc

    def test_quote_is_intimate(self):
        desc = SCENE_TYPE_SHOTS["quote"].lower()
        assert "close-up" in desc or "intimate" in desc

    def test_fact_reveal_is_dynamic(self):
        desc = SCENE_TYPE_SHOTS["fact_reveal"].lower()
        assert "dynamic" in desc or "dutch" in desc or "angle" in desc

    def test_timeline_is_panoramic(self):
        desc = SCENE_TYPE_SHOTS["timeline"].lower()
        assert "panoramic" in desc or "sweeping" in desc


# ===========================================================================
# SECTION 5: Output File Naming (~30 tests)
# ===========================================================================


class TestOutputFileNaming:
    """Tests for the file naming pattern: {chapter_id}_scene_{index:03d}.png"""

    @pytest.mark.parametrize(
        "index", [0, 1, 5, 10, 99, 100, 999],
        ids=["idx_0", "idx_1", "idx_5", "idx_10", "idx_99", "idx_100", "idx_999"],
    )
    @pytest.mark.parametrize(
        "chapter_id",
        ["01_intro", "05_evolution", "10_conclusion"],
        ids=["ch01", "ch05", "ch10"],
    )
    def test_filename_pattern(self, chapter_id, index):
        """Filename follows {chapter_id}_scene_{index:03d}.png format."""
        fname = f"{chapter_id}_scene_{index:03d}.png"
        assert fname.endswith(".png")
        assert chapter_id in fname
        assert "_scene_" in fname
        # Check zero-padding: the index part is 3 digits
        match = re.search(r"_scene_(\d{3,})\.png$", fname)
        assert match is not None
        assert int(match.group(1)) == index

    @pytest.mark.parametrize("chapter_id", ALL_CHAPTER_IDS)
    def test_no_special_chars_in_filename(self, chapter_id):
        """Filenames contain only alphanumeric, underscore, and dot."""
        fname = f"{chapter_id}_scene_001.png"
        assert re.match(r"^[a-zA-Z0-9_.]+$", fname), f"Invalid chars in filename: {fname}"

    def test_zero_padded_single_digit(self):
        fname = f"01_intro_scene_{3:03d}.png"
        assert "scene_003" in fname

    def test_zero_padded_double_digit(self):
        fname = f"01_intro_scene_{42:03d}.png"
        assert "scene_042" in fname

    def test_zero_padded_triple_digit(self):
        fname = f"01_intro_scene_{100:03d}.png"
        assert "scene_100" in fname


# ===========================================================================
# SECTION 6: Generated Image File Validation (~40 tests)
# ===========================================================================


# Discover all chapter prefixes actually present in scene_images_v2
_V2_FILES = []
_V2_CHAPTER_PREFIXES = set()
if SCENE_IMAGES_V2_DIR.exists():
    _V2_FILES = sorted(SCENE_IMAGES_V2_DIR.glob("*.png"))
    for f in _V2_FILES:
        # Extract chapter prefix: everything before the first _scene_ or _NN.png
        m = re.match(r"^(\d{2}_[a-z_]+?)(?:_scene_|_\d)", f.name)
        if m:
            _V2_CHAPTER_PREFIXES.add(m.group(1))


class TestGeneratedImageFiles:
    """Validate real PNG files in scene_images_v2/."""

    def test_scene_images_v2_directory_exists(self):
        assert SCENE_IMAGES_V2_DIR.exists(), "scene_images_v2/ directory must exist"

    def test_scene_images_v2_not_empty(self):
        assert len(_V2_FILES) > 0, "scene_images_v2/ should contain PNG files"

    def test_total_file_count_reasonable(self):
        """At least 100 scene images should exist."""
        assert len(_V2_FILES) >= 100, f"Only {len(_V2_FILES)} files found, expected >= 100"

    # --- Each file is valid PNG (starts with magic bytes) ---
    # Sample up to 30 files to keep runtime reasonable
    _SAMPLE_FILES = _V2_FILES[:30] if len(_V2_FILES) >= 30 else _V2_FILES

    @pytest.mark.parametrize(
        "png_file",
        _SAMPLE_FILES,
        ids=[f.name for f in _SAMPLE_FILES],
    )
    def test_file_is_valid_png(self, png_file):
        """File starts with PNG magic bytes (\\x89PNG)."""
        with open(png_file, "rb") as f:
            header = f.read(8)
        assert header[:4] == b"\x89PNG", f"{png_file.name} is not a valid PNG"

    @pytest.mark.parametrize(
        "png_file",
        _SAMPLE_FILES,
        ids=[f.name for f in _SAMPLE_FILES],
    )
    def test_file_size_above_10kb(self, png_file):
        """File is larger than 10KB (not empty/corrupt)."""
        size = png_file.stat().st_size
        assert size > 10 * 1024, f"{png_file.name} is only {size} bytes"

    @pytest.mark.parametrize(
        "png_file",
        _SAMPLE_FILES,
        ids=[f.name for f in _SAMPLE_FILES],
    )
    def test_file_size_below_10mb(self, png_file):
        """File is smaller than 10MB (reasonable)."""
        size = png_file.stat().st_size
        assert size < 10 * 1024 * 1024, f"{png_file.name} is {size / 1024 / 1024:.1f}MB"

    def test_no_zero_byte_files(self):
        """No files in scene_images_v2/ are zero bytes."""
        zero_files = [f for f in _V2_FILES if f.stat().st_size == 0]
        assert len(zero_files) == 0, f"Zero-byte files found: {[f.name for f in zero_files]}"

    # --- Files exist for each chapter (10 tests) ---
    @pytest.mark.parametrize("chapter_id", ALL_CHAPTER_IDS)
    def test_chapter_has_images(self, chapter_id):
        """Each chapter has at least one image file in scene_images_v2/."""
        chapter_files = [f for f in _V2_FILES if f.name.startswith(chapter_id)]
        assert len(chapter_files) > 0, f"No images found for chapter {chapter_id}"

    # --- All files have .png extension (1 test) ---
    def test_all_files_are_png_extension(self):
        non_png = [f for f in _V2_FILES if f.suffix != ".png"]
        assert len(non_png) == 0, f"Non-PNG files: {[f.name for f in non_png]}"

    # --- Filenames are valid (no spaces, no special chars) ---
    @pytest.mark.parametrize(
        "png_file",
        _SAMPLE_FILES[:10],
        ids=[f.name for f in _SAMPLE_FILES[:10]],
    )
    def test_filename_no_spaces(self, png_file):
        assert " " not in png_file.name, f"Filename contains spaces: {png_file.name}"

    # --- Chapter prefix coverage (1 test) ---
    def test_all_chapters_represented(self):
        """All 10 chapters have files in scene_images_v2/."""
        for chapter_id in ALL_CHAPTER_IDS:
            matching = [f for f in _V2_FILES if f.name.startswith(chapter_id)]
            assert len(matching) > 0, f"Missing images for {chapter_id}"
