"""GUI layout tests: item label anchoring, expansion, and full text."""

import pytest

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


LONG_TEXT = (
    "This is an intentionally very long todo item text that is over one hundred "
    "and twenty characters long so we can verify it stays fully visible on a "
    "single line in the tkinter row widget"
)


def test_item_label_layout(tmp_path):
    assert len(LONG_TEXT) >= 120, "test text must be 120+ chars"

    store = MarkdownListStore(tmp_path)
    controller = TodoController(store)
    controller.create_list("work")
    controller.add_item("work", LONG_TEXT)

    app = TodoApp(controller, config_dir=str(tmp_path / "config"))
    app.root.update()
    try:
        assert app._item_rows, "expected at least one item row"
        _var, checkbutton, label, _del = app._item_rows[0]

        # Label anchored left
        assert label.cget("anchor") == "w"

        # Label stretches across the row
        info = label.pack_info()
        assert "x" in info.get("fill", "")
        assert info.get("expand") == 1

        # No truncation: full 120+ char text visible
        assert label.cget("text") == LONG_TEXT

        # Checkbutton packed left with modest padding
        cb_info = checkbutton.pack_info()
        assert cb_info.get("side") == "left"
        assert cb_info.get("padx") != 0

        # Row frame packed with anchor w, fill x in items_frame
        row = label.master
        row_info = row.pack_info()
        assert row_info.get("anchor") == "w"
        assert "x" in row_info.get("fill", "")
    finally:
        app.root.destroy()