"""GUI tests: double-clicking an unfinished item's text opens the modal edit dialog.

Covers: double-click on an unfinished item opens the pre-populated modal,
Save persisting the edited text to the .md file, double-click on a completed
item opening no dialog (the autouse conftest dialog guard blocks any
unmocked native dialog as well), single-click toggle staying intact, and the
edit-icon path being unchanged.
"""

import tkinter as tk
from tkinter import ttk

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def _make_app(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    controller.create_list("DC")
    controller.add_item("DC", "Unfinished task")
    controller.add_item("DC", "Finished task")
    controller.toggle_item("DC", 1)  # "Finished task" becomes completed
    return TodoApp(controller, config_dir=str(tmp_path / "config"))


def _row_for(app, text):
    for row in app._item_rows:
        if row[2].cget("text") == text:
            return row
    raise AssertionError(f"no row with text {text!r}")


def _double_click(widget):
    """Generate the press/release pairs Tk recognises as a double-click.

    ``event_generate("<Double-Button-1>")" is rejected by Tcl, so a real
    double-click is simulated with two Button-1 press/release sequences.
    """
    for _ in range(2):
        widget.event_generate("<ButtonPress-1>")
        widget.event_generate("<ButtonRelease-1>")


def test_double_click_unfinished_opens_prepopulated_modal(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        app._select_list_name("DC")
        app.root.update()

        label = _row_for(app, "Unfinished task")[2]
        _double_click(label)
        app.root.update()

        assert app._edit_window is not None, "edit dialog should be open"
        assert app._edit_window.winfo_exists()
        assert app._edit_window.title() == "Edit item"
        assert isinstance(app._edit_entry, ttk.Entry)
        # Entry is pre-populated with the item's current text.
        assert app._edit_entry.get() == "Unfinished task"
    finally:
        app._close_edit_dialog()  # no-op when no dialog is open
        app.root.destroy()


def test_double_click_save_persists_edited_text(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        app._select_list_name("DC")
        app.root.update()

        label = _row_for(app, "Unfinished task")[2]
        _double_click(label)
        app.root.update()
        assert app._edit_window is not None

        app._edit_entry.delete(0, "end")
        app._edit_entry.insert(0, "Renamed via double-click")
        app._edit_save_btn.invoke()
        app.root.update()

        # Dialog closed; edited text persisted to the .md file.
        assert app._edit_window is None
        content = (tmp_path / "DC.md").read_text()
        assert "Renamed via double-click" in content
        assert "Unfinished task" not in content
        assert "Finished task" in content
        # Row refreshed with the new text.
        assert _row_for(app, "Renamed via double-click") is not None
    finally:
        app._close_edit_dialog()
        app.root.destroy()


def test_double_click_completed_opens_no_dialog(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        app._select_list_name("DC")
        app.root.update()

        label = _row_for(app, "Finished task")[2]
        _double_click(label)
        app.root.update()

        # No modal may open for a completed item; nothing to close.
        assert app._edit_window is None, "no dialog may open for completed items"
        assert app._edit_entry is None
        assert app._edit_desc_text is None
    finally:
        app.root.destroy()


def test_single_click_toggle_still_works(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        app._select_list_name("DC")
        app.root.update()

        row = _row_for(app, "Unfinished task")
        cb = row[1]
        cb.invoke()  # single click on the checkbutton
        app.root.update()

        # Toggled to completed, persisted, and no dialog opened.
        assert app._edit_window is None
        assert _row_for(app, "Unfinished task") is not None
        content = (tmp_path / "DC.md").read_text()
        assert "- [x] Unfinished task" in content
    finally:
        app.root.destroy()


def test_edit_icon_path_unchanged(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        app._select_list_name("DC")
        app.root.update()

        row = _row_for(app, "Unfinished task")
        edit_ctrl = row[4]
        # Edit icon is still the pencil Label (not the trash icon).
        assert isinstance(edit_ctrl, tk.Label)
        assert str(edit_ctrl.cget("image")) == str(app._edit_image)

        edit_ctrl.event_generate("<Button-1>")
        app.root.update()

        assert app._edit_window is not None, "edit icon should open the dialog"
        assert app._edit_window.title() == "Edit item"
        assert app._edit_entry.get() == "Unfinished task"
        # Description box is part of the same modal on the icon path.
        assert isinstance(app._edit_desc_text, tk.Text)
        assert app._edit_desc_text.get("1.0", "end-1c") == ""
    finally:
        app._close_edit_dialog()
        app.root.destroy()