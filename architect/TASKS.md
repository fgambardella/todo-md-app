# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional `<!-- Description: -->` line). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -v)` (344 pass, 2 skip, ~25s baseline).
- Targeted: `.venv/bin/python -m pytest tests/<file> -v` from `implementer/src/`.
- Refactor series R1-R8: **test files are frozen** — implementers may not add, modify, or remove any test; every task is verified against the existing suite only.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together, and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` hosts the Tkinter GUI shell, while its settings window, item rows, theme engine, edit dialog, placeholders, and dialog helpers now live in dedicated modules; `app.py` remains the target of refactor series R1-R8. All 344 tests pass.

## Active Task
None. R6 completed, verified, and merged (Implementer commit `c8b8773`). Next candidate: R7 from Queue.

## Queue
- **R7 (S):** move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py`; re-export both from `app.py`; pure move, no behavior change.
- **R8 (S):** final complexity pass on remaining `app.py`: collapse the repeated `current_list is None` guards, remove the controller `nonlocal` closure pattern, dedupe any remaining kwargs patterns, slim `__init__`; target `app.py` ≈ 400 lines or fewer.

## Active Blockers
None.

## Recently Completed
- R6 — Extract shared dialog helpers (window centering, dock icon) into `todo_md/dialogs.py`: DONE (Implementer commit c8b8773).
- R5 — Extract entry-placeholder mechanism into `todo_md/placeholders.py` (PlaceholderBinder) + `self._ph` holder: DONE (Implementer commit 8ff404b).
- R4 — Extract modal edit dialog into `todo_md/edit_dialog.py` (EditItemDialog) + delegation properties: DONE (Implementer commit 3b52df2).
- R3 — Extract theme engine (palette, apply_theme, text_colors, button_text) into `todo_md/theme.py`: DONE (Implementer commit fda5317).
- R1 — Extract Settings window (construction + save flow) into `todo_md/settings_window.py`: DONE (Implementer commit e8f3f37; merged to main at 495e9d5).
