# DESIGN.md — todo-md-app

## System Overview

- macOS desktop TODO app; Python 3, stdlib-only runtime; tkinter for GUI.
- Every list persists as its own plain Markdown file (GFM checkboxes) in `~/.todo-md-app/lists/`.
- Layered so domain, persistence, controller, and settings are testable headlessly.
- GUI is imported lazily; headless tests never require a display.
- Writes are atomic (temp file + `os.replace`); list names sanitized filesystem-safe.
- Build tooling produces an arm64-only app bundle and a versioned release zip (PyInstaller is dev-only).
- Version in `src/todo_md/VERSION`, auto-bumped by a git pre-commit hook.
- No runtime third-party dependencies; pytest is the test framework.

## Component Architecture

- `implementer/src/todo_md/models.py` — domain: `TodoItem` (text, done, created, description) and `TodoList` with validated `add_item`, `edit` (title + description), `toggle`, `remove`, `rename`.
- `implementer/src/todo_md/storage.py` — persistence: `MarkdownListStore`, one `<Name>.md` per list, atomic writes, name sanitization.
- `implementer/src/todo_md/app.py` — `TodoController` (UI-agnostic view-model; every mutation persists immediately) and `TodoApp` (Tkinter GUI: sidebar list management, checkbutton item rows with edit/trash icons, add entry, modal edit dialog, settings window, confirmations; dialogs opened centered on the main window via the self-correcting `_center_window_on_parent` placement). `TodoApp` instantiates and delegates to the settings window; tkinter imports stay lazy to keep the module importable headless.
- `implementer/src/todo_md/settings_window.py` — `SettingsWindow` owns all settings-window construction and the Save flow (widgets, vars, browse, directory decision/sync via module helpers `decide_lists_dir`, `sync_lists_directory`, `lists_dir_setting`); lazy-imported from `app.py`.
- `implementer/src/todo_md/item_row.py` — `build_item_row` builds one packed item row (checkbutton, trash + edit icons, text label with per-item callbacks) and returns the 5-tuple stored in `TodoApp._item_rows`; `bg_kwargs` collapses the conditional-bg widget-kwargs pattern; everything arrives as parameters, tkinter lazy-imported, never imports `todo_md.app`.
- `implementer/src/todo_md/theme.py` — theme engine: `apply_theme(root, app)` (native `tk appappearance` path or clam fallback with explicit palettes), `palette_for`, luminance-adaptive `text_colors`, `button_text`; duck-typed app parameter, never imports `todo_md.app`; `TodoApp` keeps `_palette` and thin `_apply_theme`/`_text_colors`/`_theme_button_text` wrappers.
- `implementer/src/todo_md/edit_dialog.py` — `EditItemDialog` builds the modal edit Toplevel (pre-populated title entry, multi-line description, save/cancel, grab, centering); duck-typed app, callbacks for save/close; `TodoApp` keeps a `_edit` holder and read-only `_edit_*` properties.
- `implementer/src/todo_md/placeholders.py` — `PlaceholderBinder` owns the muted-hint map and attach/focus/restore/value logic (no tkinter dependency, imported at `app.py` top level); `TodoApp._placeholders` is an alias of the binder's map.
- `implementer/src/todo_md/dialogs.py` — shared dialog helpers: `center_window_on_parent` (self-correcting centering over the live main window) and `apply_dock_icon` (resolves `dock_icon_path` dynamically on `todo_md.app`); tkinter lazy, no `todo_md.app` import at module level.
- `implementer/src/todo_md/settings.py` — headless `Settings` load/save and theme resolution; settings GUI has Save/Cancel, directory change with optional list movement.
- `implementer/src/todo_md/version.py` — headless `get_version()` from `todo_md/VERSION`.
- `implementer/src/todo_md/__main__.py` — entry point `run()` wiring controller + GUI.
- `implementer/src/scripts/build_app.sh`, `release_package.sh`, `bump_version.sh` — build, packaging, version hook.
- `implementer/src/tests/` — pytest suite; `conftest.py` shares isolated data/config dirs and a dialog guard; GUI tests run on a real display.

## Data Models and Flow

- Flow: GUI → `TodoController` → models → `MarkdownListStore` → `.md` files; store re-read after each mutation drives UI refresh.
- `TodoItem` owns text, description, completion state, creation timestamp; completed items keep completion order above unfinished items.
- Markdown format: `# Name` header, `- [ ]` / `- [x]` lines; an item description (optional, multi-line) is stored as two-space-indented continuation lines directly under its checkbox line; legacy files without them parse as empty description; hidden/filtered items are never deleted from disk.
- Settings persist a full payload (theme, completed-item filter count, lists directory) and apply live; relocation failures leave recoverable files and keep the old directory usable.

## External Interfaces

- Filesystem: lists directory (default `~/.todo-md-app/lists/`), one `.md` per list; hand edits are picked up on refresh.
- Settings file under the app config directory; schema in `implementer/src/todo_md/settings.py`.
- Build outputs: `src/dist/todo-md.app` and `src/dist/todo-md-<version>-arm64.zip` (gitignored; zip consumed as a GitHub release asset).
- Version badge read from `todo_md/VERSION`.

## Known Architectural Debt

- `app.py` (859 lines) is a god class: `TodoApp` (~595 lines) centers on main layout + refresh and also hosts `TodoController` plus headless helpers; settings window, item rows, theme engine, edit dialog, placeholders, and dialog helpers already split out to `settings_window.py` / `item_row.py` / `theme.py` / `edit_dialog.py` / `placeholders.py` / `dialogs.py` (R1-R6). Duplicated patterns: `current_list is None` guard four times, `nonlocal` closures in the controller. Being split by refactor series R7-R8 (plan in `TASKS.md`; tests frozen for the series).
- Filtered completion display and relocation/retry logic live in the controller, a growing class worth watching for a settings-domain split.
- GUI tests depend on a local display and geometry on the local display; no headless fallback.