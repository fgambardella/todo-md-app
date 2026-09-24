"""Controller and GUI for the todo_md package.

``TodoController`` is pure logic (no GUI imports). ``TodoApp`` is a
``tkinter`` frontend; tkinter is imported lazily *inside* methods so the
module remains importable on headless machines without a display.
"""

from __future__ import annotations

import os

from .models import TodoItem, TodoList
from .storage import MarkdownListStore
from .theme import load_theme, migrate_legacy_config, save_theme  # headless module (stdlib only)

__all__ = ["TodoController", "TodoApp", "run"]

DEFAULT_DATA_DIR = os.path.join(os.path.expanduser("~"), ".todo-md-app", "lists")


class TodoController:
    """Mediates between the user (or UI) and the MarkdownListStore.

    All methods that load/mutate a list follow the pattern:
    load -> mutate -> persist via ``store.save``.
    """

    def __init__(self, store: MarkdownListStore) -> None:
        self.store = store

    # -- list-level operations -------------------------------------------

    def list_names(self) -> list[str]:
        """Return the names of all stored lists, sorted."""
        return self.store.lists()

    def open_list(self, name: str) -> TodoList:
        """Load a list into a TodoList of TodoItem objects."""
        todo_list = TodoList(name=name)
        for text, done in self.store.load(name):
            todo_list.items.append(TodoItem(text=text, done=done))
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
        self.store.save(name, [(item.text, item.done) for item in todo_list.items])
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

        def _mutate(todo_list: TodoList) -> None:
            todo_list.toggle(index)

        todo_list = self._load_and_save(name, _mutate)
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
        self.data_dir = data_dir if data_dir is not None else self.controller.store.data_dir
        # Theme settings live in a dedicated config dir alongside (not inside)
        # the lists dir; default: <lists-parent>/config.
        self.config_dir = (
            config_dir
            if config_dir is not None
            else os.path.join(os.path.dirname(os.path.abspath(self.data_dir)), "config")
        )
        self.current_list: str | None = None
        self._item_rows: list[tuple] = []
        self._palette: dict | None = None

        self.root = tk.Tk()
        self.root.title("TODO Markdown App")
        self.root.geometry("700x420")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Theme: one-time migration of the legacy <lists>/config.json, then
        # load (first start creates settings.json) and apply before the UI
        # is built so every widget starts in the right palette.
        migrate_legacy_config(
            self.config_dir, os.path.join(os.path.abspath(self.data_dir), "config.json")
        )
        self.theme = load_theme(self.config_dir)
        self._apply_theme(self.theme)

        # Cached trash-bin icon (~18px after subsampling the 512x512 source).
        self._trash_image = tk.PhotoImage(
            file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "trash.png")
        ).subsample(28)

        self._build_ui()
        # Re-apply after the UI exists: the fallback palette must set
        # explicit backgrounds on items_frame/listbox once they are created.
        self._apply_theme(self.theme)
        self.refresh_lists(select_first=True)

    # -- construction -----------------------------------------------------

    def _build_ui(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        # --- left frame: lists ------------------------------------------
        left = ttk.Frame(self.root, padding=8)
        left.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(left, text="Lists:").pack(anchor="w")

        self.listbox = tk.Listbox(left, width=22, height=14)
        self.listbox.pack(fill=tk.X, pady=(2, 6))
        self.listbox.bind("<<ListboxSelect>>", self._on_select_list)

        self.new_name_entry = ttk.Entry(left, width=20)
        self.new_name_entry.pack(fill=tk.X)

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
            btn_bg, entry_bg = "#3c3c3c", "#2d2d2d"
            btn_active = "#2e2e2e"
        else:
            bg, fg = "#f5f5f5", "#000000"
            btn_bg, entry_bg = "#e0e0e0", "#ffffff"
            btn_active = "#d0d0d0"

        self._palette = {"bg": bg, "fg": fg, "btn_bg": btn_bg, "entry_bg": entry_bg}

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=bg, foreground=fg)
        style.configure("TLabel", background=bg, foreground=fg)
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
        # The clam TEntry field element consumes the *element* option
        # fieldbackground for its fill; background/foreground alone leave
        # a light field in dark mode, making light text invisible.
        style.configure(
            "TEntry",
            background=entry_bg,
            foreground=fg,
            fieldbackground=entry_bg,
        )
        self.root.config(bg=bg)

        # Plain tk widgets inherit the *parent's effective* background;
        # set it explicitly so the item rows and their labels flip.
        items_frame = getattr(self, "items_frame", None)
        if items_frame is not None:
            items_frame.config(bg=bg)
        listbox = getattr(self, "listbox", None)
        if listbox is not None:
            listbox.config(bg=entry_bg, fg=fg, highlightbackground=btn_bg)

    def _on_toggle_theme(self) -> None:
        new = "light" if self.theme == "dark" else "dark"
        save_theme(self.config_dir, new)
        self.theme = new
        self._apply_theme(new)
        self._theme_btn.config(text=self._theme_button_text())
        # Re-resolve the luminance-adaptive label colors.
        self._refresh_items()

    # -- list-frame handlers ----------------------------------------------

    def refresh_lists(self, select_first: bool = False) -> None:
        """Repopulate the listbox from the controller/store."""
        self.listbox.delete(0, "end")
        for name in self.controller.list_names():
            self.listbox.insert("end", name)

        if select_first and self.listbox.size():
            self.listbox.selection_set(0)
            self.listbox.see(0)
            self._select_list_name(self.listbox.get(0))
        elif self.current_list and self.current_list in self.controller.list_names():
            self._select_list_name(self.current_list)
        else:
            self.current_list = None
            self._clear_items()

    def _selected_name(self) -> str | None:
        sel = self.listbox.curselection()
        return self.listbox.get(sel[0]) if sel else None

    def _on_select_list(self, _event=None) -> None:
        name = self._selected_name()
        if name is not None:
            self._select_list_name(name)

    def _select_list_name(self, name: str) -> None:
        self.current_list = name
        self.title_label.config(text=name)
        self._refresh_items()

    def _on_create_list(self) -> None:
        name = self.new_name_entry.get().strip()
        if not name:
            return
        try:
            self.controller.create_list(name)
        except FileExistsError:
            return
        self.new_name_entry.delete(0, "end")
        self.refresh_lists(select_first=False)
        self._select_list_name(name)

    def _on_delete_list(self) -> None:
        name = self._selected_name()
        if name is None:
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
        for index, item in enumerate(todo_list.items):
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

            self._item_rows.append((var, cb, label, del_ctrl))

    def _on_toggle_item(self, index: int) -> None:
        if self.current_list is None:
            return
        self.controller.toggle_item(self.current_list, index)
        self._refresh_items()

    def _on_delete_item(self, index: int) -> None:
        if self.current_list is None:
            return
        self.controller.remove_item(self.current_list, index)
        self._refresh_items()

    def _on_add_item(self) -> None:
        if self.current_list is None:
            return
        text = self.new_item_entry.get().strip()
        if not text:
            return
        self.controller.add_item(self.current_list, text)
        self.new_item_entry.delete(0, "end")
        self._refresh_items()

    # -- lifecycle ----------------------------------------------------------

    def _on_close(self) -> None:
        self.root.destroy()

    def mainloop(self) -> None:
        """Run the tkinter main loop."""
        self.root.mainloop()


def run() -> None:
    """Build the controller + :class:`TodoApp` and start the main loop."""
    store = MarkdownListStore(DEFAULT_DATA_DIR)
    controller = TodoController(store)
    app = TodoApp(controller)
    app.mainloop()
