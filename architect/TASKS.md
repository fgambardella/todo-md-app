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
**R9 (S)** — Remove the two compat shims: canonical `dock_icon_path` + parameterized `apply_dock_icon`; canonical `relocate_lists` call in the controller (user-authorized minimal test repatch).
- Branch: `implementer/r9-shims` (base `main`; integration branch `main`).
- Scope: modify `implementer/src/todo_md/app.py`, `controller.py`, `dialogs.py`, and `implementer/src/tests/test_controller.py` only (test edit explicitly authorized by the user; limited to re-targeting 2 monkeypatch sites).
- Acceptance: no `from . import app` (or `import app_module`) left in `controller.py`/`dialogs.py`; `apply_dock_icon(root, icon_path)` is a pure parameter function; `app.dock_icon_path` still importable and monkeypatch-effective (frozen `test_gui_dock_icon.py` must pass UNCHANGED); full suite green.
- Required tests: full suite; targeted `tests/test_controller.py tests/test_gui_dock_icon.py tests/test_gui_lifecycle.py tests/test_gui_headless.py tests/test_startup.py tests/test_build_script.py`.
- Commands (from `implementer/src/`): targeted `.venv/bin/python -m pytest tests/test_controller.py tests/test_gui_dock_icon.py tests/test_gui_lifecycle.py tests/test_gui_headless.py tests/test_startup.py tests/test_build_script.py -v`; full `.venv/bin/python -m pytest tests -v`.

### Implementer Prompt (R9)
Task R9 — Remove the two compatibility shims (user has explicitly authorized the minimal test re-targeting).
Branch: work only on `implementer/r9-shims` (already checked out); base and integration branch is `main`. Never create/switch/merge/rebase/rename/delete/push branches; never commit to `main`; no broad `git add -A`, `reset`, or `clean` — stage only the files you changed.
First tool call: run `../architect/tools/implementer-run.sh` with no arguments; use that wrapper for ALL later Bash commands; follow the Mandatory Execution Clock phase rules. Executing it is permitted; modifying it is forbidden.
Before editing: verify the current branch (`git rev-parse --abbrev-ref HEAD`) and inspect the working tree (`git status --short`).
Scope — you may modify ONLY: `implementer/src/todo_md/app.py`, `implementer/src/todo_md/controller.py`, `implementer/src/todo_md/dialogs.py`, and `implementer/src/tests/test_controller.py` (the ONLY authorized test file).
Forbidden: every other file under `implementer/src/tests/` (zero modifications), all other `todo_md` modules, everything under `../architect/`, repository root.
Work:
1. `dialogs.py`:
   - Move `dock_icon_path()` here from `app.py` verbatim (it is a pure asset-path helper: `os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "dock_icon.png")`); add `import os` to its imports; keep/adjust its docstring.
   - Change the signature to `apply_dock_icon(root, icon_path: str)`: the body keeps the fail-soft PhotoImage/iconphoto logic but uses the `icon_path` parameter; DELETE the `from . import app as app_module` shim and the `app_module.dock_icon_path()` call. Update the docstring so the parameter contract is clear (caller resolves the path; tkinter lazily imported inside the function as today).
2. `app.py`:
   - Delete the local `dock_icon_path` definition; replace with a top-level re-export `from .dialogs import dock_icon_path  # re-export: tests import/patch it on todo_md.app` (dialogs is stdlib-only, so a top-level import keeps the module headless).
   - `_apply_dock_icon(self)` body becomes `from .dialogs import apply_dock_icon; self._dock_icon = apply_dock_icon(self.root, dock_icon_path())` — the call must read `dock_icon_path` from the app module globals so existing monkeypatches on `todo_md.app.dock_icon_path` keep working.
   - Change the `from .storage import MarkdownListStore, relocate_lists  # kept: frozen tests patch...` line to `from .storage import MarkdownListStore` (drop `relocate_lists` — nothing in `app.py` uses it anymore).
3. `controller.py` — in `change_lists_dir` delete the `from . import app  # compat: ...` line and call the already top-level-imported `relocate_lists(old_dir, new_dir, move)` (from `.storage`). No other controller changes.
4. `tests/test_controller.py` — authorized minimal edit: add `from todo_md import controller as controller_module` to the imports, and change the two occurrences of `monkeypatch.setattr(app_module, "relocate_lists", ...)` to `monkeypatch.setattr(controller_module, "relocate_lists", ...)`. Keep every assertion and the `app_module` import (still used for `TodoController`). No other test file may be touched.
Hard invariants:
- `tests/test_gui_dock_icon.py` must pass UNCHANGED: it imports `dock_icon_path` from `todo_md.app` (satisfied by the re-export), calls it for the real asset, and `test_missing_icon_fails_soft` patches `todo_md.app.dock_icon_path` before constructing `TodoApp` — after your change that patch must still make `app._dock_icon` become `None`.
- `import todo_md.app` stays headless; `dialogs.py`/`controller.py` keep no module-level tkinter and no `todo_md.app` import at module level.
- All `todo_md.app` module-level names used by tests/modules stay intact (`TodoController`, `TodoApp`, `run`, `visible_items`, `DEFAULT_CONFIG_DIR`, `DEFAULT_DATA_DIR`, `startup_dirs`, `dock_icon_path`).
- Production behavior identical in both fail-soft paths.
Acceptance: zero `app` references in `controller.py`/`dialogs.py`; full suite green; `test_gui_dock_icon.py` untouched.
Commands (from `implementer/src/`): targeted `.venv/bin/python -m pytest tests/test_controller.py tests/test_gui_dock_icon.py tests/test_gui_lifecycle.py tests/test_gui_headless.py tests/test_startup.py tests/test_build_script.py -v`; then full `.venv/bin/python -m pytest tests -v`.
On completion: commit the changed files on `implementer/r9-shims` (the pre-commit hook may auto-stage a VERSION bump — expected, leave it), then hand off: RESULT: SUCCESS|FAILURE, SUMMARY (3-5 bullets), BRANCH, COMMIT hash, test totals, and the exact lines changed in `test_controller.py`. Keep edits minimal and commit early; the clock is the known risk.

## Queue
- **Backlog (non-blocking):** `TodoApp` still builds the sidebar (listbox, entries, buttons) and owns the edit-dialog open/save flow in `_build_ui`/`_open_edit_dialog`; extract to dedicated modules if `app.py` grows again.

## Active Blockers
None.

## Recently Completed
- R9 (in progress) — placeholder
- R8 — Final complexity pass: no `nonlocal` in controller, row rebuild moved to `item_row.rebuild_rows`, compressed wrappers/slimmed `__init__`; app.py 713 → 589 lines: DONE (Implementer commit bd38aa1).
- R7 — Move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py` (re-exported by `app.py`; `relocate_lists` resolved via app for frozen-test compat): DONE (Implementer commit f4f87c3).
- R5 — Extract entry-placeholder mechanism into `todo_md/placeholders.py` (PlaceholderBinder) + `self._ph` holder: DONE (Implementer commit 8ff404b).
