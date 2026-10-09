"""GUI for the todo_md package.

``TodoController`` is re-exported from ``controller.py``; ``TodoApp`` is a
tkinter frontend, imported lazily inside methods so this module stays
importable on headless machines.
"""

from __future__ import annotations

import os

from .models import visible_items
from .storage import MarkdownListStore, relocate_lists  # kept: frozen tests patch app.relocate_lists
from .controller import TodoController
from .settings import (
    Settings,
    VALID_THEMES,
    load_settings,
    resolve_theme,
    save_settings,  # headless module (stdlib only)
)
from .version import get_version  # headless module (no tkinter)
from .placeholders import PlaceholderBinder  # headless module (no tkinter)

__all__ = [
    "TodoController",
    "TodoApp",
    "run",
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_DATA_DIR",
    "startup_dirs",
    "visible_items",
]

# App data root: the config dir is FIXED here (settings.json lives in
# <root>/config/) and is never derived from, nor moved by, the lists dir.
DEFAULT_APP_ROOT = os.path.join(os.path.expanduser("~"), ".todo-md-app")
DEFAULT_CONFIG_DIR = os.path.join(DEFAULT_APP_ROOT, "config")
DEFAULT_DATA_DIR = os.path.join(DEFAULT_APP_ROOT, "lists")


def startup_dirs(config_dir: str | None = None) -> tuple[str, str, Settings]:
    """Startup ordering: load settings first, then derive the data dir.

    Returns ``(config_dir, data_dir, settings)``: the fixed config dir, the
    effective lists dir (created on demand), and the loaded settings.
    """
    cfg = config_dir if config_dir is not None else DEFAULT_CONFIG_DIR
    settings = load_settings(cfg)
    data_dir = settings.lists_dir or DEFAULT_DATA_DIR
    os.makedirs(data_dir, exist_ok=True)
    return cfg, data_dir, settings


def dock_icon_path() -> str:
    """Package-relative path to the PNG dock icon asset."""
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "assets", "dock_icon.png"
    )


def _valid_lists_dir_path(path: str) -> bool:
    """Whether ``path`` is an existing dir or can be created (makedirs).

    A path that exists but is not a directory (e.g. a plain file), or
    whose parent exists but is not a directory, can never become the
    lists folder and is rejected.
    """
    if os.path.isdir(path):
        return True
    if os.path.exists(path):
        return False
    parent = os.path.dirname(os.path.abspath(path))
    if os.path.exists(parent) and not os.path.isdir(parent):
        return False
    return True


def _normalize_dir(path: str) -> str:
    """Stable absolute form of a user-entered directory path (no symlink resolution)."""
    return os.path.abspath(os.path.expanduser(path))


def _same_dir(a: str, b: str) -> bool:
    """Whether two directories are the same location (symlinks included).

    A missing side (including a path below a non-directory) falls back to
    comparing normalized paths; other filesystem errors propagate.
    """
    try:
        return os.path.samefile(a, b)
    except (FileNotFoundError, NotADirectoryError):
        return _normalize_dir(a) == _normalize_dir(b)


def _has_markdown(directory: str) -> bool:
    """Whether ``directory`` holds top-level Markdown files; missing means no."""
    try:
        with os.scandir(directory) as entries:
            return any(e.name.endswith(".md") and e.is_file() for e in entries)
    except FileNotFoundError:
        return False


# ---------------------------------------------------------------------------
# GUI layer (tkinter imported lazily, never at module level)
# ---------------------------------------------------------------------------


class TodoApp:
    """tkinter front-end for :class:`TodoController`.

    Left frame: list of lists with create/delete controls. Right frame:
    checkbutton-backed item rows plus an entry+button to add items. The UI
    refreshes after every mutation; ``tkinter`` is imported inside methods
    so importing this module never requires a display.
    """

    def __init__(
        self,
        controller: TodoController,
        data_dir: str | None = None,
        config_dir: str | None = None,
    ) -> None:
        import tkinter as tk  # lazy: keep module importable headless

        self.controller = controller
        self.data_dir = data_dir if data_dir is not None else self.controller.data_dir
        # Config dir is FIXED at ~/.todo-md-app/config (or an explicit override); never derived from the lists dir.
        self.config_dir = (
            config_dir if config_dir is not None else DEFAULT_CONFIG_DIR
        )
        self.current_list: str | None = None
        # Settings window state holder (SettingsWindow while open, else None).
        self._settings = None
        # Edit dialog state holder (EditItemDialog while open, else None).
        self._edit = None
        self._edit_index: int | None = None
        self._item_rows: list[tuple] = []
        self._palette: dict | None = None
        # Placeholder mechanism holder; ``_placeholders`` is an alias for
        # the binder's map so existing readers (theme, tests) keep working.
        self._ph = PlaceholderBinder(self)
        self._placeholders = self._ph.map

        self.root = tk.Tk()
        self.root.title("TODO Markdown App")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._dock_icon = None
        self._apply_dock_icon()

        # Resolve the theme before building the UI so every widget starts in the right palette.
        self.settings = load_settings(self.config_dir)
        self.theme = resolve_theme(self.settings)
        self._apply_theme(self.theme)

        self._load_icon_assets()

        self._build_ui()
        # Re-apply after the UI exists: the fallback palette must set
        # explicit backgrounds on items_frame/listbox once they are created.
        self._apply_theme(self.theme)
        # Fit the fixed controls before loading items: long item text or list
        # length must not dictate the window's initial or minimum dimensions.
        self.root.update_idletasks()
        width, height = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        self.root.minsize(width, height)
        self.root.geometry(f"{max(700, width)}x{max(420, height)}")
        self.refresh_lists(select_first=True)

    def _load_icon_assets(self) -> None:
        """Cache the pre-sized 18x18 trash and edit icons (refs kept alive on self)."""
        import tkinter as tk  # lazy: keep module importable headless

        assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        self._trash_image = tk.PhotoImage(file=os.path.join(assets, "trash_18.png"))
        self._edit_image = tk.PhotoImage(file=os.path.join(assets, "edit_18.png"))

    # -- construction -----------------------------------------------------

    def _build_ui(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        # --- version badge: bottom-right, unobtrusive --------------------
        # Packed first (side=bottom) so the left/right frames fill only the remaining space.
        # Fallback (clam) path: pin bg to the palette (unset tk bg stays on the system color); native path: leave unset.
        version_fg = (self._palette or {}).get("version_fg", "#808080")
        from .item_row import bg_kwargs

        version_kwargs = bg_kwargs(
            self._palette["bg"] if self._palette is not None else None, key="background"
        )
        self.version_label = tk.Label(
            self.root,
            text=f"v{get_version()}",
            font=("", 8),
            foreground=version_fg,
            padx=8,
            **version_kwargs,
        )
        self.version_label.pack(side=tk.BOTTOM, anchor="e")

        # --- left frame: lists ------------------------------------------
        left = ttk.Frame(self.root, padding=8)
        left.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(left, text="Lists:").pack(anchor="w")

        self.listbox = tk.Listbox(left, width=22, height=14, exportselection=False)
        self.listbox.pack(fill=tk.X, pady=(2, 6))
        self.listbox.bind("<<ListboxSelect>>", self._on_select_list)

        self.new_name_entry = ttk.Entry(left, width=20)
        self.new_name_entry.pack(fill=tk.X)
        self.new_name_entry.bind("<Return>", lambda _e: self._on_create_list())
        self._attach_placeholder(
            self.new_name_entry, "Insert the name of a new list here"
        )

        btn_row = ttk.Frame(left)
        btn_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btn_row, text="Create", command=self._on_create_list).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2)
        )
        ttk.Button(btn_row, text="Delete", command=self._on_delete_list).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0)
        )

        self._theme_btn = ttk.Button(
            left, text=self._theme_button_text(), command=self._on_toggle_theme
        )
        self._theme_btn.pack(fill=tk.X, pady=(6, 0))

        # --- settings button: opens the Toplevel settings window ---------
        self._settings_btn = ttk.Button(
            left, text="Settings", command=self._open_settings
        )
        self._settings_btn.pack(fill=tk.X, pady=(6, 0))

        # --- right frame: items ------------------------------------------
        right = ttk.Frame(self.root, padding=8)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.title_label = ttk.Label(right, text="(no list selected)", font=("", 12, "bold"))
        self.title_label.pack(anchor="w")

        self.items_frame = tk.Frame(right)
        self.items_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 4))

        add_row = ttk.Frame(right)
        add_row.pack(fill=tk.X)
        self.new_item_entry = ttk.Entry(add_row)
        self.new_item_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.new_item_entry.bind("<Return>", lambda _e: self._on_add_item())
        self._attach_placeholder(self.new_item_entry, "Add a new todo item here")
        ttk.Button(add_row, text="Add", command=self._on_add_item).pack(
            side=tk.LEFT, padx=(6, 0)
        )

    # -- theme ------------------------------------------------------------

    def _theme_button_text(self) -> str:
        """Label of the switcher button: the theme a click would switch TO."""
        from .theme import button_text  # lazy: keep module importable headless

        return button_text(self.theme)

    def _apply_theme(self, theme: str) -> None:
        """Apply 'dark'/'light' to the running GUI (delegates to todo_md.theme.apply_theme)."""
        from .theme import apply_theme  # lazy: keep module importable headless

        # Sync so the theme engine can read it off the app holder.
        self.theme = theme
        self._palette = apply_theme(self.root, self)

    # -- dock icon --------------------------------------------------------

    def _apply_dock_icon(self) -> None:
        """Set the macOS dock icon from the bundled PNG asset (fail-soft; ref kept on self)."""
        from .dialogs import apply_dock_icon  # lazy: keep module importable headless

        self._dock_icon = apply_dock_icon(self.root)

    # -- entry placeholders ----------------------------------------------

    def _attach_placeholder(self, entry, text: str) -> None:
        """Show ``text`` as a muted placeholder on ``entry`` (delegates to the binder)."""
        self._ph.attach(entry, text)

    def _placeholder_fg(self) -> str:
        """Muted gray for placeholder text in the current (fallback) theme."""
        return self._ph.fg()

    def _entry_value(self, entry) -> str:
        """Strip the entry's text; a displayed placeholder counts as empty."""
        return self._ph.value(entry)

    def _on_entry_focus_in(self, entry) -> None:
        self._ph.focus_in(entry)

    def _on_entry_focus_out(self, entry) -> None:
        self._ph.focus_out(entry)

    def _restore_placeholder(self, entry) -> None:
        """Re-show the placeholder on an empty, unfocused entry (delegates to the binder)."""
        self._ph.restore(entry)

    def _on_toggle_theme(self) -> None:
        new = "light" if self.theme == "dark" else "dark"
        self.settings.theme = new
        save_settings(self.config_dir, self.settings)
        self.theme = new
        self._apply_theme(new)
        self._theme_btn.config(text=self._theme_button_text())
        # Re-resolve the luminance-adaptive label colors.
        self._refresh_items()

    def _center_window_on_parent(self, win) -> None:
        """Center ``win`` over the live main window (delegates to dialogs.center_window_on_parent)."""
        from .dialogs import center_window_on_parent  # lazy: keep module importable headless

        win.update_idletasks()
        center_window_on_parent(self.root, win)

    # -- settings window --------------------------------------------------

    @property
    def settings_window(self):
        """The live Settings Toplevel, or None while the window is closed."""
        return self._settings.window if self._settings is not None else None

    @staticmethod
    def _lists_dir_setting(path: str) -> str | None:
        """Persisted form of an effective directory: None for the default."""
        from . import settings_window as sw  # lazy: keep module importable headless

        return sw.lists_dir_setting(path)

    @property
    def _settings_lists_dir_var(self):
        return self._settings.lists_dir_var

    @property
    def _settings_theme_var(self):
        return self._settings.theme_var

    @property
    def _settings_theme_rads(self):
        return self._settings.theme_rads

    @property
    def _settings_completed_var(self):
        return self._settings.completed_var

    @property
    def _settings_spinbox(self):
        return self._settings.spinbox

    @property
    def _settings_save_btn(self):
        return self._settings.save_btn

    @property
    def _settings_cancel_btn(self):
        return self._settings.cancel_btn

    @property
    def _settings_reset_btn(self):
        return self._settings.reset_btn

    def _open_settings(self) -> None:
        """Open the Toplevel settings window (single instance; construction in SettingsWindow)."""
        if (
            self._settings is not None
            and self._settings.window.winfo_exists()
        ):
            self._settings.window.lift()
            return
        from .settings_window import SettingsWindow  # lazy: keep headless

        self._settings = SettingsWindow(self)

    def _close_settings(self) -> None:
        """Teardown: destroy the window (if alive) and drop the holder."""
        if self._settings is not None:
            self._settings.close()
            self._settings = None

    # -- list-frame handlers ----------------------------------------------

    def refresh_lists(self, select_first: bool = False) -> None:
        """Repopulate the listbox from the controller/store."""
        self.listbox.delete(0, "end")
        try:
            names = self.controller.list_names()
            for name in names:
                self.listbox.insert("end", name)

            if select_first and names:
                self._select_list_name(names[0])
            elif self.current_list in names:
                self._select_list_name(self.current_list)
            else:
                self.current_list = None
                self._clear_items()
        except (OSError, UnicodeError):
            self.listbox.delete(0, "end")
            self.current_list = None
            self._clear_items()
            raise

    def _selected_name(self) -> str | None:
        sel = self.listbox.curselection()
        return self.listbox.get(sel[0]) if sel else None

    def _on_select_list(self, _event=None) -> None:
        name = self._selected_name()
        if name is not None:
            self._select_list_name(name)

    def _select_list_name(self, name: str) -> None:
        names = self.listbox.get(0, "end")
        self.listbox.selection_clear(0, "end")
        if name in names:
            index = names.index(name)
            self.listbox.selection_set(index)
            self.listbox.see(index)
        self.current_list = name
        self.title_label.config(text=name)
        self._refresh_items()

    def _on_create_list(self) -> None:
        name = self._entry_value(self.new_name_entry)
        if not name:
            return
        try:
            self.controller.create_list(name)
        except FileExistsError:
            return
        self.new_name_entry.delete(0, "end")
        self._restore_placeholder(self.new_name_entry)
        self.refresh_lists(select_first=False)
        self._select_list_name(name)

    def _on_delete_list(self) -> None:
        name = self._selected_name()
        if name is None:
            return
        from tkinter import messagebox  # lazy: keep module importable headless

        if not messagebox.askyesno(
            "Confirm deletion", f'Delete list "{name}" and all of its items?'
        ):
            return
        self.controller.delete_list(name)
        self.refresh_lists(select_first=True)

    # -- item-frame handlers ----------------------------------------------

    def _clear_items(self) -> None:
        for widget in self.items_frame.winfo_children():
            widget.destroy()
        self._item_rows = []
        self.title_label.config(text="(no list selected)")

    def _text_colors(self, reference_widget) -> tuple[str, str]:
        """Return (active_fg, done_fg) adaptive to the effective background."""
        from .theme import text_colors  # lazy: keep module importable headless

        return text_colors(self.root, reference_widget)

    def _refresh_items(self) -> None:
        for widget in self.items_frame.winfo_children():
            widget.destroy()
        self._item_rows = []
        from .item_row import rebuild_rows  # lazy: keep module importable headless

        rebuild_rows(self)

    def _on_toggle_item(self, index: int) -> None:
        self.controller.toggle_item(self.current_list, index)
        self._refresh_items()

    def _on_delete_item(self, index: int) -> None:
        from tkinter import messagebox  # lazy: keep module importable headless

        text = self.controller.open_list(self.current_list).items[index].text
        if not messagebox.askyesno("Confirm deletion", f'Delete item "{text}"?'):
            return
        self.controller.remove_item(self.current_list, index)
        self._refresh_items()

    def _on_edit_item(self, index: int) -> None:
        """Open the modal edit dialog for the item at ``index``."""
        self._open_edit_dialog(index)

    def _on_item_double_click(self, index: int) -> None:
        """Open the edit dialog when an unfinished item's text is double-clicked."""
        item = self.controller.open_list(self.current_list).items[index]
        if item.done:
            return
        self._on_edit_item(index)

    @property
    def _edit_window(self):
        return self._edit.window if self._edit is not None else None

    @property
    def _edit_entry(self):
        return self._edit.entry if self._edit is not None else None

    @property
    def _edit_desc_text(self):
        return self._edit.desc_text if self._edit is not None else None

    @property
    def _edit_save_btn(self):
        return self._edit.save_btn if self._edit is not None else None

    @property
    def _edit_cancel_btn(self):
        return self._edit.cancel_btn if self._edit is not None else None

    def _open_edit_dialog(self, index: int) -> None:
        """Open a theme-aware modal edit dialog (construction in EditItemDialog)."""
        if self.current_list is None:
            return
        from .edit_dialog import EditItemDialog  # lazy: keep module importable headless

        item = self.controller.open_list(self.current_list).items[index]
        self._edit = EditItemDialog(
            self, item, on_save=self._on_edit_save, on_close=self._close_edit_dialog
        )
        self._edit_index = index

    def _on_edit_save(self) -> None:
        """Persist title and description via controller.edit_item, then close."""
        if self._edit_window is None or self.current_list is None:
            return
        # tk.Text always appends a trailing newline; the controller strips.
        description = self._edit_desc_text.get("1.0", "end-1c")
        try:
            self.controller.edit_item(
                self.current_list,
                self._edit_index,
                self._edit_entry.get(),
                description,
            )
        except ValueError:
            pass  # empty/whitespace-only text: nothing is persisted
        self._close_edit_dialog()
        self._refresh_items()

    def _close_edit_dialog(self) -> None:
        """Teardown: destroy the window (if alive) and drop the holders."""
        if self._edit is not None:
            self._edit.close()
            self._edit = None
        self._edit_index = None

    def _on_add_item(self) -> None:
        if self.current_list is None:
            return
        text = self._entry_value(self.new_item_entry)
        if not text:
            return
        self.controller.add_item(self.current_list, text)
        self.new_item_entry.delete(0, "end")
        self._restore_placeholder(self.new_item_entry)
        self._refresh_items()

    # -- lifecycle ----------------------------------------------------------

    def _on_close(self) -> None:
        self.root.destroy()

    def mainloop(self) -> None:
        """Run the tkinter main loop."""
        self.root.mainloop()


def run(config_dir: str | None = None) -> None:
    """Build the controller + :class:`TodoApp` and start the main loop."""
    cfg, data_dir, _settings = startup_dirs(config_dir)
    store = MarkdownListStore(data_dir)
    controller = TodoController(store, data_dir=data_dir)
    app = TodoApp(controller, data_dir=data_dir, config_dir=cfg)
    app.mainloop()
