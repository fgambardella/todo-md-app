"""Headless theme configuration (stdlib only, no tkinter).

The theme choice is persisted as ``settings.json`` inside a dedicated
config directory (e.g. ``~/.todo-md-app/config``), separate from the
Markdown list files.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile

__all__ = [
    "SETTINGS_FILENAME",
    "VALID_THEMES",
    "system_default_theme",
    "load_theme",
    "save_theme",
    "migrate_legacy_config",
]

SETTINGS_FILENAME = "settings.json"
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


def _settings_path(config_dir: str) -> str:
    return os.path.join(config_dir, SETTINGS_FILENAME)


def _write_atomic(config_dir: str, payload: str) -> None:
    """Write payload to settings.json atomically (temp file + os.replace)."""
    os.makedirs(config_dir, exist_ok=True)
    path = _settings_path(config_dir)
    fd, tmp_path = tempfile.mkstemp(dir=config_dir, prefix=".tmp-", suffix=".json")
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


def load_theme(config_dir: str) -> str:
    """Return the stored theme, or detect + persist the system default.

    Falls back to ``system_default_theme()`` (and atomically rewrites
    ``settings.json``) on first start, corrupt JSON, wrong shape, or an
    invalid theme value.
    """
    path = _settings_path(config_dir)
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
    _write_atomic(config_dir, json.dumps({"theme": theme}))
    return theme


def save_theme(config_dir: str, theme: str) -> None:
    """Persist the theme choice atomically; ValueError if invalid."""
    if theme not in VALID_THEMES:
        raise ValueError(f"invalid theme: {theme!r} (expected one of {VALID_THEMES})")
    _write_atomic(config_dir, json.dumps({"theme": theme}))


def migrate_legacy_config(config_dir: str, legacy_path: str) -> None:
    """One-time migration of the legacy ``<lists>/config.json`` theme file.

    If ``legacy_path`` exists and ``<config_dir>/settings.json`` does not
    yet, the legacy file is read; when it parses and its ``theme`` value
    is valid, ``{"theme": t}`` is atomically written to the new file and
    the legacy file is deleted. A corrupt or invalid legacy file is left
    in place untouched. Never touches list ``.md`` files.
    """
    if not os.path.isfile(legacy_path):
        return
    if os.path.isfile(_settings_path(config_dir)):
        return
    try:
        with open(legacy_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        theme = data["theme"]
        if theme not in VALID_THEMES:
            return
    except (OSError, ValueError, KeyError, TypeError):
        return
    _write_atomic(config_dir, json.dumps({"theme": theme}))
    os.remove(legacy_path)