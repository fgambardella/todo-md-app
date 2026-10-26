"""List-sidebar widget construction for the todo_md GUI.

``build_sidebar`` is duck-typed against a ``TodoApp`` so this module never
imports :mod:`todo_md.app`; tkinter is imported lazily inside the function
so the module stays importable on headless machines.
"""

from __future__ import annotations


def build_sidebar(app) -> None:
    """Build the packed left "Lists:" frame on ``app.root``.

    Creates the left frame and packs, in order: the "Lists:" label, the
    list ``Listbox`` (``app.listbox``, ``<<ListboxSelect>>`` bound to
    ``app._on_select_list``), the new-list name entry
    (``app.new_name_entry``, ``<Return>`` to ``app._on_create_list``,
    muted placeholder via ``app._attach_placeholder``), the
    Create/Delete button row, the theme-toggle button
    (``app._theme_btn``), and the Settings button (``app._settings_btn``).
    """
    import tkinter as tk
    from tkinter import ttk

    left = ttk.Frame(app.root, padding=8)
    left.pack(side=tk.LEFT, fill=tk.Y)
    ttk.Label(left, text="Lists:").pack(anchor="w")

    app.listbox = tk.Listbox(left, width=22, height=14, exportselection=False)
    app.listbox.pack(fill=tk.X, pady=(2, 6))
    app.listbox.bind("<<ListboxSelect>>", app._on_select_list)

    app.new_name_entry = ttk.Entry(left, width=20)
    app.new_name_entry.pack(fill=tk.X)
    app.new_name_entry.bind("<Return>", lambda _e: app._on_create_list())
    app._attach_placeholder(
        app.new_name_entry, "Insert the name of a new list here"
    )

    btn_row = ttk.Frame(left)
    btn_row.pack(fill=tk.X, pady=(6, 0))
    ttk.Button(btn_row, text="Create", command=app._on_create_list).pack(
        side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2)
    )
    ttk.Button(btn_row, text="Delete", command=app._on_delete_list).pack(
        side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0)
    )

    app._theme_btn = ttk.Button(
        left, text=app._theme_button_text(), command=app._on_toggle_theme
    )
    app._theme_btn.pack(fill=tk.X, pady=(6, 0))

    # Settings button: opens the Toplevel settings window.
    app._settings_btn = ttk.Button(
        left, text="Settings", command=app._open_settings
    )
    app._settings_btn.pack(fill=tk.X, pady=(6, 0))
