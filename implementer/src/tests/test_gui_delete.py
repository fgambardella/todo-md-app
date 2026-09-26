"""GUI test: deleting an item via the row's delete button updates UI and .md file."""

from unittest.mock import patch

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def test_delete_item_removes_from_ui_and_file(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    controller.create_list("X")
    controller.add_item("X", "first")
    controller.add_item("X", "second")

    app = TodoApp(controller, config_dir=str(tmp_path / "config"))
    try:
        app.root.update()
        app._select_list_name("X")
        app.root.update()

        assert len(app._item_rows) == 2
        for row in app._item_rows:
            assert len(row) == 4
            delete_button = row[3]
            # 4th element is a widget
            assert delete_button is not None
            assert delete_button.winfo_exists()
            # Delete control is now an image (trash icon) button, not 'x' text
            assert str(delete_button.cget("image"))
            assert str(delete_button.cget("text")) not in ("x", "X")

        # Delete the first item (confirmation answered Yes)
        with patch("tkinter.messagebox.askyesno", return_value=True) as ask:
            app._on_delete_item(0)
        app.root.update()

        ask.assert_called_once_with("Confirm deletion", 'Delete item "first"?')

        assert len(app._item_rows) == 1
        assert app._item_rows[0][2].cget("text") == "second"

        # On-disk file reflects the deletion
        content = (tmp_path / "X.md").read_text()
        assert "first" not in content
        assert "second" in content
    finally:
        app.root.destroy()
