"""GUI tests for the theme switcher (config persistence, toggle, readability)."""

import json
from unittest.mock import Mock, patch

import pytest

from tests.conftest import managed_tk_roots
from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore
from todo_md.settings import system_default_theme


def lum(root, color):
    """Luminance of a color name, normalized to 0..1."""
    r, g, b = root.winfo_rgb(color)
    scale = root.winfo_rgb("#ffffff")[0] or 1
    return (0.299 * r + 0.587 * g + 0.114 * b) / scale


def _build_app(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    return TodoApp(controller, config_dir=str(tmp_path / "config"))


def _write_config(tmp_path, theme):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "settings.json").write_text(
        json.dumps({"theme": theme}), encoding="utf-8"
    )


def _assert_input_caret_contrast(app, entry):
    from tkinter import ttk

    assert isinstance(entry, (ttk.Entry, ttk.Spinbox))
    style = ttk.Style(app.root)
    name = entry.cget("style") or entry.winfo_class()
    # ttk uses the insertcolor style option, not tk.Entry's insertbackground.
    caret = style.lookup(name, "insertcolor", entry.state())
    background = style.lookup(name, "fieldbackground", entry.state())
    assert caret, f"{name} has no explicit insertion color"
    assert background, f"{name} has no explicit field background"
    assert caret == app._palette["fg"]
    assert background == app._palette["entry_bg"]
    assert abs(lum(app.root, caret) - lum(app.root, background)) >= 0.5


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("entry_name", ["new_name_entry", "new_item_entry"])
def test_entry_caret_contrast_preserves_focused_editing(tmp_path, monkeypatch, theme, entry_name):
    _write_config(tmp_path, theme)
    errors = []
    with managed_tk_roots() as create_root:
        monkeypatch.setattr("tkinter.Tk", create_root)
        app = _build_app(tmp_path)
        app.root.report_callback_exception = lambda exc, val, tb: errors.append(val)
        app.root.update()
        entry = getattr(app, entry_name)
        placeholder = app._placeholders[entry]
        assert entry.get() == placeholder
        _assert_input_caret_contrast(app, entry)

        entry.focus_force()
        app.root.update()
        assert entry.get() == ""
        entry.insert(0, "draft")
        entry.icursor(2)
        opposite = "dark" if theme == "light" else "light"
        for expected_theme in (theme, opposite, theme):
            if app.theme != expected_theme:
                entry.selection_range(0, 1)
                app._theme_btn.invoke()
                app.root.update()
                assert (entry.index("sel.first"), entry.index("sel.last")) == (0, 1)
                entry.selection_clear()
            assert app.theme == expected_theme
            assert app.root.focus_get() is entry
            assert entry.instate(["focus", "!disabled", "!readonly"])
            assert entry.get() == "draft"
            assert entry.index("insert") == 2
            _assert_input_caret_contrast(app, entry)
            assert str(entry.cget("foreground")) == app._palette["fg"]
            entry.event_generate("<KeyPress>", keysym="x")
            app.root.update()
            assert entry.get() == "drxaft"
            entry.event_generate("<KeyPress>", keysym="BackSpace")
            app.root.update()
            assert entry.get() == "draft"
            for other, hint in app._placeholders.items():
                if other is not entry:
                    assert other.get() == hint
                    assert str(other.cget("foreground")) == app._palette["placeholder_fg"]

        entry.delete(0, "end")
        app.listbox.focus_force()
        app.root.update()
        assert entry.get() == placeholder
        assert str(entry.cget("foreground")) == app._palette["placeholder_fg"]
        _assert_input_caret_contrast(app, entry)
    assert errors == []


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_native_appearance_leaves_styles_untouched(theme):
    app = TodoApp.__new__(TodoApp)
    app.root = Mock()
    app._palette = None
    with patch("tkinter.ttk.Style") as style:
        app._apply_theme(theme)
    app.root.tk.call.assert_called_once_with("tk", "appappearance", theme)
    style.assert_not_called()
    app.root.config.assert_not_called()
    assert app._palette is None


def test_startup_dark(tmp_path):
    _write_config(tmp_path, "dark")
    app = _build_app(tmp_path)
    try:
        root = app.root
        root.update()
        assert app.theme == "dark"
        assert lum(root, app.items_frame.cget("bg")) < 0.5
    finally:
        app.root.destroy()


def test_startup_light(tmp_path):
    _write_config(tmp_path, "light")
    app = _build_app(tmp_path)
    try:
        root = app.root
        root.update()
        assert app.theme == "light"
        assert lum(root, app.items_frame.cget("bg")) > 0.5
    finally:
        app.root.destroy()


def test_first_start_detects_system_default(tmp_path):
    app = _build_app(tmp_path)
    try:
        app.root.update()
        expected = system_default_theme()
        assert app.theme == expected
        # The "system" default is resolved at display time and is never
        # persisted on a first start (settings.json is only written on change).
        assert app.settings.theme == "system"
        new_path = tmp_path / "config" / "settings.json"
        assert not new_path.is_file()
    finally:
        app.root.destroy()


def test_toggle_persists(tmp_path):
    _write_config(tmp_path, "light")
    app = _build_app(tmp_path)
    try:
        root = app.root
        root.update()
        new_path = tmp_path / "config" / "settings.json"

        # light -> dark
        app._on_toggle_theme()
        root.update()
        assert app.theme == "dark"
        on_disk = json.loads(new_path.read_text(encoding="utf-8"))
        assert on_disk == {
            "theme": "dark",
            "lists_dir": None,
            "completed_visible": 10,
        }
        assert "Light" in app._theme_btn.cget("text")
        assert lum(root, app.items_frame.cget("bg")) < 0.5

        # dark -> light
        app._on_toggle_theme()
        root.update()
        assert app.theme == "light"
        on_disk = json.loads(new_path.read_text(encoding="utf-8"))
        assert on_disk == {
            "theme": "light",
            "lists_dir": None,
            "completed_visible": 10,
        }
        assert lum(root, app.items_frame.cget("bg")) > 0.5
    finally:
        app.root.destroy()


def test_label_readability_after_switch(tmp_path):
    _write_config(tmp_path, "light")
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    controller.create_list("Read")
    controller.add_item("Read", "Unchecked")
    app = TodoApp(controller, config_dir=str(tmp_path / "config"))
    try:
        root = app.root
        app._select_list_name("Read")
        root.update()

        app._on_toggle_theme()  # light -> dark
        root.update()

        _var, _cb, label, _del, _edit = app._item_rows[0]
        fg = lum(root, label.cget("foreground"))
        bg = lum(root, label.cget("bg"))
        assert abs(fg - bg) >= 0.5
    finally:
        app.root.destroy()


def test_tentry_field_fill_follows_theme(tmp_path):
    from tkinter import ttk

    _write_config(tmp_path, "light")
    app = _build_app(tmp_path)
    try:
        root = app.root
        root.update()

        def field_lum():
            style = ttk.Style(root)
            return lum(root, style.lookup("TEntry", "fieldbackground"))

        # light (fresh start)
        assert app.theme == "light"
        assert field_lum() > 0.5

        # light -> dark (toggle)
        app._on_toggle_theme()
        root.update()
        assert app.theme == "dark"
        assert field_lum() < 0.5

        # dark -> light (toggle back)
        app._on_toggle_theme()
        root.update()
        assert app.theme == "light"
        assert field_lum() > 0.5
    finally:
        app.root.destroy()


def test_tentry_field_fill_dark_startup(tmp_path):
    from tkinter import ttk

    _write_config(tmp_path, "dark")
    app = _build_app(tmp_path)
    try:
        root = app.root
        root.update()
        style = ttk.Style(root)
        assert lum(root, style.lookup("TEntry", "fieldbackground")) < 0.5
    finally:
        app.root.destroy()


def test_entry_fill_lighter_than_listbox_dark(tmp_path):
    from tkinter import ttk

    _write_config(tmp_path, "dark")
    app = _build_app(tmp_path)
    try:
        root = app.root
        root.update()
        style = ttk.Style(root)

        # Dark palette: entry fill is a separate, lighter value than the list.
        assert style.lookup("TEntry", "fieldbackground") == "#383838"
        assert style.lookup("TEntry", "background") == "#383838"
        assert app.listbox.cget("bg") == "#2d2d2d"
        assert lum(root, style.lookup("TEntry", "fieldbackground")) > lum(
            root, app.listbox.cget("bg")
        )
    finally:
        app.root.destroy()


def test_entry_fill_and_listbox_light(tmp_path):
    from tkinter import ttk

    _write_config(tmp_path, "light")
    app = _build_app(tmp_path)
    try:
        root = app.root
        root.update()
        style = ttk.Style(root)

        # Light palette: entries and listbox both stay white.
        assert style.lookup("TEntry", "fieldbackground") == "#ffffff"
        assert app.listbox.cget("bg") == "#ffffff"
    finally:
        app.root.destroy()
