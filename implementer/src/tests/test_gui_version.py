"""GUI test: bottom-right version label in TodoApp."""

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore
from todo_md.version import VERSION_PATH


def _iter_widgets(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _iter_widgets(child)


def _find_version_label(app):
    """Find the non-interactive label whose text starts with 'v'."""
    import tkinter as tk

    for w in _iter_widgets(app.root):
        if isinstance(w, tk.Label) and str(w.cget("text")).startswith("v"):
            return w
    return None


def _font_size(widget):
    f = widget.cget("font")
    if isinstance(f, (list, tuple)):
        return int(f[1])
    digits = "".join(ch for ch in str(f) if ch.isdigit())
    return int(digits or 0)


def test_version_label_present_and_placed(tmp_path):
    import tkinter as tk

    store = MarkdownListStore(tmp_path)
    controller = TodoController(store)
    controller.create_list("work")

    app = TodoApp(controller, config_dir=str(tmp_path / "config"))
    app.root.update()
    try:
        # (a) the version label exists
        label = _find_version_label(app)
        assert label is not None, "expected a version label in the window"
        assert not label.winfo_children(), "version label must be non-interactive"

        # (b) text starts with 'v' and contains the current VERSION content
        version = VERSION_PATH.read_text(encoding="utf-8").strip()
        text = str(label.cget("text"))
        assert text.startswith("v")
        assert version in text

        # (c) small, unobtrusive font
        assert _font_size(label) <= 10

        # (d) pinned near the bottom of the window
        root_h = app.root.winfo_height()
        bottom_edge = label.winfo_y() + label.winfo_height()
        assert root_h - bottom_edge <= 10, (
            f"version label bottom ({bottom_edge}) should be near root height "
            f"({root_h})"
        )
        # ...and on the right-hand side (anchor=e)
        root_w = app.root.winfo_width()
        assert label.winfo_x() >= root_w // 2, "version label should be right-aligned"
    finally:
        app.root.destroy()