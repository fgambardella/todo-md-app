"""Tests for the headless version loader (no display required)."""

from pathlib import Path

import todo_md
from todo_md import version


def test_get_version_matches_version_file():
    on_disk = (Path(version.__file__).parent / "VERSION").read_text(encoding="utf-8").strip()
    assert todo_md.get_version() == on_disk


def test_get_version_fallback_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(version, "VERSION_PATH", tmp_path / "does_not_exist_VERSION")
    assert version.get_version() == "0.0.0"


def test_get_version_strips_surrounding_whitespace(tmp_path, monkeypatch):
    vf = tmp_path / "VERSION"
    vf.write_text("\n  1.2.3  \n\n", encoding="utf-8")
    monkeypatch.setattr(version, "VERSION_PATH", vf)
    assert version.get_version() == "1.2.3"