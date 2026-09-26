"""Headless version loader.

Reads the VERSION file that sits alongside the package. No tkinter or GUI
dependencies — safe to import without a display.
"""

from pathlib import Path

__all__ = ["VERSION_PATH", "get_version"]

# Module-level constant so tests can monkeypatch it.
VERSION_PATH: Path = Path(__file__).resolve().parent / "VERSION"


def get_version() -> str:
    """Return the package version string.

    Reads ``VERSION_PATH`` (stripped). Returns ``"0.0.0"`` if the file is
    missing or unreadable.
    """
    try:
        return VERSION_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0"