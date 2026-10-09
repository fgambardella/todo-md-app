"""Theme engine for the todo_md GUI (extracted from :mod:`todo_md.app`).

Holds the three pieces of theme logic the app previously mixed into
``TodoApp``: the switcher-button label, the fallback (clam) palette, and
the luminance-adaptive item text colors. Everything arrives as parameters
(``root``/widgets, the ``app`` holder); this module never imports
``todo_md.app`` and tkinter is imported lazily *inside* functions so the
module remains importable on headless machines without a display.
"""

from __future__ import annotations


def button_text(theme: str) -> str:
    """Label of the switcher button: the theme a click would switch TO."""
    return "🌙 Dark" if theme == "light" else "☀️ Light"


def palette_for(theme: str) -> dict:
    """The dark/light clam-fallback palette dict for ``theme``.

    Explicit colors are required on the fallback path because plain tk
    widgets resolve an unset background to a *system* color that does not
    flip with the requested appearance.
    """
    if theme == "dark":
        bg, fg = "#1e1e1e", "#f0f0f0"
        btn_bg, entry_bg = "#3c3c3c", "#383838"
        list_bg = "#2d2d2d"
    else:
        bg, fg = "#f5f5f5", "#000000"
        btn_bg, entry_bg = "#e0e0e0", "#ffffff"
        list_bg = "#ffffff"

    return {
        "bg": bg,
        "fg": fg,
        "btn_bg": btn_bg,
        "entry_bg": entry_bg,
        "list_bg": list_bg,
        # Low-contrast badge color: legible but unobtrusive on bg.
        "version_fg": "#555555" if theme == "dark" else "#9a9a9a",
        # Muted placeholder gray: legible on entry_bg yet clearly more
        # subdued than the real text color (fg) in either theme.
        "placeholder_fg": "#8a8a8a" if theme == "dark" else "#999999",
    }


def text_colors(root, reference_widget) -> tuple[str, str]:
    """Return (active_fg, done_fg) adaptive to the effective background."""
    import tkinter as tk

    try:
        # An unset tk bg resolves to the inherited (system) color.
        color = reference_widget.cget("bg")
    except tk.TclError:
        # ttk widgets expose no -bg option; fall back to their theme style.
        from tkinter import ttk

        color = ttk.Style().lookup(reference_widget.cget("style"), "background")
    if not color:
        color = "white"

    r, g, b = root.winfo_rgb(color)
    # winfo_rgb may report 0-255 or 0-65535 channels; normalize to 0-1.
    scale = root.winfo_rgb("#ffffff")[0] or 1
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / scale
    if luminance < 0.5:
        return ("#f0f0f0", "#b0b0b0")
    return ("#000000", "#808080")


def apply_theme(root, app) -> dict | None:
    """Apply ``app.theme`` ('dark'/'light') to the running GUI.

    Primary path: ``tk appappearance`` (Tk 9) — keeps the native aqua
    look in either theme.  Fallback (``tk.TclError``): ttk "clam"
    theme with explicit palettes, since plain tk widgets resolve an
    unset background to a *system* color that does not flip.

    ``app`` is duck-typed: it must expose ``theme`` and ``_palette``
    (plus the optional widgets this refresh touches, read through the
    same guards as before). Sets ``app._palette``: ``None`` on the
    native path (returned as ``None``); the :func:`palette_for` dict on
    the fallback path (returned).
    """
    import tkinter as tk
    from tkinter import ttk

    theme = app.theme

    try:
        root.tk.call("tk", "appappearance", theme)
        app._palette = None
        return None
    except tk.TclError:
        pass

    app._palette = palette_for(theme)
    bg, fg = app._palette["bg"], app._palette["fg"]
    btn_bg, entry_bg = app._palette["btn_bg"], app._palette["entry_bg"]
    list_bg = app._palette["list_bg"]
    if theme == "dark":
        btn_active = "#2e2e2e"
    else:
        btn_active = "#d0d0d0"

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background=bg, foreground=fg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    style.configure("TRadiobutton", background=bg, foreground=fg)
    # Keep radio labels on the section background even while interacting.
    style.map(
        "TRadiobutton",
        background=[("active", bg), ("pressed", bg), ("selected", bg)],
        foreground=[("active", fg), ("pressed", fg), ("selected", fg)],
    )
    style.configure("TButton", background=btn_bg, foreground=fg)
    # Clam's default 'activeBackground' state stays light, so hovering a
    # button in dark mode flashes a light fill and hides the light text;
    # map the active/pressed states to a slightly darker fill while
    # keeping the palette foreground. Normal appearance is unchanged.
    style.map(
        "TButton",
        background=[("active", btn_active), ("pressed", btn_active)],
        foreground=[("active", fg), ("pressed", fg)],
    )
    # The clam entry/spinbox field consumes the *element* option
    # fieldbackground for its fill; background/foreground alone leave
    # a light field in dark mode, making light text invisible.
    # In dark mode the entry fill (#383838) is deliberately slightly
    # lighter than the listbox background (#2d2d2d): with identical
    # colors the entries read as *darker* than the list (optical
    # effect), so a lighter entry fill corrects the perceived contrast.
    # ttk carets use insertcolor, not the plain tk insertbackground option.
    for name in ("TEntry", "TSpinbox"):
        style.configure(
            name,
            background=entry_bg,
            foreground=fg,
            fieldbackground=entry_bg,
            insertcolor=fg,
        )
    root.config(bg=bg)
    if app.settings_window is not None and app.settings_window.winfo_exists():
        app.settings_window.config(bg=bg)

    # Plain tk widgets inherit the *parent's effective* background;
    # set it explicitly so the item rows and their labels flip.
    items_frame = getattr(app, "items_frame", None)
    if items_frame is not None:
        items_frame.config(bg=bg)
    listbox = getattr(app, "listbox", None)
    if listbox is not None:
        listbox.config(bg=list_bg, fg=fg, highlightbackground=btn_bg)
    version_label = getattr(app, "version_label", None)
    if version_label is not None:
        version_label.config(bg=bg, foreground=app._palette["version_fg"])
    # Placeholder focus handlers set a widget-level foreground, so refresh
    # both displayed hints and real text when the palette changes.
    for entry, text in app._placeholders.items():
        if entry.winfo_exists():
            entry.configure(
                foreground=app._palette["placeholder_fg"] if entry.get() == text else fg
            )

    return app._palette
