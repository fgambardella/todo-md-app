"""Shared tkinter dialog helpers: dock icon and self-correcting centering.

tkinter is imported lazily inside each function so this module stays
importable headless (mirrors ``todo_md.app``).
"""

import os


def dock_icon_path() -> str:
    """Package-relative path to the PNG dock icon asset."""
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "assets", "dock_icon.png"
    )


def apply_dock_icon(root, icon_path: str):
    """Set the macOS dock icon from the PNG at ``icon_path`` (fail-soft).

    The caller resolves the icon path (see ``dock_icon_path``); this
    function only consumes it. ``PhotoImage`` cannot decode the source
    JPEG, so a PNG conversion (``dock_icon.png``) is committed alongside
    it. The returned image is kept alive by the caller
    (``self._dock_icon`` on the app) — a tkinter image held only by the
    interpreter would otherwise be garbage-collected. If the icon file is
    missing or unreadable, ``None`` is returned and the app runs normally.
    """
    import tkinter as tk

    try:
        photo = tk.PhotoImage(file=icon_path)
    except tk.TclError:
        return None
    try:
        root.iconphoto(True, photo)
    except tk.TclError:
        # iconphoto is unsupported on some platforms (e.g. X11); the
        # image is still kept alive, but its absence must never crash.
        pass
    return photo


def center_window_on_parent(parent_root, win) -> None:
    """Center ``win`` over ``parent_root``'s current on-screen rectangle.

    Call after the dialog's size geometry has been set (or after its
    first ``update``). The position is recomputed on every open from
    the live parent geometry, so a moved main window re-centers the
    dialog on the next open. Placement is self-correcting: after the
    initial ``geometry('+x+y')`` the actual on-screen rectangles are
    re-measured and one corrective nudge removes any window-manager
    frame offset (e.g. the ~title-bar-height shift on macOS).
    """
    win.update_idletasks()
    width, height = win.winfo_width(), win.winfo_height()
    if width < 2 or height < 2:  # not measured yet: use requested size
        width, height = win.winfo_reqwidth(), win.winfo_reqheight()
    px, py = parent_root.winfo_rootx(), parent_root.winfo_rooty()
    pw, ph = parent_root.winfo_width(), parent_root.winfo_height()
    x = px + (pw - width) // 2
    y = py + (ph - height) // 2
    win.geometry(f"+{x}+{y}")
    # Some window managers (macOS in particular) honor
    # ``geometry('+x+y')`` against the window frame, not the client area, so
    # the measured client origin ends up offset from the request (roughly a
    # title-bar height on macOS). Re-measure the actual on-screen
    # rectangles and subtract the residual centering error from the
    # requested origin, instead of hardcoding frame sizes.
    win.update_idletasks()
    ox, oy = win.winfo_rootx(), win.winfo_rooty()
    ow, oh = win.winfo_width(), win.winfo_height()
    if ow < 2 or oh < 2:
        ow, oh = width, height
    ex = ox + ow // 2 - (px + pw // 2)
    ey = oy + oh // 2 - (py + ph // 2)
    if ex or ey:
        win.geometry(f"+{x - ex}+{y - ey}")
