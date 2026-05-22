"""Smoke tests for vuln-recorder end-to-end pipeline.

These tests require real system dependencies (Xvfb, ffmpeg, xterm, tmux).
They are skipped automatically if dependencies are missing.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).parent.parent
FIXTURES = ROOT_DIR / "tests" / "fixtures"
SCENARIOS = ROOT_DIR / "scenarios"
CLI = ["/usr/bin/env", "python3", "-m", "vuln_recorder"]


def _deps_available():
    return all(shutil.which(t) for t in ("Xvfb", "ffmpeg", "xterm", "tmux"))


def _ffprobe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True,
    )
    return json.loads(r.stdout)


requires_deps = pytest.mark.skipif(
    not _deps_available(),
    reason="System dependencies (Xvfb, ffmpeg, xterm, tmux) not available",
)


# ─── CLI smoke tests ────────────────────────────────────────────────

@requires_deps
def test_cli_check():
    r = subprocess.run(CLI + ["check"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "All dependencies" in r.stdout


@requires_deps
def test_cli_help():
    r = subprocess.run(CLI + ["--help"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "run" in r.stdout
    assert "check" in r.stdout


@requires_deps
def test_cli_no_args_shows_help():
    r = subprocess.run(CLI, capture_output=True, text=True)
    assert r.returncode == 0
    assert "vuln_recorder" in r.stdout


@requires_deps
@pytest.mark.parametrize("scenario_file", [
    "single_pane.yaml",
    "two_pane.yaml",
    "three_pane.yaml",
    "custom_layout.yaml",
    "openplc-delete-user.yaml",
])
def test_cli_dry_run(scenario_file):
    path = FIXTURES / scenario_file if (FIXTURES / scenario_file).exists() else SCENARIOS / scenario_file
    r = subprocess.run(CLI + ["run", str(path), "--dry-run"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "Dry run" in r.stdout


# ─── Full pipeline smoke tests ──────────────────────────────────────

@requires_deps
@pytest.mark.parametrize("scenario_file,expected_width,expected_height", [
    ("single_pane.yaml", 640, 480),
    ("two_pane.yaml", 800, 600),
    ("three_pane.yaml", 1024, 768),
    ("custom_layout.yaml", 640, 480),
])
def test_full_recording(tmp_path, scenario_file, expected_width, expected_height):
    path = FIXTURES / scenario_file
    output_dir = str(tmp_path / "out")

    r = subprocess.run(
        CLI + ["run", str(path), "--output", output_dir],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 0, f"Run failed:\nstdout: {r.stdout}\nstderr: {r.stderr}"
    assert "Recording saved to" in r.stdout

    # Verify output directory structure
    out_path = Path(r.stdout.split(":")[-1].strip())
    assert (out_path / "recording.mp4").exists()
    assert (out_path / "scenario.yaml").exists()

    # Verify video is valid MP4 with correct resolution
    info = _ffprobe(out_path / "recording.mp4")
    streams = info.get("streams", [])
    assert len(streams) >= 1, "No video streams found"

    video = streams[0]
    assert video["codec_name"] == "h264"
    assert int(video["width"]) == expected_width
    assert int(video["height"]) == expected_height
    assert float(video.get("duration", 0)) > 0


@requires_deps
def test_example_scenario_recording(tmp_path):
    path = SCENARIOS / "openplc-delete-user.yaml"
    output_dir = str(tmp_path / "out")

    r = subprocess.run(
        CLI + ["run", str(path), "--output", output_dir],
        capture_output=True, text=True, timeout=120,
    )
    assert r.returncode == 0, f"Run failed:\nstdout: {r.stdout}\nstderr: {r.stderr}"

    out_path = Path(r.stdout.split(":")[-1].strip())
    assert (out_path / "recording.mp4").exists()

    info = _ffprobe(out_path / "recording.mp4")
    video = info["streams"][0]
    assert video["codec_name"] == "h264"
    assert int(video["width"]) == 1920
    assert int(video["height"]) == 1080


# ─── Video content validation ───────────────────────────────────────

@requires_deps
def test_video_has_playable_duration(tmp_path):
    path = FIXTURES / "single_pane.yaml"
    output_dir = str(tmp_path / "out")

    r = subprocess.run(
        CLI + ["run", str(path), "--output", output_dir],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 0

    out_path = Path(r.stdout.split(":")[-1].strip())
    info = _ffprobe(out_path / "recording.mp4")
    video = info["streams"][0]
    duration = float(video.get("duration", 0))

    # single_pane.yaml has 3 steps with wait=1 each, plus ~1.5s startup
    assert duration >= 2.0, f"Video too short: {duration}s"
    assert duration <= 15.0, f"Video too long: {duration}s"


@requires_deps
def test_video_file_size_reasonable(tmp_path):
    path = FIXTURES / "single_pane.yaml"
    output_dir = str(tmp_path / "out")

    r = subprocess.run(
        CLI + ["run", str(path), "--output", output_dir],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 0

    out_path = Path(r.stdout.split(":")[-1].strip())
    mp4_size = (out_path / "recording.mp4").stat().st_size
    assert mp4_size > 1000, f"MP4 file too small: {mp4_size} bytes"
    assert mp4_size < 10_000_000, f"MP4 file suspiciously large: {mp4_size} bytes"


# ─── Scenario copy validation ───────────────────────────────────────

@requires_deps
def test_scenario_copied_to_output(tmp_path):
    path = FIXTURES / "two_pane.yaml"
    output_dir = str(tmp_path / "out")

    r = subprocess.run(
        CLI + ["run", str(path), "--output", output_dir],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 0

    out_path = Path(r.stdout.split(":")[-1].strip())
    copied = out_path / "scenario.yaml"
    assert copied.exists()
    assert copied.read_text() == path.read_text()


# ─── Sequential runs (no stale state) ───────────────────────────────

@requires_deps
def test_two_runs_back_to_back(tmp_path):
    path = FIXTURES / "single_pane.yaml"
    output_a = str(tmp_path / "run_a")
    output_b = str(tmp_path / "run_b")

    r1 = subprocess.run(
        CLI + ["run", str(path), "--output", output_a],
        capture_output=True, text=True, timeout=60,
    )
    assert r1.returncode == 0

    r2 = subprocess.run(
        CLI + ["run", str(path), "--output", output_b],
        capture_output=True, text=True, timeout=60,
    )
    assert r2.returncode == 0

    out_a = Path(r1.stdout.split(":")[-1].strip())
    out_b = Path(r2.stdout.split(":")[-1].strip())
    assert (out_a / "recording.mp4").exists()
    assert (out_b / "recording.mp4").exists()


# ─── Scenario validation smoke tests ────────────────────────────────

def test_all_fixture_scenarios_load():
    """Every fixture YAML must parse and validate without error."""
    from vuln_recorder.scenario import Scenario
    for yaml_file in FIXTURES.glob("*.yaml"):
        s = Scenario(str(yaml_file))
        data = s.load()
        assert "name" in data
        assert len(data["steps"]) > 0


def test_all_scenarios_dir_load():
    """Every YAML in scenarios/ must parse and validate."""
    from vuln_recorder.scenario import Scenario
    for yaml_file in SCENARIOS.glob("*.yaml"):
        s = Scenario(str(yaml_file))
        data = s.load()
        assert "name" in data
        assert len(data["steps"]) > 0
        assert data["display"]["width"] == 1920
        assert data["display"]["height"] == 1080


# ─── Real tmux pane/layout verification ────────────────────────────

@requires_deps
def test_tmux_pane_count_matches_scenario(tmp_path):
    """After recording, verify tmux created the correct number of panes."""
    from vuln_recorder.xvfb import XvfbManager
    from vuln_recorder.terminal import TerminalOrchestrator

    xvfb = XvfbManager(width=640, height=480)
    display = xvfb.start()
    try:
        panes = [{'name': 'a'}, {'name': 'b'}, {'name': 'c'}]
        term = TerminalOrchestrator(display, "smoke-panes", panes, "custom")
        term.create_session()

        r = subprocess.run(
            ["tmux", "-L", "vr-smoke-panes", "list-panes",
             "-t", "smoke-panes", "-F", "#{pane_index}"],
            capture_output=True, text=True,
        )
        pane_count = len(r.stdout.strip().split('\n'))
        assert pane_count == 3

        term.destroy_session()
    finally:
        xvfb.stop()


@requires_deps
def test_tmux_main_horizontal_layout_structure(tmp_path):
    """Verify main-horizontal layout: one large pane on top, smaller ones below."""
    from vuln_recorder.xvfb import XvfbManager
    from vuln_recorder.terminal import TerminalOrchestrator

    xvfb = XvfbManager(width=640, height=480)
    display = xvfb.start()
    try:
        panes = [{'name': 'env'}, {'name': 'attacker'}, {'name': 'victim'}]
        term = TerminalOrchestrator(display, "smoke-lay", panes, "main-horizontal")
        term.create_session()

        r = subprocess.run(
            ["tmux", "-L", "vr-smoke-lay", "list-panes",
             "-t", "smoke-lay", "-F", "#{pane_height}"],
            capture_output=True, text=True,
        )
        heights = [int(h) for h in r.stdout.strip().split('\n')]
        assert len(heights) == 3
        assert heights[0] > heights[1], "First pane should be taller in main-horizontal"

        term.destroy_session()
    finally:
        xvfb.stop()


@requires_deps
def test_tmux_even_vertical_layout(tmp_path):
    """Verify even-vertical layout produces panes with equal height."""
    from vuln_recorder.xvfb import XvfbManager
    from vuln_recorder.terminal import TerminalOrchestrator

    xvfb = XvfbManager(width=640, height=480)
    display = xvfb.start()
    try:
        panes = [{'name': 'top'}, {'name': 'bottom'}]
        term = TerminalOrchestrator(display, "smoke-vert", panes, "even-vertical")
        term.create_session()

        r = subprocess.run(
            ["tmux", "-L", "vr-smoke-vert", "list-panes",
             "-t", "smoke-vert", "-F", "#{pane_height}"],
            capture_output=True, text=True,
        )
        heights = [int(h) for h in r.stdout.strip().split('\n')]
        assert len(heights) == 2
        assert abs(heights[0] - heights[1]) <= 1, "Panes should have equal height in even-vertical"

        term.destroy_session()
    finally:
        xvfb.stop()


@requires_deps
def test_tmux_send_keys_executes_in_correct_pane(tmp_path):
    """Verify commands go to the correct pane by writing unique markers."""
    from vuln_recorder.xvfb import XvfbManager
    from vuln_recorder.terminal import TerminalOrchestrator
    import time

    xvfb = XvfbManager(width=640, height=480)
    display = xvfb.start()
    try:
        panes = [{'name': 'left'}, {'name': 'right'}]
        term = TerminalOrchestrator(display, "smoke-keys", panes, "even-horizontal")
        term.create_session()

        term.send_keys("left", "echo MARKER_LEFT_123")
        term.send_keys("right", "echo MARKER_RIGHT_456")
        time.sleep(1)

        r = subprocess.run(
            ["tmux", "-L", "vr-smoke-keys", "capture-pane",
             "-t", "smoke-keys.1", "-p"],
            capture_output=True, text=True,
        )
        assert "MARKER_LEFT_123" in r.stdout

        r = subprocess.run(
            ["tmux", "-L", "vr-smoke-keys", "capture-pane",
             "-t", "smoke-keys.2", "-p"],
            capture_output=True, text=True,
        )
        assert "MARKER_RIGHT_456" in r.stdout

        term.destroy_session()
    finally:
        xvfb.stop()


@requires_deps
def test_tmux_comment_line_sent_to_terminal(tmp_path):
    """Verify # comment lines are sent to the terminal (visible but not executed)."""
    from vuln_recorder.xvfb import XvfbManager
    from vuln_recorder.terminal import TerminalOrchestrator
    import time

    xvfb = XvfbManager(width=640, height=480)
    display = xvfb.start()
    try:
        panes = [{'name': 'a'}]
        term = TerminalOrchestrator(display, "smoke-cmt", panes, "custom")
        term.create_session()

        term.send_keys("a", "# === Demo Comment Line ===")
        time.sleep(0.5)

        r = subprocess.run(
            ["tmux", "-L", "vr-smoke-cmt", "capture-pane",
             "-t", "smoke-cmt", "-p"],
            capture_output=True, text=True,
        )
        assert "# === Demo Comment Line ===" in r.stdout

        term.destroy_session()
    finally:
        xvfb.stop()


@requires_deps
def test_tmux_four_pane_custom_layout(tmp_path):
    """Verify 4-pane custom layout creates 4 panes."""
    from vuln_recorder.xvfb import XvfbManager
    from vuln_recorder.terminal import TerminalOrchestrator

    xvfb = XvfbManager(width=640, height=480)
    display = xvfb.start()
    try:
        panes = [{'name': 'a'}, {'name': 'b'}, {'name': 'c'}, {'name': 'd'}]
        term = TerminalOrchestrator(display, "smoke-4p", panes, "custom")
        term.create_session()

        r = subprocess.run(
            ["tmux", "-L", "vr-smoke-4p", "list-panes",
             "-t", "smoke-4p", "-F", "#{pane_index}"],
            capture_output=True, text=True,
        )
        pane_count = len(r.stdout.strip().split('\n'))
        assert pane_count == 4

        term.destroy_session()
    finally:
        xvfb.stop()


@requires_deps
def test_recording_with_even_vertical_layout(tmp_path):
    """Full recording pipeline with even-vertical layout."""
    path = FIXTURES / "even_vertical.yaml"
    output_dir = str(tmp_path / "out")

    r = subprocess.run(
        CLI + ["run", str(path), "--output", output_dir],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 0
    out_path = Path(r.stdout.split(":")[-1].strip())
    assert (out_path / "recording.mp4").exists()

    info = _ffprobe(out_path / "recording.mp4")
    assert info["streams"][0]["codec_name"] == "h264"


@requires_deps
def test_display_auto_increment(tmp_path):
    """Running two recordings simultaneously uses different displays."""
    path = FIXTURES / "single_pane.yaml"
    out_a = str(tmp_path / "a")
    out_b = str(tmp_path / "b")

    proc_a = subprocess.Popen(
        CLI + ["run", str(path), "--output", out_a],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    proc_b = subprocess.Popen(
        CLI + ["run", str(path), "--output", out_b],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    stdout_a, stderr_a = proc_a.communicate(timeout=60)
    stdout_b, stderr_b = proc_b.communicate(timeout=60)

    assert proc_a.returncode == 0, f"Run A failed: {stderr_a.decode()}"
    assert proc_b.returncode == 0, f"Run B failed: {stderr_b.decode()}"


@requires_deps
def test_xvfb_no_stale_lock_after_run(tmp_path):
    """Xvfb lock files from our run should be cleaned up after stop."""
    from vuln_recorder.xvfb import XvfbManager
    xvfb = XvfbManager(width=640, height=480)
    display = xvfb.start()
    import os, re
    display_num = re.search(r':(\d+)', display).group(1)
    lock = f"/tmp/.X{display_num}-lock"
    assert os.path.exists(lock), f"Lock file should exist while Xvfb is running: {lock}"
    xvfb.stop()
    assert not os.path.exists(lock), f"Lock file should be removed after stop: {lock}"
