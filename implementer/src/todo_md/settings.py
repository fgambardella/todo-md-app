"""Headless settings configuration (stdlib only, no tkinter).

App settings are persisted as ``settings.json`` inside a dedicated config
directory (e.g. ``~/.todo-md-app/config``), separate from the Markdown
list files.  The file format is fully backward compatible with the
legacy single-key ``{"theme": "light"|"dark"}`` file: missing keys fall
back to their defaults, and a missing or corrupt file yields all
defaults without raising.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass

__all__ = [
    "SETTINGS_FILENAME",
    "VALID_THEMES",
    "DEFAULT_THEME",
    "DEFAULT_COMPLETED_VISIBLE",
    "Settings",
    "system_default_theme",
    "load_settings",
    "save_settings",
    "resolve_theme",
]

SETTINGS_FILENAME = "settings.json"
VALID_THEMES = ("light", "dark", "system")
DEFAULT_THEME = "system"
DEFAULT_COMPLETED_VISIBLE = 10


@dataclass
class Settings:
    """User preferences.

    ``lists_dir`` of ``None`` means the app default
    (``~/.todo-md-app/lists/``).  ``theme`` is one of ``VALID_THEMES``;
    ``"system"`` is resolved at display time (see :func:`resolve_theme`)
    and never persisted as a resolved value.  ``completed_visible`` is
    how many completed items stay visible (0 hides all completed).
    """

    theme: str = DEFAULT_THEME
    lists_dir: str | None = None
    completed_visible: int = DEFAULT_COMPLETED_VISIBLE


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


def load_settings(config_dir: str) -> Settings:
    """Read settings.json and return a :class:`Settings`.

    Never raises on read: a missing or corrupt file, wrong shapes, or
    invalid values all fall back to defaults (missing keys -> defaults,
    so the legacy ``{"theme": "light"|"dark"}`` file loads as-is).
    """
    theme = DEFAULT_THEME
    lists_dir: str | None = None
    completed_visible = DEFAULT_COMPLETED_VISIBLE
    try:
        with open(_settings_path(config_dir), "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            t = data.get("theme")
            if isinstance(t, str) and t in VALID_THEMES:
                theme = t
            ld = data.get("lists_dir")
            if isinstance(ld, str) and ld:
                lists_dir = ld
            cv = data.get("completed_visible")
            if isinstance(cv, int) and not isinstance(cv, bool) and cv >= 0:
                completed_visible = cv
    except (OSError, ValueError, TypeError):
        pass
    return Settings(theme=theme, lists_dir=lists_dir, completed_visible=completed_visible)


def save_settings(config_dir: str, settings: Settings) -> None:
    """Persist settings atomically (UTF-8); ValueError on invalid values.

    Writes exactly the keys ``theme``, ``lists_dir`` (``null`` when the
    default applies) and ``completed_visible``.
    """
    if settings.theme not in VALID_THEMES:
        raise ValueError(
            f"invalid theme: {settings.theme!r} (expected one of {VALID_THEMES})"
        )
    cv = settings.completed_visible
    if not isinstance(cv, int) or isinstance(cv, bool) or cv < 0:
        raise ValueError(
            f"completed_visible must be an int >= 0, got {cv!r}"
        )
    ld = settings.lists_dir
    if ld is not None and (not isinstance(ld, str) or not ld):
        raise ValueError(
            f"lists_dir must be a non-empty string or None (default), got {ld!r}"
        )
    payload = json.dumps(
        {
            "theme": settings.theme,
            "lists_dir": ld,
            "completed_visible": cv,
        }
    )
    _write_atomic(config_dir, payload)


def resolve_theme(settings: Settings) -> str:
    """Resolve the effective UI theme: 'light' or 'dark'.

    ``"system"`` is resolved via OS detection at call time and the
    resolved value is NOT persisted.
    """
    if settings.theme == "system":
        return system_default_theme()
    return settings.theme