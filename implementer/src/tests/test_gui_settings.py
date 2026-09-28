"""GUI tests: Settings button opens a pre-filled Toplevel settings window.

Covers the construction + pre-fill + wiring scope of task-35a: the button
exists on the main window, the Toplevel opens and closes cleanly, every
control group is present and pre-filled from the current in-memory
settings, and nothing is written to disk (Save/Cancel are stubs here).
"""

import json

from todo_md.app import DEFAULT_DATA_DIR, TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def _build_app(tmp_path, settings: dict | None = None) -> TodoApp:
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    if settings is not None:
        (config_dir / "settings.json").write_text(
            json.dumps(settings), encoding="utf-8"
        )
    return TodoApp(controller, config_dir=str(config_dir))


def _teardown(app: TodoApp) -> None:
    # GUI-test quirk: always update before destroying the root.
    app.root.update()
    app.root.destroy()


def test_settings_button_exists_and_opens_toplevel(tmp_path):
    app = _build_app(tmp_path)
    try:
        app.root.update()
        assert app._settings_btn is not None
        assert app._settings_btn.cget("text") == "Settings"

        import tkinter as tk

        assert app.settings_window is None
        app._settings_btn.invoke()
        app.root.update()

        win = app.settings_window
        assert win is not None and win.winfo_exists()
        assert isinstance(win, tk.Toplevel)
        assert win.master is app.root
        assert win.title() == "Settings"
    finally:
        _teardown(app)


def test_settings_window_opens_once(tmp_path):
    app = _build_app(tmp_path)
    try:
        app.root.update()
        app._open_settings()
        app.root.update()
        first = app.settings_window
        app._open_settings()  # must lift the existing window, not duplicate
        app.root.update()
        assert app.settings_window is first
    finally:
        _teardown(app)


def test_settings_window_closes_cleanly(tmp_path):
    app = _build_app(tmp_path)
    try:
        app.root.update()
        app._open_settings()
        app.root.update()
        win = app.settings_window
        assert win.winfo_exists()

        # Cancel closes the window cleanly.
        app._settings_cancel_btn.invoke()
        app.root.update()
        assert not win.winfo_exists()
        assert app.settings_window is None

        # The window can be reopened afterwards.
        app._open_settings()
        app.root.update()
        assert app.settings_window is not None
        assert app.settings_window.winfo_exists()
    finally:
        _teardown(app)


def test_settings_prefill_defaults(tmp_path):
    """No settings file -> app defaults pre-fill the controls."""
    app = _build_app(tmp_path)
    try:
        app.root.update()
        app._open_settings()
        app.root.update()

        assert app._settings_lists_dir_var.get() == DEFAULT_DATA_DIR
        assert app._settings_theme_var.get() == "system"
        assert app._settings_completed_var.get() == 10
        selected = [
            r.cget("value") for r in app._settings_theme_rads if r.instate(["selected"])
        ]
        assert selected == ["system"]
    finally:
        _teardown(app)


def test_settings_prefill_custom_settings(tmp_path):
    """Controls are pre-filled from the current in-memory settings."""
    custom = str(tmp_path / "customlists")
    app = _build_app(
        tmp_path, {"theme": "dark", "lists_dir": custom, "completed_visible": 5}
    )
    try:
        app.root.update()
        # Sanity: the in-memory settings match what we wrote.
        assert app.settings.theme == "dark"
        assert app.settings.lists_dir == custom
        assert app.settings.completed_visible == 5

        app._open_settings()
        app.root.update()

        # (a) lists-folder entry shows the effective (custom) data dir.
        assert app._settings_lists_dir_var.get() == custom

        # (b) theme radiobuttons reflect the saved theme.
        assert [r.cget("value") for r in app._settings_theme_rads] == [
            "system",
            "light",
            "dark",
        ]
        selected = [
            r.cget("value") for r in app._settings_theme_rads if r.instate(["selected"])
        ]
        assert selected == ["dark"]

        # (c) spinbox range and pre-filled value.
        assert int(app._settings_spinbox.cget("from")) == 0
        assert int(app._settings_spinbox.cget("to")) == 999
        assert app._settings_completed_var.get() == 5

        # Editing a var is reflected in the bound widgets.
        app._settings_theme_var.set("light")
        app.root.update()
        selected = [
            r.cget("value") for r in app._settings_theme_rads if r.instate(["selected"])
        ]
        assert selected == ["light"]
    finally:
        _teardown(app)


def test_settings_reset_to_default(tmp_path):
    custom = str(tmp_path / "custom")
    app = _build_app(tmp_path, {"lists_dir": custom})
    try:
        app.root.update()
        app._open_settings()
        app.root.update()
        assert app._settings_lists_dir_var.get() == custom

        app._settings_reset_btn.invoke()
        app.root.update()
        assert app._settings_lists_dir_var.get() == DEFAULT_DATA_DIR
    finally:
        _teardown(app)


def test_settings_opening_and_save_write_nothing(tmp_path):
    """This task must not write settings: open, edit, Save -> no disk write,
    and the in-memory settings stay untouched."""
    config_dir = tmp_path / "config"
    app = _build_app(tmp_path)
    try:
        app.root.update()
        assert not (config_dir / "settings.json").exists()

        app._open_settings()
        app.root.update()
        app._settings_lists_dir_var.set(str(tmp_path / "newdir"))
        app._settings_theme_var.set("light")
        app._settings_completed_var.set(3)

        app._settings_save_btn.invoke()
        app.root.update()

        assert not (config_dir / "settings.json").exists()
        assert app.settings.theme == "system"
        assert app.settings.lists_dir is None
        assert app.settings.completed_visible == 10
    finally:
        _teardown(app)