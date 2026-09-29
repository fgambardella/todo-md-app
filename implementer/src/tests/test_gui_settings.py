"""GUI tests: settings window apply-on-Save + full-no-op Cancel.

Covers the task-35b scope on top of the 35a construction + pre-fill
tests: a valid Save persists the full payload (theme / lists dir /
completed-visible) and re-applies theme + completed filter live, an
invalid Save is blocked with a clear error (window stays open, nothing
persisted), an empty folder entry resets to the default dir, and
Cancel is a full no-op that only closes the window.
"""

import json
from unittest.mock import patch

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


def test_save_theme_persists_full_payload_and_reapplies(tmp_path):
    """Valid Save with a changed theme persists settings.json and re-applies
    the palette live (like the theme toggle)."""
    config_dir = tmp_path / "config"
    app = _build_app(tmp_path)
    try:
        app.root.update()
        assert not (config_dir / "settings.json").exists()

        app._open_settings()
        app.root.update()
        app._settings_theme_var.set("dark")
        app._settings_save_btn.invoke()
        app.root.update()

        data = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
        assert data == {"theme": "dark", "lists_dir": None, "completed_visible": 10}
        assert app.settings.theme == "dark"
        assert app.theme == "dark"
        # Palette re-applied live (fallback clam path on this machine).
        assert app._palette is not None
        assert app._palette["bg"] == "#1e1e1e"
        assert app._theme_btn.cget("text") == "☀️ Light"
        # Window closed after a successful Save.
        assert app.settings_window is None
    finally:
        _teardown(app)


def _seed_items(app, items) -> None:
    """Write items (text, done) into list 'L' and select it in the GUI."""
    app.controller.store.save("L", items)
    app.refresh_lists(select_first=True)


def test_save_completed_visible_persists_and_filters(tmp_path):
    """A changed completed_visible is persisted and the view hides completed
    items beyond the count live (0 hides all)."""
    config_dir = tmp_path / "config"
    app = _build_app(tmp_path)  # default completed_visible = 10
    items = [
        ("a", False), ("b", False),
        ("c", True), ("d", True), ("e", True), ("f", True),
    ]
    _seed_items(app, items)
    try:
        app.root.update()
        assert len(app._item_rows) == 6  # all visible under the default count

        # Save with completed_visible = 1: only 1 of the 4 completed stays.
        app._open_settings()
        app.root.update()
        app._settings_completed_var.set(1)
        app._settings_save_btn.invoke()
        app.root.update()

        data = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
        assert data["completed_visible"] == 1
        assert app.settings.completed_visible == 1
        assert len(app._item_rows) == 3  # 2 incomplete + 1 completed

        # Save with completed_visible = 0: all completed hidden.
        app._open_settings()
        app.root.update()
        app._settings_completed_var.set(0)
        app._settings_save_btn.invoke()
        app.root.update()

        data = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
        assert data["completed_visible"] == 0
        assert app.settings.completed_visible == 0
        assert len(app._item_rows) == 2  # only the incomplete items

        # Storage itself is untouched (display-only filter).
        assert app.controller.store.load("L") == items
        assert app.settings_window is None
    finally:
        _teardown(app)


def test_save_invalid_dir_shows_error_keeps_open_persists_nothing(tmp_path):
    """A lists folder that is not an existing dir and cannot be created
    (parent is a file) is blocked: showerror is called, the window stays
    open, and nothing is written to disk."""
    config_dir = tmp_path / "config"
    app = _build_app(tmp_path)
    blocker = tmp_path / "blocker"
    blocker.write_text("i am a file, not a directory", encoding="utf-8")
    invalid = str(blocker / "sub")
    try:
        app.root.update()

        app._open_settings()
        app.root.update()
        app._settings_lists_dir_var.set(invalid)

        with patch("tkinter.messagebox.showerror") as err:
            app._settings_save_btn.invoke()
            app.root.update()

        assert err.called
        args = err.call_args.args
        assert any(invalid in str(a) for a in args)
        # Window stays open on a failed Save.
        assert app.settings_window is not None
        assert app.settings_window.winfo_exists()
        # Nothing persisted; in-memory settings untouched.
        assert not (config_dir / "settings.json").exists()
        assert app.settings.theme == "system"
        assert app.settings.lists_dir is None
        assert app.settings.completed_visible == 10
    finally:
        _teardown(app)


def test_save_empty_dir_entry_persists_default_and_closes(tmp_path):
    """An empty folder entry means "reset to default": settings.json is
    written with lists_dir null and the window closes."""
    config_dir = tmp_path / "config"
    app = _build_app(tmp_path)
    try:
        app.root.update()

        app._open_settings()
        app.root.update()
        # Simulate the user clearing the entry (equivalent to a cleared
        # bound Entry widget).
        app._settings_lists_dir_var.set("")
        app._settings_save_btn.invoke()
        app.root.update()

        data = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
        assert data == {"theme": "system", "lists_dir": None, "completed_visible": 10}
        assert app.settings.lists_dir is None
        # Window closed after a successful Save.
        assert app.settings_window is None
    finally:
        _teardown(app)


def test_cancel_edits_are_a_full_noop(tmp_path):
    """Cancel after editing every control: nothing on disk, in-memory
    settings unchanged, window closed."""
    config_dir = tmp_path / "config"
    app = _build_app(tmp_path)
    try:
        app.root.update()
        app._open_settings()
        app.root.update()

        app._settings_lists_dir_var.set(str(tmp_path / "editeddir"))
        app._settings_theme_var.set("dark")
        app._settings_completed_var.set(3)
        app._settings_cancel_btn.invoke()
        app.root.update()

        assert not (config_dir / "settings.json").exists()
        assert app.settings.theme == "system"
        assert app.settings.lists_dir is None
        assert app.settings.completed_visible == 10
        assert app.settings_window is None
        # Only the settings window closed — the main window is still up.
        assert app.root.winfo_exists()
    finally:
        _teardown(app)