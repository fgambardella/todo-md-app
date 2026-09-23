"""Headless theme configuration (stdlib only, no tkinter).

The theme choice is persisted as ``config.json`` INSIDE the lists data dir,
next to the ``.md`` list files (safe: ``MarkdownListStore.lists()`` only
picks up ``.md`` files).
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile

__all__ = ["CONFIG_FILENAME", "VALID_THEMES", "system_default_theme", "load_theme", "save_theme"]

CONFIG_FILENAME = "config.json"
VALID_THEMES = ("light", "dark")


def system_default_theme() -> str:
    """Detect the OS default UI theme; returns 'dark' or 'light'."""
    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip().lower() == "dark":
            return "dark"
    except Exception:
        pass
    return "light"


def _config_path(data_dir: str) -> str:
    return os.path.join(data_dir, CONFIG_FILENAME)


def _write_atomic(data_dir: str, payload: str) -> None:
    """Write payload to config.json atomically (temp file + os.replace)."""
    os.makedirs(data_dir, exist_ok=True)
    path = _config_path(data_dir)
    fd, tmp_path = tempfile.mkstemp(dir=data_dir, prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload)
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def load_theme(data_dir: str) -> str:
    """Return the stored theme, or detect + persist the system default.

    Falls back to ``system_default_theme()`` (and atomically rewrites
    ``config.json``) on first start, corrupt JSON, wrong shape, or an
    invalid theme value.
    """
    path = _config_path(data_dir)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            theme = data["theme"]
            if theme in VALID_THEMES:
                return theme
        except (OSError, ValueError, KeyError, TypeError):
            pass
    theme = system_default_theme()
    _write_atomic(data_dir, json.dumps({"theme": theme}))
    return theme


def save_theme(data_dir: str, theme: str) -> None:
    """Persist the theme choice atomically; ValueError if invalid."""
    if theme not in VALID_THEMES:
        raise ValueError(f"invalid theme: {theme!r} (expected one of {VALID_THEMES})")
    _write_atomic(data_dir, json.dumps({"theme": theme}))
