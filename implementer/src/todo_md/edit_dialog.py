"""Edit dialog construction and lifecycle for the todo_md GUI.

Owns the modal edit Toplevel (pre-populated title entry, multi-line
description box with vertical scrollbar, save/cancel buttons, grab,
centering) plus the open /
save / close lifecycle (``open_dialog`` / ``save_dialog`` /
``close_dialog``) so ``TodoApp`` only delegates.

``app`` is the parent :class:`todo_md.app.TodoApp`; it is duck-typed
and never imported here.

``tkinter`` is imported lazily inside methods (never at module level) so
this module remains importable on headless machines without a display.
"""

from __future__ import annotations


class EditItemDialog:
    """Builds and owns the modal edit Toplevel for one item.

    ``on_save`` fires on Save (and the entry's <Return>); ``on_close``
    fires on Cancel and on the window's WM_DELETE_WINDOW protocol. Widgets
    are exposed as public attributes (``window``, ``entry``,
    ``desc_text``, ``desc_scroll``, ``save_btn``, ``cancel_btn``,
    ``resize_grip``) so the
    app — and tests via delegating app properties — can read or drive them.
    """

    def __init__(self, app, item, *, on_save, on_close) -> None:
        import tkinter as tk  # lazy: keep module importable headless
        from tkinter import ttk

        self.app = app
        root = app.root

        win = tk.Toplevel(root)
        if app._palette is not None:
            win.configure(bg=app._palette["bg"])
        win.title("Edit item")
        win.transient(root)
        self.window = win

        row = ttk.Frame(win, padding=10)
        row.pack(fill=tk.BOTH, expand=True)
        entry = ttk.Entry(row)
        entry.pack(fill=tk.X)
        entry.insert(0, item.text)
        self.entry = entry

        # Multi-line description box below the title. Plain tk.Text is not
        # ttk-styled, so apply the entry palette colors explicitly.
        desc_kwargs = {}
        if app._palette is not None:
            desc_kwargs = {
                "bg": app._palette["entry_bg"],
                "fg": app._palette["fg"],
                "insertbackground": app._palette["fg"],
                "highlightbackground": app._palette["btn_bg"],
            }
        # Sub-frame under the title entry so the text expands with the
        # window in BOTH dimensions (C3) while a vertical scrollbar pins
        # to its right edge.
        desc_frame = ttk.Frame(row)
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        desc_text = tk.Text(
            desc_frame, height=5, width=40, wrap=tk.WORD, undo=True, **desc_kwargs
        )
        desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        desc_scroll = ttk.Scrollbar(desc_frame, command=desc_text.yview)
        desc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        desc_text.configure(yscrollcommand=desc_scroll.set)
        desc_text.insert("1.0", item.description)
        self.desc_text = desc_text
        self.desc_scroll = desc_scroll

        # Visible resize grip in the very bottom strip: a raised frame
        # with the size cursor. Packed BEFORE the bottom button frame so
        # pack (bottom-side widgets follow call order) places it below.
        # On the clam-fallback path pin the palette bg; leave unset on the
        # native path so the window background shows through.
        grip_kwargs = {}
        if app._palette is not None:
            grip_kwargs = {"bg": app._palette["bg"]}
        # "bottom_right_corner" is a size cursor (the Motif-era
        # "size_rse_nw_se" alias was removed in Tk 9).
        resize_grip = tk.Frame(win, bd=1, relief=tk.RAISED, cursor="bottom_right_corner", **grip_kwargs)
        resize_grip.pack(side=tk.BOTTOM, anchor=tk.E)
        self.resize_grip = resize_grip

        bottom = ttk.Frame(win, padding=(10, 8))
        bottom.pack(side=tk.BOTTOM)
        save_btn = ttk.Button(bottom, text="save")
        save_btn.pack(side=tk.RIGHT, padx=(6, 0))
        cancel_btn = ttk.Button(bottom, text="cancel")
        cancel_btn.pack(side=tk.RIGHT)
        self.save_btn = save_btn
        self.cancel_btn = cancel_btn

        save_btn.config(command=on_save)
        cancel_btn.config(command=on_close)
        entry.bind("<Return>", lambda _e: on_save())
        win.protocol("WM_DELETE_WINDOW", on_close)

        win.grab_set()
        win.update()
        app._center_window_on_parent(win)

    def close(self) -> None:
        """Destroy the window if it still exists."""
        if self.window.winfo_exists():
            self.window.destroy()


def open_dialog(app, index: int) -> None:
    """Open a theme-aware modal edit dialog for the item at ``index``."""
    if app.current_list is None:
        return

    item = app.controller.open_list(app.current_list).items[index]
    app._edit = EditItemDialog(
        app, item, on_save=lambda: save_dialog(app), on_close=lambda: close_dialog(app)
    )
    app._edit_index = index


def save_dialog(app) -> None:
    """Persist title and description via controller.edit_item, then close."""
    if app._edit_window is None or app.current_list is None:
        return
    # tk.Text always appends a trailing newline; the controller strips.
    description = app._edit_desc_text.get("1.0", "end-1c")
    try:
        app.controller.edit_item(
            app.current_list,
            app._edit_index,
            app._edit_entry.get(),
            description,
        )
    except ValueError:
        pass  # empty/whitespace-only text: nothing is persisted
    close_dialog(app)
    app._refresh_items()


def close_dialog(app) -> None:
    """Teardown: destroy the window (if alive) and drop the holders."""
    if app._edit is not None:
        app._edit.close()
        app._edit = None
    app._edit_index = None
