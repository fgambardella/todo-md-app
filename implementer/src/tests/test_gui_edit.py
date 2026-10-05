"""GUI tests: per-item edit icon and the modal edit dialog.

Covers: icon presence and positioning (left of the trash icon), the dialog
opening with the entry pre-populated with the item text, Save persisting
the new text to the .md file and closing, Cancel closing with no change,
and Save with empty/whitespace input persisting nothing. Also covers the
description box: pre-population, Save persisting (and round-tripping as
indented continuation lines), blank descriptions persisting as "", and
Cancel / empty-title Save leaving both title and description unchanged.
"""

import os

import tkinter as tk
from tkinter import ttk

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def _make_app(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    controller.create_list("Edits")
    controller.add_item("Edits", "Edit me")
    controller.add_item("Edits", "Other")
    return TodoApp(controller, config_dir=str(tmp_path / "config"))


def _open_edit(app, row_index=0):
    app._item_rows[row_index][4].event_generate("<Button-1>")
    app.root.update()
    assert app._edit_window is not None, "edit dialog should be open"
    return app._edit_window


def test_edit_icon_present_left_of_trash(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        app._select_list_name("Edits")
        app.root.update()

        assert len(app._item_rows) == 2
        for _var, _cb, _label, del_ctrl, edit_ctrl in app._item_rows:
            # (a) EDIT ICON PRESENT: a Label showing the cached pencil asset
            assert isinstance(edit_ctrl, tk.Label)
            assert not isinstance(edit_ctrl, tk.Button)
            assert str(edit_ctrl.cget("image")) == str(app._edit_image)
            assert str(del_ctrl.cget("image")) == str(app._trash_image)

        # (b) SIZE: displayed icon ~18px
        assert 14 <= app._edit_image.width() <= 22
        assert 14 <= app._edit_image.height() <= 22

        # (c) POSITION: edit icon strictly to the left of the trash icon
        _var, _cb, _label, del_ctrl, edit_ctrl = app._item_rows[0]
        assert edit_ctrl.winfo_x() < del_ctrl.winfo_x()

        # (d) SOURCE TRANSPARENCY: PNG IHDR color type byte (offset 25)
        icon_path = os.path.join("todo_md", "assets", "edit_18.png")
        with open(icon_path, "rb") as fh:
            data = fh.read()
        assert data[:4] == b"\x89PNG"
        assert data[25] in (4, 6)
    finally:
        app.root.destroy()


def test_edit_dialog_opens_prepopulated(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        app._select_list_name("Edits")
        app.root.update()

        win = _open_edit(app)
        assert win.winfo_exists()
        assert win.title() == "Edit item"
        assert isinstance(app._edit_entry, ttk.Entry)
        # Entry is pre-populated with the item's current text.
        assert app._edit_entry.get() == "Edit me"
    finally:
        app._close_edit_dialog()  # no-op when no dialog is open
        app.root.destroy()


def test_edit_save_persists_and_closes(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        app._select_list_name("Edits")
        app.root.update()

        _open_edit(app)
        app._edit_entry.delete(0, "end")
        app._edit_entry.insert(0, "Renamed task")
        app._edit_save_btn.invoke()
        app.root.update()

        # Dialog closed.
        assert app._edit_window is None
        # New text persisted to the .md file; old text replaced.
        content = (tmp_path / "Edits.md").read_text()
        assert "Renamed task" in content
        assert "Edit me" not in content
        assert "Other" in content
        # Row refreshed with the new text.
        assert app._item_rows[0][2].cget("text") == "Renamed task"
    finally:
        app._close_edit_dialog()
        app.root.destroy()


def test_edit_cancel_closes_without_change(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        app._select_list_name("Edits")
        app.root.update()

        _open_edit(app)
        before = (tmp_path / "Edits.md").read_text()
        app._edit_entry.delete(0, "end")
        app._edit_entry.insert(0, "Should not persist")
        app._edit_cancel_btn.invoke()
        app.root.update()

        # Dialog closed, file and row unchanged.
        assert app._edit_window is None
        assert (tmp_path / "Edits.md").read_text() == before
        assert app._item_rows[0][2].cget("text") == "Edit me"
    finally:
        app._close_edit_dialog()
        app.root.destroy()


def test_edit_save_empty_persists_nothing(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        app._select_list_name("Edits")
        app.root.update()

        for text in ("", "   "):
            _open_edit(app)
            app._edit_entry.delete(0, "end")
            app._edit_entry.insert(0, text)
            app._edit_save_btn.invoke()
            app.root.update()
            # Dialog still closes on failed validation.
            assert app._edit_window is None

        # Nothing persisted: original text intact, row unchanged.
        content = (tmp_path / "Edits.md").read_text()
        assert "Edit me" in content
        assert app._item_rows[0][2].cget("text") == "Edit me"
    finally:
        app._close_edit_dialog()
        app.root.destroy()


def _make_app_with_description(tmp_path, description="Old line one\nOld line two"):
    app = _make_app(tmp_path)
    app.controller.edit_item("Edits", 0, "Edit me", description)
    return app


def _set_description(app, text):
    app._edit_desc_text.delete("1.0", "end")
    app._edit_desc_text.insert("1.0", text)


def _continuation_lines(path):
    return [ln for ln in path.read_text().splitlines() if ln.startswith("  ")]


def test_edit_dialog_prepopulates_description(tmp_path):
    app = _make_app_with_description(tmp_path)
    try:
        app.root.update()
        app._select_list_name("Edits")
        app.root.update()

        _open_edit(app)
        assert isinstance(app._edit_desc_text, tk.Text)
        assert app._edit_desc_text.get("1.0", "end-1c") == (
            "Old line one\nOld line two"
        )
        # Title entry still pre-populated alongside it.
        assert app._edit_entry.get() == "Edit me"
    finally:
        app._close_edit_dialog()
        assert app._edit_desc_text is None
        app.root.destroy()


def test_edit_dialog_empty_description_box_for_plain_item(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        app._select_list_name("Edits")
        app.root.update()

        _open_edit(app)
        assert app._edit_desc_text.get("1.0", "end-1c") == ""
    finally:
        app._close_edit_dialog()
        app.root.destroy()


def test_edit_save_persists_description(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        app._select_list_name("Edits")
        app.root.update()

        _open_edit(app)
        _set_description(app, "First detail\nSecond detail")
        app._edit_save_btn.invoke()
        app.root.update()

        assert app._edit_window is None
        assert app._edit_desc_text is None
        items = app.controller.store.load("Edits")
        assert items[0] == ("Edit me", False, "First detail\nSecond detail")
        assert items[1] == ("Other", False, "")
        # On disk: indented continuation lines directly under the checkbox.
        lines = (tmp_path / "Edits.md").read_text().splitlines()
        idx = lines.index("- [ ] Edit me")
        assert lines[idx + 1] == "  First detail"
        assert lines[idx + 2] == "  Second detail"
        # Round-trip through a fresh store reading the same file.
        fresh = MarkdownListStore(str(tmp_path)).load("Edits")
        assert fresh[0] == ("Edit me", False, "First detail\nSecond detail")
    finally:
        app._close_edit_dialog()
        app.root.destroy()


def test_edit_save_title_and_description_together(tmp_path):
    app = _make_app_with_description(tmp_path)
    try:
        app.root.update()
        app._select_list_name("Edits")
        app.root.update()

        _open_edit(app)
        app._edit_entry.delete(0, "end")
        app._edit_entry.insert(0, "Renamed task")
        _set_description(app, "New detail")
        app._edit_save_btn.invoke()
        app.root.update()

        items = app.controller.store.load("Edits")
        assert items[0] == ("Renamed task", False, "New detail")
        assert _continuation_lines(tmp_path / "Edits.md") == ["  New detail"]
        assert app._item_rows[0][2].cget("text") == "Renamed task"
    finally:
        app._close_edit_dialog()
        app.root.destroy()


def test_edit_save_blank_description_persists_empty(tmp_path):
    for blank in ("", "   ", "  \n\t\n "):
        case_dir = tmp_path / f"case{len(blank)}"
        case_dir.mkdir()
        app = _make_app_with_description(case_dir)
        try:
            app.root.update()
            app._select_list_name("Edits")
            app.root.update()
            assert _continuation_lines(case_dir / "Edits.md")  # seeded

            _open_edit(app)
            _set_description(app, blank)
            app._edit_save_btn.invoke()
            app.root.update()

            assert app._edit_window is None
            items = app.controller.store.load("Edits")
            assert items[0] == ("Edit me", False, "")
            # No continuation lines remain in the .md file.
            assert _continuation_lines(case_dir / "Edits.md") == []
        finally:
            app._close_edit_dialog()
            app.root.destroy()


def test_edit_cancel_discards_description_change(tmp_path):
    app = _make_app_with_description(tmp_path)
    try:
        app.root.update()
        app._select_list_name("Edits")
        app.root.update()

        before = (tmp_path / "Edits.md").read_text()
        _open_edit(app)
        app._edit_entry.delete(0, "end")
        app._edit_entry.insert(0, "Should not persist")
        _set_description(app, "Discarded detail")
        app._edit_cancel_btn.invoke()
        app.root.update()

        assert app._edit_window is None
        assert app._edit_desc_text is None
        assert (tmp_path / "Edits.md").read_text() == before
        items = app.controller.store.load("Edits")
        assert items[0] == ("Edit me", False, "Old line one\nOld line two")
    finally:
        app._close_edit_dialog()
        app.root.destroy()


def test_edit_save_empty_title_ignores_description(tmp_path):
    app = _make_app_with_description(tmp_path)
    try:
        app.root.update()
        app._select_list_name("Edits")
        app.root.update()

        before = (tmp_path / "Edits.md").read_text()
        for text in ("", "   "):
            _open_edit(app)
            app._edit_entry.delete(0, "end")
            app._edit_entry.insert(0, text)
            _set_description(app, "Must not persist")
            app._edit_save_btn.invoke()
            app.root.update()
            assert app._edit_window is None

        # Neither title nor description persisted.
        assert (tmp_path / "Edits.md").read_text() == before
        items = app.controller.store.load("Edits")
        assert items[0] == ("Edit me", False, "Old line one\nOld line two")
        assert app._item_rows[0][2].cget("text") == "Edit me"
    finally:
        app._close_edit_dialog()
        app.root.destroy()
