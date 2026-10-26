# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional multi-line description). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -q)` (baseline after R10: 348 pass, 2 skip, ~26s).
- Targeted: `.venv/bin/python -m pytest tests/<file> -q` from `implementer/src/`.
- Refactor series (R*): **test files are frozen** — no adding/modifying/removing tests; verify against the existing suite only. A minimal import-only test repatch is permitted solely if a test references a private symbol that moved, and must be called out explicitly in the handoff.
- Change requests (C*): may add tests for the new behavior and update tests that assert the old (superseded) behavior; all other tests must stay green.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together, and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; in the dark theme the settings spinbox arrows stay visible in normal, hover, and disabled states, with a clearly contrasting hover fill (B1/B2/B3); it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` hosts the Tkinter GUI shell, while its list sidebar, settings window, item rows, theme engine, edit dialog (construction + lifecycle), placeholders, dialog helpers, controller, and visible-items filter now live in dedicated modules (R1-R10). All 348 tests pass.

## Active Task
**C1** (S) — Make the edit-modal description text box user-resizable.
- **Branch:** `implementer/c1-resizable-desc-box` (base: `main`)
- **Scope:** `implementer/src/todo_md/edit_dialog.py` only — pair the description `tk.Text` with a vertical `ttk.Scrollbar` (scrollbar `command=desc_text.yview`, text `yscrollcommand=scrollbar.set`), packed in a sub-frame so the text keeps expanding to fill the dialog while content beyond the fixed 5-line viewport becomes reachable. Keep the palette kwargs, widget surface (`self.desc_text`, `self.entry`, `self.save_btn`, `self.cancel_btn`, `self.window`), grab, and centering unchanged; module stays headless-importable.
- **Acceptance criteria:** (1) description content longer than the viewport is reachable by the user via the scrollbar (both directions wired); (2) scrollbar palette-consistent in light and dark themes; (3) existing `_edit_desc_text` behavior (pre-population, save round trip) unchanged; (4) full suite green.
- **Required tests:** new GUI test file `implementer/src/tests/test_gui_edit_resizable.py` (change request: adding tests allowed; do not modify existing tests). From `implementer/src`: targeted `.venv/bin/python -m pytest tests/test_gui_edit_resizable.py tests/test_gui_edit.py tests/test_gui_double_click.py tests/test_gui_theme.py -q`, then full `.venv/bin/python -m pytest tests -q` (348 existing + new tests pass, 2 skipped).
- **Prompt for Implementer:**

> You are the Implementer agent for the todo-md-app repository. Your assigned implementation branch is `implementer/c1-resizable-desc-box`; `main` is the base and integration branch. First action: verify you are on that branch and the working tree is clean (`git branch --show-current`, `git status --short`).
>
> Your first tool call MUST run `../architect/tools/implementer-run.sh` without arguments; every subsequent Bash command MUST use that wrapper (execution is permitted, modification is forbidden), and you MUST follow the Implementer Mandatory Execution Clock phase rules.
>
> Task C1 (change request): in the todo item edit modal window (class `EditItemDialog` in `implementer/src/todo_md/edit_dialog.py`) the multi-line description `tk.Text` (height 5, width 40, wrap word) cannot be scrolled — content beyond the viewport is unreachable. Make it user-resizable: pair it with a vertical `ttk.Scrollbar` (scrollbar `command=desc_text.yview`, text `yscrollcommand=scrollbar.set`) packed in a sub-frame beneath the title entry so the text keeps its `fill=tk.X` expansion while the scrollbar sits at the right edge (`fill=tk.Y`). Preserve every existing widget surface (`self.window`, `self.entry`, `self.desc_text`, `self.save_btn`, `self.cancel_btn`), the palette kwargs, the grab, and the centering flow; `edit_dialog.py` must stay importable on a headless machine. Do not modify `app.py` or any other module.
>
> Change boundaries: modify only files under `implementer/` (expected: `implementer/src/todo_md/edit_dialog.py` plus a NEW test file `implementer/src/tests/test_gui_edit_resizable.py`). NEVER touch anything under `architect/` or the repository root. This is a change request: you may ADD the new test file, but do not modify or remove any existing test. The new tests must assert: the dialog opens; a scrollbar widget exists; it is wired in both directions (`desc_text` yscrollcommand / scrollbar command); content longer than the viewport is reachable (insert a multi-page text, confirm `desc_text.yview()` / the scrollbar fraction responds); and the scrollbar renders in both light and dark themes.
>
> Verify your branch and the working tree before editing. Before committing run from `implementer/src`: `.venv/bin/python -m pytest tests/test_gui_edit_resizable.py tests/test_gui_edit.py tests/test_gui_double_click.py tests/test_gui_theme.py -q` and then the full suite `.venv/bin/python -m pytest tests -q` — all must pass (348 existing + your new tests, 2 skipped). Commit the completed work (stage only the files you changed; no broad `git add -A`, no destructive working-tree operations). Do not create, switch, merge, rebase, rename, delete, or push branches, and never commit to `main`.
>
> Handoff format: RESULT: SUCCESS|FAILURE, BRANCH: implementer/c1-resizable-desc-box, COMMIT: <hash>, plus test counts and a one-line description of the widget layout chosen.

## Queue
- **C2** (S): preserve empty lines in an item description: write a blank description line as the two-space continuation line (e.g. `"  "`); on load, a blank line indented ≥2 spaces continues the description (empty line appended), while a truly unindented blank line keeps terminating it — full save→load round trip of `"a\n\nb"` must reproduce `"a\n\nb"`.

## Active Blockers
None.

## Recently Completed
- R10 — Extract list-sidebar construction into `sidebar.py` (R10a) and the edit-dialog open/save/close lifecycle into `edit_dialog.py` (R10b); app.py 589→533 lines; no test repatch: DONE (Implementer commits 178304e, d61e460).
- B3 — Spinbox hover contrast: new `spin_hover` palette fill (`#565656` dark / `#d0d0d0` light) mapped to `TSpinbox` active/pressed `background`; hover now clearly visible: DONE (Implementer commit 4388e2d).
- B2 — Spinbox hover: `TSpinbox` state maps pin `-background`/`-arrowcolor` (active/pressed → palette `btn_active`/`fg`, disabled → `fg_disabled`); `btn_active` promoted into `palette_for`: DONE (Implementer commit cb53a91).
- B1 — Dark-theme spinbox arrows: `apply_theme` pins `TSpinbox -arrowcolor` to palette fg (Tk 9 C Arrow element otherwise defaults near-black); new `test_gui_spinbox_arrows.py`: DONE (Implementer commit eb3cd40).
- R9 — Remove both compat shims: `dock_icon_path` canonical in `dialogs.py` + `apply_dock_icon(root, icon_path)` param, `relocate_lists` called directly in controller, authorized 2-line test repatch: DONE (Implementer commit 6d81255).
