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
**R8 (S)** — Final complexity pass: dedupe guards/closures/kwargs, slim `__init__`, move row-rebuild to `item_row.py`; target `app.py` reduced ≥ 80 lines (≤ 630).
- Branch: `implementer/r8-slim` (base `main`; integration branch `main`).
- Scope: modify `implementer/src/todo_md/app.py`, `implementer/src/todo_md/controller.py`, `implementer/src/todo_md/item_row.py` only.
- Acceptance: no `nonlocal` in `controller.py`; the five row/add handlers free of unreachable `current_list is None` guards; `_refresh_items` loop moved to `item_row.rebuild_rows(app)`; one-line wrappers compressed; `__init__` slimmer; all public/module-level names and `__all__` unchanged; zero test edits; full suite green; headless import intact; `app.py` ≤ 630 lines.
- Required tests: full suite; targeted `tests/test_controller.py tests/test_gui_toggle.py tests/test_gui_delete.py tests/test_gui_edit.py tests/test_gui_add.py tests/test_gui_theme.py tests/test_gui_theme_switch.py tests/test_gui_placeholders.py tests/test_gui_contrast.py tests/test_gui_headless.py`.
- Commands (from `implementer/src/`): targeted `.venv/bin/python -m pytest tests/test_controller.py tests/test_gui_toggle.py tests/test_gui_delete.py tests/test_gui_edit.py tests/test_gui_add.py tests/test_gui_theme.py tests/test_gui_theme_switch.py tests/test_gui_placeholders.py tests/test_gui_contrast.py tests/test_gui_headless.py -v` (run only files that exist); full `.venv/bin/python -m pytest tests -v`.

### Implementer Prompt (R8)
Task R8 — Final complexity pass over `app.py` / `controller.py` / `item_row.py` (no new features, no behavior change).
Branch: work only on `implementer/r8-slim` (already checked out); base and integration branch is `main`. Never create/switch/merge/rebase/rename/delete/push branches; never commit to `main`; no broad `git add -A`, `reset`, or `clean` — stage only the files you changed.
First tool call: run `../architect/tools/implementer-run.sh` with no arguments; use that wrapper for ALL later Bash commands; follow the Mandatory Execution Clock phase rules. Executing it is permitted; modifying it is forbidden.
Before editing: verify the current branch (`git rev-parse --abbrev-ref HEAD`) and inspect the working tree (`git status --short`).
Scope — you may modify ONLY: `implementer/src/todo_md/app.py`, `implementer/src/todo_md/controller.py`, and `implementer/src/todo_md/item_row.py`.
Forbidden: every file under `implementer/src/tests/` (tests are frozen — zero modifications), all other `todo_md` modules, everything under `../architect/`, repository root.
Work (in order):
1. `controller.py` — remove the `nonlocal` closure pattern: in `add_item`, `toggle_item`, and `remove_item` inline the pattern `todo_list = self.open_list(name)` → mutate → `self.store.save(name, [(i.text, i.done, i.description) for i in todo_list.items])` → return the produced item. Delete `_load_and_save` if it becomes unused. Public signatures, docstrings, and error messages stay identical.
2. `app.py` — in `_on_toggle_item`, `_on_delete_item`, `_on_edit_item`, `_on_item_double_click`, and `_on_add_item` delete the leading `if self.current_list is None: return` guards (item rows are only rendered while a list is selected, so they are unreachable; keep the `current_list is None` guards in `_on_edit_save` and `_open_edit_dialog` — the dialog can outlive list state).
3. `item_row.py` + `app.py` — add `rebuild_rows(app)` in `item_row.py` containing the current `_refresh_items` body after the children-destroy line (visible-items loop, per-item font/fg, row build, `_item_rows` population, and the `(no list selected)` title branch); `TodoApp._refresh_items` becomes: destroy children, reset `self._item_rows = []`, `from .item_row import rebuild_rows` (lazy), `rebuild_rows(self)`. `item_row.py` must keep its no-`todo_md.app`-import rule (duck-typed `app` parameter; `visible_items` imported from `.models`, `text_colors` lazily from `.theme`).
4. `app.py` — compress the one-line delegation wrappers: for `_apply_theme`, `_text_colors`, `_theme_button_text`, `_attach_placeholder`, `_placeholder_fg`, `_entry_value`, `_on_entry_focus_in`, `_on_entry_focus_out`, `_restore_placeholder`, and the `_settings_*`/`_edit_*` property getters, keep the method names and behavior exactly but collapse multi-line docstrings to at most one short line (or delete where the name is self-evident).
5. `app.py` `__init__` — condense the 3-5 line comments to one line each; extract the two `tk.PhotoImage` creations into a private `_load_icon_assets(self)` helper called from `__init__`. No behavior change (same asset paths, same attribute names `_trash_image`/`_edit_image`).
6. `app.py` `_build_ui` — trim the 5-line version-badge comment to 2 lines; no structural change.
Hard invariants:
- Zero test modifications. Every `TodoApp` method name, attribute, and module-level name referenced by tests or by `settings_window.py`/`theme.py`/`edit_dialog.py`/`placeholders.py`/`dialogs.py` (including `app._palette`, `app._placeholders`, `app._normalize_dir`, `app._same_dir`, `app._has_markdown`, `app.dock_icon_path`) must keep working unchanged.
- `import todo_md.app` stays headless; no new top-level tkinter imports in `item_row.py`.
- Identical behavior: this is a complexity pass, not a feature.
Acceptance: `app.py` at most 630 lines (was 713); `controller.py` free of `nonlocal`; full suite green with zero test edits.
Commands (from `implementer/src/`): targeted `.venv/bin/python -m pytest tests/test_controller.py tests/test_gui_toggle.py tests/test_gui_delete.py tests/test_gui_edit.py tests/test_gui_add.py tests/test_gui_theme.py tests/test_gui_theme_switch.py tests/test_gui_placeholders.py tests/test_gui_contrast.py tests/test_gui_headless.py -v` (run only files that exist); then full `.venv/bin/python -m pytest tests -v`.
On completion: commit the changed files on `implementer/r8-slim` (the pre-commit hook may auto-stage a VERSION bump — expected, leave it), then hand off: RESULT: SUCCESS|FAILURE, SUMMARY (3-5 bullets incl. final `app.py` line count), BRANCH, COMMIT hash, test totals. Keep edits minimal and commit early; the clock is the known risk.

## Queue
- **Backlog (non-blocking):** `TodoApp` still builds the sidebar (listbox, entries, buttons) and owns the edit-dialog open/save flow in `_build_ui`/`_open_edit_dialog`; extract to dedicated modules if `app.py` grows again.

## Active Blockers
None.

## Recently Completed
- R7 — Move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py` (re-exported by `app.py`; `relocate_lists` resolved via app for frozen-test compat): DONE (Implementer commit f4f87c3).
- R6 — Extract shared dialog helpers (window centering, dock icon) into `todo_md/dialogs.py`: DONE (Implementer commit c8b8773).
- R5 — Extract entry-placeholder mechanism into `todo_md/placeholders.py` (PlaceholderBinder) + `self._ph` holder: DONE (Implementer commit 8ff404b).
- R4 — Extract modal edit dialog into `todo_md/edit_dialog.py` (EditItemDialog) + delegation properties: DONE (Implementer commit 3b52df2).
- R3 — Extract theme engine (palette, apply_theme, text_colors, button_text) into `todo_md/theme.py`: DONE (Implementer commit fda5317).
