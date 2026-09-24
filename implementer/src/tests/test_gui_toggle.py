"""GUI test: toggling an item updates the row UI (check state, gray, strikethrough)."""

import tkinter.font as tkfont
import tkinter.ttk  # noqa: F401  (ensure ttk available)

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def _parse_rgb(value: str) -> tuple:
    """Parse a tkinter color string into an (r, g, b) int tuple."""
    value = value.strip().lstrip("#")
    assert len(value) == 6, f"expected hex color, got {value!r}"
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _overstrike(label) -> bool:
    font = tkfont.Font(font=label.cget("font"))
    return bool(font.actual("overstrike"))


def test_toggle_updates_gui(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    controller.create_list("test-list")
    controller.add_item("test-list", "first item")
    controller.add_item("test-list", "second item")

    app = TodoApp(controller, config_dir=str(tmp_path / "config"))
    try:
        app.root.update()
        app._select_list_name("test-list")
        app.root.update()

        assert len(app._item_rows) == 2
        var, _cb, label, _del = app._item_rows[0]

        # Initially undone
        assert var.get() == 0
        assert not _overstrike(label)

        # Toggle item 0 to done
        app._on_toggle_item(0)
        app.root.update()

        var, _cb, label, _del = app._item_rows[0]
        assert var.get() == 1

        r, g, b = _parse_rgb(label.cget("foreground"))
        assert max(r, g, b) - min(r, g, b) <= 10, "foreground should be gray"

        assert _overstrike(label)

        # Item text preserved on the label
        assert label.cget("text") == "first item"

        # Second row untouched
        var2, _cb2, label2, _del2 = app._item_rows[1]
        assert var2.get() == 0
        assert not _overstrike(label2)

        # Toggle back to undone
        app._on_toggle_item(0)
        app.root.update()

        var, _cb, label, _del = app._item_rows[0]
        assert var.get() == 0
        assert not _overstrike(label)
    finally:
        app.root.destroy()
