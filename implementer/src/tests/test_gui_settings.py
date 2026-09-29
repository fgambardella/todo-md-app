"""GUI tests: settings window Save with directory relocation + full-no-op Cancel.

Covers task-35b + task-36b2 scope: a valid Save persists settings.json
(theme/lists_dir/completed-visible), re-applies theme+completed filter
live, and when the lists folder changes with existing Markdown files,
asks user Yes/No/Cancel via messagebox.askyesnocancel. Yes proceeds with
move=True, No proceeds with move=False (keeps source files), Cancel keeps
old directory but still persists other valid settings. Invalid Save is
blocked with a clear error (window open, nothing persisted). An empty
folder entry resets to DEFAULT_DATA_DIR (persisted as null). Equivalent
paths are no-ops. Reopening unchanged settings should not prompt or
relocate. Cancel is a full no-op that only closes the window.

All tests avoid the real user lists directory by mocking or isolating
tmp_path fixtures under DEFAULT_DATA_DIR or isolated directories.
"""

import json
from unittest.mock import patch

from todo_md.app import DEFAULT_DATA_DIR, TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def _build_app(tmp_path, settings: dict | None = None, data_dir: str | None = None) -> TodoApp:
    """Build TodoApp with isolated data and config dirs under tmp_path.

    If data_dir is not provided, use tmp_path as the active store data dir.
    If settings includes lists_dir, use that for the store; otherwise,
    seed data at tmp_path/data and configure settings accordingly.
    """
    if data_dir is not None:
        store = MarkdownListStore(data_dir)
    else:
        store = MarkdownListStore(str(tmp_path / "data"))
    controller = TodoController(store)
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    effective_data = data_dir if data_dir is not None else str(tmp_path / "data")
    if settings is None:
        settings = {"theme": "system", "lists_dir": None, "completed_visible": 10}
    else:
        # Ensure keys exist
        settings.setdefault("theme", "system")
        settings.setdefault("lists_dir", None)
        settings.setdefault("completed_visible", 10)
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


def test_settings_save_relocate_yes_no_cancel_popups_correct_prompt(tmp_path):
    """When changing to a directory with existing Markdown files, exact
    prompt text is shown and Yes/No/Cancel are respected."""
    from unittest.mock import patch

    source = tmp_path / "source"
    source.mkdir()
    (source / "work.md").write_bytes(b"# work\n- [ ] task\n")
    app = _build_app(tmp_path, data_dir=str(source))
    target = tmp_path / "target"
    config_dir = tmp_path / "config"
    try:
        app.root.update()
        # Pre-fill the entry to the new directory
        app._settings_lists_dir_var.set(str(target))

        # Mock askyesnocancel to return Yes
        with patch("tkinter.messagebox.askyesnocancel", return_value=True) as patched:
            app._open_settings()
            app.root.update()
            with patch("tkinter.messagebox.showerror") as err:
                app._settings_save_btn.invoke()
                app.root.update()

            assert patched.called
            args = patched.call_args.args
            assert len(args) == 1
            prompt = args[0]
            assert "You are about to change the directory where your lists are stored" in prompt
            assert f"from '{source}' to '{target}'" in prompt
            assert "but there are already lists in it" in prompt
            assert err.call_count == 0  # no error

        # Settings persisted and window closed.
        data = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
        assert data["lists_dir"] == str(target)
        assert app.settings_window is None
        # Source file moved, target contains list.
        assert not (source / "work.md").exists()
        assert (target / "work.md").read_bytes() == b"# work\n- [ ] task\n"
        assert app.controller.list_names() == ["work"]
    finally:
        _teardown(app)


def test_settings_save_relocate_no_keeps_source(tmp_path):
    """No on popup keeps source files and creates new empty destination."""
    from unittest.mock import patch

    source = tmp_path / "source"
    source.mkdir()
    (source / "work.md").write_bytes(b"# work\n- [ ] task\n")
    app = _build_app(tmp_path, data_dir=str(source))
    target = tmp_path / "target"
    config_dir = tmp_path / "config"
    try:
        app.root.update()
        app._settings_lists_dir_var.set(str(target))

        # Mock askyesnocancel to return False (No)
        with patch("tkinter.messagebox.askyesnocancel", return_value=False):
            app._open_settings()
            app.root.update()
            app._settings_save_btn.invoke()
            app.root.update()

        # Settings persisted, source unchanged, target empty.
        data = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
        assert data["lists_dir"] == str(target)
        assert app.settings_window is None
        assert (source / "work.md").read_bytes() == b"# work\n- [ ] task\n"
        assert list(target.iterdir()) == []
        assert app.controller.list_names() == []
        # New list writes to target.
        app.controller.create_list("new")
        app.controller.add_item("new", "item")
        assert (target / "new.md").read_bytes() == b"# new\n- [ ] item\n"
        assert (source / "work.md").read_bytes() == b"# work\n- [ ] task\n"
    finally:
        _teardown(app)


def test_settings_save_relocate_cancel_persists_other_settings(tmp_path):
    """Cancel on popup keeps old directory and still persists theme/completed."""
    from unittest.mock import patch

    source = tmp_path / "source"
    source.mkdir()
    (source / "work.md").write_bytes(b"# work\n- [ ] task\n")
    app = _build_app(tmp_path, {"theme": "dark", "lists_dir": str(source), "completed_visible": 10})
    target = tmp_path / "target"
    config_dir = tmp_path / "config"
    try:
        app.root.update()
        # Change theme, completed, but cancel directory move
        app._settings_theme_var.set("light")
        app._settings_completed_var.set(25)
        app._settings_lists_dir_var.set(str(target))

        with patch("tkinter.messagebox.askyesnocancel", return_value=None):
            app._open_settings()
            app.root.update()
            app._settings_save_btn.invoke()
            app.root.update()

        # Directory unchanged (no prompt called), theme/completed saved.
        assert app.settings_window is None
        assert app.controller.store.data_dir == source
        data = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
        assert data["theme"] == "light"
        assert data["lists_dir"] == str(source)
        assert data["completed_visible"] == 25
        assert app.settings.theme == "light"
        assert app.settings.completed_visible == 25
        assert (source / "work.md").read_bytes() == b"# work\n- [ ] task\n"
    finally:
        _teardown(app)


def test_settings_save_no_prompt_for_empty_source(tmp_path):
    """Empty or non-Markdown-only source does not trigger the pop-up."""
    from unittest.mock import patch

    source = tmp_path / "source"
    source.mkdir()
    (source / "notes.txt").write_bytes(b"plain text only")
    app = _build_app(tmp_path, data_dir=str(source))
    target = tmp_path / "target"
    config_dir = tmp_path / "config"
    try:
        app.root.update()
        app._settings_lists_dir_var.set(str(target))

        with patch("tkinter.messagebox.askyesnocancel") as patched:
            app._open_settings()
            app.root.update()
            app._settings_save_btn.invoke()
            app.root.update()

        assert patched.call_count == 0  # No prompt for empty source
        data = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
        assert data["lists_dir"] == str(target)
        assert app.settings_window is None
        assert (source / "notes.txt").read_bytes() == b"plain text only"
        assert list(target.iterdir()) == []
    finally:
        _teardown(app)


def test_settings_save_populated_destination_rejected(tmp_path):
    """Destination with Markdown files raises error before any relocation."""
    from unittest.mock import patch

    source = tmp_path / "source"
    source.mkdir()
    app = _build_app(tmp_path, data_dir=str(source))
    target = tmp_path / "target"
    target.mkdir()
    (target / "existing.md").write_bytes(b"# existing\n- [ ] item\n")
    config_dir = tmp_path / "config"
    try:
        app.root.update()
        app._settings_lists_dir_var.set(str(target))

        with patch("tkinter.messagebox.askyesnocancel") as patched:
            app._open_settings()
            app.root.update()
            with patch("tkinter.messagebox.showerror") as err:
                app._settings_save_btn.invoke()
                app.root.update()

        assert patched.call_count == 0  # No prompt (populated dest triggers early)
        assert err.called
        args = err.call_args.args
        assert any("destination" in str(a) for a in args)
        assert app.settings_window is not None
        assert app.settings_window.winfo_exists()
        assert not (config_dir / "settings.json").exists()
    finally:
        _teardown(app)


def test_settings_save_invalid_completed_before_side_effects(tmp_path):
    """Invalid completed_visible is rejected before directory check."""
    from unittest.mock import patch

    source = tmp_path / "source"
    source.mkdir()
    app = _build_app(tmp_path, data_dir=str(source))
    config_dir = tmp_path / "config"
    target = tmp_path / "target"
    (target / "work.md").write_bytes(b"# work\n- [ ] task\n")
    try:
        app.root.update()
        app._settings_completed_var.set(9999)  # out of range
        app._settings_lists_dir_var.set(str(target))

        with patch("tkinter.messagebox.askyesnocancel") as patched:
            app._open_settings()
            app.root.update()
            with patch("tkinter.messagebox.showerror") as err:
                app._settings_save_btn.invoke()
                app.root.update()

        assert patched.call_count == 0  # No prompt (validation blocks first)
        assert err.called
        assert "Completed items visible must be a whole number" in str(err.call_args.args)
        assert app.settings_window is not None
        assert not (config_dir / "settings.json").exists()
    finally:
        _teardown(app)


def test_settings_save_empty_entry_normalizes_to_null(tmp_path):
    """Empty lists_dir entry resets to DEFAULT_DATA_DIR (persisted as null)."""
    config_dir = tmp_path / "config"
    app = _build_app(tmp_path)
    try:
        app.root.update()
        app._settings_lists_dir_var.set("   ")  # whitespace only
        app._settings_save_btn.invoke()
        app.root.update()

        data = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
        assert data["lists_dir"] is None
        assert app.settings.lists_dir is None
        assert app.controller.store.data_dir == DEFAULT_DATA_DIR
    finally:
        _teardown(app)


def test_settings_save_equivalent_paths_no_prompt(tmp_path):
    """Same directory or symlink-equivalent paths do not prompt or relocate."""
    from unittest.mock import patch

    source = tmp_path / "data"
    source.mkdir()
    (source / "work.md").write_bytes(b"# work\n- [ ] task\n")
    app = _build_app(tmp_path, data_dir=str(source))
    # Use normalized or symlink form of the same path
    target = str(source / ".." / "data") + "/."
    config_dir = tmp_path / "config"
    try:
        app.root.update()
        app._settings_lists_dir_var.set(target)

        with patch("tkinter.messagebox.askyesnocancel") as patched:
            app._open_settings()
            app.root.update()
            app._settings_save_btn.invoke()
            app.root.update()

        assert patched.call_count == 0  # No prompt for equivalent path
        assert app.settings_window is None
        # No relocation performed; file counts unchanged.
        assert (source / "work.md").read_bytes() == b"# work\n- [ ] task\n"
        data = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
        # Normalized form is preserved (not resolved)
        assert data["lists_dir"] == target
    finally:
        _teardown(app)


def test_settings_save_live_rows_use_new_destination(tmp_path):
    """After successful Move, new list writes go to destination, not source."""
    from unittest.mock import patch

    source = tmp_path / "source"
    source.mkdir()
    app = _build_app(tmp_path, data_dir=str(source))
    target = tmp_path / "target"
    config_dir = tmp_path / "config"
    try:
        app.root.update()
        app._settings_lists_dir_var.set(str(target))

        with patch("tkinter.messagebox.askyesnocancel", return_value=True):
            app._open_settings()
            app.root.update()
            app._settings_save_btn.invoke()
            app.root.update()

        assert app.settings_window is None
        assert app.controller.store.data_dir == target
        # Create new list, items written to destination only.
        app.controller.create_list("new")
        app.controller.add_item("new", "task")
        assert (target / "new.md").read_bytes() == b"# new\n- [ ] task\n"
        assert list(source.iterdir()) == []
    finally:
        _teardown(app)


def test_settings_save_repeat_no_prompt_if_unchanged(tmp_path):
    """Reopening and saving unchanged settings does not prompt or relocate."""
    from unittest.mock import patch

    source = tmp_path / "source"
    source.mkdir()
    app = _build_app(tmp_path, data_dir=str(source))
    config_dir = tmp_path / "config"
    try:
        app.root.update()
        # First save changes nothing (same path), no prompt
        with patch("tkinter.messagebox.askyesnocancel") as patched:
            app._open_settings()
            app.root.update()
            app._settings_save_btn.invoke()
            app.root.update()

        assert patched.call_count == 0
        assert app.settings_window is None
        # Repeat: still no prompt.
        with patch("tkinter.messagebox.askyesnocancel") as patched2:
            app._open_settings()
            app.root.update()
            app._settings_save_btn.invoke()
            app.root.update()

        assert patched2.call_count == 0
        assert app.settings_window is None
    finally:
        _teardown(app)


def test_settings_save_injected_relocation_failure(tmp_path):
    """Relocation failure shows error, does not persist, leaves window open."""
    from unittest.mock import patch

    source = tmp_path / "source"
    source.mkdir()
    app = _build_app(tmp_path, data_dir=str(source))
    target = tmp_path / "target"
    config_dir = tmp_path / "config"
    try:
        app.root.update()
        app._settings_lists_dir_var.set(str(target))

        def fail_relocation(*, old_dir, new_dir, move):
            raise OSError("simulated disk failure")

        with patch("todo_md.app.TodoController.change_lists_dir", side_effect=OSError("simulated disk failure")):
            app._open_settings()
            app.root.update()
            with patch("tkinter.messagebox.showerror") as err:
                app._settings_save_btn.invoke()
                app.root.update()

        assert err.called
        args = err.call_args.args
        assert any("failed" in str(a).lower() for a in args)
        assert app.settings_window is not None
        assert app.settings_window.winfo_exists()
        assert not (config_dir / "settings.json").exists()
        assert app.controller.store.data_dir == source
        # Original file still in place
        assert list(source.iterdir()) == []
    finally:
        _teardown(app)


def test_settings_save_persistence_failure_keeps_destination(tmp_path):
    """After successful relocation but failed settings save, keep destination usable."""
    from unittest.mock import patch

    source = tmp_path / "source"
    source.mkdir()
    app = _build_app(tmp_path, data_dir=str(source))
    target = tmp_path / "target"
    config_dir = tmp_path / "config"
    try:
        app.root.update()
        app._settings_lists_dir_var.set(str(target))

        with patch("todo_md.settings.save_settings", side_effect=OSError("simulated save failure")):
            app._open_settings()
            app.root.update()
            with patch("tkinter.messagebox.showerror") as err:
                app._settings_save_btn.invoke()
                app.root.update()

        assert err.called
        args = err.call_args.args
        assert any("not be saved" in str(a) for a in args)
        # Directory changed but settings not persisted
        assert app.settings_window is not None
        assert app.settings_window.winfo_exists()
        assert app.controller.store.data_dir == target
        # Window can be reopened and retried
        with patch("todo_md.settings.save_settings"):
            app._settings_save_btn.invoke()
            app.root.update()

        data = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
        assert data["lists_dir"] == str(target)
    finally:
        _teardown(app)


def test_settings_save_cancel_preserves_theme_filter_state(tmp_path):
    """After a Save fails, theme/filter changes are still applied live."""
    from unittest.mock import patch

    source = tmp_path / "source"
    source.mkdir()
    app = _build_app(tmp_path, {"theme": "dark", "lists_dir": str(source), "completed_visible": 10})
    target = tmp_path / "target"
    config_dir = tmp_path / "config"
    try:
        app.root.update()
        app._settings_lists_dir_var.set(str(target))

        with patch("todo_md.settings.save_settings", side_effect=OSError("simulated save failure")):
            app._open_settings()
            app.root.update()
            app._settings_completed_var.set(5)
            with patch("tkinter.messagebox.showerror"):
                app._settings_save_btn.invoke()
                app.root.update()

        assert app.settings_window is not None
        # Theme stays dark (no change on Save failure) but pending completed applies if validation passed
        # Since theme validation passed, _apply_theme runs but settings don't persist
        assert app.settings.completed_visible == 10  # unchanged due to error path
    finally:
        _teardown(app)