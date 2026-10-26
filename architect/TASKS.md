# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional multi-line description). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -q)` (baseline after C2: 356 pass, 2 skip, ~26s).
- Targeted: `.venv/bin/python -m pytest tests/<file> -q` from `implementer/src/`.
- Refactor series (R*): **test files are frozen** — no adding/modifying/removing tests; verify against the existing suite only. A minimal import-only test repatch is permitted solely if a test references a private symbol that moved, and must be called out explicitly in the handoff.
- Change requests (C*): may add tests for the new behavior and update tests that assert the old (superseded) behavior; all other tests must stay green.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together (the description box has a vertical scrollbar, C1; internal empty lines of the description are preserved, C2), and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; in the dark theme the settings spinbox arrows stay visible in normal, hover, and disabled states, with a clearly contrasting hover fill (B1/B2/B3); it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` hosts the Tkinter GUI shell, while its list sidebar, settings window, item rows, theme engine, edit dialog (construction + lifecycle), placeholders, dialog helpers, controller, and visible-items filter now live in dedicated modules (R1-R10). All 356 tests pass.

## Active Task
**C3** (S) — Make the edit-modal description box truly user-resizable (C1 only made it scrollable: `desc_text` is packed `fill=X` so it never grows vertically; the box must follow window resizing and offer a visible grip).
- **Branch:** `implementer/c3-resize-desc-box` (base: `main`)
- **Scope:** `implementer/src/todo_md/edit_dialog.py` only — make the description `tk.Text` expand vertically with the dialog: `row.pack(fill=BOTH, expand=True)`, `desc_frame.pack(fill=BOTH, expand=True)`, `desc_text.pack(side=LEFT, fill=BOTH, expand=True)` (height 5 / width 40 remain the *initial* size only), scrollbar keeps `fill=Y`; add a small resize grip (`tk.Frame`, `bd=1, relief=RAISED, cursor="size_rse_nw_se"`, palette bg on the fallback path, exposed as `self.resize_grip`) packed `side=tk.BOTTOM, anchor=tk.E` before the bottom button frame (true bottom-right corner). Preserve the whole widget surface (`self.window`, `self.entry`, `self.desc_text`, `self.desc_scroll`, `self.save_btn`, `self.cancel_btn`), grab, and centering; module stays headless-importable.
- **Acceptance criteria:** (1) growing the dialog window's height grows `desc_text.winfo_height()` (vertical resize propagates); (2) a resize grip exists (size cursor, bottom-right, both themes); (3) horizontal expansion and the two-way scrollbar wiring still work (existing C1 tests stay green, updated only if they pin the old layout); (4) full suite green.
- **Required tests:** change request: extend `implementer/src/tests/test_gui_edit_resizable.py` — add a test that the description box grows when the dialog window is resized taller (and a grip test); existing assertions that pinned the C1 layout may be updated, no other test files may change. From `implementer/src`: targeted `.venv/bin/python -m pytest tests/test_gui_edit_resizable.py tests/test_gui_edit.py tests/test_gui_double_click.py tests/test_gui_theme.py -q`, then full `.venv/bin/python -m pytest tests -q`.
- **Prompt for Implementer:**

> You are the Implementer agent for the todo-md-app repository. Your assigned implementation branch is `implementer/c3-resize-desc-box`; `main` is the base and integration branch. First action: verify you are on that branch and the working tree is clean (`git branch --show-current`, `git status --short`).
>
> Your first tool call MUST run `../architect/tools/implementer-run.sh` without arguments; every subsequent Bash command MUST use that wrapper (execution is permitted, modification is forbidden), and you MUST follow the Implementer Mandatory Execution Clock phase rules.
>
> Task C3 (change request, follow-up to C1): in the edit dialog (`EditItemDialog` in `implementer/src/todo_md/edit_dialog.py`) the description `tk.Text` is scrollable but NOT resizable: it is packed `fill=tk.X` in a `fill=tk.X` frame, so growing the dialog window never grows the box. Make it truly user-resizable: (1) pack the `row` frame `fill=tk.BOTH, expand=True`; (2) pack the description sub-frame `fill=tk.BOTH, expand=True` (keep `pady=(8, 0)`); (3) pack `desc_text` `side=tk.LEFT, fill=tk.BOTH, expand=True` so it follows the window in BOTH dimensions — keep `height=5, width=40` as the initial size; (4) keep the scrollbar packed `side=RIGHT, fill=Y` (it must track the taller box); (5) add a visible resize grip: a `tk.Frame(win, bd=1, relief=tk.RAISED, cursor="size_rse_nw_se")` exposed as `self.resize_grip`, packed `side=tk.BOTTOM, anchor=tk.E` BEFORE the bottom button frame is packed (pack allocates bottom-side widgets in call order, so the grip must be packed first to occupy the very bottom strip); pin its background to the palette bg on the clam-fallback path, leave it unset on the native path (reuse the `bg_kwargs`-style conditional pattern). Preserve every existing widget surface (`self.window`, `self.entry`, `self.desc_text`, `self.desc_scroll`, `self.save_btn`, `self.cancel_btn`), the grab, and the centering flow. Do not modify `app.py` or any other module. `edit_dialog.py` must stay importable on a headless machine.
>
> Change boundaries: modify only files under `implementer/` (expected: `implementer/src/todo_md/edit_dialog.py` and `implementer/src/tests/test_gui_edit_resizable.py`). NEVER touch anything under `architect/` or the repository root. This is a change request: you may extend `tests/test_gui_edit_resizable.py` (add: a test that resizing the dialog window taller makes `desc_text.winfo_height()` grow, and that the resize grip exists with the size cursor in both themes; update any existing assertion that pinned the C1 fill options if it conflicts) and do not modify or remove any other test file. Do not weaken the existing scrollbar tests — they must still pass.
>
> Verify your branch and the working tree before editing. Before committing run from `implementer/src`: `.venv/bin/python -m pytest tests/test_gui_edit_resizable.py tests/test_gui_edit.py tests/test_gui_double_click.py tests/test_gui_theme.py -q` and then the full suite `.venv/bin/python -m pytest tests -q` — all must pass (356 existing + your new tests, 2 skipped). Commit the completed work (stage only the files you changed; no broad `git add -A`, no destructive working-tree operations). Do not create, switch, merge, rebase, rename, delete, or push branches, and never commit to `main`.
>
> Handoff format: RESULT: SUCCESS|FAILURE, BRANCH: implementer/c3-resize-desc-box, COMMIT: <hash>, plus test counts and a one-line description of the resize mechanics achieved.

## Queue
None — empty; the only backlog item (further `app.py` slimming) is tracked as Known Architectural Debt in `DESIGN.md`.

## Active Blockers
None.

## Recently Completed
- C2 — Blank description lines preserved: `save` writes every description line (blank = two spaces), `load` treats an indented blank line as an empty description line while a truly unindented blank still terminates it; 4 new tests: DONE (Implementer commit 8089479).
- C1 — Edit-modal description box now paired with a vertical `ttk.Scrollbar` (two-way wired, palette-consistent); new `test_gui_edit_resizable.py` (4 tests): DONE (Implementer commit b2ce023).
- R10 — Extract list-sidebar construction into `sidebar.py` (R10a) and the edit-dialog open/save/close lifecycle into `edit_dialog.py` (R10b); app.py 589→533 lines; no test repatch: DONE (Implementer commits 178304e, d61e460).
- B3 — Spinbox hover contrast: new `spin_hover` palette fill (`#565656` dark / `#d0d0d0` light) mapped to `TSpinbox` active/pressed `background`; hover now clearly visible: DONE (Implementer commit 4388e2d).
- B2 — Spinbox hover: `TSpinbox` state maps pin `-background`/`-arrowcolor` (active/pressed → palette `btn_active`/`fg`, disabled → `fg_disabled`); `btn_active` promoted into `palette_for`: DONE (Implementer commit cb53a91).
