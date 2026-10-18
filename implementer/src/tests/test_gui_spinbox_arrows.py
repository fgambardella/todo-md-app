"""GUI test: TSpinbox arrow glyphs stay visible in both clam themes (B1).

On this machine's Tcl/Tk 9.1 ``tk appappearance`` raises TclError, so the
clam fallback runs. Tk 9's C Arrow element falls back to a near-black
default when ``-arrowcolor`` is unset; against the dark theme's field
fill (#383838) the settings spinbox up/down arrows then render at a
contrast of about 1.3:1 — effectively invisible. The TSpinbox style must
therefore pin ``-arrowcolor`` to the palette foreground (light arrows in
dark, black in light) and keep it clearly separated from the field fill.

B2 additionally pins the *state maps*: TSpinbox inherits TCombobox's clam
maps, which flash a light "lighter" button-box fill on hover and make the
chevron disappear. State lookups are done through Tcl directly
(``ttk::style lookup ... <state>``) because ``ttk.Style.lookup`` mishandles
the state argument.

B3 replaces the hover fill with a dedicated ``spin_hover`` palette color
that is clearly lighter than the normal arrow-box fill in dark mode.
"""

import json

import pytest
from tkinter import ttk

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def lum(root, color):
    """Luminance of a color name, normalized to 0..1."""
    r, g, b = root.winfo_rgb(color)
    scale = root.winfo_rgb("#ffffff")[0] or 1
    return (0.299 * r + 0.587 * g + 0.114 * b) / scale


def _build_app(tmp_path, theme):
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "settings.json").write_text(
        json.dumps({"theme": theme}), encoding="utf-8"
    )
    store = MarkdownListStore(str(tmp_path / "lists"))
    controller = TodoController(store)
    return TodoApp(controller, config_dir=str(config_dir))


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_spinbox_arrowcolor_matches_palette_fg(tmp_path, theme):
    app = _build_app(tmp_path, theme)
    try:
        root = app.root
        # Force the requested clam-fallback theme.
        app.theme = theme
        app._apply_theme(theme)
        if app._palette is None:
            pytest.skip(
                "native `tk appappearance` path is active; "
                "this test exercises the clam fallback only"
            )
        root.update()

        # Open the real settings window so the assertion exercises the
        # live widget's style.
        app._open_settings()
        root.update()
        assert app._settings is not None
        spinbox = app._settings_spinbox
        assert spinbox.winfo_exists()

        arrowcolor = ttk.Style().lookup("TSpinbox", "arrowcolor")
        assert arrowcolor == app._palette["fg"]

        fieldbackground = ttk.Style().lookup("TSpinbox", "fieldbackground")
        assert abs(lum(root, arrowcolor) - lum(root, fieldbackground)) > 0.35

        # B2: active-state button box and chevron must stay legible.
        if app._palette is not None:
            active_bg = root.tk.call(
                "ttk::style", "lookup", "TSpinbox", "-background", "active"
            )
            active_arrow = root.tk.call(
                "ttk::style", "lookup", "TSpinbox", "-arrowcolor", "active"
            )
            assert active_bg == app._palette["spin_hover"]
            assert active_arrow == app._palette["fg"]
            assert abs(lum(root, active_arrow) - lum(root, active_bg)) > 0.35

            # The inherited -fieldbackground map must still resolve its
            # readonly/disabled entries to a real color.
            for state in ("readonly", "disabled"):
                value = root.tk.call(
                    "ttk::style", "lookup", "TSpinbox", "-fieldbackground", state
                )
                assert value
    finally:
        app.root.destroy()


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_spinbox_hover_fill_clearly_contrasts_normal_fill(tmp_path, theme):
    """B3: the active-state button-box fill must clearly differ from the
    normal-state fill in both themes."""
    app = _build_app(tmp_path, theme)
    try:
        root = app.root
        app.theme = theme
        app._apply_theme(theme)
        if app._palette is None:
            pytest.skip(
                "native `tk appappearance` path is active; "
                "this test exercises the clam fallback only"
            )
        root.update()

        normal_bg = root.tk.call("ttk::style", "lookup", "TSpinbox", "-background")
        active_bg = root.tk.call(
            "ttk::style", "lookup", "TSpinbox", "-background", "active"
        )
        assert active_bg == app._palette["spin_hover"]
        assert abs(lum(root, normal_bg) - lum(root, active_bg)) > 0.08

        active_arrow = root.tk.call(
            "ttk::style", "lookup", "TSpinbox", "-arrowcolor", "active"
        )
        assert abs(lum(root, active_arrow) - lum(root, active_bg)) > 0.35

        for state in ("readonly", "disabled"):
            value = root.tk.call(
                "ttk::style", "lookup", "TSpinbox", "-fieldbackground", state
            )
            assert value
    finally:
        app.root.destroy()
