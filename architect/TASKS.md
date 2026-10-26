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
**R10a** (M, micro-task 1 of 2 of R10) — Extract the list-sidebar construction out of `TodoApp._build_ui` into a new `todo_md/sidebar.py`.
- **Branch:** `implementer/r10a-extract-sidebar` (base: `main`)
- **Scope:** new module `implementer/src/todo_md/sidebar.py` (mirrors the `item_row.py` pattern: duck-typed `app` parameter, tkinter imported lazily inside functions, never imports `todo_md.app`) containing `build_sidebar(app)` which builds the entire left frame currently inlined in `_build_ui`: "Lists:" label, `app.listbox` (width 22, height 14, `exportselection=False`, `<<ListboxSelect>>` → `app._on_select_list`), `app.new_name_entry` (width 20, Return → `app._on_create_list`, placeholder "Insert the name of a new list here" via `app._attach_placeholder`), the Create/Delete button row, `app._theme_btn`, `app._settings_btn` — with identical widget options, pack order, padding, and placeholder text as today. `TodoApp._build_ui` must call `build_sidebar(app)` (lazy import) and keep only the version badge and the right frame inline. No behavior, naming, or attribute change; all widgets remain attributes of the app instance.
- **Acceptance criteria:** (1) new `sidebar.py` exists and holds the complete sidebar construction; (2) `_build_ui` no longer contains the inlined sidebar block and is strictly shorter; (3) `app.py` line count drops (report before/after in handoff); (4) every app attribute tests rely on (`listbox`, `new_name_entry`, `_theme_btn`, `_settings_btn`) unchanged; (5) `sidebar.py` is importable headless; (6) full suite green.
- **Required tests:** test files frozen per Test Policy (minimal import-only repatch allowed and must be reported). Run from `implementer/src`: targeted `.venv/bin/python -m pytest tests/test_gui_layout.py tests/test_gui_new_list.py tests/test_gui_delete.py tests/test_gui_theme.py tests/test_gui_placeholders.py tests/test_gui_headless.py -q`, then full `.venv/bin/python -m pytest tests -q`.
- **Prompt for Implementer:**

> You are the Implementer agent for the todo-md-app repository. Your assigned implementation branch is `implementer/r10a-extract-sidebar`; `main` is the base and integration branch. First action: verify you are on that branch and the working tree is clean (`git branch --show-current`, `git status --short`).
>
> Your first tool call MUST run `../architect/tools/implementer-run.sh` without arguments; every subsequent Bash command MUST use that wrapper (execution is permitted, modification is forbidden), and you MUST follow the Implementer Mandatory Execution Clock phase rules.
>
> Task R10a (refactor, behavior-preserving): extract the list-sidebar construction out of `TodoApp._build_ui` in `implementer/src/todo_md/app.py` into a new module `implementer/src/todo_md/sidebar.py`, following the existing `todo_md/item_row.py` pattern (duck-typed `app` parameter, tkinter imported lazily inside functions, never import `todo_md.app`). Create `build_sidebar(app)` that builds the entire left frame: "Lists:" label; `app.listbox` (tk.Listbox, width 22, height 14, exportselection False, `<<ListboxSelect>>` bound to `app._on_select_list`); `app.new_name_entry` (ttk.Entry width 20, `<Return>` → `app._on_create_list`, placeholder "Insert the name of a new list here" attached via `app._attach_placeholder`); the Create/Delete ttk button row (Create → `app._on_create_list`, Delete → `app._on_delete_list`); `app._theme_btn` (text from `app._theme_button_text()`, command `app._on_toggle_theme`); `app._settings_btn` (text "Settings", command `app._open_settings`). Preserve every widget option, pack side/fill/expand/padx/pady, and pack order exactly as the current code, so no visual or behavioral change occurs. In `app.py`, replace the inlined sidebar block in `_build_ui` with a lazy-imported `build_sidebar(app)` call; leave the version badge and the right frame in `_build_ui`. `sidebar.py` must remain importable on a headless machine.
>
> Change boundaries: modify only files under `implementer/` (expected: `implementer/src/todo_md/sidebar.py` (new), `implementer/src/todo_md/app.py`). NEVER touch anything under `architect/` or the repository root. Test files are frozen: do not add, modify, or remove any test, except that a minimal import-only repatch is permitted if a test references a private symbol that moved; report any such repatch explicitly.
>
> Verify your branch and the working tree before editing. Before committing run from `implementer/src`: `.venv/bin/python -m pytest tests/test_gui_layout.py tests/test_gui_new_list.py tests/test_gui_delete.py tests/test_gui_theme.py tests/test_gui_placeholders.py tests/test_gui_headless.py -q` and then the full suite `.venv/bin/python -m pytest tests -q` — all must pass (348 passed, 2 skipped expected). Commit the completed work (stage only the files you changed; `git commit -am`-style precise staging, no broad `git add -A`). Do not create, switch, merge, rebase, rename, delete, or push branches, and never commit to `main`.
>
> Handoff format: RESULT: SUCCESS|FAILURE, BRANCH: implementer/r10a-extract-sidebar, COMMIT: <hash>, plus app.py before/after line counts and any (expected: none) test repatch.

## Queue
- **R10b** (M, micro-task 2 of 2 of R10): extract the edit-dialog open/save/teardown flow (`_open_edit_dialog`, `_on_edit_save`, `_close_edit_dialog` logic) from `app.py` into `edit_dialog.py`, following the `sidebar`/`item_row` delegation pattern; keep the `_edit*` attribute/property surface for tests.
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
