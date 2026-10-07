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
**R1 (M)** — Extract the Settings window from `TodoApp` into `todo_md/settings_window.py`. R1.1 DONE+verified (`c85ed9b`). R1.2 attempt 1 TIMED OUT, no changes. R1.2a attempt 2 TIMED OUT but committed WIP `d8aaa2f` (relocation done; 79/80 targeted green) — INDEPENDENTLY VERIFIED the one failure: frozen test `test_post_switch_preference_resolution_error_still_synchronizes_live_view` does `patch.object(app, "_lists_dir_setting", side_effect=...)` on the TodoApp instance. Architect decision: keep that instance seam on the live call path. Active micro-task: R1.2a-fix on the same branch.
- Branch: `implementer/r1-settings-window` (base `main`; integration branch `main`). Checkpoint: `d8aaa2f` (Implementer WIP; relocation faithful, one known failure to fix).
- Scope: `implementer/src/todo_md/settings_window.py` + `implementer/src/todo_md/app.py` only.
- Acceptance (task R1): settings construction AND save flow fully owned by `settings_window.py`; zero behavior change; full suite green with zero test edits; headless import intact.
- Required tests: full suite; targeted `tests/test_gui_settings.py tests/test_gui_centering.py tests/test_gui_headless.py tests/test_startup.py`.
- Commands (from `implementer/src/`): full `.venv/bin/python -m pytest tests -v`; targeted `.venv/bin/python -m pytest tests/test_gui_settings.py tests/test_gui_centering.py tests/test_gui_headless.py tests/test_startup.py -v`.

### Implementer Prompt (micro-task R1.2a-fix — restore frozen-test seam)
Task R1.2a-fix — Preserve the frozen-test seam for `_lists_dir_setting`. Current state: commit `d8aaa2f` already relocated the three helpers to `settings_window.py` (that part is approved in shape). One frozen test fails because it patches the attribute on the app instance.
Branch: work only on `implementer/r1-settings-window` (already checked out at `d8aaa2f`); base and integration branch is `main`. Never create/switch/merge/rebase/rename/delete/push branches; never commit to `main`.
First tool call: run `../architect/tools/implementer-run.sh` with no arguments; use that wrapper for ALL later Bash commands; follow the Mandatory Execution Clock phase rules. Executing it is permitted; modifying it is forbidden.
Before editing: verify the current branch and inspect the working tree (`git status --short`).
Scope — you may create/modify ONLY: `implementer/src/todo_md/settings_window.py` and `implementer/src/todo_md/app.py`.
Forbidden: every file under `implementer/src/tests/`, everything under `architect/`, repository root, and all other `todo_md` modules.
Work (nothing else):
1. In `settings_window.py`, function `sync_lists_directory(app)`: replace the direct module-level call `lists_dir_setting(app.settings.lists_dir)` with the instance-attribute path `app._lists_dir_setting(app.settings.lists_dir)` (this is the frozen-test seam; keep a short comment saying so).
2. In `app.py`, restore `TodoApp._lists_dir_setting` as a thin `@staticmethod` that delegates: docstring 'Persisted form of an effective directory: None for the default.' then lazy `from . import settings_window as sw` and `return sw.lists_dir_setting(path)`.
3. No other changes; zero test modifications.
Acceptance: `tests/test_gui_settings.py` fully green (including `test_post_switch_preference_resolution_error_still_synchronizes_live_view`) and full suite green.
Commands (from `implementer/src/`): targeted `.venv/bin/python -m pytest tests/test_gui_settings.py tests/test_gui_headless.py tests/test_startup.py -v`; full `.venv/bin/python -m pytest tests -v`.
On completion (or stabilized partial work): commit on `implementer/r1-settings-window`, then hand off with RESULT: SUCCESS|FAILURE, SUMMARY (3-5 bullets), BRANCH, COMMIT hash, and the test totals.

## Queue
- **R1.2b (S):** move `TodoApp._settings_on_save` body into `SettingsWindow.on_save()`; Save button command becomes `self.on_save`; re-apply step calls app (`self.app.theme = resolve_theme(...)`, `_apply_theme`, `_theme_btn.config`, `_refresh_items`, then `_close_settings`); read `save_settings` via dynamic `app_module` lookup (tests monkeypatch `todo_md.app.save_settings`); delete the method from `TodoApp`.
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