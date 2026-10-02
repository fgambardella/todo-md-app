"""GUI test: item-row backgrounds follow theme switches (Tk 9 fallback fix).

On Tcl/Tk 9.0.4 `tk appappearance` raises TclError, so the clam fallback
runs. Plain tk widgets created under a dark system appearance pin their
default -bg to `systemWindowBackgroundColor`, which never re-resolves.
The app must therefore pass explicit palette colors to the row widgets.
"""

import json

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def lum(root, color):
    """Luminance of a color name, normalized to 0..1."""
    r, g, b = root.winfo_rgb(color)
    scale = root.winfo_rgb("#ffffff")[0] or 1
    return (0.299 * r + 0.587 * g + 0.114 * b) / scale


def _build_app(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    return controller, TodoApp(controller, config_dir=str(tmp_path / "config"))


def test_item_rows_follow_theme_switches(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "settings.json").write_text(
        json.dumps({"theme": "light"}), encoding="utf-8"
    )
    controller, app = _build_app(tmp_path)
    try:
        root = app.root
        controller.create_list("Rows")
        controller.add_item("Rows", "Alpha")
        controller.add_item("Rows", "Beta")
        controller.toggle_item("Rows", 1)  # Beta -> done
        app._select_list_name("Rows")
        root.update()

        # Force the dark baseline.
        app.theme = "dark"
        app._apply_theme("dark")
        app._refresh_items()
        root.update()

        _var, checkbutton, label, _del, _edit = app._item_rows[1]
        assert label.cget("text") == "Alpha"
        row_frame = checkbutton.master

        def _row_widgets():
            """Fetch the incomplete row (rows are rebuilt on every refresh)."""
            cb = app._item_rows[1][1]
            return cb.master, cb, app._item_rows[1][2]

        assert lum(root, row_frame.cget("bg")) < 0.5
        assert lum(root, checkbutton.cget("bg")) < 0.5

        # dark -> light
        app._on_toggle_theme()
        root.update()
        row_frame, checkbutton, label = _row_widgets()
        assert app.theme == "light"
        assert lum(root, row_frame.cget("bg")) > 0.5
        assert lum(root, checkbutton.cget("bg")) > 0.5
        assert lum(root, label.cget("bg")) > 0.5
        unchecked_fg = lum(root, label.cget("foreground"))
        assert unchecked_fg < 0.5
        assert abs(lum(root, label.cget("foreground")) - lum(root, label.cget("bg"))) >= 0.5

        # light -> dark again
        app._on_toggle_theme()
        root.update()
        row_frame, _cb, label = _row_widgets()
        assert app.theme == "dark"
        assert lum(root, row_frame.cget("bg")) < 0.5
        assert lum(root, label.cget("foreground")) > 0.5
    finally:
        app.root.destroy()
