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
None. R9 completed, verified, and merged (Implementer commit `6d81255`). Queue holds only the non-blocking backlog entry.

## Queue
- **Backlog (non-blocking):** `TodoApp` still builds the sidebar (listbox, entries, buttons) and owns the edit-dialog open/save flow in `_build_ui`/`_open_edit_dialog`; extract to dedicated modules if `app.py` grows again.

## Active Blockers
None.

## Recently Completed
- R9 — Remove both compat shims: `dock_icon_path` canonical in `dialogs.py` + `apply_dock_icon(root, icon_path)` param, `relocate_lists` called directly in controller, authorized 2-line test repatch: DONE (Implementer commit 6d81255).
- R8 — Final complexity pass: no `nonlocal` in controller, row rebuild moved to `item_row.rebuild_rows`, compressed wrappers/slimmed `__init__`; app.py 713 → 589 lines: DONE (Implementer commit bd38aa1).
- R7 — Move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py` (re-exported by `app.py`; `relocate_lists` resolved via app for frozen-test compat): DONE (Implementer commit f4f87c3).
- R5 — Extract entry-placeholder mechanism into `todo_md/placeholders.py` (PlaceholderBinder) + `self._ph` holder: DONE (Implementer commit 8ff404b).
