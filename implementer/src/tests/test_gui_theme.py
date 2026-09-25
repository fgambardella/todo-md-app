"""GUI tests for the theme switcher (config persistence, toggle, readability)."""

import json

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore
from todo_md.theme import system_default_theme


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
        new_path = tmp_path / "config" / "settings.json"
        assert new_path.is_file()
        on_disk = json.loads(new_path.read_text(encoding="utf-8"))
        assert on_disk == {"theme": app.theme}
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
        assert on_disk == {"theme": "dark"}
        assert "Light" in app._theme_btn.cget("text")
        assert lum(root, app.items_frame.cget("bg")) < 0.5

        # dark -> light
        app._on_toggle_theme()
        root.update()
        assert app.theme == "light"
        on_disk = json.loads(new_path.read_text(encoding="utf-8"))
        assert on_disk == {"theme": "light"}
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

        _var, _cb, label, _del = app._item_rows[0]
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