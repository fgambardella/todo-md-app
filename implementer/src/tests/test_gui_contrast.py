"""GUI test: item label foreground adapts to the effective background color."""

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def lum(root, color):
    """Relative luminance of a color name or an (r, g, b) tuple."""
    if isinstance(color, str):
        r, g, b = root.winfo_rgb(color)
    else:
        r, g, b = color
    return 0.299 * r + 0.587 * g + 0.114 * b


def test_label_foreground_adapts_to_background(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    controller.create_list("Contrast")
    controller.add_item("Contrast", "Alpha")
    controller.add_item("Contrast", "Beta")
    controller.toggle_item("Contrast", 1)  # Beta is done

    app = TodoApp(controller)
    try:
        root = app.root
        app._select_list_name("Contrast")

        # Case A: light background -> dark text
        app.items_frame.config(bg="#ffffff")
        app._refresh_items()
        root.update()

        _var, _cb, active_label, _del = app._item_rows[0]
        assert lum(root, active_label.cget("foreground")) < 0.5
        bg_lum = lum(root, root.winfo_rgb(active_label.cget("bg")))
        assert abs(lum(root, active_label.cget("foreground")) - bg_lum) >= 0.5

        # Case B: dark background -> light text
        app.items_frame.config(bg="#1e1e1e")
        app._refresh_items()
        root.update()

        _var, _cb, active_label, _del = app._item_rows[0]
        assert lum(root, active_label.cget("foreground")) > 0.5

        _var, _cb, done_label, _del = app._item_rows[1]
        assert lum(root, done_label.cget("foreground")) >= 0.3

        bg_lum = lum(root, root.winfo_rgb(active_label.cget("bg")))
        assert abs(lum(root, active_label.cget("foreground")) - bg_lum) >= 0.5
    finally:
        app.root.destroy()