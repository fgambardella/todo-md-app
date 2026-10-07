# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional `<!-- Description: -->` line). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -v)` (344 pass, 2 skip, ~30s baseline).
- Targeted: `.venv/bin/python -m pytest tests/<file> -v` from `implementer/src/`.
- Refactor series R1-R8: **test files are frozen** — implementers may not add, modify, or remove any test; every task is verified against the existing suite only.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together, and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` also hosts the full Tkinter GUI, which is the current largest module and the target of refactor series R1-R8. All 344 tests pass.

## Active Task
**R1 (M)** — Extract the Settings window from `TodoApp` into `todo_md/settings_window.py`. Micro-tasks R1.1 → R1.2 run sequentially on one branch.
- Branch: `implementer/r1-settings-window` (base `main`; integration branch `main`).
- Scope: create `implementer/src/todo_md/settings_window.py`; modify `implementer/src/todo_md/app.py`. Nothing else.
- R1.1: `SettingsWindow` class owns all settings-window construction (Toplevel, centering, vars, entry, theme radio group, spinbox, buttons, browse, close); `TodoApp` keeps thin delegation.
- R1.2: move the save flow (`_settings_on_save`, `_decide_lists_dir`, `_sync_lists_directory`, `_lists_dir_setting`) into the `SettingsWindow`/module; `TodoApp` delegates.
- Acceptance: settings construction+save fully owned by the new module; zero behavior change (widgets, layout, defaults, focus, centering, validation, persistence, error strings identical); test suite fully green with zero test edits; headless import intact.
- Required tests: full suite; targeted `tests/test_gui_settings.py tests/test_gui_centering.py tests/test_gui_headless.py tests/test_startup.py`.
- Commands (from `implementer/src/`): full `.venv/bin/python -m pytest tests -v`; targeted `.venv/bin/python -m pytest tests/test_gui_settings.py tests/test_gui_centering.py tests/test_gui_headless.py tests/test_startup.py -v`.

### Implementer Prompt (micro-task R1.1)
Task R1.1 — Extract settings-window construction into `todo_md/settings_window.py`.
Branch: work only on `implementer/r1-settings-window` (already checked out); base and integration branch is `main`. Never create/switch/merge/rebase/rename/delete/push branches; never commit to `main`.
First tool call: run `../architect/tools/implementer-run.sh` with no arguments; use that wrapper for ALL later Bash commands; follow the Mandatory Execution Clock phase rules. Executing it is permitted; modifying it is forbidden.
Before editing: verify the current branch and inspect the working tree (`git status --short`). Read the `Component Architecture` section of `architect/DESIGN.md` for context.
Scope — you may create/modify ONLY: `implementer/src/todo_md/settings_window.py` (new) and `implementer/src/todo_md/app.py`.
Forbidden: every file under `implementer/src/tests/`, everything under `architect/`, repository root, and all other `todo_md` modules.
Work:
1. Create `SettingsWindow` in `settings_window.py` owning all construction currently in `TodoApp._open_settings`: Toplevel creation, centering, `lists_dir` entry + vars, theme radio group, completed spinbox, save/cancel/reset/browse buttons and their handlers, close handler. Public attributes for each widget/var (`window`, `lists_dir_var`, `theme_var`, `theme_rads`, `completed_var`, `spinbox`, `save_btn`, `cancel_btn`, `reset_btn`). The save flow stays on `TodoApp` in this micro-task (R1.2 moves it); the window must expose what the app needs to run it.
2. `TodoApp._open_settings` becomes a thin method instantiating `SettingsWindow`; `_close_settings` delegates.
3. Add delegating `@property` entries on `TodoApp` so every attribute tests read keeps working: `settings_window`, `_settings_lists_dir_var`, `_settings_theme_var`, `_settings_theme_rads`, `_settings_completed_var`, `_settings_spinbox`, `_settings_save_btn`, `_settings_cancel_btn`, `_settings_reset_btn`.
4. No behavior change: identical widgets, layout, defaults, focus handling, centering, close semantics.
Hard invariants:
- `import todo_md.app` must stay headless: no top-level `import tkinter` in `app.py` or the new module (import tkinter inside functions/methods).
- `todo_md.app.__all__` must still contain "TodoApp" and "run".
- Module attributes `DEFAULT_CONFIG_DIR`, `DEFAULT_DATA_DIR`, `_has_markdown`, `_valid_lists_dir_path`, `_same_dir`, `dock_icon_path`, `startup_dirs`, `visible_items` must remain on the `todo_md.app` module (they are monkeypatch targets).
- Any code reading those patchable names must use dynamic module lookup (`import todo_md.app as app_module; app_module._has_markdown(...)`) — never a name imported into another module's namespace.
Acceptance: all settings construction lives in `SettingsWindow`; `TodoApp` only delegates; full suite green with zero test modifications.
Commands (from `implementer/src/`): full `.venv/bin/python -m pytest tests -v`; targeted `.venv/bin/python -m pytest tests/test_gui_settings.py tests/test_gui_centering.py tests/test_gui_headless.py tests/test_startup.py -v`.
On completion (or stabilized partial work): commit on `implementer/r1-settings-window`, then hand off with RESULT: SUCCESS|FAILURE, SUMMARY (3-5 bullets), BRANCH, COMMIT hash, and the test totals.

## Queue
- **R1.2 (S):** move settings save flow (`_settings_on_save`, `_decide_lists_dir`, `_sync_lists_directory`, `_lists_dir_setting`) into `settings_window.py`; `TodoApp` delegates; keep dynamic `todo_md.app` lookups for all patchable names.
- **R2 (S):** extract item-row rendering from `_refresh_items` into `todo_md/item_row.py`; collapse the five duplicated `{"bg": ...} if ... else {}` kwargs patterns into one helper.
- **R3 (S):** extract the theme engine (palette, `_apply_theme`, luminance `_text_colors`, `_theme_button_text`) into `todo_md/theme.py`; `TodoApp` keeps `_palette`, `_apply_theme`, `_theme_button_text` as thin wrappers.
- **R4 (S):** extract the modal edit dialog into `todo_md/edit_dialog.py` (`EditItemDialog`); `TodoApp` keeps `_edit_window`, `_edit_entry`, `_edit_desc_text`, `_edit_save_btn`, `_edit_cancel_btn`, `_open_edit_dialog`, `_close_edit_dialog` via delegation.
- **R5 (S):** extract the entry-placeholder mechanism into `todo_md/placeholders.py`; `TodoApp` keeps `_placeholders`, `_entry_value`, `_restore_placeholder` as thin wrappers.
- **R6 (S):** extract shared dialog helpers into `todo_md/dialogs.py` (window centering, dock-icon apply — must call `todo_md.app.dock_icon_path` via dynamic lookup since tests monkeypatch it).
- **R7 (S):** move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py`; re-export both from `app.py` for import compatibility; pure move, no behavior change.
- **R8 (S):** final complexity pass on remaining `app.py`: collapse the repeated `current_list is None` guards, remove the controller `nonlocal` closure pattern, dedupe any remaining kwargs patterns, slim `__init__`; target `app.py` ≈ 400 lines or fewer.

## Active Blockers
None.

## Recently Completed
- 47 — Center modal dialogs on the main window (edit + settings): DONE (v1.0.0 released; Implementer commit d547cbf).
- 46 — Persist settings.json on every change: DONE (Implementer commit c9f9711).
- 45 — Fix dark-theme unreadable gray text: DONE (Implementer commit 0c9e64b).
- 44 — Theme system with live switching and dock icon: DONE (Implementer commit 893d7a9).
- 43 — Fix settings "Select..." open on top of main window: DONE (Implementer commit 7743607).