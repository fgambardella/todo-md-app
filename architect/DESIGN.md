# DESIGN.md — todo-md-app

Architect-owned compact snapshot of the current architecture. Not a journal; history lives in Git.

## System Overview

- macOS desktop TODO app; Python 3, stdlib only (no runtime deps; Tkinter lazy-imported so the package stays importable headlessly).
- Every list is persisted as its own plain Markdown file with GFM checkbox syntax — no database.
- Layered: domain models → Markdown storage → headless controller (view-model) → Tkinter GUI; all business logic testable without a display.
- Testing: pytest; full suite `.venv/bin/python -m pytest tests -v` from `implementer/src` (system Python is PEP-668 managed).
- App data lives in `~/.todo-md-app/lists/` (one `.md` per list); app settings live in a dedicated `~/.todo-md-app/config/settings.json`.
- Primary target OS: macOS; system theme detection via `defaults read -g AppleInterfaceStyle` with graceful fallback.

## Component Architecture

```
implementer/src/
├── todo_md/
│   ├── __init__.py     # package exports
│   ├── models.py       # Domain: TodoItem, TodoList
│   ├── storage.py      # Persistence: MarkdownListStore
│   ├── settings.py     # Headless settings config (Settings, load/save, theme resolution)
│   ├── version.py      # Headless version loader (get_version, reads VERSION)
│   ├── app.py          # TodoController (headless) + TodoApp (tkinter GUI)
│   ├── __main__.py     # Entry point: python -m todo_md
│   ├── VERSION         # App version (X.Y.Z), auto-bumped by git pre-commit hook
│   └── assets/         # trash.png (512×512, CC-BY 4.0) + LICENSE.txt; dock_icon.jpg (source) + dock_icon.png (Tk-compatible copy)
└── tests/              # pytest suite (GUI tests run on a real display here)
```

Repo-level: `implementer/src/scripts/bump_version.sh` (+ `--install-hook`) maintains `.git/hooks/pre-commit`, which bumps the PATCH of `VERSION` and stages it into every commit; the hook is git-internal and must be (re)installed per clone. `implementer/src/scripts/build_app.sh` builds a self-contained `dist/todo-md.app` with PyInstaller (`--onedir --windowed`, `--collect-data todo_md`, arm64 host guard, post-build launch smoke check); before the build it generates `build/todo_md.icns` from `todo_md/assets/dock_icon.png` via macOS `sips`/`iconutil` and passes it via `--icon`, so the bundle shows the custom Finder icon; PyInstaller is dev-only, pinned in `implementer/src/requirements-dev.txt`. `implementer/src/scripts/release_package.sh` runs `build_app.sh`, validates `todo_md/VERSION` as strict `X.Y.Z`, and zips the bundle via `ditto -c -k --noextattr --noqtn` into `dist/todo-md-<version>-arm64.zip` (`todo-md.app` at zip root) for GitHub release upload; artifacts are never committed.

- **Domain** — `todo_md/models.py`: `TodoItem(text, done, created)`, `TodoList(name, items)` with validated add/toggle/remove/rename.
- **Persistence** — `todo_md/storage.py`: `MarkdownListStore(data_dir)`; atomic writes (temp file + `os.replace`); names sanitized to `[A-Za-z0-9_-]`; `lists()` picks up `.md` files only.
- **Settings config** — `todo_md/settings.py`: headless (no tkinter); `Settings(theme, lists_dir, completed_visible)` dataclass (theme ∈ `("light", "dark", "system")` default `"system"`, `lists_dir` None = app default dir, `completed_visible` int ≥ 0 default 10, 0 hides all completed); `load_settings` never raises (legacy single-key `{"theme"}` files load; missing/corrupt → defaults); `save_settings` validates (ValueError) and writes `settings.json` atomically; `resolve_theme` resolves `"system"` via `system_default_theme` (macOS `defaults read -g AppleInterfaceStyle`, fallback `"light"`) at call time — the resolved value is never persisted; only explicit user choices are written.
- **Version** — `todo_md/version.py`: headless `get_version()` reads `todo_md/VERSION` package-relative, returns `0.0.0` if missing/unreadable. `TodoApp` shows `v<version>` in a bottom-right `tk.Label` (font 8, `version_fg` palette entry, unobtrusive); on the fallback path its background is pinned to the palette `bg` and refreshed with `fg` on theme toggle (unset bg stays on a system color), native path leaves bg unset.
- **View-model** — `todo_md/app.py` (`TodoController`): bridges models and storage; every mutation persists immediately; no tkinter at module import; exposes `data_dir` (optional constructor override, defaulting to the store's) which the GUI uses to derive data/config locations.
- **Presentation** — `todo_md/app.py` (`TodoApp`): list sidebar (create/delete), checkbutton item rows with luminance-adaptive label colors (rows respect the pure display-only `visible_items` filter: hides completed beyond the configured count, top-first; 0 hides all; storage unchanged), per-row trash-icon delete (`tk.Label` + bound `<Button-1>`, pre-sized `trash_18.png` asset loaded directly; 512×512 source kept in `assets/`), entry+Add with muted-gray placeholder hints (cleared on focus-in, restored on empty focus-out only when the entry has genuinely lost focus — never re-inserted into a still-focused field after submit — counted as empty on submit), theme switcher button. macOS dock icon set at startup via `root.iconphoto` from `assets/dock_icon.png` (kept alive in `self._dock_icon`; fail-soft: missing/unsupported icon is skipped, startup unaffected). Destructive GUI actions (delete list, delete item) are gated by a modal `messagebox.askyesno` (lazy-imported per handler); No is a full no-op. `_apply_theme` tries `tk appappearance`, falls back to ttk "clam" + explicit palettes stored in `self._palette` on `TclError`; `_refresh_items` applies the palette bg to every row widget.
- **Entry point** — `todo_md/__main__.py`: `run()` builds controller + GUI.

## Data Models & Flow

- `TodoItem(text: str, done: bool, created: float)`; `TodoList(name: str, items: list[TodoItem])`.
- Disk: `<lists>/<Name>.md` = `# <Name>` header + `- [ ]`/`- [x]` lines; plus the settings JSON `{"theme": "light"|"dark"|"system", "lists_dir": str|null, "completed_visible": int}` at `<app-root>/config/settings.json` (config dir FIXED at `~/.todo-md-app/config`, never derived from the lists dir; legacy single-key theme files load compatibly).
- Data flow: GUI → `TodoController` → `MarkdownListStore` → `.md` files; store re-read after each mutation drives UI refresh.
- Startup flow: headless `startup_dirs` (fixed config dir → `load_settings` → data dir from `settings.lists_dir` or `~/.todo-md-app/lists`, created on demand) → build store/controller with that dir → `resolve_theme` (`"system"` detected live, never persisted; nothing written on first start) → `_apply_theme` → build UI → idempotent re-apply after `_build_ui`. Toggle → `save_settings` (full payload) → re-apply → `_refresh_items` (row bgs + adaptive label fgs re-resolve). `TodoApp`/`run` accept `config_dir` overrides for tests.

## External Interfaces

- **CLI**: `python -m todo_md` (from `implementer/src`, using the venv); `implementer/src/scripts/bump_version.sh [--install-hook]` (from repo root).
- **Git**: installed pre-commit hook bumps `todo_md/VERSION` (patch) and stages it in every commit — every commit therefore carries a version bump.
- **Disk**: `~/.todo-md-app/lists/*.md` + settings JSON at `~/.todo-md-app/config/settings.json` (UTF-8; keys `theme`, `lists_dir`, `completed_visible`).
- **OS**: macOS `defaults read -g AppleInterfaceStyle` (dark → "dark"; non-macOS or error → "light").
- **Tk/Tcl**: on this machine (Tcl/Tk 9.0.4) `tk appappearance` raises `TclError` (clam fallback is always live), `compound="image"` is rejected (use `"center"`), and the clam `TEntry` field element fills from the `fieldbackground` element option — setting `background` alone leaves a light field in dark mode; clam `TButton` likewise needs an explicit `style.map("TButton", background=[("active", …)])` or hover falls back to a light `activeBackground` that hides light text. Dark-mode entry fill (`#383838`) is deliberately slightly lighter than the listbox background (`#2d2d2d`): identical colors read as entries looking darker (optical effect). GUI test quirk: destroying a Tk root that was never `update()`d corrupts the next in-process Tk instance (later `update()` hits Trace/BPT trap) — call `root.update()` before `destroy()` in every GUI test.

## Known Architectural Debt

None outstanding — the 2026-09-27 debt triage resolved all four items (two executed as tasks, two accepted as constraints; see `decisions/2026-09-27-debt-triage.md`).