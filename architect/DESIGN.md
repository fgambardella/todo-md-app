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

- `implementer/src/todo_md/models.py` — domain: `TodoItem` (text, done, created, description), `TodoList` with validated `add_item`, `edit` (title + description), `toggle`, `remove`, `rename`, and the display-only `visible_items` filter.
- `implementer/src/todo_md/storage.py` — persistence: `MarkdownListStore`, one `<Name>.md` per list, atomic writes, name sanitization.
- `implementer/src/todo_md/controller.py` — headless `TodoController` (UI-agnostic view-model; every mutation persists immediately; calls `storage.relocate_lists` directly — no GUI-module references); re-exported by `app.py`.
- `implementer/src/todo_md/app.py` (533 lines) — `TodoApp` (Tkinter GUI shell: main window layout, list/item handlers, confirmations; dialogs opened centered via the self-correcting `_center_window_on_parent` placement). Delegates to the extracted modules (sidebar, settings window, item rows, theme, edit dialog, placeholders, dialogs); tkinter imports stay lazy to keep the module importable headless.
- `implementer/src/todo_md/settings_window.py` — `SettingsWindow` owns all settings-window construction and the Save flow (widgets, vars, browse, directory decision/sync via module helpers `decide_lists_dir`, `sync_lists_directory`, `lists_dir_setting`); lazy-imported from `app.py`.
- `implementer/src/todo_md/sidebar.py` — `build_sidebar(app)` builds the packed left "Lists:" frame (listbox, new-list entry with placeholder, Create/Delete row, theme + Settings buttons, all stored as app attributes); duck-typed app, tkinter lazy, never imports `todo_md.app` (R10a).
- `implementer/src/todo_md/item_row.py` — `build_item_row` builds one packed item row (checkbutton, trash + edit icons, text label with per-item callbacks) and `rebuild_rows(app)` repopulates `TodoApp._item_rows` for the current list; `bg_kwargs` collapses the conditional-bg widget-kwargs pattern; everything arrives as parameters, tkinter lazy-imported, never imports `todo_md.app`.
- `implementer/src/todo_md/theme.py` — theme engine: `apply_theme(root, app)` (native `tk appappearance` path or clam fallback with explicit palettes) and sets `TSpinbox -arrowcolor` to the palette fg and maps its `-background`/`-arrowcolor` for the `active`/`pressed` states to a dedicated `spin_hover` fill (Tk 9 C Arrow element defaults near-black and inherits the TCombobox light hover background; hover fill deliberately more contrasting than `btn_active` — B1/B2/B3), `palette_for`, luminance-adaptive `text_colors`, `button_text`; duck-typed app parameter, never imports `todo_md.app`; `TodoApp` keeps `_palette` and thin `_apply_theme`/`_text_colors`/`_theme_button_text` wrappers.
- `implementer/src/todo_md/edit_dialog.py` — `EditItemDialog` builds the modal edit Toplevel (pre-populated title entry, multi-line description with vertical scrollbar, user-resizable in both dimensions via a BOTH/expand pack chain + resize grip (C1/C3), save/cancel, grab, centering); duck-typed app, callbacks for save/close; plus the open/save/close lifecycle as `open_dialog`/`save_dialog`/`close_dialog` (R10b); `TodoApp` keeps a `_edit` holder, `_edit_index`, and read-only `_edit_*` properties, with one-line delegating wrappers.
- `implementer/src/todo_md/placeholders.py` — `PlaceholderBinder` owns the muted-hint map and attach/focus/restore/value logic (no tkinter dependency, imported at `app.py` top level); `TodoApp._placeholders` is an alias of the binder's map.
- `implementer/src/todo_md/dialogs.py` — shared dialog helpers: `center_window_on_parent` (self-correcting centering over the live main window) and `apply_dock_icon(root, icon_path)` (fail-soft; path passed by caller); canonical home of `dock_icon_path`, re-exported by `app.py` for test import/patch compatibility; tkinter lazy, no `todo_md.app` import.
- `implementer/src/todo_md/settings.py` — headless `Settings` load/save and theme resolution; settings GUI has Save/Cancel, directory change with optional list movement.
- `implementer/src/todo_md/version.py` — headless `get_version()` from `todo_md/VERSION`.
- `implementer/src/todo_md/__main__.py` — entry point `run()` wiring controller + GUI.
- `implementer/src/scripts/build_app.sh`, `release_package.sh`, `bump_version.sh` — build, packaging, version hook.
- `implementer/src/tests/` — pytest suite; `conftest.py` shares isolated data/config dirs and a dialog guard; GUI tests run on a real display.

## Data Models and Flow

- Flow: GUI → `TodoController` → models → `MarkdownListStore` → `.md` files; store re-read after each mutation drives UI refresh.
- `TodoItem` owns text, description, completion state, creation timestamp; completed items keep completion order above unfinished items.
- Markdown format: `# Name` header, `- [ ]` / `- [x]` lines; an item description (optional, multi-line) is stored as two-space-indented continuation lines directly under its checkbox line — internal blank lines as two-space-only lines, so they round-trip (C2); legacy files without them parse as empty description; hidden/filtered items are never deleted from disk.
- Settings persist a full payload (theme, completed-item filter count, lists directory) and apply live; relocation failures leave recoverable files and keep the old directory usable.

## External Interfaces

- Filesystem: lists directory (default `~/.todo-md-app/lists/`), one `.md` per list; hand edits are picked up on refresh.
- Settings file under the app config directory; schema in `implementer/src/todo_md/settings.py`.
- Build outputs: `src/dist/todo-md.app` and `src/dist/todo-md-<version>-arm64.zip` (gitignored; zip consumed as a GitHub release asset).
- Version badge read from `todo_md/VERSION`.

## Known Architectural Debt

- `app.py` is the largest module (533 lines): `TodoApp` still owns the main window layout (version badge, right item frame), the list/item frame handlers, and thin delegations; sidebar, settings window, item rows, theme engine, edit dialog (construction + lifecycle), placeholders, dialog helpers, controller, and visible-items filter are split out (R1-R8, R10, complete). Watch for re-growth after further feature work.
- Relocation/retry logic and per-item load-mutate-save live in the controller, a growing class worth watching for a settings-domain split.
- GUI tests depend on a local display and geometry on the local display; no headless fallback.