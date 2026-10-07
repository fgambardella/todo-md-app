# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional `<!-- Description: -->` line). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -v)` (344 pass, 2 skip, ~25s baseline).
- Targeted: `.venv/bin/python -m pytest tests/<file> -v` from `implementer/src/`.
- Refactor series R1-R8: **test files are frozen** — implementers may not add, modify, or remove any test; every task is verified against the existing suite only.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together, and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` also hosts the full Tkinter GUI — its settings-window construction now lives in a dedicated module while the rest stays in `app.py`, the target of refactor series R1-R8. All 344 tests pass.

## Active Task
**R1 (M)** — Extract the Settings window from `TodoApp` into `todo_md/settings_window.py`. R1.1 DONE+verified (commit `c85ed9b`, 344 pass/2 skip). R1.2 first attempt TIMED OUT with no commit and a clean tree (verified `COMMIT: NONE`); R1.2 split into R1.2a (active) → R1.2b.
- Branch: `implementer/r1-settings-window` (base `main`; integration branch `main`). Checkpoint: `dc20bd3` (architect commit; no Implementer changes yet).
- Scope: `implementer/src/todo_md/settings_window.py` + `implementer/src/todo_md/app.py` only.
- Acceptance (task R1): settings construction AND save flow fully owned by `settings_window.py`; zero behavior change (widgets, layout, defaults, focus, centering, validation order, error strings, persistence identical); full suite green with zero test edits; headless import intact.
- Required tests: full suite; targeted `tests/test_gui_settings.py tests/test_gui_centering.py tests/test_gui_headless.py tests/test_startup.py`.
- Commands (from `implementer/src/`): full `.venv/bin/python -m pytest tests -v`; targeted `.venv/bin/python -m pytest tests/test_gui_settings.py tests/test_gui_centering.py tests/test_gui_headless.py tests/test_startup.py -v`.

### Implementer Prompt (micro-task R1.2a — helpers only)
Task R1.2a — Relocate the three settings helpers from `TodoApp` to `todo_md/settings_window.py` as module functions. This is a pure function relocation: small diff, no logic changes.
Branch: work only on `implementer/r1-settings-window` (already checked out at `dc20bd3`); base and integration branch is `main`. Never create/switch/merge/rebase/rename/delete/push branches; never commit to `main`.
First tool call: run `../architect/tools/implementer-run.sh` with no arguments; use that wrapper for ALL later Bash commands; follow the Mandatory Execution Clock phase rules. Executing it is permitted; modifying it is forbidden.
Before editing: verify the current branch and inspect the working tree (`git status --short`).
Scope — you may create/modify ONLY: `implementer/src/todo_md/settings_window.py` and `implementer/src/todo_md/app.py`.
Forbidden: every file under `implementer/src/tests/`, everything under `architect/`, repository root, and all other `todo_md` modules.
Work (nothing else):
1. Add three module-level functions to `settings_window.py`, ported 1:1 from `TodoApp` with `self.` → `app.` and docstrings preserved:
   - `decide_lists_dir(app, messagebox, entry_text)` (from `TodoApp._decide_lists_dir`)
   - `sync_lists_directory(app)` (from `TodoApp._sync_lists_directory`)
   - `lists_dir_setting(path)` (from `TodoApp._lists_dir_setting`)
   Inside `decide_lists_dir`, the call to the sync helper becomes `sync_lists_directory(app)`.
2. Delete `_decide_lists_dir`, `_sync_lists_directory`, `_lists_dir_setting` from `TodoApp`.
3. In `TodoApp._settings_on_save`, replace the call sites with lazy-imported module calls, e.g. `from . import settings_window as sw` at the top of the method, then `sw.decide_lists_dir(self, messagebox, target)`, `sw.sync_lists_directory(self)`, `sw.lists_dir_setting(...)`. Do not change any other line of `_settings_on_save` or any other code.
Hard invariants:
- `import todo_md.app` stays headless; no top-level tkinter in `settings_window.py`.
- The relocated functions must read test-patched names via the existing dynamic lookup: `app_module._has_markdown`, `app_module._valid_lists_dir_path`, `app_module._same_dir`, `app_module._normalize_dir`, `app_module.DEFAULT_DATA_DIR` — never top-level imports of those names.
- Zero test modifications; identical behavior.
Acceptance: the three helpers exist only in `settings_window.py`; `TodoApp` no longer defines them; full suite green.
Commands (from `implementer/src/`): full `.venv/bin/python -m pytest tests -v`; targeted `.venv/bin/python -m pytest tests/test_gui_settings.py tests/test_gui_headless.py tests/test_startup.py -v`.
On completion (or stabilized partial work): commit on `implementer/r1-settings-window`, then hand off with RESULT: SUCCESS|FAILURE, SUMMARY (3-5 bullets), BRANCH, COMMIT hash, and the test totals.

## Queue
- **R1.2b (S):** move `TodoApp._settings_on_save` body into `SettingsWindow.on_save()`; Save button command becomes `self.on_save`; re-apply step calls app (`self.app.theme = resolve_theme(...)`, `_apply_theme`, `_theme_btn.config`, `_refresh_items`, then `_close_settings`); read `save_settings`/`DEFAULT_CONFIG_DIR` via dynamic `app_module` lookup; delete the method from `TodoApp`.
- **R2 (S):** extract item-row rendering from `_refresh_items` into `todo_md/item_row.py`; collapse the five duplicated `{"bg": ...} if ... else {}` kwargs patterns into one helper.
- **R3 (S):** extract the theme engine (palette, `_apply_theme`, luminance `_text_colors`, `_theme_button_text`) into `todo_md/theme.py`; `TodoApp` keeps `_palette`, `_apply_theme`, `_theme_button_text` as thin wrappers.
- **R4 (S):** extract the modal edit dialog into `todo_md/edit_dialog.py` (`EditItemDialog`); `TodoApp` keeps `_edit_window`, `_edit_entry`, `_edit_desc_text`, `_edit_save_btn`, `_edit_cancel_btn`, `_open_edit_dialog`, `_close_edit_dialog` via delegation.
- **R5 (S):** extract the entry-placeholder mechanism into `todo_md/placeholders.py`; `TodoApp` keeps `_placeholders`, `_entry_value`, `_restore_placeholder` as thin wrappers.
- **R6 (S):** extract shared dialog helpers into `todo_md/dialogs.py` (window centering, dock-icon apply — must call `todo_md.app.dock_icon_path` via dynamic lookup since tests monkeypatch it).
- **R7 (S):** move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py`; re-export both from `app.py`; pure move, no behavior change.
- **R8 (S):** final complexity pass on remaining `app.py`: collapse the repeated `current_list is None` guards, remove the controller `nonlocal` closure pattern, dedupe any remaining kwargs patterns, slim `__init__`; target `app.py` ≈ 400 lines or fewer.

## Active Blockers
None.

## Recently Completed
- 47 — Center modal dialogs on the main window (edit + settings): DONE (v1.0.0 released; Implementer commit d547cbf).
- 46 — Persist settings.json on every change: DONE (Implementer commit c9f9711).
- 45 — Fix dark-theme unreadable gray text: DONE (Implementer commit 0c9e64b).
- 44 — Theme system with live switching and dock icon: DONE (Implementer commit 893d7a9).
- 43 — Fix settings "Select..." open on top of main window: DONE (Implementer commit 7743607).