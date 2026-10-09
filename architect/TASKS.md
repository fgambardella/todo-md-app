# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional `<!-- Description: -->` line). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -v)` (344 pass, 2 skip, ~25s baseline).
- Targeted: `.venv/bin/python -m pytest tests/<file> -v` from `implementer/src/`.
- Refactor series R1-R8: **test files are frozen** — implementers may not add, modify, or remove any test; every task is verified against the existing suite only.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together, and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` hosts the Tkinter GUI shell, while its settings window, item rows, theme engine, edit dialog, placeholders, dialog helpers, controller, and visible-items filter now live in dedicated modules; `app.py` remains the target of refactor series R1-R8. All 344 tests pass.

## Active Task
**R7 (S)** — Move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py`; re-export both from `app.py`; pure move, no behavior change.
- Branch: `implementer/r7-controller` (base `main`; integration branch `main`).
- Scope: create `implementer/src/todo_md/controller.py`; modify `implementer/src/todo_md/models.py` and `implementer/src/todo_md/app.py` only.
- Acceptance: `TodoController` and `visible_items` defined in the new locations; `todo_md.app` still exports both (and `TodoApp`, `run`, `dock_icon_path`) with identical behavior; zero test edits; full suite green; headless import intact.
- Required tests: full suite; targeted `tests/test_visible_items.py tests/test_controller.py tests/test_storage.py tests/test_models.py tests/test_gui_toggle.py tests/test_gui_items.py tests/test_gui_headless.py tests/test_startup.py`.
- Commands (from `implementer/src/`): targeted `.venv/bin/python -m pytest tests/test_visible_items.py tests/test_controller.py tests/test_storage.py tests/test_models.py tests/test_gui_toggle.py tests/test_gui_items.py tests/test_gui_headless.py tests/test_startup.py -v`; full `.venv/bin/python -m pytest tests -v`.

### Implementer Prompt (R7)
Task R7 — Move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py` (pure moves, no behavior change).
Branch: work only on `implementer/r7-controller` (already checked out); base and integration branch is `main`. Never create/switch/merge/rebase/rename/delete/push branches; never commit to `main`; no broad `git add -A`, `reset`, or `clean` — stage only the files you changed.
First tool call: run `../architect/tools/implementer-run.sh` with no arguments; use that wrapper for ALL later Bash commands; follow the Mandatory Execution Clock phase rules. Executing it is permitted; modifying it is forbidden.
Before editing: verify the current branch (`git rev-parse --abbrev-ref HEAD`) and inspect the working tree (`git status --short`).
Scope — you may create/modify ONLY: `implementer/src/todo_md/controller.py` (new), `implementer/src/todo_md/models.py`, and `implementer/src/todo_md/app.py`.
Forbidden: every file under `implementer/src/tests/` (tests are frozen — zero modifications), all other `todo_md` modules, everything under `implementer/../architect/` (i.e. `../architect/`), repository root.
Work:
1. Create `implementer/src/todo_md/controller.py`: move the `TodoController` class verbatim (all methods, docstrings, comments unchanged) with the imports it needs: `from __future__ import annotations`, `import os`, `from .models import TodoItem, TodoList`, `from .storage import MarkdownListStore, relocate_lists`. Add a one-paragraph module docstring noting it is the headless controller layer (no tkinter dependency).
2. In `implementer/src/todo_md/models.py`: move the `visible_items` function verbatim (docstring and ValueError message unchanged) into the module.
3. In `implementer/src/todo_md/app.py`:
   - Delete the `TodoController` class definition and the `visible_items` function.
   - Imports: `from .models import visible_items` and `from .controller import TodoController`; keep `from .storage import MarkdownListStore` (drop `relocate_lists` — only the controller used it); drop `from .models import TodoItem, TodoList` if no longer referenced in `app.py` (verify first — if any remaining reference exists, keep it).
   - `__all__` keeps the exact same names (`TodoController`, `TodoApp`, `run`, `DEFAULT_CONFIG_DIR`, `DEFAULT_DATA_DIR`, `startup_dirs`, `visible_items`).
   - Update the module docstring's first line if it names `TodoController` as defined here (it should now say the controller lives in `controller.py` and is re-exported for compatibility; keep the headless-import note).
   - No other `app.py` changes.
Hard invariants:
- Zero test modifications; 22 test files do `from todo_md.app import TodoController` and `tests/test_visible_items.py` imports `visible_items` from `todo_md.app` — the re-exports must keep every one working.
- `import todo_md.app` must stay headless; `controller.py` and `models.py` have no tkinter dependency (module-level imports fine there).
- Identical behavior: this is a pure move; no signature, message, or ordering changes.
Acceptance: both objects live in their new canonical modules; `todo_md.app` re-exports them; full suite green with zero test edits.
Commands (from `implementer/src/`): targeted `.venv/bin/python -m pytest tests/test_visible_items.py tests/test_controller.py tests/test_storage.py tests/test_models.py tests/test_gui_toggle.py tests/test_gui_items.py tests/test_gui_headless.py tests/test_startup.py -v`; then full `.venv/bin/python -m pytest tests -v`.
On completion: commit the changed files on `implementer/r7-controller` (the pre-commit hook may auto-stage a VERSION bump — expected, leave it), then hand off: RESULT: SUCCESS|FAILURE, SUMMARY (3-5 bullets), BRANCH, COMMIT hash, test totals. Keep edits minimal and commit early; the clock is the known risk.

## Queue
- **R8 (S):** final complexity pass on remaining `app.py`: collapse the repeated `current_list is None` guards, remove the controller `nonlocal` closure pattern, dedupe any remaining kwargs patterns, slim `__init__`; target `app.py` ≈ 400 lines or fewer.

## Active Blockers
None.

## Recently Completed
- R6 — Extract shared dialog helpers (window centering, dock icon) into `todo_md/dialogs.py`: DONE (Implementer commit c8b8773).
- R5 — Extract entry-placeholder mechanism into `todo_md/placeholders.py` (PlaceholderBinder) + `self._ph` holder: DONE (Implementer commit 8ff404b).
- R4 — Extract modal edit dialog into `todo_md/edit_dialog.py` (EditItemDialog) + delegation properties: DONE (Implementer commit 3b52df2).
- R3 — Extract theme engine (palette, apply_theme, text_colors, button_text) into `todo_md/theme.py`: DONE (Implementer commit fda5317).
- R1 — Extract Settings window (construction + save flow) into `todo_md/settings_window.py`: DONE (Implementer commit e8f3f37; merged to main at 495e9d5).
