#!/usr/bin/env python3
"""
Voice QA Gate — Pipeline gate that blocks rendering until voice quality passes.

Integrates test_voice_quality.py as a hard gate in the production pipeline.
If critical artifacts are found, it:
  1. Identifies the exact timestamp and type of artifact
  2. Auto-regenerates ONLY the failed chapter audio via ElevenLabs
  3. Re-transcribes with Whisper
  4. Re-runs quality checks
  5. Only passes the gate when all chapters are clean

Usage:
    python3 voice_qa_gate.py                    # Run gate, fail if artifacts found
    python3 voice_qa_gate.py --auto-fix         # Auto-regenerate failed chapters
    python3 voice_qa_gate.py --max-retries 3    # Retry up to 3 times per chapter
    python3 voice_qa_gate.py --chapters 08_ai_disruption 10_future_outro  # Specific chapters
"""

import argparse
import json
import os
import sys
import time
import subprocess
from pathlib import Path
from dataclasses import dataclass

# Import the test module
sys.path.insert(0, str(Path(__file__).parent))
from test_voice_quality import analyze_chapter, ArtifactReport, CHAPTERS

SCRIPT_DIR = Path(__file__).parent
AUDIO_DIR = SCRIPT_DIR / "audio"
TRANSCRIPT_DIR = SCRIPT_DIR / "transcripts"
REMOTION_AUDIO = SCRIPT_DIR / ".." / ".." / "public" / "seo_audio"
QA_REPORT_DIR = Path(__file__).parent / "qa_reports"
QA_REPORT_DIR.mkdir(parents=True, exist_ok=True)

ELEVENLABS_API_KEY = os.getenv(
    "ELEVENLABS_API_KEY",
    "sk_2252654c95162d4e0e644a1e2a540892d3faa828a36cace5",
)
VOICE_ID = "k0HDiJKO5QdXkGN6NSLI"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


@dataclass
class GateResult:
    chapter_id: str
    passed: bool
    attempt: int
    critical_issues: list[dict]
    warning_issues: list[dict]
    regenerated: bool = False


def regenerate_chapter_audio(chapter_id: str, script_text: str) -> bool:
    """Re-generate a single chapter's audio via ElevenLabs."""
    import urllib.request

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    payload = json.dumps({
        "text": script_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True,
        },
    }).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            audio_data = resp.read()

        output_path = AUDIO_DIR / f"{chapter_id}.mp3"
        output_path.write_bytes(audio_data)

        # Sync to Remotion
        remotion_path = REMOTION_AUDIO / f"{chapter_id}.mp3"
        remotion_path.write_bytes(audio_data)

        print(f"      Regenerated: {output_path.name} ({len(audio_data) // 1024}KB)")
        return True
    except Exception as e:
        print(f"      Failed to regenerate: {e}")
        return False


def retranscribe_chapter(chapter_id: str) -> bool:
    """Re-transcribe a chapter using Whisper API."""
    if not OPENAI_API_KEY:
        print("      No OPENAI_API_KEY — skipping retranscription")
        return False

    audio_path = AUDIO_DIR / f"{chapter_id}.mp3"
    if not audio_path.exists():
        return False

    import urllib.request
    import urllib.error

    # Use multipart form upload for Whisper
    boundary = "----WhisperBoundary"
    audio_data = audio_path.read_bytes()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{chapter_id}.mp3"\r\n'
        f"Content-Type: audio/mpeg\r\n\r\n"
    ).encode() + audio_data + (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\n'
        f"whisper-1\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="response_format"\r\n\r\n'
        f"verbose_json\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="timestamp_granularities[]"\r\n\r\n'
        f"word\r\n"
        f"--{boundary}--\r\n"
    ).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions",
        data=body,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())

        words = [
            {"word": w["word"], "start": w["start"], "end": w["end"]}
            for w in data.get("words", [])
        ]

        transcript_path = TRANSCRIPT_DIR / f"{chapter_id}.json"
        transcript_path.write_text(json.dumps({
            "text": data.get("text", ""),
            "words": words,
            "duration": data.get("duration", 0),
        }, indent=2))

        print(f"      Retranscribed: {len(words)} words")
        return True
    except Exception as e:
        print(f"      Retranscription failed: {e}")
        return False


def load_chapter_script(chapter_id: str) -> str | None:
    """Load chapter script text from generate_voiceover.py."""
    voiceover_path = Path(__file__).parent / "generate_voiceover.py"
    if not voiceover_path.exists():
        return None

    content = voiceover_path.read_text()

    # Extract the chapter's script text from the CHAPTERS dict
    import re
    # Find the chapter entry: "chapter_id": """text""",
    pattern = rf'"{chapter_id}":\s*"""(.*?)"""'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def run_gate(
    chapters: list[str],
    auto_fix: bool = False,
    max_retries: int = 2,
) -> tuple[list[GateResult], bool]:
    """
    Run the voice QA gate on specified chapters.

    Returns (results, all_passed).
    """
    results: list[GateResult] = []
    all_passed = True

    for chapter_id in chapters:
        print(f"\n  Gate: {chapter_id}")
        attempt = 0
        passed = False

        while attempt <= max_retries:
            attempt += 1
            print(f"    Attempt {attempt}/{max_retries + 1}...")

            report = analyze_chapter(chapter_id)
            critical = [i for i in report.issues if i["severity"] == "critical"]
            warnings = [i for i in report.issues if i["severity"] == "warning"]

            if report.passed:
                print(f"    ✓ PASS ({report.duration_secs:.1f}s)")
                results.append(GateResult(
                    chapter_id=chapter_id,
                    passed=True,
                    attempt=attempt,
                    critical_issues=[],
                    warning_issues=warnings,
                ))
                passed = True
                break

            print(f"    ✗ {len(critical)} critical, {len(warnings)} warnings")
            for issue in critical:
                time_str = f" @ {issue['time_secs']:.1f}s" if issue.get("time_secs") else ""
                print(f"      ✗ [{issue['type']}]{time_str}: {issue['detail']}")

            if not auto_fix or attempt > max_retries:
                break

            # Auto-fix: regenerate the chapter
            print(f"    Regenerating chapter audio...")
            script_text = load_chapter_script(chapter_id)
            if not script_text:
                print(f"      Could not load script for {chapter_id}")
                break

            success = regenerate_chapter_audio(chapter_id, script_text)
            if not success:
                break

            # Re-transcribe
            retranscribe_chapter(chapter_id)
            time.sleep(2)  # Brief pause before re-test

        if not passed:
            all_passed = False
            results.append(GateResult(
                chapter_id=chapter_id,
                passed=False,
                attempt=attempt,
                critical_issues=critical,
                warning_issues=warnings,
                regenerated=auto_fix and attempt > 1,
            ))

    return results, all_passed


def main():
    parser = argparse.ArgumentParser(description="Voice QA Gate — Pipeline Quality Gate")
    parser.add_argument("--auto-fix", action="store_true", help="Auto-regenerate failed chapters")
    parser.add_argument("--max-retries", type=int, default=2, help="Max regeneration retries")
    parser.add_argument("--chapters", nargs="+", help="Specific chapters to test")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    chapters = args.chapters or CHAPTERS

    print("=" * 60)
    print("  Voice QA Gate — ElevenLabs Artifact Quality Gate")
    print("=" * 60)

    results, all_passed = run_gate(
        chapters=chapters,
        auto_fix=args.auto_fix,
        max_retries=args.max_retries,
    )

    # Summary
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    regenerated = sum(1 for r in results if r.regenerated)

    print(f"\n{'=' * 60}")
    print(f"  Gate Result: {'PASS' if all_passed else 'FAIL'}")
    print(f"  Chapters: {passed}/{len(results)} passed")
    if failed:
        print(f"  Failed: {', '.join(r.chapter_id for r in results if not r.passed)}")
    if regenerated:
        print(f"  Regenerated: {regenerated} chapters")
    print(f"{'=' * 60}")

    # Save report
    if args.json or True:  # Always save
        report = {
            "gate_passed": all_passed,
            "timestamp": time.time(),
            "results": [
                {
                    "chapter_id": r.chapter_id,
                    "passed": r.passed,
                    "attempt": r.attempt,
                    "regenerated": r.regenerated,
                    "critical_issues": r.critical_issues,
                    "warning_issues": r.warning_issues,
                }
                for r in results
            ],
        }
        report_path = QA_REPORT_DIR / f"voice_qa_{int(time.time())}.json"
        report_path.write_text(json.dumps(report, indent=2))
        print(f"\n  Report: {report_path}")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
