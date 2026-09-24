# DESIGN.md — todo-md-app

Architect-owned compact snapshot of the current architecture. Not a journal; history lives in Git.

## System Overview

- macOS desktop TODO app; Python 3, stdlib only (no runtime deps; Tkinter lazy-imported so the package stays importable headlessly).
- Every list is persisted as its own plain Markdown file with GFM checkbox syntax — no database.
- Layered: domain models → Markdown storage → headless controller (view-model) → Tkinter GUI; all business logic testable without a display.
- Testing: pytest; full suite `.venv/bin/python -m pytest tests -v` from `implementer/src` (system Python is PEP-668 managed).
- App data lives in `~/.todo-md-app/lists/` (one `.md` per list); the theme setting currently lives at `<lists>/config.json` and is being moved to `<app-root>/config/settings.json` (see Known Architectural Debt).
- Primary target OS: macOS; system theme detection via `defaults read -g AppleInterfaceStyle` with graceful fallback.

## Component Architecture

```
implementer/src/
├── todo_md/
│   ├── __init__.py     # package exports
│   ├── models.py       # Domain: TodoItem, TodoList
│   ├── storage.py      # Persistence: MarkdownListStore
│   ├── theme.py        # Headless theme config (load/save/system detection)
│   ├── app.py          # TodoController (headless) + TodoApp (tkinter GUI)
│   ├── __main__.py     # Entry point: python -m todo_md
│   └── assets/         # trash.png (512×512, CC-BY 4.0) + LICENSE.txt
└── tests/              # pytest suite (GUI tests run on a real display here)
```

- **Domain** — `todo_md/models.py`: `TodoItem(text, done, created)`, `TodoList(name, items)` with validated add/toggle/remove/rename.
- **Persistence** — `todo_md/storage.py`: `MarkdownListStore(data_dir)`; atomic writes (temp file + `os.replace`); names sanitized to `[A-Za-z0-9_-]`; `lists()` picks up `.md` files only.
- **Theme config** — `todo_md/theme.py`: headless (no tkinter); system-default detection; atomic JSON load/save; validates against `("light", "dark")`.
- **View-model** — `todo_md/app.py` (`TodoController`): bridges models and storage; every mutation persists immediately; no tkinter at module import.
- **Presentation** — `todo_md/app.py` (`TodoApp`): list sidebar (create/delete), checkbutton item rows with luminance-adaptive label colors, per-row trash-icon delete (`tk.Label` + bound `<Button-1>`, `.subsample(28)` → ~18px), entry+Add, theme switcher button. `_apply_theme` tries `tk appappearance`, falls back to ttk "clam" + explicit palettes stored in `self._palette` on `TclError`; `_refresh_items` applies the palette bg to every row widget.
- **Entry point** — `todo_md/__main__.py`: `run()` builds controller + GUI.

## Data Models & Flow

- `TodoItem(text: str, done: bool, created: float)`; `TodoList(name: str, items: list[TodoItem])`.
- Disk: `<lists>/<Name>.md` = `# <Name>` header + `- [ ]`/`- [x]` lines; plus the theme setting JSON `{"theme": "light"|"dark"}` (currently `<lists>/config.json`).
- Data flow: GUI → `TodoController` → `MarkdownListStore` → `.md` files; store re-read after each mutation drives UI refresh.
- Theme flow: startup → `load_theme` (first start: detect system default and persist) → `_apply_theme` → build UI → idempotent re-apply after `_build_ui` so the palette reaches built widgets. Toggle → `save_theme` → re-apply → `_refresh_items` (row bgs + adaptive label fgs re-resolve).

## External Interfaces

- **CLI**: `python -m todo_md` (from `implementer/src`, using the venv).
- **Disk**: `~/.todo-md-app/lists/*.md` + theme setting JSON (UTF-8, key `theme`).
- **OS**: macOS `defaults read -g AppleInterfaceStyle` (dark → "dark"; non-macOS or error → "light").
- **Tk/Tcl**: on this machine (Tcl/Tk 9.0.4) `tk appappearance` raises `TclError` (clam fallback is always live) and `compound="image"` is rejected (use `"center"`).

## Known Architectural Debt

1. Theme setting lives inside the lists dir (`<lists>/config.json`); move it to `~/.todo-md-app/config/settings.json` with a one-time legacy migration (Task 14 in TASKS.md).
2. `TodoApp` reaches into `controller.store.data_dir` to derive data/config locations — implicit controller→store coupling; an explicit data_dir parameter on the controller would be cleaner.
3. The native `tk appappearance` path is dead on this machine (Tcl 9.0.4 rejects it); theming depends on Tcl build behavior and the clam fallback.
4. Plain `tk` widgets pin their default `-bg` to `systemWindowBackgroundColor` resolved once — any theming work must keep explicit per-widget palette backgrounds (current constraint, handled via `self._palette`).
5. `trash.png` is 512×512 and subsampled 28× at runtime; a pre-sized ~18px asset would be cleaner.