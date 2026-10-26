# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional multi-line description). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -q)` (baseline: 348 pass, 2 skip, ~26s).
- Targeted: `.venv/bin/python -m pytest tests/<file> -q` from `implementer/src/`.
- Refactor series (R*): **test files are frozen** — no adding/modifying/removing tests; verify against the existing suite only. A minimal import-only test repatch is permitted solely if a test references a private symbol that moved, and must be called out explicitly in the handoff.
- Change requests (C*): may add tests for the new behavior and update tests that assert the old (superseded) behavior; all other tests must stay green.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together, and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; in the dark theme the settings spinbox arrows stay visible in normal, hover, and disabled states, with a clearly contrasting hover fill (B1/B2/B3); it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` hosts the Tkinter GUI shell, while its settings window, item rows, theme engine, edit dialog, placeholders, dialog helpers, controller, and visible-items filter now live in dedicated modules. All 348 tests pass.

## Active Task
**R10b** (M, micro-task 2 of 2 of R10) — Extract the edit-dialog open/save/teardown flow from `app.py` into `edit_dialog.py`. Checkpoint: R10a done and verified (commit `178304e`, sidebar extracted to `sidebar.py`, app.py 583→552 lines, 348 pass/2 skip).
- **Branch:** `implementer/r10a-extract-sidebar` (same branch as R10a; tip `178304e`)
- **Scope:** move the *logic* of `_open_edit_dialog`, `_on_edit_save`, `_close_edit_dialog` from `TodoApp` into `implementer/src/todo_md/edit_dialog.py` as duck-typed module functions (`open_dialog(app, index)`, `save_dialog(app)`, `close_dialog(app)`) following the `sidebar.py`/`item_row.py` delegation pattern (never import `todo_md.app`; tkinter lazy). `TodoApp` keeps thin one-line delegating wrappers (lazy import) for all three methods and keeps the `_edit` holder, `_edit_index`, and every `_edit_*` property unchanged (tests drive them). No behavior change; `edit_dialog.py` stays headless-importable.
- **Acceptance criteria:** (1) the three methods' logic lives in `edit_dialog.py`; (2) app wrappers are one-line delegations; (3) `_edit*` property surface and holder attributes unchanged; (4) `app.py` strictly shorter (report before/after); (5) full suite green, no test repatch.
- **Required tests:** frozen per Test Policy. From `implementer/src`: targeted `.venv/bin/python -m pytest tests/test_gui_edit.py tests/test_gui_double_click.py tests/test_gui_centering.py tests/test_gui_headless.py -q`, then full `.venv/bin/python -m pytest tests -q`.
- **Prompt for Implementer:**

> You are the Implementer agent for the todo-md-app repository. Your assigned implementation branch is `implementer/r10a-extract-sidebar` (its tip is `178304e`); `main` is the base and integration branch. First action: verify you are on that branch and the working tree is clean (`git branch --show-current`, `git status --short`).
>
> Your first tool call MUST run `../architect/tools/implementer-run.sh` without arguments; every subsequent Bash command MUST use that wrapper (execution is permitted, modification is forbidden), and you MUST follow the Implementer Mandatory Execution Clock phase rules.
>
> Task R10b (refactor, behavior-preserving): move the logic of `TodoApp._open_edit_dialog(index)`, `_on_edit_save()`, and `_close_edit_dialog()` out of `implementer/src/todo_md/app.py` into `implementer/src/todo_md/edit_dialog.py` as module functions `open_dialog(app, index)`, `save_dialog(app)`, `close_dialog(app)`, following the delegation pattern of `sidebar.py`/`item_row.py` (duck-typed `app`, never import `todo_md.app`, tkinter imported lazily). Preserve the logic verbatim: open guards on `app.current_list is None`, opens the list via `app.controller.open_list`, instantiates `EditItemDialog(app, item, on_save=..., on_close=...)`, stores it in `app._edit` and records `app._edit_index`; save reads `app._edit_desc_text.get("1.0", "end-1c")` and `app._edit_entry.get()`, calls `app.controller.edit_item(app.current_list, app._edit_index, text, description)` swallowing `ValueError`, then closes and calls `app._refresh_items()`; close destroys the window if alive, drops `app._edit` and `app._edit_index`. In `app.py` the three methods become one-line lazy-import delegations; keep the `_edit` holder, `_edit_index`, and all `_edit_*` properties exactly as they are (tests rely on them). `edit_dialog.py` must remain importable on a headless machine.
>
> Change boundaries: modify only files under `implementer/` (expected: `implementer/src/todo_md/edit_dialog.py`, `implementer/src/todo_md/app.py`). NEVER touch anything under `architect/` or the repository root. Test files are frozen: do not add, modify, or remove any test, except a minimal import-only repatch if a test references a private symbol that moved; report any such repatch explicitly.
>
> Verify your branch and the working tree before editing. Before committing run from `implementer/src`: `.venv/bin/python -m pytest tests/test_gui_edit.py tests/test_gui_double_click.py tests/test_gui_centering.py tests/test_gui_headless.py -q` and then the full suite `.venv/bin/python -m pytest tests -q` — all must pass (348 passed, 2 skipped expected). Commit the completed work (stage only the files you changed; no broad `git add -A`, no destructive working-tree operations). Do not create, switch, merge, rebase, rename, delete, or push branches, and never commit to `main`.
>
> Handoff format: RESULT: SUCCESS|FAILURE, BRANCH: implementer/r10a-extract-sidebar, COMMIT: <hash>, plus app.py before/after line counts and any (expected: none) test repatch.

## Queue
- **C1** (S): make the edit-modal description text box user-resizable (pair it with a palette-aware scrollbar; dialog must not rely on fixed height only).
- **C2** (S): preserve empty lines in an item description: write a blank description line as the two-space continuation line (e.g. `"  "`); on load, a blank line indented ≥2 spaces continues the description (empty line appended), while a truly unindented blank line keeps terminating it — full save→load round trip of `"a\n\nb"` must reproduce `"a\n\nb"`.
- **C1** (S): make the edit-modal description text box user-resizable (pair it with a palette-aware scrollbar; dialog must not rely on fixed height only).
- **C2** (S): preserve empty lines in an item description: write a blank description line as the two-space continuation line (e.g. `"  "`); on load, a blank line indented ≥2 spaces continues the description (empty line appended), while a truly unindented blank line keeps terminating it — full save→load round trip of `"a\n\nb"` must reproduce `"a\n\nb"`.

## Active Blockers
None.

## Recently Completed
- B3 — Spinbox hover contrast: new `spin_hover` palette fill (`#565656` dark / `#d0d0d0` light) mapped to `TSpinbox` active/pressed `background`; hover now clearly visible: DONE (Implementer commit 4388e2d).
- B2 — Spinbox hover: `TSpinbox` state maps pin `-background`/`-arrowcolor` (active/pressed → palette `btn_active`/`fg`, disabled → `fg_disabled`); `btn_active` promoted into `palette_for`: DONE (Implementer commit cb53a91).
- B1 — Dark-theme spinbox arrows: `apply_theme` pins `TSpinbox -arrowcolor` to palette fg (Tk 9 C Arrow element otherwise defaults near-black); new `test_gui_spinbox_arrows.py`: DONE (Implementer commit eb3cd40).
- R9 — Remove both compat shims: `dock_icon_path` canonical in `dialogs.py` + `apply_dock_icon(root, icon_path)` param, `relocate_lists` called directly in controller, authorized 2-line test repatch: DONE (Implementer commit 6d81255).
- R8 — Final complexity pass: no `nonlocal` in controller, row rebuild moved to `item_row.rebuild_rows`, compressed wrappers/slimmed `__init__`; app.py 713 → 589 lines: DONE (Implementer commit bd38aa1).
