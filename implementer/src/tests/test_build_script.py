"""Tests for ``scripts/build_app.sh``.

Fast static tests always run and keep the default suite quick. The full
build + bundle-launch integration test is expensive, so it is skipped
unless the environment variable ``RUN_BUILD_TESTS=1`` is set:

    RUN_BUILD_TESTS=1 .venv/bin/python -m pytest tests/test_build_script.py -v
"""

import os
import subprocess
import time
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SRC_DIR / "scripts" / "build_app.sh"
APP_BIN = SRC_DIR / "dist" / "todo-md.app" / "Contents" / "MacOS" / "todo-md"


def test_script_exists_and_is_executable():
    assert SCRIPT.is_file(), f"missing build script: {SCRIPT}"
    assert os.access(SCRIPT, os.X_OK), f"build script is not executable: {SCRIPT}"


def test_script_syntax_is_valid_bash():
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT)], capture_output=True, text=True
    )
    assert result.returncode == 0, f"bash -n failed:\n{result.stderr}"


def test_script_contains_arm64_host_guard():
    content = SCRIPT.read_text(encoding="utf-8")
    assert "uname -m" in content, "script must probe the host architecture"
    assert "arm64" in content, "script must guard on arm64 (Apple Silicon)"


@pytest.mark.skipif(
    os.environ.get("RUN_BUILD_TESTS") != "1",
    reason="full build integration test only runs with RUN_BUILD_TESTS=1",
)
def test_full_build_produces_launchable_bundle():
    """Run the real build, then launch the bundle and verify it survives."""
    build = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=SRC_DIR,
        timeout=600,
    )
    assert build.returncode == 0, (
        f"build failed (rc={build.returncode})\n"
        f"--- stdout ---\n{build.stdout}\n--- stderr ---\n{build.stderr}"
    )
    assert APP_BIN.is_file(), f"bundle executable missing: {APP_BIN}"
    assert os.access(APP_BIN, os.X_OK), f"bundle executable not runnable: {APP_BIN}"

    proc = subprocess.Popen(
        [str(APP_BIN)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
    )
    try:
        time.sleep(3)
        assert proc.poll() is None, (
            "bundle process exited within 3s of launch:\n"
            f"{proc.stderr.read().decode('utf-8', errors='replace')}"
        )
    finally:
        if proc.poll() is None:
            proc.terminate()
        try:
            stderr = proc.communicate(timeout=15)[1]
        except subprocess.TimeoutExpired:
            proc.kill()
            stderr = proc.communicate()[1]
    assert b"Traceback" not in stderr, (
        f"traceback in bundle stderr:\n{stderr.decode('utf-8', errors='replace')}"
    )