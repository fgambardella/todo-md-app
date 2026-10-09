"""Edit dialog construction for the todo_md GUI.

Owns the modal edit Toplevel (pre-populated title entry, multi-line
description box, save/cancel buttons, grab, centering) so ``TodoApp``
only instantiates and delegates.

``app`` is the parent :class:`todo_md.app.TodoApp`; it is duck-typed
(``app.root`` / ``app._palette``) and never imported here.

``tkinter`` is imported lazily inside methods (never at module level) so
this module remains importable on headless machines without a display.
"""

from __future__ import annotations


class EditItemDialog:
    """Builds and owns the modal edit Toplevel for one item.

    ``on_save`` fires on Save (and the entry's <Return>); ``on_close``
    fires on Cancel and on the window's WM_DELETE_WINDOW protocol. Widgets
    are exposed as public attributes (``window``, ``entry``,
    ``desc_text``, ``save_btn``, ``cancel_btn``) so the app — and tests
    via delegating app properties — can read or drive them.
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
        row.pack(fill=tk.X)
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
        desc_text = tk.Text(
            row, height=5, width=40, wrap=tk.WORD, undo=True, **desc_kwargs
        )
        desc_text.pack(fill=tk.X, pady=(8, 0))
        desc_text.insert("1.0", item.description)
        self.desc_text = desc_text

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
