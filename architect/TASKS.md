# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional multi-line description). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -q)` (baseline after C1: 352 pass, 2 skip, ~26s).
- Targeted: `.venv/bin/python -m pytest tests/<file> -q` from `implementer/src/`.
- Refactor series (R*): **test files are frozen** — no adding/modifying/removing tests; verify against the existing suite only. A minimal import-only test repatch is permitted solely if a test references a private symbol that moved, and must be called out explicitly in the handoff.
- Change requests (C*): may add tests for the new behavior and update tests that assert the old (superseded) behavior; all other tests must stay green.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together (the description box has a vertical scrollbar, C1), and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; in the dark theme the settings spinbox arrows stay visible in normal, hover, and disabled states, with a clearly contrasting hover fill (B1/B2/B3); it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` hosts the Tkinter GUI shell, while its list sidebar, settings window, item rows, theme engine, edit dialog (construction + lifecycle), placeholders, dialog helpers, controller, and visible-items filter now live in dedicated modules (R1-R10). All 352 tests pass.

## Active Task
**C2** (S) — Preserve empty lines in an item description.
- **Branch:** `implementer/c2-preserve-blank-lines` (base: `main`)
- **Scope:** `implementer/src/todo_md/storage.py` — in `save()`, write *every* description line, including blank ones, as the two-space continuation line (a blank line becomes two spaces); in `load()`, a blank line indented ≥2 spaces continues the description (appends an empty line), while a truly unindented blank line keeps terminating it (existing semantics; `test_description_stops_at_header_checkbox_and_blank` must keep passing unchanged). Models/controller already preserve internal newlines via `.strip()`.
- **Acceptance criteria:** (1) `save`→`load` round trip of description `"a\n\nb"` reproduces `"a\n\nb"`; (2) the on-disk file represents the empty line as a two-space-indented line; (3) a genuinely unindented blank line in a hand-written file still terminates the description (old test unchanged); (4) full suite green.
- **Required tests:** change request: add tests to `implementer/src/tests/test_storage.py` (round trip with internal blank line; exact saved bytes for a description containing a blank line; load of a hand-written file with an indented blank line) and, if practical, one end-to-end controller round trip in `test_controller.py`; do not weaken existing tests. From `implementer/src`: targeted `.venv/bin/python -m pytest tests/test_storage.py tests/test_models.py tests/test_controller.py -q`, then full `.venv/bin/python -m pytest tests -q` (352 existing + new pass, 2 skipped).
- **Prompt for Implementer:**

> You are the Implementer agent for the todo-md-app repository. Your assigned implementation branch is `implementer/c2-preserve-blank-lines`; `main` is the base and integration branch. First action: verify you are on that branch and the working tree is clean (`git branch --show-current`, `git status --short`).
>
> Your first tool call MUST run `../architect/tools/implementer-run.sh` without arguments; every subsequent Bash command MUST use that wrapper (execution is permitted, modification is forbidden), and you MUST follow the Implementer Mandatory Execution Clock phase rules.
>
> Task C2 (change request): today an empty line typed in the edit dialog's description box is lost after save. In `implementer/src/todo_md/storage.py` fix `MarkdownListStore.save` to write *every* description line — including blank ones — as a two-space-indented continuation line (a blank line is written as exactly two spaces, i.e. the indent with nothing after it), and fix `MarkdownListStore.load` so that while collecting a description, a blank line indented by ≥2 spaces appends an empty line to the description; a genuinely unindented blank line must keep terminating the description as it does today (the existing `test_description_stops_at_header_checkbox_and_blank` must pass unchanged). The description is joined with newlines and stripped, so internal blank lines round-trip and leading/trailing ones are dropped as before. Keep the module stdlib-only and keep the docstrings accurate.
>
> Change boundaries: modify only files under `implementer/` (expected: `implementer/src/todo_md/storage.py` and `implementer/src/tests/test_storage.py`; optionally `implementer/src/tests/test_controller.py` for one end-to-end round trip). NEVER touch anything under `architect/` or the repository root. This is a change request: ADD the new tests (round trip with an internal blank line; exact saved bytes for a description containing a blank line; load of a hand-written file containing an indented blank line), but do not weaken or remove existing tests.
>
> Verify your branch and the working tree before editing. Before committing run from `implementer/src`: `.venv/bin/python -m pytest tests/test_storage.py tests/test_models.py tests/test_controller.py -q` and then the full suite `.venv/bin/python -m pytest tests -q` — all must pass (352 existing + your new tests, 2 skipped). Commit the completed work (stage only the files you changed; no broad `git add -A`, no destructive working-tree operations). Do not create, switch, merge, rebase, rename, delete, or push branches, and never commit to `main`.
>
> Handoff format: RESULT: SUCCESS|FAILURE, BRANCH: implementer/c2-preserve-blank-lines, COMMIT: <hash>, plus test counts and the exact bytes written for a description of "a\n\nb".

## Queue
None — the queue is empty after C2; the only backlog item (further `app.py` slimming) is tracked as Known Architectural Debt in `DESIGN.md`.

## Active Blockers
None.

## Recently Completed
- C1 — Edit-modal description box now paired with a vertical `ttk.Scrollbar` (two-way wired, palette-consistent); new `test_gui_edit_resizable.py` (4 tests): DONE (Implementer commit b2ce023).
- R10 — Extract list-sidebar construction into `sidebar.py` (R10a) and the edit-dialog open/save/close lifecycle into `edit_dialog.py` (R10b); app.py 589→533 lines; no test repatch: DONE (Implementer commits 178304e, d61e460).
- B3 — Spinbox hover contrast: new `spin_hover` palette fill (`#565656` dark / `#d0d0d0` light) mapped to `TSpinbox` active/pressed `background`; hover now clearly visible: DONE (Implementer commit 4388e2d).
- B2 — Spinbox hover: `TSpinbox` state maps pin `-background`/`-arrowcolor` (active/pressed → palette `btn_active`/`fg`, disabled → `fg_disabled`); `btn_active` promoted into `palette_for`: DONE (Implementer commit cb53a91).
- B1 — Dark-theme spinbox arrows: `apply_theme` pins `TSpinbox -arrowcolor` to palette fg (Tk 9 C Arrow element otherwise defaults near-black); new `test_gui_spinbox_arrows.py`: DONE (Implementer commit eb3cd40).
