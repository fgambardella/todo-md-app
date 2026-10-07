"""Settings window construction for the todo_md GUI.

Owns every widget of the Settings Toplevel (vars, lists-folder row, theme
radios, completed spinbox, Save/Cancel/Reset/Browse buttons, close
handler, centering) so ``TodoApp`` only instantiates and delegates. The
Save flow itself stays on ``TodoApp`` (see ``_settings_on_save``).

``tkinter`` is imported lazily inside methods (never at module level) so
this module remains importable on headless machines without a display.
"""

from __future__ import annotations

# Dynamic module lookup: patchable names (DEFAULT_DATA_DIR) must be read
# from the todo_md.app module at use time, never imported here.
import todo_md.app as app_module


class SettingsWindow:
    """Builds and owns the Toplevel settings window.

    ``app`` is the parent :class:`todo_md.app.TodoApp`. State holders
    (StringVar/IntVar) and widgets are exposed as public attributes so
    the app (and tests) can read or drive them.
    """

    def __init__(self, app) -> None:
        import tkinter as tk  # lazy: keep module importable headless
        from tkinter import ttk

        self.app = app
        root = app.root

        win = tk.Toplevel(root)
        if app._palette is not None:
            win.configure(bg=app._palette["bg"])
        win.title("Settings")
        win.transient(root)
        self.window = win

        # State holders: one var per control group (lists folder, theme,
        # completed-visible count).
        self.lists_dir_var = tk.StringVar(
            value=app.settings.lists_dir or app_module.DEFAULT_DATA_DIR
        )
        self.theme_var = tk.StringVar(value=app.settings.theme)
        self.completed_var = tk.IntVar(value=app.settings.completed_visible)

        # (a) lists-folder row: entry + Browse… + Reset to default --------
        folder_row = ttk.Frame(win, padding=(10, 8))
        folder_row.pack(fill=tk.X)
        ttk.Label(folder_row, text="Lists folder:").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 2)
        )
        ttk.Entry(folder_row, textvariable=self.lists_dir_var).grid(
            row=1, column=0, columnspan=3, sticky="we", pady=(0, 2)
        )
        ttk.Button(
            folder_row,
            text="Browse…",
            command=self._browse,
        ).grid(row=2, column=0, sticky="w", padx=(0, 4))
        self.reset_btn = ttk.Button(
            folder_row,
            text="Reset to default",
            command=lambda: self.lists_dir_var.set(app_module.DEFAULT_DATA_DIR),
        )
        self.reset_btn.grid(row=2, column=1, columnspan=2, sticky="w")
        folder_row.columnconfigure(0, weight=1)

        # (b) theme radiobuttons ------------------------------------------
        theme_row = ttk.LabelFrame(win, text="Theme", padding=(10, 8))
        theme_row.pack(fill=tk.X, padx=10)
        self.theme_rads = []
        for value, label in (("system", "System default"), ("light", "Light"), ("dark", "Dark")):
            rad = ttk.Radiobutton(
                theme_row, text=label, value=value, variable=self.theme_var
            )
            rad.pack(anchor="w")
            self.theme_rads.append(rad)

        # (c) completed-visible spinbox (0 = hide all completed) ----------
        cv_row = ttk.Frame(win, padding=(10, 8))
        cv_row.pack(fill=tk.X)
        ttk.Label(cv_row, text="Completed items visible:").pack(side=tk.LEFT)
        self.spinbox = ttk.Spinbox(
            cv_row, from_=0, to=999, width=6, textvariable=self.completed_var
        )
        self.spinbox.pack(side=tk.LEFT, padx=(8, 0))

        # (d) Save / Cancel ----------------------------------------------
        bottom = ttk.Frame(win, padding=(10, 8))
        bottom.pack(side=tk.BOTTOM)
        self.save_btn = ttk.Button(
            bottom, text="Save", command=self.app._settings_on_save
        )
        self.save_btn.pack(side=tk.RIGHT, padx=(6, 0))
        self.cancel_btn = ttk.Button(
            bottom, text="Cancel", command=self._on_close
        )
        self.cancel_btn.pack(side=tk.RIGHT)

        win.protocol("WM_DELETE_WINDOW", self._on_close)
        # Fit all controls using the current theme's font and widget metrics.
        win.update_idletasks()
        width, height = win.winfo_reqwidth(), win.winfo_reqheight()
        win.minsize(width, height)
        win.geometry(f"{max(420, width)}x{max(280, height)}")
        win.update()
        self.app._center_window_on_parent(win)

    def _browse(self) -> None:
        """Pick a directory via filedialog and store it in ``lists_dir_var``."""
        from tkinter import filedialog  # lazy: keep module importable headless

        path = filedialog.askdirectory(
            parent=self.window, initialdir=self.lists_dir_var.get()
        )
        if path:
            self.lists_dir_var.set(path)

    def _on_close(self) -> None:
        """Close handler: delegate the coordinated teardown to the app."""
        self.app._close_settings()

    def close(self) -> None:
        """Destroy the window if it still exists."""
        if self.window.winfo_exists():
            self.window.destroy()