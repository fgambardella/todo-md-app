# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional multi-line description). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -q)` (baseline after C4: 361 pass, 2 skip, ~27s).
- Targeted: `.venv/bin/python -m pytest tests/<file> -q` from `implementer/src/`.
- Refactor series (R*): **test files are frozen** — no adding/modifying/removing tests; verify against the existing suite only. A minimal import-only test repatch is permitted solely if a test references a private symbol that moved, and must be called out explicitly in the handoff.
- Change requests (C*): may add tests for the new behavior and update tests that assert the old (superseded) behavior; all other tests must stay green.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together (the description box is user-resizable with a scrollbar, C1/C3; it opens at 50% of the main window size centered, C4; internal empty lines of the description are preserved, C2), and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; in the dark theme the settings spinbox arrows stay visible in normal, hover, and disabled states, with a clearly contrasting hover fill (B1/B2/B3); it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` hosts the Tkinter GUI shell, while its list sidebar, settings window, item rows, theme engine, edit dialog (construction + lifecycle), placeholders, dialog helpers, controller, and visible-items filter now live in dedicated modules (R1-R10). All 361 tests pass.

## Active Task
None. C4 completed, verified, and merged (Implementer commit de8ffd6). The queue is empty.

## Queue
None — empty; the only backlog item (further `app.py` slimming) is tracked as Known Architectural Debt in `DESIGN.md`.

## Active Blockers
None.

## Recently Completed
- C4 — Edit modal opens sized at 50% of the live main window (200/150 px floor, re-applied on every open) then centered on both axes; new `test_gui_edit_size.py` (3 tests): DONE (Implementer commit de8ffd6).
- C3 — Description box truly user-resizable: BOTH/expand pack chain (row → desc_frame → desc_text), size-cursor resize grip in the bottom strip (Tk 9 uses `bottom_right_corner`; the `size_rse_nw_se` alias no longer exists); 2 new tests: DONE (Implementer commit 99c372e).
- C2 — Blank description lines preserved: `save` writes every description line (blank = two spaces), `load` treats an indented blank line as an empty description line while a truly unindented blank still terminates it; 4 new tests: DONE (Implementer commit 8089479).
- C1 — Edit-modal description box now paired with a vertical `ttk.Scrollbar` (two-way wired, palette-consistent); new `test_gui_edit_resizable.py` (4 tests): DONE (Implementer commit b2ce023).
- R10 — Extract list-sidebar construction into `sidebar.py` (R10a) and the edit-dialog open/save/close lifecycle into `edit_dialog.py` (R10b); app.py 589→533 lines; no test repatch: DONE (Implementer commits 178304e, d61e460).
- B3 — Spinbox hover contrast: new `spin_hover` palette fill (`#565656` dark / `#d0d0d0` light) mapped to `TSpinbox` active/pressed `background`; hover now clearly visible: DONE (Implementer commit 4388e2d).
