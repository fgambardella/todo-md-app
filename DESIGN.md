# DESIGN.md — todo-md-app

Single source of truth for the architecture of the TODO desktop application. Owned exclusively by the Architect agent.

## System Overview

A macOS desktop TODO application in Python 3 (stdlib only, no runtime dependencies). Its defining trait: **every list is persisted as its own plain Markdown file** with GitHub-flavored checkbox syntax — no database. The GUI is native-feeling **Tkinter** (lazy-imported so the package stays importable headlessly). Testing framework: **pytest** (run via `src/.venv/bin/python -m pytest tests -v`; system Python is PEP-668 managed).

## Component Architecture

```
src/
├── todo_md/
│   ├── __init__.py     # package exports
│   ├── models.py       # Domain: TodoItem, TodoList (validated add/toggle/remove/rename)
│   ├── storage.py      # Persistence: MarkdownListStore (<Name>.md, atomic writes)
│   ├── theme.py        # Theme config: config.json next to lists, system detection, load/save
│   ├── app.py          # TodoController (headless view-model) + TodoApp (tkinter GUI)
│   ├── __main__.py     # Entry point: python -m todo_md
│   └── assets/         # trash.png (512×512, CC-BY 4.0), LICENSE.txt
└── tests/              # pytest suite (GUI tests run with a real display on this Mac)
```

- **Domain (`models.py`)**: `TodoItem(text, done, created)`, `TodoList(name, items)` with validated mutations.
- **Persistence (`storage.py`)**: `MarkdownListStore(data_dir)` — `lists()` (`.md` files only, sorted), `load`, `save` (atomic: temp file + `os.replace`), `create`, `delete`; names sanitized to `[A-Za-z0-9_-]`.
- **Theme config (`theme.py`)**: headless module, no tkinter. `CONFIG_FILENAME = "config.json"` stored **inside the lists data dir** (next to the `.md` files; safe because `lists()` only picks up `.md`). `system_default_theme()` detects the OS default on macOS via `defaults read -g AppleInterfaceStyle` (dark → "dark", anything else/error → "light"). `load_theme(data_dir)` returns the stored theme, or — on first start / corrupt file / invalid value — detects the system default, **writes it to config.json (atomic)**, and returns it. `save_theme(data_dir, theme)` validates against `("light", "dark")` (else `ValueError`) and writes atomically.
- **View-model (`app.py`, `TodoController`)**: pure logic bridging domain and storage; every mutation persists immediately; no tkinter imports at module level.
- **Presentation (`app.py`, `TodoApp`)**: Tkinter GUI — left frame (listbox, create/delete), right frame (title, checkbutton-backed item rows with adaptive label colors + trash-icon delete, entry+Add). On startup it loads the theme from `config.json` (creating it on first start) and applies it via `_apply_theme`: primary path is `root.tk.call("tk", "appappearance", theme)` (Tk 9 keeps the native aqua look in either theme); fallback for `TclError` is `ttk` "clam" theme with explicit light/dark palettes. A toggle button flips the theme, persists via `save_theme`, re-applies it and refreshes items so the luminance-adaptive label colors (`_text_colors`) re-resolve.

## Data Models & Flow

- `TodoItem(text: str, done: bool, created: float)`; `TodoList(name: str, items: list[TodoItem])`.
- Disk layout (`~/.todo-md-app/lists/` by default): `<Name>.md` = `# <Name>` header + `- [ ]`/`- [x]` lines; plus `config.json` = `{"theme": "light" | "dark"}`.
- **Data flow**: GUI → `TodoController` → `MarkdownListStore` → `.md` files; store re-read after each mutation drives UI refresh.
- **Theme flow**: startup → `load_theme(data_dir)` (first start: detects system default and initializes the file) → `_apply_theme(theme)` → UI built. Toggle click → `save_theme(data_dir, new_theme)` → `_apply_theme` → `_refresh_items()` (adaptive label fg re-resolved from effective bg luminance).

## External Interfaces

- **CLI**: `python -m todo_md` (from `src/`, using the venv).
- **Disk**: `~/.todo-md-app/lists/*.md`, `~/.todo-md-app/lists/config.json` (UTF-8 JSON, key `theme`).
- **OS**: macOS `defaults read -g AppleInterfaceStyle` for system theme detection (graceful fallback to "light" off-macOS or on error).
- **Tk/Tcl**: on this machine (Tcl/Tk 9.0.4) the `tk appappearance` subcommand is NOT available (raises `TclError`) even though it is a documented Tk 9 feature; `_apply_theme` therefore always takes the "clam" palette fallback here, with the `appappearance` attempt kept as the primary path for Tk builds that do support it.

## Current State & Known Debt

- **Done (Tasks 1–12, 51 tests passing)**: storage, models, controller, GUI, toggle bug fix, layout, trash-icon delete control (18px transparent icon on a `tk.Label` bound to `<Button-1>`), luminance-adaptive label foreground, headless `theme.py` config (config.json next to the lists, system default detection, atomic load/save), and the GUI theme switcher: `TodoApp.__init__(controller, data_dir=None)` loads and applies the theme before building the UI and re-applies it after `_build_ui()` (idempotent) so the clam-palette fallback sets explicit backgrounds on `items_frame`/`listbox`; `self._theme_btn` toggles light/dark, persists via `save_theme`, and `_refresh_items()` re-resolves adaptive label colors.
- **No pending tasks.**
- **Known quirks**: `trash.png` is 512×512 (displayed via `.subsample(28)` → ~18px); Tcl 9.0.4 on this machine rejects BOTH `compound="image"` (use `"center"`) AND `tk appappearance` (TclError → clam fallback is always live); OS default appearance on this Mac is dark; GUI tests must destroy `root` in `finally` and call `root.update()` after building; effective widget background is probed via `winfo_rgb(widget.cget("bg"))` normalized by `winfo_rgb("#ffffff")[0]`.