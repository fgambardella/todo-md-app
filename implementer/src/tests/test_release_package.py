"""Tests for ``scripts/release_package.sh``.

Fast static tests always run and keep the default suite quick. The full
build + zip integration test is expensive, so it is skipped unless the
environment variable ``RUN_RELEASE_TESTS=1`` is set:

    RUN_RELEASE_TESTS=1 .venv/bin/python -m pytest tests/test_release_package.py -v
"""

import hashlib
import os
import re
import subprocess
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SRC_DIR / "scripts" / "release_package.sh"
VERSION_FILE = SRC_DIR / "todo_md" / "VERSION"


def _current_version():
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def test_script_exists_and_is_executable():
    assert SCRIPT.is_file(), f"missing release package script: {SCRIPT}"
    assert os.access(SCRIPT, os.X_OK), (
        f"release package script is not executable: {SCRIPT}"
    )


def test_script_syntax_is_valid_bash():
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT)], capture_output=True, text=True
    )
    assert result.returncode == 0, f"bash -n failed:\n{result.stderr}"


def test_script_delegates_to_build_app_and_reads_version():
    content = SCRIPT.read_text(encoding="utf-8")
    assert "build_app.sh" in content, (
        "script must invoke build_app.sh to (re)build the bundle"
    )
    assert "VERSION" in content, "script must read the VERSION file"
    assert "arm64" in content, (
        "script must produce an -arm64 named release artifact"
    )
    assert "-arm64" in content, (
        "release zip name must carry the -arm64 suffix"
    )


def test_script_uses_ditto_for_zipping():
    content = SCRIPT.read_text(encoding="utf-8")
    assert "ditto" in content, "script must zip the bundle via macOS ditto"
    assert "-c -k" in content, "script must use ditto in create-archive mode"
    assert "--noextattr" in content, (
        "script must pass --noextattr to avoid __MACOSX junk entries"
    )
    assert "--noqtn" in content, (
        "script must pass --noqtn so the zip carries no .DS_Store/AppleDouble"
    )


@pytest.mark.skipif(
    os.environ.get("RUN_RELEASE_TESTS") != "1",
    reason="full release integration test only runs with RUN_RELEASE_TESTS=1",
)
def test_full_release_package_produces_valid_zip():
    """Run the real build + packaging, then inspect the resulting zip."""
    release = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=SRC_DIR,
        timeout=900,
    )
    assert release.returncode == 0, (
        f"release packaging failed (rc={release.returncode})\n"
        f"--- stdout ---\n{release.stdout}\n--- stderr ---\n{release.stderr}"
    )

    version = _current_version()
    zip_path = SRC_DIR / "dist" / f"todo-md-{version}-arm64.zip"
    assert zip_path.is_file(), (
        f"release zip missing for current VERSION {version!r}: {zip_path}"
    )

    listing = subprocess.run(
        ["unzip", "-l", str(zip_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "todo-md.app/Contents/MacOS/todo-md" in listing.stdout, (
        "todo-md.app must sit at the zip root "
        f"(expected entry 'todo-md.app/Contents/MacOS/todo-md'):\n"
        f"{listing.stdout}"
    )
    assert "__MACOSX" not in listing.stdout, (
        f"zip must not contain __MACOSX entries:\n{listing.stdout}"
    )

    expected_sha256 = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    assert expected_sha256 in release.stdout, (
        "script stdout must report the zip SHA-256:\n"
        f"expected {expected_sha256}\n"
        f"--- stdout ---\n{release.stdout}"
    )
    assert re.search(r"^[0-9a-f]{64}$", expected_sha256), (
        "sanity: computed digest must be a 64-char sha256 hex string"
    )