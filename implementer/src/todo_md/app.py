"""Controller and GUI for the todo_md package.

``TodoController`` is pure logic (no GUI imports). ``TodoApp`` is a
``tkinter`` frontend; tkinter is imported lazily *inside* methods so the
module remains importable on headless machines without a display.
"""

from __future__ import annotations

import os

from .models import TodoItem, TodoList
from .storage import MarkdownListStore, relocate_lists
from .settings import (
    Settings,
    VALID_THEMES,
    load_settings,
    resolve_theme,
    save_settings,  # headless module (stdlib only)
)
from .version import get_version  # headless module (no tkinter)

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

    Returns ``(config_dir, data_dir, settings)`` where:

    * ``config_dir`` is the fixed config dir (``~/.todo-md-app/config`` by
      default, or an explicit override) — it is *never* inside the lists
      dir and changing the lists dir never moves the settings file;
    * ``data_dir`` is the effective lists dir: ``settings.lists_dir`` when
      saved, else ``~/.todo-md-app/lists`` (created on demand).

    Headless (no tkinter) so the startup flow is testable without a
    display. Callers build the store/controller from the returned
    ``data_dir``.
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


def visible_items(
    items: list[TodoItem], completed_visible: int
) -> list[TodoItem]:
    """Show the newest N completions, oldest-first, then all incomplete items.

    Relative completed order in ``items`` records completion order, including
    legacy interleaved files. ``completed_visible`` must be >= 0; zero hides
    all completions. Incomplete items keep their relative order.

    This never touches storage: the on-disk list keeps every item; the
    result is a new list (never the input) for display only.
    """
    if completed_visible < 0:
        raise ValueError(f"completed_visible must be >= 0, got {completed_visible!r}")
    completed = [item for item in items if item.done]
    incomplete = [item for item in items if not item.done]
    return (completed[-completed_visible:] if completed_visible else []) + incomplete


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


class TodoController:
    """Mediates between the user (or UI) and the MarkdownListStore.

    All methods that load/mutate a list follow the pattern:
    load -> mutate -> persist via ``store.save``.
    """

    def __init__(
        self, store: MarkdownListStore, data_dir: str | None = None
    ) -> None:
        self.store = store
        self.data_dir = data_dir if data_dir is not None else store.data_dir

    def change_lists_dir(self, new_dir: str | os.PathLike[str], move: bool) -> None:
        """Switch storage after relocation succeeds; equivalent paths are a no-op.

        Errors propagate without changing either binding. Relocation is per-file,
        so an error can still leave some lists at the destination; no rollback is
        attempted. Settings persistence is the caller's responsibility.
        """
        old_dir = self.store.data_dir
        try:
            if os.path.samefile(old_dir, new_dir):
                return
        except FileNotFoundError:
            pass  # Relocation handles missing source/destination directories.

        relocate_lists(old_dir, new_dir, move)
        new_store = MarkdownListStore(new_dir)
        self.store = new_store
        self.data_dir = new_store.data_dir

    # -- list-level operations -------------------------------------------

    def list_names(self) -> list[str]:
        """Return the names of all stored lists, sorted."""
        return self.store.lists()

    def open_list(self, name: str) -> TodoList:
        """Load a list into a TodoList of TodoItem objects."""
        todo_list = TodoList(name=name)
        for text, done, description in self.store.load(name):
            todo_list.items.append(
                TodoItem(text=text, done=done, description=description)
            )
        return todo_list

    def create_list(self, name: str) -> None:
        """Create an empty list; the name must be non-empty."""
        if not name or not name.strip():
            raise ValueError("list name must not be empty")
        self.store.create(name)

    def delete_list(self, name: str) -> None:
        """Delete a list."""
        self.store.delete(name)

    # -- item-level operations (load -> mutate -> save) -------------------

    def _load_and_save(self, name: str, mutate) -> TodoList:
        todo_list = self.open_list(name)
        mutate(todo_list)
        self.store.save(
            name, [(item.text, item.done, item.description) for item in todo_list.items]
        )
        return todo_list

    def add_item(self, name: str, text: str) -> TodoItem:
        """Add an item to the list and persist the change."""
        if not text or not text.strip():
            raise ValueError("todo item text must not be empty")

        def _mutate(todo_list: TodoList) -> None:
            todo_list.add_item(text)

        todo_list = self._load_and_save(name, _mutate)
        return todo_list.items[-1]

    def toggle_item(self, name: str, index: int) -> TodoItem:
        """Flip the done state of the item at ``index`` and persist it."""

        toggled = None

        def _mutate(todo_list: TodoList) -> None:
            nonlocal toggled
            toggled = todo_list.toggle(index)

        self._load_and_save(name, _mutate)
        return toggled

    def edit_item(
        self, name: str, index: int, text: str, description: str = ''
    ) -> TodoItem:
        """Replace the text (and optionally the description) at ``index``.

        Empty or whitespace-only text is rejected before anything is
        loaded or persisted. Saving unchanged text *and* unchanged
        description (ignoring surrounding whitespace) is a no-op: nothing
        is written; a description-only change is still persisted.
        """
        stripped = (text or "").strip()
        if not stripped:
            raise ValueError("todo item text must not be empty")
        stripped_desc = (description or "").strip()

        todo_list = self.open_list(name)
        item = todo_list.items[index]
        if item.text == stripped and item.description == stripped_desc:
            return item

        todo_list.edit(index, stripped, stripped_desc)
        self.store.save(
            name, [(i.text, i.done, i.description) for i in todo_list.items]
        )
        return todo_list.items[index]

    def remove_item(self, name: str, index: int) -> TodoItem:
        """Remove the item at ``index`` and persist the change."""

        removed = None

        def _mutate(todo_list: TodoList) -> None:
            nonlocal removed
            removed = todo_list.remove(index)

        self._load_and_save(name, _mutate)
        return removed


# ---------------------------------------------------------------------------
# GUI layer (tkinter imported lazily, never at module level)
# ---------------------------------------------------------------------------


class TodoApp:
    """tkinter front-end for :class:`TodoController`.

    Left frame: list of lists with create/delete controls.
    Right frame: checkbutton-backed item rows plus an entry+button to add
    items. The UI refreshes after every mutation.

    ``tkinter`` is imported inside methods so constructing / importing
    this class's module never requires a display.
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
        # Theme settings live in a dedicated config dir that is FIXED at
        # ~/.todo-md-app/config (or an explicit override): it is never
        # derived from the lists dir, so changing the lists path never
        # moves the settings file.
        self.config_dir = (
            config_dir if config_dir is not None else DEFAULT_CONFIG_DIR
        )
        self.current_list: str | None = None
        self.settings_window = None
        # Edit dialog state (None while no edit modal is open).
        self._edit_window = None
        self._edit_index: int | None = None
        self._edit_entry = None
        self._edit_desc_text = None
        self._edit_save_btn = None
        self._edit_cancel_btn = None
        self._item_rows: list[tuple] = []
        self._palette: dict | None = None
        # entry widget -> its placeholder text (empty fields show this muted
        # hint; a displayed placeholder counts as "empty" for submission).
        self._placeholders: dict = {}

        self.root = tk.Tk()
        self.root.title("TODO Markdown App")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._dock_icon = None
        self._apply_dock_icon()

        # Theme: load settings and resolve (system detection is never
        # persisted) before the UI is built so every widget starts in the
        # right palette.
        self.settings = load_settings(self.config_dir)
        self.theme = resolve_theme(self.settings)
        self._apply_theme(self.theme)

        # Cached trash-bin icon (pre-sized 18x18 asset; source 512x512 kept in assets/).
        self._trash_image = tk.PhotoImage(
            file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "trash_18.png")
        )
        # Cached pencil edit icon (pre-sized 18x18 asset; source 512x512 kept in assets/).
        self._edit_image = tk.PhotoImage(
            file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "edit_18.png")
        )

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

    # -- construction -----------------------------------------------------

    def _build_ui(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        # --- version badge: bottom-right, unobtrusive --------------------
        # Packed first (side=bottom) so the left/right frames fill only the
        # remaining space and the existing layout is undisturbed.
        # Fallback (clam) path: pin the background to the palette bg, since an
        # unset tk bg stays on the system color and does not flip. Native path
        # (self._palette is None): leave the background unset so it inherits
        # the root and flips with `tk appappearance`.
        version_fg = (self._palette or {}).get("version_fg", "#808080")
        version_kwargs = (
            {"background": self._palette["bg"]} if self._palette is not None else {}
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
        return "🌙 Dark" if self.theme == "light" else "☀️ Light"

    def _apply_theme(self, theme: str) -> None:
        """Apply 'dark'/'light' to the running GUI.

        Primary path: ``tk appappearance`` (Tk 9) — keeps the native aqua
        look in either theme.  Fallback (``tk.TclError``): ttk "clam"
        theme with explicit palettes, since plain tk widgets resolve an
        unset background to a *system* color that does not flip.
        """
        import tkinter as tk
        from tkinter import ttk

        try:
            self.root.tk.call("tk", "appappearance", theme)
            self._palette = None
            return
        except tk.TclError:
            pass

        if theme == "dark":
            bg, fg = "#1e1e1e", "#f0f0f0"
            btn_bg, entry_bg = "#3c3c3c", "#383838"
            list_bg = "#2d2d2d"
            btn_active = "#2e2e2e"
        else:
            bg, fg = "#f5f5f5", "#000000"
            btn_bg, entry_bg = "#e0e0e0", "#ffffff"
            list_bg = "#ffffff"
            btn_active = "#d0d0d0"

        self._palette = {
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

        style = ttk.Style(self.root)
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
        self.root.config(bg=bg)
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.config(bg=bg)

        # Plain tk widgets inherit the *parent's effective* background;
        # set it explicitly so the item rows and their labels flip.
        items_frame = getattr(self, "items_frame", None)
        if items_frame is not None:
            items_frame.config(bg=bg)
        listbox = getattr(self, "listbox", None)
        if listbox is not None:
            listbox.config(bg=list_bg, fg=fg, highlightbackground=btn_bg)
        version_label = getattr(self, "version_label", None)
        if version_label is not None:
            version_label.config(bg=bg, foreground=self._palette["version_fg"])
        # Placeholder focus handlers set a widget-level foreground, so refresh
        # both displayed hints and real text when the palette changes.
        for entry, text in self._placeholders.items():
            if entry.winfo_exists():
                entry.configure(
                    foreground=self._palette["placeholder_fg"] if entry.get() == text else fg
                )

    # -- dock icon --------------------------------------------------------

    def _apply_dock_icon(self) -> None:
        """Set the macOS dock icon from the bundled PNG asset (fail-soft).

        ``PhotoImage`` cannot decode the source JPEG, so a PNG conversion
        (``dock_icon.png``) is committed alongside it. The image is kept
        alive on ``self._dock_icon`` — a tkinter image held only by the
        interpreter would otherwise be garbage-collected. If the icon file
        is missing or unreadable, the icon is skipped and the app runs
        normally.
        """
        import tkinter as tk

        try:
            photo = tk.PhotoImage(file=dock_icon_path())
        except tk.TclError:
            self._dock_icon = None
            return
        self._dock_icon = photo
        try:
            self.root.iconphoto(True, photo)
        except tk.TclError:
            # iconphoto is unsupported on some platforms (e.g. X11); the
            # image is still kept alive, but its absence must never crash.
            pass

    # -- entry placeholders ----------------------------------------------

    def _attach_placeholder(self, entry, text: str) -> None:
        """Show ``text`` as a muted placeholder on ``entry``.

        The hint is removed the instant the entry gains focus (only when it
        is still the displayed content) and restored when focus leaves an
        empty entry. A displayed placeholder is treated as empty by the
        submit handlers, so it can never be created as a list/item.
        """
        self._placeholders[entry] = text
        entry.insert(0, text)
        entry.configure(foreground=self._placeholder_fg())
        entry.bind("<FocusIn>", lambda _e, e=entry: self._on_entry_focus_in(e))
        entry.bind("<FocusOut>", lambda _e, e=entry: self._on_entry_focus_out(e))

    def _placeholder_fg(self) -> str:
        """Muted gray for placeholder text in the current (fallback) theme."""
        return (self._palette or {}).get("placeholder_fg", "#808080")

    def _entry_value(self, entry) -> str:
        """Strip the entry's text; a displayed placeholder counts as empty."""
        if entry.get() == self._placeholders.get(entry, ""):
            return ""
        return entry.get().strip()

    def _on_entry_focus_in(self, entry) -> None:
        if entry.get() == self._placeholders.get(entry, ""):
            entry.delete(0, "end")
            entry.configure(foreground=(self._palette or {}).get("fg", "#000000"))

    def _on_entry_focus_out(self, entry) -> None:
        if entry.get().strip() == "":
            self._restore_placeholder(entry)

    def _restore_placeholder(self, entry) -> None:
        """Re-show the placeholder on an empty entry that no longer has focus.

        While the entry still holds the focus (e.g. right after a submit
        that cleared it), writing the hint would leave stale placeholder
        text in a focused field, since no FocusIn will re-fire to clear it.
        """
        if self.root.focus_get() is entry:
            return
        entry.delete(0, "end")
        entry.insert(0, self._placeholders[entry])
        entry.configure(foreground=self._placeholder_fg())

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
        """Center ``win`` over the main window's current on-screen rectangle.

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
        px, py = self.root.winfo_rootx(), self.root.winfo_rooty()
        pw, ph = self.root.winfo_width(), self.root.winfo_height()
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

    # -- settings window --------------------------------------------------

    def _open_settings(self) -> None:
        """Open the Toplevel settings window (single instance).

        The window is pre-filled from the in-memory ``self.settings``
        (effective lists dir = ``settings.lists_dir`` or the app default)
        and every control is bound to a small state holder on ``self``
        (StringVar/IntVar) so the Save handler can read the edited
        values in one place. Save validates and applies (see
        ``_settings_on_save``); Cancel is a full no-op that only closes
        the window.
        """
        import tkinter as tk
        from tkinter import ttk

        if (
            getattr(self, "settings_window", None) is not None
            and self.settings_window.winfo_exists()
        ):
            self.settings_window.lift()
            return

        win = tk.Toplevel(self.root)
        if self._palette is not None:
            win.configure(bg=self._palette["bg"])
        win.title("Settings")
        win.transient(self.root)
        self.settings_window = win

        # State holders: one var per control group (lists folder, theme,
        # completed-visible count).
        self._settings_lists_dir_var = tk.StringVar(
            value=self.settings.lists_dir or DEFAULT_DATA_DIR
        )
        self._settings_theme_var = tk.StringVar(value=self.settings.theme)
        self._settings_completed_var = tk.IntVar(value=self.settings.completed_visible)

        # (a) lists-folder row: entry + Browse… + Reset to default --------
        folder_row = ttk.Frame(win, padding=(10, 8))
        folder_row.pack(fill=tk.X)
        ttk.Label(folder_row, text="Lists folder:").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 2)
        )
        ttk.Entry(folder_row, textvariable=self._settings_lists_dir_var).grid(
            row=1, column=0, columnspan=3, sticky="we", pady=(0, 2)
        )
        ttk.Button(
            folder_row,
            text="Browse…",
            command=lambda: self._settings_browse(self._settings_lists_dir_var),
        ).grid(row=2, column=0, sticky="w", padx=(0, 4))
        self._settings_reset_btn = ttk.Button(
            folder_row,
            text="Reset to default",
            command=lambda: self._settings_lists_dir_var.set(DEFAULT_DATA_DIR),
        )
        self._settings_reset_btn.grid(row=2, column=1, columnspan=2, sticky="w")
        folder_row.columnconfigure(0, weight=1)

        # (b) theme radiobuttons ------------------------------------------
        theme_row = ttk.LabelFrame(win, text="Theme", padding=(10, 8))
        theme_row.pack(fill=tk.X, padx=10)
        self._settings_theme_rads = []
        for value, label in (("system", "System default"), ("light", "Light"), ("dark", "Dark")):
            rad = ttk.Radiobutton(
                theme_row, text=label, value=value, variable=self._settings_theme_var
            )
            rad.pack(anchor="w")
            self._settings_theme_rads.append(rad)

        # (c) completed-visible spinbox (0 = hide all completed) ----------
        cv_row = ttk.Frame(win, padding=(10, 8))
        cv_row.pack(fill=tk.X)
        ttk.Label(cv_row, text="Completed items visible:").pack(side=tk.LEFT)
        self._settings_spinbox = ttk.Spinbox(
            cv_row, from_=0, to=999, width=6, textvariable=self._settings_completed_var
        )
        self._settings_spinbox.pack(side=tk.LEFT, padx=(8, 0))

        # (d) Save / Cancel ----------------------------------------------
        bottom = ttk.Frame(win, padding=(10, 8))
        bottom.pack(side=tk.BOTTOM)
        self._settings_save_btn = ttk.Button(
            bottom, text="Save", command=self._settings_on_save
        )
        self._settings_save_btn.pack(side=tk.RIGHT, padx=(6, 0))
        self._settings_cancel_btn = ttk.Button(
            bottom, text="Cancel", command=self._close_settings
        )
        self._settings_cancel_btn.pack(side=tk.RIGHT)

        win.protocol("WM_DELETE_WINDOW", self._close_settings)
        # Fit all controls using the current theme's font and widget metrics.
        win.update_idletasks()
        width, height = win.winfo_reqwidth(), win.winfo_reqheight()
        win.minsize(width, height)
        win.geometry(f"{max(420, width)}x{max(280, height)}")
        win.update()
        self._center_window_on_parent(win)

    def _settings_browse(self, var) -> None:
        """Pick a directory via filedialog and store it in ``var``."""
        from tkinter import filedialog  # lazy: keep module importable headless

        path = filedialog.askdirectory(parent=self.settings_window, initialdir=var.get())
        if path:
            var.set(path)

    def _settings_on_save(self) -> None:
        """Validate, apply the directory decision, persist, and live-apply; close.

        Theme and completed-visible (int 0-999) are validated first, before
        any filesystem check, prompt, creation, relocation, or persistence;
        invalid input shows ``showerror`` and keeps the window open. A blank
        entry means the actual ``DEFAULT_DATA_DIR``. Paths are normalized to
        absolute form and compared with ``controller.store.data_dir``; an
        equivalent path (including via symlinks) neither prompts nor relocates.
        The effective default directory is always persisted as ``lists_dir:
        null``.

        For a changed target whose active directory holds Markdown lists, a
        Yes/No/Cancel prompt asks whether to move them (Yes), switch without
        moving (No), or keep the active directory (Cancel, which still
        persists the other valid settings and never inspects or creates the
        abandoned target). Empty, missing, or non-Markdown-only sources need
        no prompt. The chosen target is validated only after the decision and
        applied through ``controller.change_lists_dir``. Filesystem errors are
        reported, never raised into Tk. The live view follows the bound store
        even if relocation partially fails or preferences cannot be saved.
        Completed moves are never rolled back.

        A valid Save writes the full payload via ``save_settings``, replaces
        the in-memory settings, then re-applies the theme and refreshes rows.
        """
        from tkinter import messagebox  # lazy: keep module importable headless

        theme = self._settings_theme_var.get()
        try:
            completed = int(self._settings_spinbox.get().strip())
        except ValueError:
            completed = None
        if completed is not None and not 0 <= completed <= 999:
            completed = None

        if completed is None:
            messagebox.showerror(
                "Settings",
                "Completed items visible must be a whole number between 0 and 999.",
            )
            return
        if theme not in VALID_THEMES:
            messagebox.showerror(
                "Settings", f"Unknown theme: {theme!r}."
            )
            return

        old_dir = str(self.controller.store.data_dir)
        target = self._settings_lists_dir_var.get()
        try:
            proceed, new_lists_dir = self._decide_lists_dir(
                messagebox, target
            )
            if not proceed:
                return
            self._sync_lists_directory()
            new_lists_dir = self._lists_dir_setting(new_lists_dir)
        except (OSError, UnicodeError) as e:
            messagebox.showerror(
                "Settings",
                f"Could not inspect or refresh the lists folders from '{old_dir}' "
                f"to '{_normalize_dir(target.strip() or DEFAULT_DATA_DIR)}':\n{e}\n\n"
                f"The active lists folder is '{self.controller.store.data_dir}'. "
                "Some files may already be at the destination; completed moves "
                "have not been undone. The directory preference is not saved "
                "for restart. You can retry Save.",
            )
            return

        new_settings = Settings(
            theme=theme,
            lists_dir=new_lists_dir,
            completed_visible=completed,
        )

        try:
            save_settings(self.config_dir, new_settings)
        except OSError as e:
            messagebox.showerror(
                "Settings save failed",
                f"The directory preference could not be saved:\n{e}\n\n"
                f"The active lists folder is '{self.controller.store.data_dir}'. "
                "Its preference is not saved for restart. Completed moves have "
                "not been undone. You can retry Save without moving files again.",
            )
            return

        self.settings = new_settings

        # Re-apply the theme exactly like the toggle button does, then
        # refresh the current rows so the re-applied palette and the new
        # completed-visible count take effect immediately.
        self.theme = resolve_theme(new_settings)
        self._apply_theme(self.theme)
        self._theme_btn.config(text=self._theme_button_text())
        self._refresh_items()

        self._close_settings()

    def _decide_lists_dir(self, messagebox, entry_text: str) -> tuple[bool, str | None]:
        """Resolve the entry into ``(proceed, chosen_directory)``.

        ``proceed`` is False when an error was already reported (nothing
        persisted). Successful paths are absolute, including the default.
        Raises OSError for directory inspection/equivalence failures.
        """
        target = _normalize_dir(entry_text.strip() or DEFAULT_DATA_DIR)
        old_dir = str(self.controller.store.data_dir)

        if _same_dir(old_dir, target):
            return True, target

        move = True
        if _has_markdown(old_dir):
            prompt = (
                "You are about to change the directory where your lists are stored "
                f"from '{old_dir}' to '{target}' but there are already lists in it."
                " Do you want to copy them in the new path?"
            )
            answer = messagebox.askyesnocancel("Confirm directory change", prompt)
            if answer is None:  # Cancel: keep active directory, abandon target.
                return True, _normalize_dir(old_dir)
            move = answer

        if not _valid_lists_dir_path(target):
            messagebox.showerror(
                "Settings",
                "The lists folder is not an existing directory and cannot\n"
                f"be created:\n{target}",
            )
            return False, None
        try:
            self.controller.change_lists_dir(target, move=move)
        except OSError as e:
            refresh_error = ""
            try:
                self._sync_lists_directory()
            except (OSError, UnicodeError) as refresh_exc:
                refresh_error = f"\nCould not refresh the active lists folder: {refresh_exc}"
            messagebox.showerror(
                "Directory change failed",
                f"Could not switch lists folder from '{old_dir}' to '{target}': "
                f"{e}\n\nSome files may already be at the destination. "
                "Completed moves have not been undone. "
                f"The active lists folder is '{self.controller.store.data_dir}'. "
                f"The directory preference is not saved for restart.{refresh_error}",
            )
            return False, None
        return True, target

    def _sync_lists_directory(self) -> None:
        """Follow the bound store without applying pending theme/filter edits."""
        self.data_dir = str(self.controller.store.data_dir)
        # Keep an accurate runtime path even if default equivalence cannot be read.
        self.settings.lists_dir = _normalize_dir(self.data_dir)
        try:
            self.settings.lists_dir = self._lists_dir_setting(self.settings.lists_dir)
        finally:
            self.refresh_lists()

    @staticmethod
    def _lists_dir_setting(path: str) -> str | None:
        """Persisted form of an effective directory: None for the default."""
        if _same_dir(path, _normalize_dir(DEFAULT_DATA_DIR)):
            return None
        return path

    def _close_settings(self) -> None:
        win = getattr(self, "settings_window", None)
        if win is not None and win.winfo_exists():
            win.destroy()
        self.settings_window = None

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

        r, g, b = self.root.winfo_rgb(color)
        # winfo_rgb may report 0-255 or 0-65535 channels; normalize to 0-1.
        scale = self.root.winfo_rgb("#ffffff")[0] or 1
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / scale
        if luminance < 0.5:
            return ("#f0f0f0", "#b0b0b0")
        return ("#000000", "#808080")

    def _refresh_items(self) -> None:
        import tkinter as tk
        from tkinter import font as tkfont

        for widget in self.items_frame.winfo_children():
            widget.destroy()
        self._item_rows = []

        if self.current_list is None:
            self.title_label.config(text="(no list selected)")
            return

        base_font = tkfont.nametofont("TkDefaultFont").copy()
        active_fg, done_fg = self._text_colors(self.items_frame)

        todo_list = self.controller.open_list(self.current_list)
        row_bg = self._palette["bg"] if self._palette is not None else None
        # Display order can differ from storage; equal duplicate items still
        # need their own original indices for toggle/delete callbacks.
        stored_indexes = {id(item): index for index, item in enumerate(todo_list.items)}
        for item in visible_items(todo_list.items, self.settings.completed_visible):
            index = stored_indexes[id(item)]
            row_kwargs = {"bg": row_bg} if row_bg is not None else {}
            row = tk.Frame(self.items_frame, **row_kwargs)
            row.pack(anchor="w", fill=tk.X)

            var = tk.IntVar(value=1 if item.done else 0)
            cb_kwargs = {"bg": row_bg} if row_bg is not None else {}
            cb = tk.Checkbutton(
                row,
                variable=var,
                command=lambda i=index: self._on_toggle_item(i),
                **cb_kwargs,
            )
            cb.pack(side=tk.LEFT, padx=(4, 6))

            del_kwargs = {"bg": row_bg} if row_bg is not None else {}
            del_ctrl = tk.Label(row, image=self._trash_image, cursor="hand2", **del_kwargs)
            del_ctrl.pack(side=tk.RIGHT, padx=(6, 4))
            del_ctrl.bind("<Button-1>", lambda e, i=index: self._on_delete_item(i))

            # Edit (pencil) icon: packed after the trash icon, so with the
            # same side=RIGHT it lands strictly to its left.
            edit_kwargs = {"bg": row_bg} if row_bg is not None else {}
            edit_ctrl = tk.Label(row, image=self._edit_image, cursor="hand2", **edit_kwargs)
            edit_ctrl.pack(side=tk.RIGHT, padx=(6, 0))
            edit_ctrl.bind("<Button-1>", lambda e, i=index: self._on_edit_item(i))

            label_font = base_font.copy()
            if item.done:
                label_font.config(overstrike=1)
            else:
                label_font.config(overstrike=0)

            label_kwargs = {"bg": row_bg} if row_bg is not None else {}
            label = tk.Label(
                row,
                text=item.text,
                anchor="w",
                font=label_font,
                foreground=done_fg if item.done else active_fg,
                **label_kwargs,
            )
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            label.bind(
                "<Double-Button-1>",
                lambda _e, i=index: self._on_item_double_click(i),
            )

            self._item_rows.append((var, cb, label, del_ctrl, edit_ctrl))

    def _on_toggle_item(self, index: int) -> None:
        if self.current_list is None:
            return
        self.controller.toggle_item(self.current_list, index)
        self._refresh_items()

    def _on_delete_item(self, index: int) -> None:
        if self.current_list is None:
            return
        from tkinter import messagebox  # lazy: keep module importable headless

        text = self.controller.open_list(self.current_list).items[index].text
        if not messagebox.askyesno("Confirm deletion", f'Delete item "{text}"?'):
            return
        self.controller.remove_item(self.current_list, index)
        self._refresh_items()

    def _on_edit_item(self, index: int) -> None:
        """Open the modal edit dialog for the item at ``index``."""
        if self.current_list is None:
            return
        self._open_edit_dialog(index)

    def _on_item_double_click(self, index: int) -> None:
        """Open the edit dialog when an unfinished item's text is double-clicked.

        Mirrors the edit-icon path (same pre-populated modal). Completed
        items ignore the double-click so no dialog opens for them.
        """
        if self.current_list is None:
            return
        item = self.controller.open_list(self.current_list).items[index]
        if item.done:
            return
        self._on_edit_item(index)

    def _open_edit_dialog(self, index: int) -> None:
        """Open a theme-aware modal dialog to edit the item's title and description.

        Window styling follows the other dialogs (Toplevel, theme bg,
        transient). The title entry and the multi-line description box start
        pre-populated with the item's current values. ``save`` calls
        ``controller.edit_item`` with both, then
        closes the dialog and refreshes the list; empty/whitespace-only
        input raises ValueError in the controller and persists nothing, but
        the dialog still closes. ``cancel`` closes the dialog with no
        changes.
        """
        import tkinter as tk
        from tkinter import ttk

        win = tk.Toplevel(self.root)
        if self._palette is not None:
            win.configure(bg=self._palette["bg"])
        win.title("Edit item")
        win.transient(self.root)

        item = self.controller.open_list(self.current_list).items[index]
        row = ttk.Frame(win, padding=10)
        row.pack(fill=tk.X)
        entry = ttk.Entry(row)
        entry.pack(fill=tk.X)
        entry.insert(0, item.text)

        # Multi-line description box below the title. Plain tk.Text is not
        # ttk-styled, so apply the entry palette colors explicitly.
        desc_kwargs = {}
        if self._palette is not None:
            desc_kwargs = {
                "bg": self._palette["entry_bg"],
                "fg": self._palette["fg"],
                "insertbackground": self._palette["fg"],
                "highlightbackground": self._palette["btn_bg"],
            }
        desc_text = tk.Text(
            row, height=5, width=40, wrap=tk.WORD, undo=True, **desc_kwargs
        )
        desc_text.pack(fill=tk.X, pady=(8, 0))
        desc_text.insert("1.0", item.description)

        bottom = ttk.Frame(win, padding=(10, 8))
        bottom.pack(side=tk.BOTTOM)
        save_btn = ttk.Button(bottom, text="save")
        save_btn.pack(side=tk.RIGHT, padx=(6, 0))
        cancel_btn = ttk.Button(bottom, text="cancel")
        cancel_btn.pack(side=tk.RIGHT)

        save_btn.config(command=self._on_edit_save)
        cancel_btn.config(command=self._close_edit_dialog)
        entry.bind("<Return>", lambda _e: self._on_edit_save())
        win.protocol("WM_DELETE_WINDOW", self._close_edit_dialog)

        self._edit_window = win
        self._edit_index = index
        self._edit_entry = entry
        self._edit_desc_text = desc_text
        self._edit_save_btn = save_btn
        self._edit_cancel_btn = cancel_btn

        win.grab_set()
        win.update()
        self._center_window_on_parent(win)

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
        win = self._edit_window
        self._edit_window = None
        self._edit_index = None
        self._edit_entry = None
        self._edit_desc_text = None
        self._edit_save_btn = None
        self._edit_cancel_btn = None
        if win is not None and win.winfo_exists():
            win.destroy()

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
    """Build the controller + :class:`TodoApp` and start the main loop.

    Startup order: load settings from the fixed config dir, derive the
    effective lists data dir from ``settings.lists_dir`` (or the default,
    created on demand), then build the store/controller with it.
    """
    cfg, data_dir, _settings = startup_dirs(config_dir)
    store = MarkdownListStore(data_dir)
    controller = TodoController(store, data_dir=data_dir)
    app = TodoApp(controller, data_dir=data_dir, config_dir=cfg)
    app.mainloop()
