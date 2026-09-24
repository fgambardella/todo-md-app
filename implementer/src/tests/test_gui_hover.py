"""GUI tests for TButton active/pressed state colors (dark-mode hover fix).

Regression: on the clam fallback path, clam's default 'activeBackground'
state stays light, so hovering a button in dark mode flashed a light fill
that hid the light text. _apply_theme must map the active/pressed states
to a slightly darker fill than the normal button background while keeping
the palette foreground.
"""

import json

import pytest

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def lum(root, color):
    """Luminance of a color name, normalized to 0..1."""
    r, g, b = root.winfo_rgb(color)
    scale = root.winfo_rgb("#ffffff")[0] or 1
    return (0.299 * r + 0.587 * g + 0.114 * b) / scale


def _build_app(tmp_path, theme):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "settings.json").write_text(
        json.dumps({"theme": theme}), encoding="utf-8"
    )
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    return TodoApp(controller, config_dir=str(config_dir))


@pytest.mark.parametrize(
    ("theme", "btn_bg", "fg"),
    [("dark", "#3c3c3c", "#f0f0f0"), ("light", "#e0e0e0", "#000000")],
)
def test_button_active_state_darker_fg_unchanged(tmp_path, theme, btn_bg, fg):
    app = _build_app(tmp_path, theme)
    try:
        root = app.root
        root.update()
        from tkinter import ttk

        style = ttk.Style(root)
        normal_bg = style.lookup("TButton", "background")
        normal_fg = style.lookup("TButton", "foreground")
        active_bg = style.lookup("TButton", "background", ("active",))
        pressed_bg = style.lookup("TButton", "background", ("pressed",))
        active_fg = style.lookup("TButton", "foreground", ("active",))
        pressed_fg = style.lookup("TButton", "foreground", ("pressed",))

        # Normal (non-hover) appearance is unchanged for this theme.
        assert abs(lum(root, normal_bg) - lum(root, btn_bg)) < 0.02
        assert abs(lum(root, normal_fg) - lum(root, fg)) < 0.02

        # Active/pressed fills are darker than the normal background.
        assert lum(root, active_bg) < lum(root, normal_bg)
        assert lum(root, pressed_bg) < lum(root, normal_bg)

        # Text stays the palette foreground in the hovered states.
        assert abs(lum(root, active_fg) - lum(root, fg)) < 0.02
        assert abs(lum(root, pressed_fg) - lum(root, fg)) < 0.02

        # Force a real button into the active state and re-probe.
        button = app._theme_btn
        button.state(["active"])
        root.update()
        active_bg = style.lookup("TButton", "background", ("active",))
        assert lum(root, active_bg) < lum(root, normal_bg)
        button.state(["!active"])
        root.update()
    finally:
        app.root.destroy()
