"""GUI tests: settings window Save (directory decisions) and full-no-op Cancel.

Covers a valid Save persisting settings.json (theme/lists_dir/completed-
visible) and re-applying theme and completed filter live; validation of
theme and completed-visible before any filesystem work; the Yes/No/Cancel
decision when the lists folder changes and the active directory holds
Markdown lists; blank entry meaning the actual default directory (persisted
as null); equivalent (normalized/symlink) paths being no-ops; and Cancel
being a full no-op for unsaved controls.

Everything is isolated under tmp_path (patched DEFAULT_DATA_DIR, config dir
under tmp_path). The autouse dialog guard blocks unmocked native dialogs;
each test mocks exactly the dialogs it expects. Every app records uncaught
Tk callback exceptions and the fixture fails the test if any occurred.
"""

import json
import os
import shutil
from unittest.mock import patch

import pytest

from tests.conftest import managed_tk_roots
from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore

MD = b"# work\n- [ ] task\n"


@pytest.fixture(autouse=True)
def default_dir(tmp_path, monkeypatch):
    """Patch DEFAULT_DATA_DIR into tmp_path; returns the patched path."""
    path = str(tmp_path / "default_lists")
    monkeypatch.setattr("todo_md.app.DEFAULT_DATA_DIR", path)
    return path


@pytest.fixture
def make_app(tmp_path, default_dir):
    """Factory building isolated apps; always updates/destroys the roots and
    fails the test on uncaught Tk callback exceptions."""
    apps = []

    def build(
        settings: dict | None = None,
        data_dir: str | None = None,
        app_data_dir: str | None = None,
    ) -> TodoApp:
        """Actual store: explicit data_dir, else saved lists_dir, else default.

        settings=None writes no settings.json; a dict is copied verbatim
        (only its own keys) and is never mutated.
        """
        config_dir = tmp_path / "config"
        config_dir.mkdir(exist_ok=True)
        if settings is not None:
            (config_dir / "settings.json").write_text(
                json.dumps(dict(settings)), encoding="utf-8"
            )
        store_dir = data_dir or (settings or {}).get("lists_dir") or default_dir
        controller = TodoController(MarkdownListStore(store_dir))
        with patch("tkinter.Tk", create_root):
            app = TodoApp(controller, data_dir=app_data_dir, config_dir=str(config_dir))
        app.callback_errors = []
        app.root.report_callback_exception = (
            lambda exc, val, tb: app.callback_errors.append(val)
        )
        apps.append(app)
        app.root.update()
        return app

    with managed_tk_roots() as create_root:
        yield build

    errors = [error for app in apps for error in app.callback_errors]
    assert errors == [], f"uncaught Tk callback errors: {errors!r}"


def _open(app: TodoApp) -> None:
    app._open_settings()
    app.root.update()


def _save(app: TodoApp, decision="unexpected"):
    """Invoke Save with explicit dialog mocks; returns (ask, err).

    decision: the askyesnocancel return value (True/False/None), or the
    default "unexpected" meaning the prompt must not appear.
    """
    ask_kwargs = {} if decision == "unexpected" else {"return_value": decision}
    with patch("tkinter.messagebox.askyesnocancel", **ask_kwargs) as ask:
        with patch("tkinter.messagebox.showerror") as err:
            app._settings_save_btn.invoke()
            app.root.update()
    if decision == "unexpected":
        ask.assert_not_called()
    return ask, err


def _payload(tmp_path) -> dict:
    return json.loads((tmp_path / "config" / "settings.json").read_text(encoding="utf-8"))


def _no_settings_file(tmp_path) -> bool:
    return not (tmp_path / "config" / "settings.json").exists()


def _message(old, new) -> str:
    return (
        "You are about to change the directory where your lists are stored "
        f"from '{old}' to '{new}' but there are already lists in it."
    )


def _make_source(tmp_path, name="source") -> str:
    source = tmp_path / name
    source.mkdir()
    (source / "work.md").write_bytes(MD)
    return str(source)


def _assert_view(app, names, selected, items):
    assert app.listbox.get(0, "end") == tuple(names)
    assert app.current_list == selected
    assert app._selected_name() == selected
    assert app.listbox.curselection() == (
        (names.index(selected),) if selected is not None else ()
    )
    assert app.title_label.cget("text") == (selected or "(no list selected)")
    assert [(label.cget("text"), bool(var.get())) for var, _, label, _ in app._item_rows] == items
    assert len(app.items_frame.winfo_children()) == len(items)
    assert all(widget.winfo_exists() for row in app._item_rows for widget in row[1:])
    assert app.callback_errors == []


def _select_in_ui(app, name):
    index = app.listbox.get(0, "end").index(name)
    app.listbox.selection_clear(0, "end")
    app.listbox.selection_set(index)
    app.listbox.event_generate("<<ListboxSelect>>")
    app.root.update()


def _submit_entry(app, entry, text):
    entry.delete(0, "end")
    entry.insert(0, text)
    entry.focus_force()
    app.root.update()
    entry.event_generate("<Return>")
    app.root.update()


# -- opening / prefill ---------------------------------------------------


def test_settings_button_exists_and_opens_toplevel(make_app):
    import tkinter as tk

    app = make_app()
    assert app._settings_btn.cget("text") == "Settings"
    assert app.settings_window is None
    app._settings_btn.invoke()
    app.root.update()
    win = app.settings_window
    assert win is not None and win.winfo_exists()
    assert isinstance(win, tk.Toplevel)
    assert win.master is app.root
    assert win.title() == "Settings"


def test_settings_window_opens_once(make_app):
    app = make_app()
    _open(app)
    first = app.settings_window
    _open(app)  # lifts the existing window, no duplicate
    assert app.settings_window is first


def test_settings_window_closes_cleanly(make_app):
    app = make_app()
    _open(app)
    win = app.settings_window
    app._settings_cancel_btn.invoke()
    app.root.update()
    assert not win.winfo_exists()
    assert app.settings_window is None
    _open(app)
    assert app.settings_window.winfo_exists()


def test_settings_prefill_defaults(make_app, default_dir):
    app = make_app()
    _open(app)
    assert app._settings_lists_dir_var.get() == default_dir
    assert app._settings_theme_var.get() == "system"
    assert app._settings_completed_var.get() == 10
    selected = [r.cget("value") for r in app._settings_theme_rads if r.instate(["selected"])]
    assert selected == ["system"]


def test_settings_prefill_custom_settings(make_app, tmp_path):
    custom = str(tmp_path / "customlists")
    app = make_app({"theme": "dark", "lists_dir": custom, "completed_visible": 5})
    assert app.controller.store.data_dir == custom
    assert app.settings.theme == "dark"
    assert app.settings.lists_dir == custom
    assert app.settings.completed_visible == 5

    _open(app)
    assert app._settings_lists_dir_var.get() == custom
    assert [r.cget("value") for r in app._settings_theme_rads] == ["system", "light", "dark"]
    selected = [r.cget("value") for r in app._settings_theme_rads if r.instate(["selected"])]
    assert selected == ["dark"]
    assert int(app._settings_spinbox.cget("from")) == 0
    assert int(app._settings_spinbox.cget("to")) == 999
    assert app._settings_completed_var.get() == 5

    app._settings_theme_var.set("light")
    app.root.update()
    selected = [r.cget("value") for r in app._settings_theme_rads if r.instate(["selected"])]
    assert selected == ["light"]


def test_settings_reset_to_default(make_app, tmp_path, default_dir):
    custom = str(tmp_path / "custom")
    app = make_app({"lists_dir": custom})
    _open(app)
    assert app._settings_lists_dir_var.get() == custom
    app._settings_reset_btn.invoke()
    app.root.update()
    assert app._settings_lists_dir_var.get() == default_dir


def test_fixture_alignment_and_caller_dict_untouched(make_app, tmp_path, default_dir):
    caller = {"theme": "dark"}
    app = make_app(caller)
    assert caller == {"theme": "dark"}
    assert app.controller.store.data_dir == default_dir
    assert _payload(tmp_path) == {"theme": "dark"}  # absent keys stay absent
    explicit = str(tmp_path / "explicit")
    app2 = make_app({"lists_dir": str(tmp_path / "saved")}, data_dir=explicit)
    assert app2.controller.store.data_dir == explicit


def test_constructor_override_is_preserved_until_directory_operation(make_app, tmp_path):
    source = _make_source(tmp_path)
    override = str(tmp_path / "display_override")
    app = make_app({"lists_dir": source}, data_dir=source, app_data_dir=override)
    assert app.data_dir == override
    _open(app)
    app._settings_cancel_btn.invoke()
    assert app.data_dir == override
    _assert_view(app, ["work"], "work", [("task", False)])

    _open(app)
    target = str(tmp_path / "target")
    app._settings_lists_dir_var.set(target)
    _, err = _save(app, True)
    err.assert_not_called()
    assert app.data_dir == app.controller.data_dir == app.controller.store.data_dir == target
    assert app.settings.lists_dir == target
    _assert_view(app, ["work"], "work", [("task", False)])


# -- Save: theme / completed-visible -----------------------------------


def test_save_theme_persists_full_payload_and_reapplies(make_app, tmp_path):
    app = make_app()
    assert _no_settings_file(tmp_path)
    _open(app)
    app._settings_theme_var.set("dark")
    _, err = _save(app)

    err.assert_not_called()
    # Effective default directory is persisted as null.
    assert _payload(tmp_path) == {"theme": "dark", "lists_dir": None, "completed_visible": 10}
    assert app.settings.theme == "dark"
    assert app.theme == "dark"
    assert app._palette["bg"] == "#1e1e1e"
    assert app._theme_btn.cget("text") == "☀️ Light"
    assert app.settings_window is None


def test_save_unchanged_custom_dir_persists_normalized_path(make_app, tmp_path):
    custom = str(tmp_path / "custom")
    app = make_app({"lists_dir": custom})
    _open(app)
    _save(app)
    assert _payload(tmp_path)["lists_dir"] == custom
    assert app.settings_window is None


def test_save_completed_visible_persists_and_filters(make_app, tmp_path):
    data_dir = str(tmp_path / "data")
    app = make_app({"lists_dir": data_dir})
    items = [("a", False), ("b", False), ("c", True), ("d", True), ("e", True), ("f", True)]
    app.controller.store.save("L", items)
    app.refresh_lists(select_first=True)
    app.root.update()
    assert len(app._item_rows) == 6

    _open(app)
    app._settings_completed_var.set(1)
    _save(app)
    assert _payload(tmp_path)["completed_visible"] == 1
    assert app.settings.completed_visible == 1
    assert len(app._item_rows) == 3

    _open(app)
    app._settings_completed_var.set(0)
    _save(app)
    assert _payload(tmp_path)["completed_visible"] == 0
    assert len(app._item_rows) == 2
    assert app.controller.store.load("L") == items
    assert app.settings_window is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("count", "9999"),
        ("count", "1000"),
        ("count", "-1"),
        ("count", "abc"),
        ("count", ""),
        ("theme", "neon"),
    ],
)
def test_invalid_theme_or_count_blocks_all_filesystem_and_relocation(
    make_app, tmp_path, field, value
):
    """Validation precedes every filesystem check, prompt, creation,
    relocation, and persistence, even with a changed, populated target."""
    source = _make_source(tmp_path)
    app = make_app(data_dir=source)
    target = tmp_path / "target"
    _open(app)
    app._settings_lists_dir_var.set(str(target))
    if field == "count":
        app._settings_spinbox.delete(0, "end")
        app._settings_spinbox.insert(0, value)
    else:
        app._settings_theme_var.set(value)

    with patch("tkinter.messagebox.askyesnocancel") as ask:
        with patch("tkinter.messagebox.showerror") as err:
            with patch("todo_md.app.TodoController.change_lists_dir") as change:
                with patch("todo_md.app._has_markdown") as has_md:
                    with patch("todo_md.app._valid_lists_dir_path") as valid:
                        with patch("todo_md.app._same_dir") as same:
                            with patch("os.makedirs") as makedirs:
                                with patch("os.scandir") as scandir:
                                    with patch("todo_md.app.save_settings") as save:
                                        app._settings_save_btn.invoke()

    err.assert_called_once()
    for mock in (ask, change, has_md, valid, same, makedirs, scandir, save):
        mock.assert_not_called()
    assert app.settings_window is not None and app.settings_window.winfo_exists()
    assert _no_settings_file(tmp_path)
    assert not target.exists()
    assert (tmp_path / "source" / "work.md").read_bytes() == MD


# -- Save: directory decisions ------------------------------------------


def test_invalid_dir_empty_source_shows_error_keeps_open_persists_nothing(make_app, tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("i am a file, not a directory", encoding="utf-8")
    invalid = str(blocker / "sub")
    app = make_app(data_dir=str(tmp_path / "data"))
    _open(app)
    app._settings_lists_dir_var.set(invalid)
    _, err = _save(app)

    err.assert_called_once()
    assert invalid in str(err.call_args.args)
    assert app.settings_window is not None and app.settings_window.winfo_exists()
    assert _no_settings_file(tmp_path)
    assert app.controller.store.data_dir == str(tmp_path / "data")
    assert app.settings.lists_dir is None


def test_yes_moves_to_target_with_exact_prompt(make_app, tmp_path):
    source = _make_source(tmp_path)
    (tmp_path / "source" / "archive.md").write_bytes(b"# archive\n- [x] earlier\n")
    target = str(tmp_path / "target")
    app = make_app(data_dir=source)
    _select_in_ui(app, "work")
    _assert_view(app, ["archive", "work"], "work", [("task", False)])
    _open(app)
    app._settings_lists_dir_var.set(target)
    ask, err = _save(app, True)

    ask.assert_called_once()
    assert ask.call_args.args == ("Confirm directory change", _message(source, target))
    err.assert_not_called()
    assert _payload(tmp_path)["lists_dir"] == target
    assert app.settings.lists_dir == target
    assert app.settings_window is None
    assert not os.path.exists(os.path.join(source, "work.md"))
    assert (tmp_path / "target" / "work.md").read_bytes() == MD
    assert app.controller.store.data_dir == target
    assert app.controller.list_names() == ["archive", "work"]
    assert app.data_dir == app.controller.data_dir == target
    _assert_view(app, ["archive", "work"], "work", [("task", False)])
    assert (tmp_path / "target" / "archive.md").read_bytes() == b"# archive\n- [x] earlier\n"

    # Real widget callbacks must edit the destination, not recreate source files.
    app._item_rows[0][1].invoke()
    app.root.update()
    _assert_view(app, ["archive", "work"], "work", [("task", True)])
    assert (tmp_path / "target" / "work.md").read_bytes() == b"# work\n- [x] task\n"
    _submit_entry(app, app.new_name_entry, "new")
    _submit_entry(app, app.new_item_entry, "task")
    _assert_view(app, ["archive", "new", "work"], "new", [("task", False)])
    assert (tmp_path / "target" / "new.md").read_bytes() == b"# new\n- [ ] task\n"
    assert os.listdir(source) == []


def test_no_switches_without_moving(make_app, tmp_path):
    source = _make_source(tmp_path)
    target = str(tmp_path / "target")
    app = make_app(data_dir=source)
    _assert_view(app, ["work"], "work", [("task", False)])
    old_widgets = app._item_rows[0][1:]
    _open(app)
    app._settings_lists_dir_var.set(target)
    ask, err = _save(app, False)

    ask.assert_called_once()
    assert ask.call_args.args == ("Confirm directory change", _message(source, target))
    err.assert_not_called()
    assert _payload(tmp_path)["lists_dir"] == target
    assert app.settings_window is None
    assert (tmp_path / "source" / "work.md").read_bytes() == MD
    assert os.listdir(target) == []
    assert app.controller.list_names() == []
    assert app.data_dir == app.controller.data_dir == app.settings.lists_dir == target
    _assert_view(app, [], None, [])
    assert all(not widget.winfo_exists() for widget in old_widgets)
    _submit_entry(app, app.new_item_entry, "must not edit the source")
    assert os.listdir(target) == []
    _submit_entry(app, app.new_name_entry, "new")
    _submit_entry(app, app.new_item_entry, "item")
    _assert_view(app, ["new"], "new", [("item", False)])
    assert (tmp_path / "target" / "new.md").read_bytes() == b"# new\n- [ ] item\n"
    assert (tmp_path / "source" / "work.md").read_bytes() == MD


def test_blank_entry_yes_moves_lists_to_actual_default(make_app, tmp_path, default_dir):
    source = _make_source(tmp_path)
    app = make_app({"lists_dir": source})
    _open(app)
    app._settings_lists_dir_var.set("")
    ask, err = _save(app, True)

    ask.assert_called_once()
    assert ask.call_args.args == ("Confirm directory change", _message(source, default_dir))
    err.assert_not_called()
    assert _payload(tmp_path) == {"theme": "system", "lists_dir": None, "completed_visible": 10}
    assert app.settings.lists_dir is None
    assert app.controller.store.data_dir == default_dir
    assert (tmp_path / "default_lists" / "work.md").read_bytes() == MD
    assert not os.path.exists(os.path.join(source, "work.md"))
    assert app.settings_window is None

    app.controller.create_list("later")
    app.controller.add_item("later", "x")
    assert (tmp_path / "default_lists" / "later.md").read_bytes() == b"# later\n- [ ] x\n"
    assert os.listdir(source) == []


def test_whitespace_entry_no_switches_to_default_without_moving(make_app, tmp_path, default_dir):
    source = _make_source(tmp_path)
    app = make_app({"lists_dir": source})
    _open(app)
    app._settings_lists_dir_var.set("   ")
    ask, _ = _save(app, False)

    ask.assert_called_once()
    assert ask.call_args.args[1] == _message(source, default_dir)
    assert _payload(tmp_path)["lists_dir"] is None
    assert app.controller.store.data_dir == default_dir
    assert (tmp_path / "source" / "work.md").read_bytes() == MD
    assert os.listdir(default_dir) == []


@pytest.mark.parametrize("decision", [True, False])
def test_populated_default_rejected_for_yes_and_no(make_app, tmp_path, default_dir, decision):
    source = _make_source(tmp_path)
    os.makedirs(default_dir)
    with open(os.path.join(default_dir, "existing.md"), "wb") as fh:
        fh.write(b"# existing\n- [ ] item\n")
    app = make_app({"lists_dir": source})
    before = (tmp_path / "config" / "settings.json").read_bytes()
    store_before = app.controller.store
    _open(app)
    app._settings_lists_dir_var.set("")
    ask, err = _save(app, decision)

    ask.assert_called_once()
    err.assert_called_once()
    assert "destination" in " ".join(str(a) for a in err.call_args.args)
    assert app.settings_window is not None and app.settings_window.winfo_exists()
    assert (tmp_path / "config" / "settings.json").read_bytes() == before
    assert app.controller.store is store_before
    assert app.controller.store.data_dir == source
    assert (tmp_path / "source" / "work.md").read_bytes() == MD
    assert os.listdir(default_dir) == ["existing.md"]
    assert app.settings.lists_dir == source


def test_populated_target_rejected_when_source_empty_without_prompt(make_app, tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    (target / "existing.md").write_bytes(b"# existing\n")
    app = make_app(data_dir=str(source))
    _open(app)
    app._settings_lists_dir_var.set(str(target))
    _, err = _save(app)

    err.assert_called_once()
    assert "destination" in " ".join(str(a) for a in err.call_args.args)
    assert app.settings_window is not None
    assert _no_settings_file(tmp_path)
    assert app.controller.store.data_dir == str(source)


def test_cancel_from_default_preserves_null_and_applies_other_edits(
    make_app, tmp_path, default_dir
):
    app = make_app()
    app.controller.store.save("work", [("task", False)])
    target = tmp_path / "target"
    _open(app)
    app._settings_theme_var.set("light")
    app._settings_completed_var.set(25)
    app._settings_lists_dir_var.set(str(target))
    ask, err = _save(app, None)

    ask.assert_called_once()
    assert ask.call_args.args == ("Confirm directory change", _message(default_dir, str(target)))
    err.assert_not_called()
    assert _payload(tmp_path) == {"theme": "light", "lists_dir": None, "completed_visible": 25}
    assert app.settings.theme == "light"
    assert app.settings.completed_visible == 25
    assert app.settings.lists_dir is None
    assert app.controller.store.data_dir == default_dir
    assert not target.exists()
    assert app.controller.list_names() == ["work"]
    assert app.settings_window is None


def test_cancel_from_custom_dir_keeps_active_dir_and_persists_it(make_app, tmp_path):
    source = _make_source(tmp_path)
    app = make_app({"theme": "dark", "lists_dir": source, "completed_visible": 10})
    target = tmp_path / "target"
    _open(app)
    app._settings_theme_var.set("light")
    app._settings_completed_var.set(25)
    app._settings_lists_dir_var.set(str(target))
    _save(app, None)

    assert _payload(tmp_path) == {"theme": "light", "lists_dir": source, "completed_visible": 25}
    assert app.controller.store.data_dir == source
    assert not target.exists()
    assert (tmp_path / "source" / "work.md").read_bytes() == MD
    assert app.settings_window is None


def test_cancel_ignores_unusable_abandoned_target(make_app, tmp_path):
    source = _make_source(tmp_path)
    blocker = tmp_path / "blocker"
    blocker.write_text("file", encoding="utf-8")
    invalid = str(blocker / "sub")
    app = make_app({"lists_dir": source})
    _open(app)
    app._settings_theme_var.set("dark")
    app._settings_completed_var.set(3)
    app._settings_lists_dir_var.set(invalid)
    ask, err = _save(app, None)

    ask.assert_called_once()
    err.assert_not_called()  # abandoned target is never validated
    assert _payload(tmp_path) == {"theme": "dark", "lists_dir": source, "completed_visible": 3}
    assert app.settings.theme == "dark"
    assert app.controller.store.data_dir == source
    assert blocker.read_text(encoding="utf-8") == "file"
    assert app.settings_window is None


def test_invalid_target_after_yes_is_reported_and_nothing_changes(make_app, tmp_path):
    source = _make_source(tmp_path)
    blocker = tmp_path / "blocker"
    blocker.write_text("file", encoding="utf-8")
    invalid = str(blocker / "sub")
    app = make_app(data_dir=source)
    _open(app)
    app._settings_lists_dir_var.set(invalid)
    ask, err = _save(app, True)

    ask.assert_called_once()
    err.assert_called_once()
    assert invalid in str(err.call_args.args)
    assert app.settings_window is not None
    assert _no_settings_file(tmp_path)
    assert (tmp_path / "source" / "work.md").read_bytes() == MD
    assert app.controller.store.data_dir == source


@pytest.mark.parametrize("kind", ["empty", "non_markdown", "missing"])
def test_no_popup_sources_create_target_through_controller(make_app, tmp_path, kind):
    source = tmp_path / "source"
    source.mkdir()
    if kind == "non_markdown":
        (source / "notes.txt").write_bytes(b"plain text only")
    app = make_app(data_dir=str(source))
    if kind == "missing":
        shutil.rmtree(source)
    target = tmp_path / "target"
    _open(app)
    app._settings_lists_dir_var.set(str(target))
    with patch(
        "todo_md.app.TodoController.change_lists_dir",
        autospec=True,
        side_effect=TodoController.change_lists_dir,
    ) as change:
        _, err = _save(app)

    change.assert_called_once_with(app.controller, str(target), move=True)
    err.assert_not_called()
    assert target.is_dir()
    assert _payload(tmp_path)["lists_dir"] == str(target)
    assert app.controller.store.data_dir == str(target)
    assert app.settings_window is None
    if kind == "non_markdown":
        assert (source / "notes.txt").read_bytes() == b"plain text only"


def test_missing_source_with_blank_entry_supported(make_app, tmp_path, default_dir):
    source = tmp_path / "source"
    app = make_app({"lists_dir": str(source)})
    shutil.rmtree(source)
    _open(app)
    app._settings_lists_dir_var.set("")
    _, err = _save(app)

    err.assert_not_called()
    assert _payload(tmp_path)["lists_dir"] is None
    assert app.controller.store.data_dir == default_dir
    assert os.path.isdir(default_dir)


@pytest.mark.parametrize("bound_is_link", [True, False])
def test_equivalent_symlink_and_normalized_paths_do_not_prompt_or_relocate(
    make_app, tmp_path, bound_is_link
):
    real = _make_source(tmp_path, "real")
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    bound, entry_base = (str(link), real) if bound_is_link else (real, str(link))
    entry = f"{tmp_path}/./sub/../{os.path.basename(entry_base)}/"
    (tmp_path / "sub").mkdir()
    app = make_app(data_dir=bound)
    _open(app)
    app._settings_lists_dir_var.set(entry)
    with patch("todo_md.app.TodoController.change_lists_dir") as change:
        _, err = _save(app)

    change.assert_not_called()
    err.assert_not_called()
    assert app.settings_window is None
    assert (tmp_path / "real" / "work.md").read_bytes() == MD
    assert app.controller.store.data_dir == bound
    # Stable absolute form: normalized but not symlink-resolved.
    assert _payload(tmp_path)["lists_dir"] == entry_base


def test_symlink_to_default_persists_null_without_relocation(make_app, tmp_path, default_dir):
    app = make_app()
    link = tmp_path / "deflink"
    link.symlink_to(default_dir, target_is_directory=True)
    _open(app)
    app._settings_lists_dir_var.set(str(link))
    with patch("todo_md.app.TodoController.change_lists_dir") as change:
        _save(app)
    change.assert_not_called()
    assert _payload(tmp_path)["lists_dir"] is None


def test_repeat_save_unchanged_never_prompts(make_app, tmp_path):
    source = _make_source(tmp_path)
    app = make_app({"lists_dir": source})
    for _ in range(2):
        _open(app)
        _save(app)
        assert app.settings_window is None
    assert _payload(tmp_path)["lists_dir"] == source
    assert (tmp_path / "source" / "work.md").read_bytes() == MD


def test_inspection_error_is_reported_not_raised_into_tk(make_app, tmp_path):
    source = _make_source(tmp_path)
    app = make_app(data_dir=source)
    _open(app)
    app._settings_lists_dir_var.set(str(tmp_path / "target"))
    with patch("todo_md.app._has_markdown", side_effect=PermissionError("denied")):
        _, err = _save(app)

    err.assert_called_once()
    assert "denied" in " ".join(str(a) for a in err.call_args.args)
    assert app.settings_window is not None
    assert _no_settings_file(tmp_path)
    assert app.callback_errors == []


def test_equivalence_error_is_reported_not_raised_into_tk(make_app, tmp_path):
    app = make_app(data_dir=str(tmp_path / "data"))
    _open(app)
    app._settings_lists_dir_var.set(str(tmp_path / "target"))
    with patch("os.path.samefile", side_effect=PermissionError("nope")):
        _, err = _save(app)

    err.assert_called_once()
    assert "nope" in " ".join(str(a) for a in err.call_args.args)
    assert _no_settings_file(tmp_path)
    assert app.callback_errors == []


def test_relocation_failure_reports_and_keeps_bindings(make_app, tmp_path):
    source = _make_source(tmp_path)
    app = make_app(data_dir=source)
    store_before = app.controller.store
    _open(app)
    app._settings_lists_dir_var.set(str(tmp_path / "target"))
    with patch(
        "todo_md.app.TodoController.change_lists_dir",
        side_effect=OSError("simulated disk failure"),
    ):
        ask, err = _save(app, True)

    ask.assert_called_once()
    err.assert_called_once()
    assert "failed" in " ".join(str(a) for a in err.call_args.args).lower()
    assert app.settings_window is not None and app.settings_window.winfo_exists()
    assert _no_settings_file(tmp_path)
    assert app.controller.store is store_before
    assert (tmp_path / "source" / "work.md").read_bytes() == MD


@pytest.mark.parametrize("selected", ["ahead", "work"])
def test_partial_relocation_refreshes_remaining_source_without_rollback(
    make_app, tmp_path, selected
):
    source = _make_source(tmp_path)
    moved_bytes = b"# ahead\n\n- [ ] move first\nretained formatting\n"
    (tmp_path / "source" / "ahead.md").write_bytes(moved_bytes)
    target = str(tmp_path / "target")
    app = make_app({"lists_dir": source})
    before = (tmp_path / "config" / "settings.json").read_bytes()
    store_before = app.controller.store
    _select_in_ui(app, selected)
    old_widgets = app._item_rows[0][1:]
    _open(app)
    app._settings_lists_dir_var.set(target)
    copy = shutil.copyfileobj

    def fail_second_copy(incoming, outgoing):
        if os.path.basename(incoming.name) == "work.md":
            outgoing.write(b"partial copy")
            raise OSError("second copy failed")
        return copy(incoming, outgoing)

    with patch("todo_md.storage.shutil.copyfileobj", side_effect=fail_second_copy) as copying:
        with patch("todo_md.app.save_settings") as save:
            ask, err = _save(app, True)

    ask.assert_called_once()
    err.assert_called_once()
    save.assert_not_called()
    assert copying.call_count == 2
    message = err.call_args.args[1]
    for text in (source, target, "second copy failed", "Some files", "not been undone"):
        assert text in message
    assert app.settings_window.winfo_exists()
    assert app.controller.store is store_before
    assert app.data_dir == app.controller.data_dir == app.settings.lists_dir == source
    assert (tmp_path / "config" / "settings.json").read_bytes() == before
    assert (tmp_path / "target" / "ahead.md").read_bytes() == moved_bytes
    assert not (tmp_path / "source" / "ahead.md").exists()
    assert (tmp_path / "source" / "work.md").read_bytes() == MD
    assert not (tmp_path / "target" / "work.md").exists()
    assert all(not widget.winfo_exists() for widget in old_widgets)
    if selected == "ahead":
        _assert_view(app, ["work"], None, [])
        _submit_entry(app, app.new_item_entry, "must not recreate moved list")
        assert not (tmp_path / "source" / "ahead.md").exists()
        _select_in_ui(app, "work")
    _assert_view(app, ["work"], "work", [("task", False)])
    app._item_rows[0][1].invoke()
    app.root.update()
    _assert_view(app, ["work"], "work", [("task", True)])
    assert (tmp_path / "source" / "work.md").read_bytes() == b"# work\n- [x] task\n"
    assert (tmp_path / "target" / "ahead.md").read_bytes() == moved_bytes
    assert sorted(os.listdir(source)) == ["work.md"]
    assert sorted(os.listdir(target)) == ["ahead.md"]


@pytest.mark.parametrize("read_method", ["lists", "load"])
def test_relocation_failure_with_unreadable_source_clears_stale_view(
    make_app, tmp_path, read_method
):
    source = _make_source(tmp_path)
    target = str(tmp_path / "target")
    app = make_app({"lists_dir": source})
    before = (tmp_path / "config" / "settings.json").read_bytes()
    store_before = app.controller.store
    old_widgets = app._item_rows[0][1:]
    _open(app)
    app._settings_lists_dir_var.set(target)
    with patch.object(app.controller, "change_lists_dir", side_effect=OSError("move failed")):
        with patch.object(store_before, read_method, side_effect=PermissionError("read denied")):
            with patch("todo_md.app.save_settings") as save:
                _, err = _save(app, True)

    err.assert_called_once()
    save.assert_not_called()
    message = err.call_args.args[1]
    for text in (source, target, "move failed", "Could not refresh", "read denied"):
        assert text in message
    assert app.controller.store is store_before
    assert app.data_dir == app.controller.data_dir == app.settings.lists_dir == source
    assert app.settings_window.winfo_exists()
    assert (tmp_path / "config" / "settings.json").read_bytes() == before
    assert (tmp_path / "source" / "work.md").read_bytes() == MD
    _assert_view(app, [], None, [])
    assert all(not widget.winfo_exists() for widget in old_widgets)
    _submit_entry(app, app.new_item_entry, "must not edit a stale list")
    assert (tmp_path / "source" / "work.md").read_bytes() == MD


@pytest.mark.parametrize("read_method", ["lists", "load"])
def test_successful_switch_with_refresh_error_retains_destination_and_retries(
    make_app, tmp_path, read_method
):
    source = _make_source(tmp_path)
    target = str(tmp_path / "target")
    app = make_app({"theme": "light", "lists_dir": source})
    before = (tmp_path / "config" / "settings.json").read_bytes()
    _open(app)
    app._settings_lists_dir_var.set(target)
    app._settings_theme_var.set("dark")
    with patch.object(MarkdownListStore, read_method, side_effect=PermissionError("read denied")):
        with patch("todo_md.app.save_settings") as save:
            _, err = _save(app, True)

    err.assert_called_once()
    save.assert_not_called()
    message = err.call_args.args[1]
    for text in (source, target, "read denied", "not saved for restart", "retry Save"):
        assert text in message
    assert app.data_dir == app.controller.data_dir == app.controller.store.data_dir == target
    assert app.settings.lists_dir == target
    assert app.settings.theme == app.theme == "light"
    assert app.settings_window.winfo_exists()
    assert (tmp_path / "config" / "settings.json").read_bytes() == before
    assert (tmp_path / "target" / "work.md").read_bytes() == MD
    assert os.listdir(source) == []
    _assert_view(app, [], None, [])

    with patch.object(app.controller, "change_lists_dir") as change:
        _, err = _save(app)
    change.assert_not_called()
    err.assert_not_called()
    _assert_view(app, ["work"], None, [])
    _select_in_ui(app, "work")
    app._item_rows[0][1].invoke()
    app.root.update()
    _assert_view(app, ["work"], "work", [("task", True)])
    assert (tmp_path / "target" / "work.md").read_bytes() == b"# work\n- [x] task\n"
    assert os.listdir(source) == []
    assert _payload(tmp_path)["lists_dir"] == target


def test_post_switch_preference_resolution_error_still_synchronizes_live_view(make_app, tmp_path):
    source = _make_source(tmp_path)
    target = str(tmp_path / "target")
    app = make_app({"lists_dir": source})
    before = (tmp_path / "config" / "settings.json").read_bytes()
    _open(app)
    app._settings_lists_dir_var.set(target)
    with patch.object(app, "_lists_dir_setting", side_effect=PermissionError("default denied")):
        with patch("todo_md.app.save_settings") as save:
            _, err = _save(app, True)

    err.assert_called_once()
    save.assert_not_called()
    assert "default denied" in err.call_args.args[1]
    assert target in err.call_args.args[1]
    assert app.data_dir == app.controller.data_dir == app.controller.store.data_dir == target
    assert app.settings.lists_dir == target
    assert (tmp_path / "config" / "settings.json").read_bytes() == before
    assert (tmp_path / "target" / "work.md").read_bytes() == MD
    assert os.listdir(source) == []
    _assert_view(app, ["work"], "work", [("task", False)])
    app._item_rows[0][1].invoke()
    app.root.update()
    assert (tmp_path / "target" / "work.md").read_bytes() == b"# work\n- [x] task\n"
    with patch.object(app.controller, "change_lists_dir") as change:
        _, err = _save(app)
    change.assert_not_called()
    err.assert_not_called()
    assert _payload(tmp_path)["lists_dir"] == target
    _assert_view(app, ["work"], "work", [("task", True)])


# -- Cancel ------------------------------------------------------------


def test_cancel_edits_are_a_full_noop(make_app, tmp_path):
    app = make_app()
    _open(app)
    app._settings_lists_dir_var.set(str(tmp_path / "editeddir"))
    app._settings_theme_var.set("dark")
    app._settings_completed_var.set(3)
    with patch("tkinter.messagebox.askyesnocancel") as ask:
        with patch("tkinter.messagebox.showerror") as err:
            app._settings_cancel_btn.invoke()
            app.root.update()

    ask.assert_not_called()
    err.assert_not_called()
    assert _no_settings_file(tmp_path)
    assert app.settings.theme == "system"
    assert app.settings.lists_dir is None
    assert app.settings.completed_visible == 10
    assert not (tmp_path / "editeddir").exists()
    assert app.settings_window is None
    assert app.root.winfo_exists()


# -- Persistence failure and retry -------------------------------------


def test_settings_save_failure_keeps_destination_and_retry_persists(make_app, tmp_path):
    source = _make_source(tmp_path)
    original = b"# work\n- [ ] task\n- [x] older\n- [x] latest\n"
    (tmp_path / "source" / "work.md").write_bytes(original)
    target = str(tmp_path / "target")
    app = make_app({"lists_dir": source, "theme": "light", "completed_visible": 10})
    before = (tmp_path / "config" / "settings.json").read_bytes()
    palette_before = dict(app._palette)
    _assert_view(app, ["work"], "work", [("task", False), ("older", True), ("latest", True)])
    _open(app)
    app._settings_lists_dir_var.set(target)
    app._settings_theme_rads[2].invoke()
    app._settings_spinbox.delete(0, "end")
    app._settings_spinbox.insert(0, "0")
    with patch("todo_md.settings.os.replace", side_effect=OSError("simulated save failure")):
        ask, err = _save(app, True)

    ask.assert_called_once()
    err.assert_called_once()
    assert "not be saved" in " ".join(str(a) for a in err.call_args.args)
    for text in (target, "active lists folder", "not saved for restart", "retry Save"):
        assert text in err.call_args.args[1]
    assert app.settings_window is not None and app.settings_window.winfo_exists()
    assert app.controller.store.data_dir == target
    assert app.data_dir == app.controller.data_dir == app.settings.lists_dir == target
    assert (tmp_path / "target" / "work.md").read_bytes() == original
    assert os.listdir(source) == []
    assert (tmp_path / "config" / "settings.json").read_bytes() == before
    assert os.listdir(tmp_path / "config") == ["settings.json"]
    assert app.settings.theme == app.theme == "light"
    assert app.settings.completed_visible == 10
    assert app._palette == palette_before
    assert app._settings_theme_var.get() == "dark"
    assert app._settings_completed_var.get() == 0
    _assert_view(app, ["work"], "work", [("task", False), ("older", True), ("latest", True)])

    # The destination stays editable even before the preference can be saved.
    app._item_rows[0][1].invoke()
    app.root.update()
    _submit_entry(app, app.new_item_entry, "destination edit")
    _assert_view(app, ["work"], "work", [
        ("task", True), ("older", True), ("latest", True), ("destination edit", False)
    ])
    edited = b"# work\n- [x] task\n- [x] older\n- [x] latest\n- [ ] destination edit\n"
    assert (tmp_path / "target" / "work.md").read_bytes() == edited
    assert (tmp_path / "config" / "settings.json").read_bytes() == before
    assert os.listdir(source) == []

    with patch.object(app.controller, "change_lists_dir") as change:
        _, err = _save(app)
    change.assert_not_called()
    err.assert_not_called()
    assert _payload(tmp_path)["lists_dir"] == target
    assert _payload(tmp_path) == {"theme": "dark", "lists_dir": target, "completed_visible": 0}
    assert app.settings_window is None
    assert app.settings.theme == app.theme == "dark"
    assert app.settings.completed_visible == 0
    assert app._palette["bg"] == "#1e1e1e"
    _assert_view(app, ["work"], "work", [("destination edit", False)])
    assert (tmp_path / "target" / "work.md").read_bytes() == edited
    assert os.listdir(source) == []


@pytest.mark.parametrize("close", ["cancel", "window"])
@pytest.mark.parametrize("persist", ["save", "theme"])
def test_close_after_save_failure_keeps_active_directory_on_reopen(
    make_app, tmp_path, close, persist
):
    source = _make_source(tmp_path)
    target = str(tmp_path / "target")
    app = make_app({"lists_dir": source, "theme": "light", "completed_visible": 10})
    before = (tmp_path / "config" / "settings.json").read_bytes()
    _open(app)
    app._settings_lists_dir_var.set(target)
    app._settings_theme_rads[2].invoke()
    app._settings_completed_var.set(0)
    with patch("todo_md.settings.os.replace", side_effect=OSError("save denied")):
        _, err = _save(app, True)
    err.assert_called_once()
    assert (tmp_path / "target" / "work.md").read_bytes() == MD
    assert (tmp_path / "config" / "settings.json").read_bytes() == before
    win = app.settings_window
    if close == "cancel":
        app._settings_cancel_btn.invoke()
    else:
        win.tk.call(win.protocol("WM_DELETE_WINDOW"))
    app.root.update()
    assert not win.winfo_exists()
    assert app.settings_window is None
    assert app.settings.theme == app.theme == "light"
    assert app.settings.completed_visible == 10
    assert app.data_dir == app.controller.data_dir == app.settings.lists_dir == target
    _assert_view(app, ["work"], "work", [("task", False)])
    _submit_entry(app, app.new_item_entry, "after closing")
    assert (tmp_path / "target" / "work.md").read_bytes() == b"# work\n- [ ] task\n- [ ] after closing\n"
    assert os.listdir(source) == []

    with patch.object(app.controller, "change_lists_dir") as change:
        with patch("tkinter.messagebox.askyesnocancel") as ask:
            _open(app)
            assert app._settings_lists_dir_var.get() == target
            assert app._settings_theme_var.get() == "light"
            assert app._settings_completed_var.get() == 10
            assert (tmp_path / "config" / "settings.json").read_bytes() == before
            if persist == "save":
                app._settings_save_btn.invoke()
            else:
                app._settings_cancel_btn.invoke()
                app._theme_btn.invoke()
            app.root.update()
        ask.assert_not_called()
        change.assert_not_called()
    assert _payload(tmp_path) == {
        "theme": "light" if persist == "save" else "dark",
        "lists_dir": target,
        "completed_visible": 10,
    }
    _assert_view(app, ["work"], "work", [("task", False), ("after closing", False)])
    assert os.listdir(source) == []
