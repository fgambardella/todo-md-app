"""GUI test: trash icon size, source transparency, and widget transparency."""

import os
from unittest.mock import patch

import tkinter as tk

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def test_trash_icon_size_transparency_and_click(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    controller.create_list("Trash")
    controller.add_item("Trash", "Alpha")
    controller.add_item("Trash", "Beta")

    app = TodoApp(controller, config_dir=str(tmp_path / "config"))
    try:
        app.root.update()
        app._select_list_name("Trash")
        app.root.update()

        # (a) SIZE: displayed icon ~18px
        assert 14 <= app._trash_image.width() <= 22
        assert 14 <= app._trash_image.height() <= 22

        # (b) SOURCE TRANSPARENCY: PNG IHDR color type byte (offset 25) is 6 or 4
        icon_path = os.path.join("todo_md", "assets", "trash_18.png")
        with open(icon_path, "rb") as fh:
            data = fh.read()
        assert data[:4] == b"\x89PNG"
        assert data[25] in (4, 6)

        # (c) WIDGET TRANSPARENCY: delete control is a tk.Label, not tk.Button
        assert len(app._item_rows) == 2
        for row in app._item_rows:
            del_ctrl = row[3]
            assert isinstance(del_ctrl, tk.Label)
            assert not isinstance(del_ctrl, tk.Button)

        # (d) CLICK: bound Button-1 handler removes the item and persists
        # (confirmation answered Yes)
        with patch("tkinter.messagebox.askyesno", return_value=True) as ask:
            app._item_rows[0][3].event_generate("<Button-1>")
        app.root.update()

        ask.assert_called_once_with("Confirm deletion", 'Delete item "Alpha"?')

        assert len(app._item_rows) == 1
        content = (tmp_path / "Trash.md").read_text()
        assert "Alpha" not in content
        assert "Beta" in content
    finally:
        app.root.destroy()