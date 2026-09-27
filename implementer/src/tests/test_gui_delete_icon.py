"""GUI test: the per-item delete control is a transparent trash-icon label."""

import os
from unittest.mock import patch

import tkinter as tk

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def test_delete_control_is_trash_icon_label(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    controller.create_list("Del")
    controller.add_item("Del", "Alpha")
    controller.add_item("Del", "Beta")

    # Provisioned royalty-free icon exists and is a real PNG
    icon_path = os.path.join("todo_md", "assets", "trash_18.png")
    assert os.path.isfile(icon_path)
    with open(icon_path, "rb") as fh:
        assert fh.read(4) == b"\x89PNG"

    app = TodoApp(controller, config_dir=str(tmp_path / "config"))
    try:
        app.root.update()
        app._select_list_name("Del")
        app.root.update()

        assert len(app._item_rows) == 2
        for row in app._item_rows:
            assert len(row) == 4
            delete_ctrl = row[3]
            assert isinstance(delete_ctrl, tk.Label)
            assert str(delete_ctrl.cget("image"))  # non-empty image (photo)
            assert str(delete_ctrl.cget("text")) == ""

        # Delete by clicking the icon label (invokes the bound handler);
        # the confirmation dialog is answered Yes.
        with patch("tkinter.messagebox.askyesno", return_value=True) as ask:
            app._item_rows[0][3].event_generate("<Button-1>")
        app.root.update()

        ask.assert_called_once_with("Confirm deletion", 'Delete item "Alpha"?')

        assert len(app._item_rows) == 1
        assert app._item_rows[0][2].cget("text") == "Beta"

        content = (tmp_path / "Del.md").read_text()
        assert "Alpha" not in content
        assert "Beta" in content
    finally:
        app.root.destroy()