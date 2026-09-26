"""GUI tests: destructive actions (list/item delete) require a yes/no confirmation.

Answering No must be a full no-op: no controller call, no refresh, no file change.
"""

from unittest.mock import patch

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def test_list_delete_declined_keeps_list(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    controller.create_list("Keep")
    controller.add_item("Keep", "item")

    app = TodoApp(controller, config_dir=str(tmp_path / "config"))
    try:
        app.root.update()
        app._select_list_name("Keep")
        app.root.update()

        assert len(app._item_rows) == 1
        with patch("tkinter.messagebox.askyesno", return_value=False) as ask:
            app._on_delete_list()
        app.root.update()

        # Confirmation was requested with the exact message, answered No.
        ask.assert_called_once_with(
            "Confirm deletion", 'Delete list "Keep" and all of its items?'
        )
        # No file change: the list file is still on disk with its item.
        assert (tmp_path / "Keep.md").is_file()
        content = (tmp_path / "Keep.md").read_text()
        assert "item" in content
        # Still listed in the sidebar and its items still shown.
        assert "Keep" in app.listbox.get(0, "end")
        assert app.current_list == "Keep"
        assert len(app._item_rows) == 1
        assert app._item_rows[0][2].cget("text") == "item"
    finally:
        app.root.destroy()


def test_item_delete_declined_keeps_item(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    controller.create_list("Keep")
    controller.add_item("Keep", "Alpha")
    controller.add_item("Keep", "Beta")

    app = TodoApp(controller, config_dir=str(tmp_path / "config"))
    try:
        app.root.update()
        app._select_list_name("Keep")
        app.root.update()

        assert len(app._item_rows) == 2
        with patch("tkinter.messagebox.askyesno", return_value=False) as ask:
            app._on_delete_item(0)
        app.root.update()

        # Confirmation was requested with the exact message, answered No.
        ask.assert_called_once_with("Confirm deletion", 'Delete item "Alpha"?')
        # No file change: both items remain on disk.
        content = (tmp_path / "Keep.md").read_text()
        assert "Alpha" in content
        assert "Beta" in content
        # Item row still present in the UI.
        assert len(app._item_rows) == 2
        assert app._item_rows[0][2].cget("text") == "Alpha"
        assert app._item_rows[1][2].cget("text") == "Beta"
    finally:
        app.root.destroy()
