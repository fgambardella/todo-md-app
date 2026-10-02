"""GUI tests: per-item edit icon and the modal edit dialog.

Covers: icon presence and positioning (left of the trash icon), the dialog
opening with the entry pre-populated with the item text, Save persisting
the new text to the .md file and closing, Cancel closing with no change,
and Save with empty/whitespace input persisting nothing.
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
