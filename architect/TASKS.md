# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional multi-line description). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -q)` (baseline after C3: 358 pass, 2 skip, ~26s).
- Targeted: `.venv/bin/python -m pytest tests/<file> -q` from `implementer/src/`.
- Refactor series (R*): **test files are frozen** — no adding/modifying/removing tests; verify against the existing suite only. A minimal import-only test repatch is permitted solely if a test references a private symbol that moved, and must be called out explicitly in the handoff.
- Change requests (C*): may add tests for the new behavior and update tests that assert the old (superseded) behavior; all other tests must stay green.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together (the description box is user-resizable with a scrollbar, C1/C3; internal empty lines of the description are preserved, C2), and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; in the dark theme the settings spinbox arrows stay visible in normal, hover, and disabled states, with a clearly contrasting hover fill (B1/B2/B3); it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` hosts the Tkinter GUI shell, while its list sidebar, settings window, item rows, theme engine, edit dialog (construction + lifecycle), placeholders, dialog helpers, controller, and visible-items filter now live in dedicated modules (R1-R10). All 358 tests pass.

## Active Task
**C4** (S) — Open the edit modal at 50% of the main window size, centered on both axes.
- **Branch:** `implementer/c4-modal-size` (base: `main`)
- **Scope:** `implementer/src/todo_md/edit_dialog.py` only — in `EditItemDialog.__init__`, after the current `win.update()`, set the dialog geometry to half the main window: `main = app.root; win.geometry(f"{main.winfo_width() // 2}x{main.winfo_height() // 2}")` (guard against zero/negative sizes with a sensible minimum, e.g. 200x150, in case the main window is tiny), then `win.update()` again, then keep the existing `app._center_window_on_parent(win)` call. This must apply on every open (the dialog is rebuilt each time). Preserve the whole widget surface (`self.window`, `self.entry`, `self.desc_text`, `self.desc_scroll`, `self.resize_grip`, `self.save_btn`, `self.cancel_btn`), the grab, and centering semantics; `edit_dialog.py` stays headless-importable. Do not modify `app.py` or any other module.
- **Acceptance criteria:** (1) with a known main-window size, the opened dialog's `winfo_width()`/`winfo_height()` equal 50% of the main window (integer division, modulo a few pixels); (2) the dialog is centered on the main window both horizontally and vertically (same tolerance as existing centering tests); (3) the C1/C3 resize + scrollbar behavior still works on the pre-sized dialog; (4) all existing tests green.
- **Required tests:** change request: add tests (new `tests/test_gui_edit_size.py` or extend `tests/test_gui_edit_resizable.py`) — size the main root to a known geometry (e.g. 800x600), open the edit dialog, assert ~50% size on both axes and centered position on both axes; do not modify or remove other test files.
- **Prompt for Implementer:**

> You are the Implementer agent for the todo-md-app repository. Your assigned implementation branch is `implementer/c4-modal-size`; `main` is the base and integration branch. First action: verify you are on that branch and the working tree is clean (`git branch --show-current`, `git status --short`).
>
> Your first tool call MUST run `../architect/tools/implementer-run.sh` without arguments; every subsequent Bash command MUST use that wrapper (execution is permitted, modification is forbidden), and you MUST follow the Implementer Mandatory Execution Clock phase rules.
>
> Task C4 (change request): the todo item edit modal should open sized at 50% of the main window, centered on both axes. In `implementer/src/todo_md/edit_dialog.py` (`EditItemDialog.__init__`), after the existing `win.update()`, size the dialog: read the main window `main = self.app.root`, compute `w = max(200, main.winfo_width() // 2)` and `h = max(150, main.winfo_height() // 2)` (the floor guards against a tiny main window; Tk clamps to the content minimum anyway), then `win.geometry(f"{w}x{h}")`, then `win.update()` once more, then keep the existing `app._center_window_on_parent(win)` call (which already centers on the live main window in both axes). The dialog is rebuilt on every open, so the geometry applies each time. Preserve every existing widget surface (`self.window`, `self.entry`, `self.desc_text`, `self.desc_scroll`, `self.resize_grip`, `self.save_btn`, `self.cancel_btn`), the grab, and the centering flow; keep the module importable headless. Do not modify `app.py` or any other module.
>
> Change boundaries: modify only files under `implementer/` (expected: `implementer/src/todo_md/edit_dialog.py` plus a new `implementer/src/tests/test_gui_edit_size.py` — or extend `tests/test_gui_edit_resizable.py`). NEVER touch anything under `architect/` or the repository root. This is a change request: ADD tests — in each, size the main root to a known geometry (e.g. `app.root.geometry("800x600")`, `app.root.update()`), open the edit dialog, assert `win.winfo_width()` and `win.winfo_height()` are ~400/300 (50%, allow a few pixels), and that the window's on-screen position centers it on the main window on BOTH axes (use the same position math the existing centering tests use). Do not modify or remove any other test file; if an existing test pins a specific dialog size, only that assertion may be updated.
>
> Verify your branch and the working tree before editing. Before committing run from `implementer/src`: `.venv/bin/python -m pytest tests/test_gui_edit_size.py tests/test_gui_edit_resizable.py tests/test_gui_edit.py tests/test_gui_centering.py tests/test_gui_double_click.py -q` and then the full suite `.venv/bin/python -m pytest tests -q` — all must pass (358 existing + your new tests, 2 skipped). Commit the completed work (stage only the files you changed; no broad `git add -A`, no destructive working-tree operations). Do not create, switch, merge, rebase, rename, delete, or push branches, and never commit to `main`.
>
> Handoff format: RESULT: SUCCESS|FAILURE, BRANCH: implementer/c4-modal-size, COMMIT: <hash>, plus test counts and the resulting dialog size for an 800x600 main window.

## Queue
None — empty; the only backlog item (further `app.py` slimming) is tracked as Known Architectural Debt in `DESIGN.md`.

## Active Blockers
None.

## Recently Completed
- C3 — Description box truly user-resizable: BOTH/expand pack chain (row → desc_frame → desc_text), size-cursor resize grip in the bottom strip (Tk 9 uses `bottom_right_corner`; the `size_rse_nw_se` alias no longer exists); 2 new tests: DONE (Implementer commit 99c372e).
- C2 — Blank description lines preserved: `save` writes every description line (blank = two spaces), `load` treats an indented blank line as an empty description line while a truly unindented blank still terminates it; 4 new tests: DONE (Implementer commit 8089479).
- C1 — Edit-modal description box now paired with a vertical `ttk.Scrollbar` (two-way wired, palette-consistent); new `test_gui_edit_resizable.py` (4 tests): DONE (Implementer commit b2ce023).
- R10 — Extract list-sidebar construction into `sidebar.py` (R10a) and the edit-dialog open/save/close lifecycle into `edit_dialog.py` (R10b); app.py 589→533 lines; no test repatch: DONE (Implementer commits 178304e, d61e460).
- B3 — Spinbox hover contrast: new `spin_hover` palette fill (`#565656` dark / `#d0d0d0` light) mapped to `TSpinbox` active/pressed `background`; hover now clearly visible: DONE (Implementer commit 4388e2d).
- B2 — Spinbox hover: `TSpinbox` state maps pin `-background`/`-arrowcolor` (active/pressed → palette `btn_active`/`fg`, disabled → `fg_disabled`); `btn_active` promoted into `palette_for`: DONE (Implementer commit cb53a91).
