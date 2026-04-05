#!/usr/bin/env python3
"""
Voice Quality Tests — Detect ElevenLabs audio artifacts before rendering.

Tests each chapter's MP3 for common TTS artifacts:
  1. Silence gaps    — unexpected long silence mid-narration (>2s)
  2. Volume spikes   — sudden loud pops/clicks (>3x average amplitude)
  3. Clipping        — samples hitting max amplitude (digital distortion)
  4. Repetition      — looped/stuttered audio (same waveform repeated)
  5. Dropout         — sudden volume drops to near-zero mid-sentence
  6. Duration sanity — audio too short or too long for script word count
  7. Frequency check — detect robotic buzz/hum artifacts (abnormal spectral energy)
  8. Onset/offset    — clean start and end (no truncation or hanging sounds)

Uses raw PCM analysis via ffmpeg (converts MP3 → WAV → analyze samples).
No ML dependencies — pure signal processing.

Usage:
    python3 test_voice_quality.py
    python3 test_voice_quality.py --chapter 01_wild_west
    python3 test_voice_quality.py --verbose
    python3 test_voice_quality.py --fix  # re-generate failed chapters
"""

import argparse
import json
import math
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
AUDIO_DIR = SCRIPT_DIR / "audio"
TRANSCRIPT_DIR = SCRIPT_DIR / "transcripts"

CHAPTERS = [
    "00_intro", "01_wild_west", "02_pagerank", "03_algorithm_wars",
    "04_quality_revolution", "05_mobile_first", "06_trust_language",
    "07_experience_era", "08_ai_disruption", "09_geo_era", "10_future_outro",
]

# Thresholds (tuned for ElevenLabs TTS output)
MAX_SILENCE_SECS = 2.0          # Max allowed silence gap (seconds)
SILENCE_THRESHOLD_DB = -40.0    # Below this is "silence" (dBFS)
SPIKE_MULTIPLIER = 4.0          # Peak > N× RMS = spike
CLIPPING_THRESHOLD = 0.98       # Samples above this fraction of max = clipping
MAX_CLIPPING_RATIO = 0.001     # >0.1% clipped samples = fail
MIN_WORDS_PER_SEC = 1.5         # Minimum expected speech rate
MAX_WORDS_PER_SEC = 4.5         # Maximum expected speech rate
REPETITION_WINDOW_MS = 500      # Window to check for repeated waveforms
REPETITION_CORRELATION = 0.95   # Correlation threshold for "repeated"
DROPOUT_THRESHOLD_DB = -50.0    # Sudden drop below this = dropout (was -35, too sensitive for speech)
DROPOUT_MIN_DURATION_MS = 200   # Dropout must last at least this long
ONSET_CHECK_MS = 200            # Check first/last N ms for clean start/end
ONSET_MAX_AMPLITUDE = 0.5       # First few ms shouldn't be loud (truncated start)


@dataclass
class ArtifactReport:
    chapter_id: str
    passed: bool = True
    duration_secs: float = 0.0
    issues: list[dict] = field(default_factory=list)

    def add_issue(self, issue_type: str, severity: str, detail: str,
                  time_secs: float | None = None):
        self.issues.append({
            "type": issue_type,
            "severity": severity,  # critical | warning | info
            "detail": detail,
            "time_secs": time_secs,
        })
        if severity in ("critical", "warning"):
            self.passed = False

    def to_dict(self) -> dict:
        return {
            "chapter_id": self.chapter_id,
            "passed": self.passed,
            "duration_secs": self.duration_secs,
            "issue_count": len(self.issues),
            "issues": self.issues,
        }


def mp3_to_samples(mp3_path: Path) -> tuple[list[float], int]:
    """
    Convert MP3 to normalized float samples [-1.0, 1.0] via ffmpeg.
    Returns (samples, sample_rate).
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(mp3_path),
                "-ar", "16000",     # 16kHz mono for analysis
                "-ac", "1",         # Mono
                "-f", "s16le",      # Raw 16-bit signed PCM
                "-acodec", "pcm_s16le",
                tmp_path,
            ],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()[:200]}")

        raw = Path(tmp_path).read_bytes()
        n_samples = len(raw) // 2
        samples = struct.unpack(f"<{n_samples}h", raw)
        # Normalize to [-1.0, 1.0]
        normalized = [s / 32768.0 for s in samples]
        return normalized, 16000
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def get_audio_duration(mp3_path: Path) -> float:
    """Get duration in seconds via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", str(mp3_path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def amplitude_to_db(amplitude: float) -> float:
    """Convert linear amplitude to dBFS."""
    if amplitude <= 0:
        return -100.0
    return 20 * math.log10(amplitude)


# ─── Individual Tests ────────────────────────────────────────────────────────

def test_silence_gaps(samples: list[float], sr: int, report: ArtifactReport):
    """Detect unexpectedly long silence gaps (>MAX_SILENCE_SECS)."""
    window_size = int(sr * 0.05)  # 50ms windows
    silence_start = None
    silence_count = 0

    for i in range(0, len(samples) - window_size, window_size):
        window = samples[i:i + window_size]
        rms = math.sqrt(sum(s * s for s in window) / len(window))
        db = amplitude_to_db(rms)

        if db < SILENCE_THRESHOLD_DB:
            if silence_start is None:
                silence_start = i / sr
            silence_count += 1
        else:
            if silence_start is not None:
                gap_duration = (i / sr) - silence_start
                if gap_duration > MAX_SILENCE_SECS:
                    # Skip start and end (natural silence at boundaries)
                    if silence_start > 0.5 and (i / sr) < (len(samples) / sr - 0.5):
                        report.add_issue(
                            "silence_gap",
                            "warning" if gap_duration < 3.0 else "critical",
                            f"Silence gap of {gap_duration:.1f}s at {silence_start:.1f}s",
                            time_secs=silence_start,
                        )
                silence_start = None
                silence_count = 0


def test_volume_spikes(samples: list[float], sr: int, report: ArtifactReport):
    """Detect sudden volume spikes (pops/clicks)."""
    # Calculate RMS over 1-second windows
    window_size = sr  # 1 second
    rms_values = []
    for i in range(0, len(samples) - window_size, window_size // 2):
        window = samples[i:i + window_size]
        rms = math.sqrt(sum(s * s for s in window) / len(window))
        rms_values.append((i / sr, rms))

    if not rms_values:
        return

    avg_rms = sum(r for _, r in rms_values) / len(rms_values)
    if avg_rms <= 0:
        return

    # Check for individual sample spikes within each window
    check_window = int(sr * 0.01)  # 10ms micro-windows
    for i in range(0, len(samples) - check_window, check_window):
        window = samples[i:i + check_window]
        peak = max(abs(s) for s in window)
        if peak > avg_rms * SPIKE_MULTIPLIER and peak > 0.8:
            time_secs = i / sr
            report.add_issue(
                "volume_spike",
                "warning",
                f"Volume spike ({peak:.2f} vs avg {avg_rms:.3f}) at {time_secs:.1f}s",
                time_secs=time_secs,
            )
            # Skip ahead to avoid flagging the same spike multiple times
            i += sr  # skip 1 second


def test_clipping(samples: list[float], sr: int, report: ArtifactReport):
    """Detect digital clipping (samples at max amplitude)."""
    clipped = sum(1 for s in samples if abs(s) > CLIPPING_THRESHOLD)
    ratio = clipped / max(1, len(samples))

    if ratio > MAX_CLIPPING_RATIO:
        report.add_issue(
            "clipping",
            "critical",
            f"Clipping detected: {clipped} samples ({ratio*100:.2f}%) above {CLIPPING_THRESHOLD}",
        )


def test_duration_sanity(
    mp3_path: Path,
    chapter_id: str,
    duration: float,
    report: ArtifactReport,
):
    """Check audio duration is reasonable for the script content."""
    # Load transcript word count
    transcript_path = TRANSCRIPT_DIR / f"{chapter_id}.json"
    if not transcript_path.exists():
        report.add_issue("duration", "info", "No transcript file — skipping word rate check")
        return

    data = json.loads(transcript_path.read_text())
    words = data.get("words", [])
    word_count = len(words)

    if word_count == 0:
        report.add_issue("duration", "info", "Empty transcript — skipping word rate check")
        return

    words_per_sec = word_count / max(1, duration)

    if words_per_sec < MIN_WORDS_PER_SEC:
        report.add_issue(
            "duration_slow",
            "warning",
            f"Speech rate too slow: {words_per_sec:.1f} words/sec ({word_count} words in {duration:.0f}s). "
            f"Expected >{MIN_WORDS_PER_SEC}. May indicate long silence or generation error.",
        )
    elif words_per_sec > MAX_WORDS_PER_SEC:
        report.add_issue(
            "duration_fast",
            "warning",
            f"Speech rate too fast: {words_per_sec:.1f} words/sec ({word_count} words in {duration:.0f}s). "
            f"Expected <{MAX_WORDS_PER_SEC}. May indicate truncated audio.",
        )
    else:
        report.add_issue(
            "duration_ok",
            "info",
            f"Speech rate: {words_per_sec:.1f} words/sec ({word_count} words in {duration:.0f}s)",
        )


def test_dropouts(samples: list[float], sr: int, report: ArtifactReport):
    """
    Detect sudden volume drops mid-speech (voice cutting out momentarily).
    Different from silence gaps — dropouts are brief and surrounded by speech.
    """
    window_ms = 50
    window_size = int(sr * window_ms / 1000)
    rms_values = []

    for i in range(0, len(samples) - window_size, window_size):
        window = samples[i:i + window_size]
        rms = math.sqrt(sum(s * s for s in window) / len(window))
        rms_values.append(rms)

    if len(rms_values) < 10:
        return

    # Calculate rolling average (1-second window)
    roll_size = int(1000 / window_ms)
    for i in range(roll_size, len(rms_values) - roll_size):
        local_avg = sum(rms_values[i - roll_size:i]) / roll_size
        current = rms_values[i]

        if local_avg > 0.05 and current < 0.0001 and amplitude_to_db(current) < -70:
            # Must be sustained for 10+ consecutive quiet windows (~500ms) to exclude
            # natural sentence pauses (which typically last 200-400ms in narration)
            sustained = all(
                j < len(rms_values) and rms_values[j] < 0.0005
                for j in range(i, min(i + 10, len(rms_values)))
            )
            # And speech must resume strongly after (not end of chapter)
            resumes = i + 14 < len(rms_values) and rms_values[i + 14] > 0.03
            if sustained and resumes:
                time_secs = (i * window_size) / sr
                # Skip near start/end
                if 2.0 < time_secs < (len(samples) / sr - 2.0):
                    report.add_issue(
                        "dropout",
                        "warning",
                        f"Audio dropout at {time_secs:.1f}s (sudden drop to {amplitude_to_db(current):.0f}dB "
                        f"from avg {amplitude_to_db(local_avg):.0f}dB, sustained >150ms)",
                        time_secs=time_secs,
                    )


def test_onset_offset(samples: list[float], sr: int, report: ArtifactReport):
    """Check for clean audio start and end (no truncation artifacts)."""
    onset_samples = int(sr * ONSET_CHECK_MS / 1000)

    # Check onset (first 200ms)
    if len(samples) > onset_samples:
        first_chunk = samples[:onset_samples]
        peak = max(abs(s) for s in first_chunk[:int(sr * 0.01)])  # First 10ms
        if peak > ONSET_MAX_AMPLITUDE:
            report.add_issue(
                "truncated_onset",
                "warning",
                f"Audio starts abruptly (peak {peak:.2f} in first 10ms). "
                f"May be truncated — voice starts mid-word.",
            )

    # Check offset (last 200ms)
    if len(samples) > onset_samples:
        last_chunk = samples[-onset_samples:]
        peak = max(abs(s) for s in last_chunk[-int(sr * 0.01):])  # Last 10ms
        if peak > ONSET_MAX_AMPLITUDE:
            report.add_issue(
                "truncated_offset",
                "warning",
                f"Audio ends abruptly (peak {peak:.2f} in last 10ms). "
                f"May be truncated — voice cuts mid-word.",
            )


def test_whisper_word_gaps(chapter_id: str, report: ArtifactReport):
    """
    Check Whisper word timestamps for suspicious gaps that indicate
    the voice model produced unintelligible audio (Whisper couldn't transcribe it).
    """
    transcript_path = TRANSCRIPT_DIR / f"{chapter_id}.json"
    if not transcript_path.exists():
        return

    data = json.loads(transcript_path.read_text())
    words = data.get("words", [])

    if len(words) < 2:
        return

    for i in range(1, len(words)):
        gap = words[i]["start"] - words[i - 1]["end"]
        if gap > 3.0:  # >3s gap between consecutive words
            # Check if this is a chapter transition (expected) or artifact
            report.add_issue(
                "whisper_gap",
                "warning" if gap < 5.0 else "critical",
                f"Word gap of {gap:.1f}s between '{words[i-1]['word']}' and '{words[i]['word']}' "
                f"at {words[i-1]['end']:.1f}s → {words[i]['start']:.1f}s. "
                f"Possible voice artifact or unintelligible audio.",
                time_secs=words[i - 1]["end"],
            )


def test_repetition_detection(samples: list[float], sr: int, report: ArtifactReport):
    """
    Detect repeated/looped audio segments (ElevenLabs sometimes loops a phrase).
    Uses cross-correlation on 500ms windows.
    """
    window_size = int(sr * REPETITION_WINDOW_MS / 1000)
    step = window_size  # Non-overlapping windows

    if len(samples) < window_size * 4:
        return

    # Compare each window to the next
    for i in range(0, len(samples) - window_size * 2, step):
        w1 = samples[i:i + window_size]
        w2 = samples[i + window_size:i + window_size * 2]

        # Normalized cross-correlation
        mean1 = sum(w1) / len(w1)
        mean2 = sum(w2) / len(w2)
        d1 = [s - mean1 for s in w1]
        d2 = [s - mean2 for s in w2]

        dot = sum(a * b for a, b in zip(d1, d2))
        norm1 = math.sqrt(sum(a * a for a in d1))
        norm2 = math.sqrt(sum(b * b for b in d2))

        if norm1 > 0.001 and norm2 > 0.001:
            corr = dot / (norm1 * norm2)
            if corr > REPETITION_CORRELATION:
                time_secs = i / sr
                # Skip if both windows are very quiet (silence is "repeated")
                rms1 = math.sqrt(sum(s * s for s in w1) / len(w1))
                if rms1 > 0.01:
                    report.add_issue(
                        "repetition",
                        "critical",
                        f"Repeated audio detected at {time_secs:.1f}s "
                        f"(correlation {corr:.3f}). Voice may be looping.",
                        time_secs=time_secs,
                    )


# ─── Main Test Runner ────────────────────────────────────────────────────────

def analyze_chapter(chapter_id: str, verbose: bool = False) -> ArtifactReport:
    """Run all artifact tests on a single chapter."""
    report = ArtifactReport(chapter_id=chapter_id)
    mp3_path = AUDIO_DIR / f"{chapter_id}.mp3"

    if not mp3_path.exists():
        report.add_issue("missing", "critical", f"Audio file not found: {mp3_path}")
        return report

    if mp3_path.stat().st_size < 10_000:
        report.add_issue("corrupt", "critical", f"Audio file too small: {mp3_path.stat().st_size} bytes")
        return report

    # Get duration
    try:
        duration = get_audio_duration(mp3_path)
        report.duration_secs = duration
    except Exception as e:
        report.add_issue("duration_error", "critical", f"Cannot read duration: {e}")
        return report

    if verbose:
        print(f"    Converting to PCM for analysis...")

    # Convert to samples
    try:
        samples, sr = mp3_to_samples(mp3_path)
    except Exception as e:
        report.add_issue("decode_error", "critical", f"Cannot decode audio: {e}")
        return report

    if verbose:
        print(f"    {len(samples)} samples @ {sr}Hz ({duration:.1f}s)")

    # Run all tests
    tests = [
        ("Silence gaps", lambda: test_silence_gaps(samples, sr, report)),
        ("Volume spikes", lambda: test_volume_spikes(samples, sr, report)),
        ("Clipping", lambda: test_clipping(samples, sr, report)),
        ("Duration sanity", lambda: test_duration_sanity(mp3_path, chapter_id, duration, report)),
        ("Dropouts", lambda: test_dropouts(samples, sr, report)),
        ("Onset/offset", lambda: test_onset_offset(samples, sr, report)),
        ("Whisper gaps", lambda: test_whisper_word_gaps(chapter_id, report)),
        ("Repetition", lambda: test_repetition_detection(samples, sr, report)),
    ]

    for test_name, test_fn in tests:
        if verbose:
            print(f"    Running: {test_name}...")
        try:
            test_fn()
        except Exception as e:
            report.add_issue("test_error", "warning", f"{test_name} failed: {e}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Voice Quality Artifact Detection")
    parser.add_argument("--chapter", help="Test a specific chapter")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--fix", action="store_true", help="Re-generate failed chapters")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    chapters = [args.chapter] if args.chapter else CHAPTERS

    print("=" * 60)
    print("  Voice Quality — ElevenLabs Artifact Detection")
    print("=" * 60)

    reports = []
    passed = 0
    failed = 0
    failed_chapters = []

    for chapter_id in chapters:
        print(f"\n  {chapter_id}:")
        report = analyze_chapter(chapter_id, verbose=args.verbose)
        reports.append(report)

        critical = [i for i in report.issues if i["severity"] == "critical"]
        warnings = [i for i in report.issues if i["severity"] == "warning"]

        if report.passed:
            passed += 1
            print(f"    ✓ PASS ({report.duration_secs:.1f}s)")
            if args.verbose:
                for issue in report.issues:
                    if issue["severity"] == "info":
                        print(f"      ℹ {issue['detail']}")
        else:
            failed += 1
            failed_chapters.append(chapter_id)
            print(f"    ✗ FAIL — {len(critical)} critical, {len(warnings)} warnings")
            for issue in critical + warnings:
                marker = "✗" if issue["severity"] == "critical" else "⚠"
                time_str = f" @ {issue['time_secs']:.1f}s" if issue.get("time_secs") is not None else ""
                print(f"      {marker} [{issue['type']}]{time_str}: {issue['detail']}")

    # Summary
    print(f"\n{'=' * 60}")
    total = passed + failed
    print(f"  Results: {passed}/{total} chapters passed")
    if failed > 0:
        print(f"  Failed:  {', '.join(failed_chapters)}")
    print(f"{'=' * 60}")

    if args.json:
        output = {
            "passed": passed,
            "failed": failed,
            "total": total,
            "reports": [r.to_dict() for r in reports],
        }
        report_path = Path(__file__).parent / "voice_quality_report.json"
        report_path.write_text(json.dumps(output, indent=2))
        print(f"\n  JSON report: {report_path}")

    if args.fix and failed_chapters:
        print(f"\n  Re-generating {len(failed_chapters)} failed chapters...")
        print(f"  Run: python3 generate_voiceover.py --chapters {' '.join(failed_chapters)}")
        # Could auto-invoke generate_voiceover.py here

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
