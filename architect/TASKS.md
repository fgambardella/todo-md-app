# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional `<!-- Description: -->` line). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -v)` (344 pass, 2 skip, ~25s baseline).
- Targeted: `.venv/bin/python -m pytest tests/<file> -v` from `implementer/src/`.
- Refactor series R1-R8: **test files are frozen** — implementers may not add, modify, or remove any test; every task is verified against the existing suite only.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together, and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` hosts the Tkinter GUI shell, while its settings window, item rows, theme engine, edit dialog, and placeholder mechanism now live in dedicated modules; `app.py` remains the target of refactor series R1-R8. All 344 tests pass.

## Active Task
**R6 (S)** — Extract shared dialog helpers into `todo_md/dialogs.py` (window centering, dock-icon apply — the dock-icon path must be looked up dynamically on `todo_md.app` since tests monkeypatch `app.dock_icon_path`).
- Branch: `implementer/r6-dialogs` (base `main`; integration branch `main`).
- Scope: create `implementer/src/todo_md/dialogs.py`; modify `implementer/src/todo_md/app.py` only.
- Acceptance: centering + dock-icon logic lives in `dialogs.py`; `TodoApp._apply_dock_icon` / `TodoApp._center_window_on_parent` keep their names/behavior (edit_dialog and settings_window still call them); `dock_icon_path` remains a `todo_md.app` module-level name; zero test edits; full suite green; headless import intact.
- Required tests: full suite; targeted `tests/test_gui_dock_icon.py tests/test_gui_lifecycle.py tests/test_gui_centering.py tests/test_gui_edit.py tests/test_gui_settings_window.py tests/test_gui_headless.py tests/test_startup.py tests/test_build_script.py`.
- Commands (from `implementer/src/`): targeted `.venv/bin/python -m pytest tests/test_gui_dock_icon.py tests/test_gui_lifecycle.py tests/test_gui_centering.py tests/test_gui_edit.py tests/test_gui_settings_window.py tests/test_gui_headless.py tests/test_startup.py tests/test_build_script.py -v`; full `.venv/bin/python -m pytest tests -v`.

### Implementer Prompt (R6)
Task R6 — Extract shared dialog helpers into `todo_md/dialogs.py`.
Branch: work only on `implementer/r6-dialogs` (already checked out); base and integration branch is `main`. Never create/switch/merge/rebase/rename/delete/push branches; never commit to `main`; no broad `git add -A`, `reset`, or `clean` — stage only the files you changed.
First tool call: run `../architect/tools/implementer-run.sh` with no arguments; use that wrapper for ALL later Bash commands; follow the Mandatory Execution Clock phase rules. Executing it is permitted; modifying it is forbidden.
Before editing: verify the current branch (`git rev-parse --abbrev-ref HEAD`) and inspect the working tree (`git status --short`).
Scope — you may create/modify ONLY: `implementer/src/todo_md/dialogs.py` (new) and `implementer/src/todo_md/app.py`.
Forbidden: every file under `src/tests/` (tests are frozen — zero modifications), all other `todo_md` modules, everything under `../architect/`, repository root.
Work:
1. Create `implementer/src/todo_md/dialogs.py` with two functions (tkinter imported lazily inside functions; no module-level tkinter import):
   - `center_window_on_parent(parent_root, win)` — the exact body of `TodoApp._center_window_on_parent` with `self.root` → `parent_root` (preserve the full docstring and all explanatory comments).
   - `apply_dock_icon(root)` — the body of `TodoApp._apply_dock_icon`: try `tk.PhotoImage(file=...)` except `tk.TclError` → return `None`; then `root.iconphoto(True, photo)` inside the existing TclError try/except; return the photo. The icon file path MUST be obtained via dynamic lookup so tests that monkeypatch `todo_md.app.dock_icon_path` keep working: `from . import app as app_module` (inside the function) and `app_module.dock_icon_path()`. Preserve all explanatory comments.
2. In `app.py` replace the two method bodies with thin wrappers (lazy `from .dialogs import ...` inside each method, docstrings preserved):
   - `_apply_dock_icon(self)` → `self._dock_icon = apply_dock_icon(self.root)`
   - `_center_window_on_parent(self, win)` → `center_window_on_parent(self.root, win)`
   - Keep the module-level `dock_icon_path` function exactly as-is (tests import it from `todo_md.app`). No other `app.py` changes.
Hard invariants:
- Zero test modifications. `tests/test_gui_dock_icon.py` imports `dock_icon_path` from `todo_md.app`, asserts `app._dock_icon` is a `tk.PhotoImage` (or `None` when the monkeypatched path is missing), and `tests/test_gui_lifecycle.py` monkeypatches `TodoApp._apply_dock_icon` — all must keep working identically.
- `edit_dialog.py` and `settings_window.py` call `app._center_window_on_parent(...)` — leave them untouched.
- `import todo_md.app` must stay headless; `dialogs.py` must have no top-level tkinter import.
- All `todo_md.app` module-level names and `__all__` must remain untouched.
Acceptance: helpers live in `dialogs.py`; both methods behave identically; full suite green with zero test edits.
Commands (from `src/`): targeted `.venv/bin/python -m pytest tests/test_gui_dock_icon.py tests/test_gui_lifecycle.py tests/test_gui_centering.py tests/test_gui_edit.py tests/test_gui_settings_window.py tests/test_gui_headless.py tests/test_startup.py tests/test_build_script.py -v`; then full `.venv/bin/python -m pytest tests -v`.
On completion: commit BOTH files on `implementer/r6-dialogs` (the pre-commit hook may auto-stage a VERSION bump — expected, leave it), then hand off: RESULT: SUCCESS|FAILURE, SUMMARY (3-5 bullets), BRANCH, COMMIT hash, test totals. Keep edits minimal and commit early; the clock is the known risk.

## Queue
- **R7 (S):** move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py`; re-export both from `app.py`; pure move, no behavior change.
- **R8 (S):** final complexity pass on remaining `app.py`: collapse the repeated `current_list is None` guards, remove the controller `nonlocal` closure pattern, dedupe any remaining kwargs patterns, slim `__init__`; target `app.py` ≈ 400 lines or fewer.

## Active Blockers
None.

## Recently Completed
- R5 — Extract entry-placeholder mechanism into `todo_md/placeholders.py` (PlaceholderBinder) + `self._ph` holder: DONE (Implementer commit 8ff404b).
- R4 — Extract modal edit dialog into `todo_md/edit_dialog.py` (EditItemDialog) + delegation properties: DONE (Implementer commit 3b52df2).
- R3 — Extract theme engine (palette, apply_theme, text_colors, button_text) into `todo_md/theme.py`: DONE (Implementer commit fda5317).
- R2 — Extract item-row rendering into `todo_md/item_row.py` + `bg_kwargs` helper: DONE (Implementer commit aee8051).
- R1 — Extract Settings window (construction + save flow) into `todo_md/settings_window.py`: DONE (Implementer commit e8f3f37; merged to main at 495e9d5).
