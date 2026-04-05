"""
Shared fixtures for SEO Documentary test suite.

All paths point to real files on disk. No mocks.
"""
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

# ─── Project paths ────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(str(SCRIPT_DIR))
REMOTION_DIR = Path(str(SCRIPT_DIR / ".." / ".."))

RESEARCH_DIR = PROJECT_ROOT / "research" / "seo_and_geo_in_2026_2030_what_actually_works_what_s_changing"
CONFIG_PATH = RESEARCH_DIR / "generate_config.json"

AUDIO_DIR = PROJECT_ROOT / "audio_v2_hq"
TRANSCRIPT_DIR = PROJECT_ROOT / "transcripts_v2_hq"
SCENE_IMAGES_DIR = PROJECT_ROOT / "scene_images_v2"
RENDER_PROPS_PATH = PROJECT_ROOT / "render_props_v2_hq.json"
SCENES_SYNCED_PATH = PROJECT_ROOT / "scenes_synced_v2_hq.json"

PRODUCE_SCRIPT = PROJECT_ROOT / "produce_documentary.sh"
UPLOAD_SCRIPT = PROJECT_ROOT / "upload_youtube.py"

# ─── Ensure upload_youtube is importable ──────────────────────────────────────
sys.path.insert(0, str(PROJECT_ROOT))


# ─── Chapter IDs (from real config) ──────────────────────────────────────────
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


@pytest.fixture(scope="session")
def project_root():
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def remotion_dir():
    return REMOTION_DIR


@pytest.fixture(scope="session")
def config_path():
    return CONFIG_PATH


@pytest.fixture(scope="session")
def config_data():
    """Load the real generate_config.json once per session."""
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def audio_dir():
    return AUDIO_DIR


@pytest.fixture(scope="session")
def transcript_dir():
    return TRANSCRIPT_DIR


@pytest.fixture(scope="session")
def scene_images_dir():
    return SCENE_IMAGES_DIR


@pytest.fixture(scope="session")
def render_props_path():
    return RENDER_PROPS_PATH


@pytest.fixture(scope="session")
def render_props_data():
    """Load the real render_props_v2_hq.json once per session."""
    with open(RENDER_PROPS_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def scenes_synced_path():
    return SCENES_SYNCED_PATH


@pytest.fixture(scope="session")
def scenes_synced_data():
    """Load the real scenes_synced_v2_hq.json once per session."""
    with open(SCENES_SYNCED_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def chapter_ids():
    return CHAPTER_IDS


@pytest.fixture(scope="session")
def produce_script():
    return PRODUCE_SCRIPT


def make_args(**kwargs):
    """Create a SimpleNamespace mimicking argparse output for resolve_metadata."""
    defaults = {
        "video_file": "dummy.mp4",
        "config": None,
        "title": None,
        "description": None,
        "privacy": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)
