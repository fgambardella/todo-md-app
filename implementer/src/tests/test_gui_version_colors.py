"""GUI test: version badge colors follow the theme (clam fallback path)."""

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def _find_version_label(app):
    import tkinter as tk

    for widget in _iter_widgets(app.root):
        if isinstance(widget, tk.Label) and str(widget.cget("text")).startswith("v"):
            return widget
    return None


def _iter_widgets(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _iter_widgets(child)


def _luminance(rgb, scale):
    r, g, b = rgb
    return (0.299 * r + 0.587 * g + 0.114 * b) / scale


def test_version_badge_colors_match_theme(tmp_path):
    import tkinter as tk  # noqa: F401  (ensures tkinter is importable here)

    store = MarkdownListStore(tmp_path)
    controller = TodoController(store)

    app = TodoApp(controller, config_dir=str(tmp_path / "config"))
    try:
        assert app._palette is not None, (
            "expected the clam fallback palette to be active on this machine"
        )
        for theme in ("light", "dark"):
            if app.theme != theme:
                app._on_toggle_theme()
            app.root.update()
            assert app.theme == theme

            label = _find_version_label(app)
            assert label is not None, f"version label missing in {theme} mode"

            scale = app.root.winfo_rgb("#ffffff")[0] or 1
            root_bg = app.root.winfo_rgb(app.root.cget("bg"))
            label_bg = app.root.winfo_rgb(label.cget("bg"))
            label_fg = app.root.winfo_rgb(label.cget("foreground"))
            main_fg = app.root.winfo_rgb(app._palette["fg"])

            # (1) label background equals root background (effective colors)
            assert label_bg == root_bg, (
                f"{theme}: label bg {label_bg} != root bg {root_bg}"
            )

            # (2) foreground is a plain gray (r == g == b), not pure white
            # or pure black in either theme
            r, g, b = label_fg
            assert r == g == b, f"{theme}: version fg {label_fg} is not a gray"
            assert (r, g, b) != (scale, scale, scale), "fg must not be pure white"
            assert (r, g, b) != (0, 0, 0), "fg must not be pure black"

            # (3) foreground sits strictly between the background and the
            # main text color: muted, visible, low-contrast
            lum_bg = _luminance(root_bg, scale)
            lum_fg = _luminance(label_fg, scale)
            lum_main = _luminance(main_fg, scale)
            lo, hi = sorted((lum_bg, lum_main))
            assert lo < lum_fg < hi, (
                f"{theme}: fg luminance {lum_fg:.3f} not between bg "
                f"{lum_bg:.3f} and main text {lum_main:.3f}"
            )
    finally:
        app.root.destroy()