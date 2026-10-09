# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional `<!-- Description: -->` line). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -v)` (344 pass, 2 skip, ~25s baseline).
- Targeted: `.venv/bin/python -m pytest tests/<file> -v` from `implementer/src/`.
- Refactor series R1-R8: **test files are frozen** — implementers may not add, modify, or remove any test; every task is verified against the existing suite only.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together, and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` hosts the Tkinter GUI shell, while its settings window, item rows, theme engine, and edit dialog now live in dedicated modules; `app.py` remains the target of refactor series R1-R8. All 344 tests pass.

## Active Task
**R5 (S)** — Extract the entry-placeholder mechanism into `todo_md/placeholders.py` (`PlaceholderBinder`); `TodoApp` keeps `_placeholders` plus thin `_attach_placeholder`/`_placeholder_fg`/`_entry_value`/`_on_entry_focus_in`/`_on_entry_focus_out`/`_restore_placeholder` wrappers.
- Branch: `implementer/r5-placeholders` (base `main`; integration branch `main`).
- Scope: create `implementer/src/todo_md/placeholders.py`; modify `implementer/src/todo_md/app.py` only.
- Acceptance: placeholder logic lives in `placeholders.py`; `app._placeholders` stays the same dict object (theme.py and tests read it); identical focus/submit behavior; zero test edits; full suite green; headless import intact.
- Required tests: full suite; targeted `tests/test_gui_placeholders.py tests/test_gui_theme.py tests/test_gui_theme_switch.py tests/test_gui_new_list.py tests/test_gui_edit.py tests/test_gui_items.py tests/test_gui_headless.py tests/test_startup.py`.
- Commands (from `implementer/src/`): targeted `.venv/bin/python -m pytest tests/test_gui_placeholders.py tests/test_gui_theme.py tests/test_gui_theme_switch.py tests/test_gui_new_list.py tests/test_gui_edit.py tests/test_gui_items.py tests/test_gui_headless.py tests/test_startup.py -v`; full `.venv/bin/python -m pytest tests -v`.

### Implementer Prompt (R5)
Task R5 — Extract the entry-placeholder mechanism into `todo_md/placeholders.py`.
Branch: work only on `implementer/r5-placeholders` (already checked out); base and integration branch is `main`. Never create/switch/merge/rebase/rename/delete/push branches; never commit to `main`; no broad `git add -A`, `reset`, or `clean` — stage only the files you changed.
First tool call: run `../architect/tools/implementer-run.sh` with no arguments; use that wrapper for ALL later Bash commands; follow the Mandatory Execution Clock phase rules. Executing it is permitted; modifying it is forbidden.
Before editing: verify the current branch (`git rev-parse --abbrev-ref HEAD`) and inspect the working tree (`git status --short`).
Scope — you may create/modify ONLY: `implementer/src/todo_md/placeholders.py` (new) and `implementer/src/todo_md/app.py`.
Forbidden: every file under `src/tests/` (tests are frozen — zero modifications), all other `todo_md` modules (including `theme.py`), everything under `../architect/`, repository root.
Work:
1. Create `implementer/src/todo_md/placeholders.py` with class `PlaceholderBinder` holding all six pieces currently in `TodoApp` (move the methods with `app` instead of `self`, preserving every explanatory comment):
   - `__init__(self, app)`: stores the duck-typed `app` (uses only `app.root` and `app._palette`); creates `self.map: dict = {}` (entry widget → hint text).
   - `attach(self, entry, text)`, `fg(self)`, `value(self, entry)`, `focus_in(self, entry)`, `focus_out(self, entry)`, `restore(self, entry)` — bodies copied verbatim from `_attach_placeholder`, `_placeholder_fg`, `_entry_value`, `_on_entry_focus_in`, `_on_entry_focus_out`, `_restore_placeholder` with `self._placeholders` → `self.map`, `self._palette` → `self.app._palette`, `self.root` → `self.app.root`.
   - No tkinter import needed; no `todo_md.app` import (duck-typed).
2. In `app.py`:
   - In `TodoApp.__init__` replace `self._placeholders: dict = {}` (and its comment) with a `self._ph = PlaceholderBinder(self)` holder (lazy `from .placeholders import PlaceholderBinder` at module top is allowed ONLY if placeholders.py imports no tkinter — it must stay importable headless, which it will) plus `self._placeholders = self._ph.map` (alias keeps the exact same dict object; `theme.py` and tests read `app._placeholders`).
   - Replace the six placeholder method bodies with one-line delegations to `self._ph.<method>(...)`, keeping the current names and docstrings on the app side.
   - No other `app.py` changes.
Hard invariants:
- Zero test modifications; tests read `app._placeholders[entry]` / iterate `app._placeholders.items()` and drive behavior via `entry.event_generate("<FocusIn>"/"<FocusOut>")` — all must keep working identically.
- `self._placeholders` must be the very same dict object the binder mutates (theme.apply_theme iterates it on every theme change).
- Identical placeholder fg (palette `placeholder_fg` else `#808080`), focus-clear (palette `fg` else `#000000`), and focus-restore-skip-when-focused behavior.
- `import todo_md.app` must stay headless.
- All `todo_md.app` module-level names and `__all__` must remain untouched.
Acceptance: placeholder mechanism lives in `placeholders.py`; delegated names behave identically; full suite green with zero test edits.
Commands (from `src/`): targeted `.venv/bin/python -m pytest tests/test_gui_placeholders.py tests/test_gui_theme.py tests/test_gui_theme_switch.py tests/test_gui_new_list.py tests/test_gui_edit.py tests/test_gui_items.py tests/test_gui_headless.py tests/test_startup.py -v`; then full `.venv/bin/python -m pytest tests -v`.
On completion: commit BOTH files on `implementer/r5-placeholders` (the pre-commit hook may auto-stage a VERSION bump — expected, leave it), then hand off: RESULT: SUCCESS|FAILURE, SUMMARY (3-5 bullets), BRANCH, COMMIT hash, test totals. Keep edits minimal and commit early; the clock is the known risk.

## Queue
- **R6 (S):** extract shared dialog helpers into `todo_md/dialogs.py` (window centering, dock-icon apply — must call `todo_md.app.dock_icon_path` via dynamic lookup since tests monkeypatch it).
- **R7 (S):** move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py`; re-export both from `app.py`; pure move, no behavior change.
- **R8 (S):** final complexity pass on remaining `app.py`: collapse the repeated `current_list is None` guards, remove the controller `nonlocal` closure pattern, dedupe any remaining kwargs patterns, slim `__init__`; target `app.py` ≈ 400 lines or fewer.

## Active Blockers
None.

## Recently Completed
- R4 — Extract modal edit dialog into `todo_md/edit_dialog.py` (EditItemDialog) + delegation properties: DONE (Implementer commit 3b52df2).
- R3 — Extract theme engine (palette, apply_theme, text_colors, button_text) into `todo_md/theme.py`: DONE (Implementer commit fda5317).
- R2 — Extract item-row rendering into `todo_md/item_row.py` + `bg_kwargs` helper: DONE (Implementer commit aee8051).
- R1 — Extract Settings window (construction + save flow) into `todo_md/settings_window.py`: DONE (Implementer commit e8f3f37; merged to main at 495e9d5).
- 47 — Center modal dialogs on the main window (edit + settings): DONE (v1.0.0 released; Implementer commit d547cbf).
