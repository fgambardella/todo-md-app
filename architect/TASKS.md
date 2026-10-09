# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional `<!-- Description: -->` line). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -v)` (344 pass, 2 skip, ~25s baseline).
- Targeted: `.venv/bin/python -m pytest tests/<file> -v` from `implementer/src/`.
- Refactor series R1-R8: **test files are frozen** — implementers may not add, modify, or remove any test; every task is verified against the existing suite only.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together, and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` also hosts the full Tkinter GUI — its settings-window construction now lives in a dedicated module while the rest stays in `app.py`, the target of refactor series R1-R8. All 344 tests pass.

## Active Task
**R2 (S)** — Extract item-row rendering from `_refresh_items` into `todo_md/item_row.py`; collapse the six duplicated conditional-bg kwargs patterns (five in `_refresh_items` + the `background` one in `_build_ui`) into one `bg_kwargs` helper.
- Branch: `implementer/r2-item-row` (base `main`; integration branch `main`).
- Scope: create `implementer/src/todo_md/item_row.py`; modify `implementer/src/todo_md/app.py` only.
- Acceptance: item-row construction lives in `item_row.py`; all conditional-bg patterns go through `bg_kwargs`; zero behavior change; full suite green with zero test edits; headless import intact.
- Required tests: full suite; targeted `tests/test_gui_toggle.py tests/test_gui_layout.py tests/test_gui_delete.py tests/test_gui_delete_icon.py tests/test_gui_double_click.py tests/test_gui_hover.py tests/test_gui_contrast.py tests/test_gui_theme.py tests/test_gui_theme_switch.py`.
- Commands (from `implementer/src/`): targeted `.venv/bin/python -m pytest tests/test_gui_toggle.py tests/test_gui_layout.py tests/test_gui_delete.py tests/test_gui_delete_icon.py tests/test_gui_double_click.py tests/test_gui_hover.py tests/test_gui_contrast.py tests/test_gui_theme.py tests/test_gui_theme_switch.py -v`; full `.venv/bin/python -m pytest tests -v`.

### Implementer Prompt (R2)
Task R2 — Extract item-row rendering into `todo_md/item_row.py` and collapse the duplicated conditional-bg kwargs pattern.
Branch: work only on `implementer/r2-item-row` (already checked out); base and integration branch is `main`. Never create/switch/merge/rebase/rename/delete/push branches; never commit to `main`; no broad `git add -A`, `reset`, or `clean` — stage only the two files you changed.
First tool call: run `../architect/tools/implementer-run.sh` with no arguments; use that wrapper for ALL later Bash commands; follow the Mandatory Execution Clock phase rules. Executing it is permitted; modifying it is forbidden.
Before editing: verify the current branch (`git rev-parse --abbrev-ref HEAD`) and inspect the working tree (`git status --short`).
Scope — you may create/modify ONLY: `implementer/src/todo_md/item_row.py` (new) and `implementer/src/todo_md/app.py`.
Forbidden: every file under `implementer/src/tests/` (tests are frozen — zero modifications), `implementer/src/todo_md/__init__.py`, all other `todo_md` modules, everything under `architect/`, repository root.
Work:
1. Create `implementer/src/todo_md/item_row.py` containing:
   - `bg_kwargs(bg: str | None, key: str = "bg") -> dict`: returns `{key: bg}` when `bg is not None`, else `{}`.
   - `build_item_row(parent, *, item, index, row_bg, active_fg, done_fg, base_font, trash_image, edit_image, on_toggle, on_delete, on_edit, on_double_click) -> tuple`: creates and packs EXACTLY the row `TodoApp._refresh_items` currently builds inline — a `tk.Frame(parent)` row using the bg kwarg, packed `anchor="w", fill=tk.X`; a `tk.IntVar` initialized from `item.done` plus a `tk.Checkbutton` (command `on_toggle(index)`) packed `side=LEFT, padx=(4, 6)`; a trash `tk.Label` (image=trash_image, cursor="hand2") packed `side=RIGHT, padx=(6, 4)` with `<Button-1>` bound to `on_delete(index)`; a pencil `tk.Label` (image=edit_image, cursor="hand2") packed `side=RIGHT, padx=(6, 0)` with `<Button-1>` bound to `on_edit(index)`; a text `tk.Label` (anchor="w", per-item copy of base_font with overstrike only when `item.done`, foreground `done_fg if item.done else active_fg`) packed `side=LEFT, fill=tk.X, expand=True` with `<Double-Button-1>` bound to `on_double_click(index)`. Returns the 5-tuple `(var, checkbutton, label, trash_label, edit_label)` in exactly that order.
   - Import tkinter only inside functions (headless-import invariant). Do NOT import `todo_md.app` or any name from it — everything arrives as parameters, because tests monkeypatch names on the `todo_md.app` module.
2. In `app.py`: `TodoApp._refresh_items` keeps the children-destroy loop, `self._item_rows = []`, the `current_list is None` early return + title update, and the `visible_items` loop with `stored_indexes`; inside the loop it calls `build_item_row(...)` and appends the returned tuple to `self._item_rows`. Replace the five inline `{"bg": row_bg} if row_bg is not None else {}` expressions and the `background` one in `_build_ui` (version badge) with `bg_kwargs(...)` calls; lazy-import from `.item_row` inside the methods. Keep the `tkfont` base-font computation in `_refresh_items`. No other `app.py` changes.
Hard invariants:
- Zero test modifications.
- `import todo_md.app` must stay headless: no top-level tkinter import in `app.py` or `item_row.py`.
- `self._item_rows` must remain a list of the same 5-tuple `(var, checkbutton, label, del_ctrl, edit_ctrl)` — tests unpack by position.
- Identical widgets, packing order, padding, bindings, fonts, and foreground logic; identical user-visible behavior.
- All `todo_md.app` module-level names (`TodoApp`, `TodoController`, `run`, `dock_icon_path`, `visible_items`, `DEFAULT_DATA_DIR`, `DEFAULT_CONFIG_DIR`, `_has_markdown`, `_valid_lists_dir_path`, `_same_dir`, `_normalize_dir`, `startup_dirs`) and `__all__` must remain untouched.
Acceptance: item-row construction lives in `item_row.py`; every conditional-bg dict in `app.py` goes through `bg_kwargs`; full suite green with zero test edits.
Commands (from `implementer/src/`): targeted `.venv/bin/python -m pytest tests/test_gui_toggle.py tests/test_gui_layout.py tests/test_gui_delete.py tests/test_gui_delete_icon.py tests/test_gui_double_click.py tests/test_gui_hover.py tests/test_gui_contrast.py tests/test_gui_theme.py tests/test_gui_theme_switch.py -v`; then full `.venv/bin/python -m pytest tests -v`.
On completion: commit BOTH files on `implementer/r2-item-row` (the pre-commit hook may auto-stage a VERSION bump — expected, leave it), then hand off: RESULT: SUCCESS|FAILURE, SUMMARY (3-5 bullets), BRANCH, COMMIT hash, test totals. Keep edits minimal and commit early; the clock is the known risk.

## Queue
- **R3 (S):** extract the theme engine (palette, `_apply_theme`, luminance `_text_colors`, `_theme_button_text`) into `todo_md/theme.py`; `TodoApp` keeps `_palette`, `_apply_theme`, `_theme_button_text` as thin wrappers.
- **R4 (S):** extract the modal edit dialog into `todo_md/edit_dialog.py` (`EditItemDialog`); `TodoApp` keeps `_edit_window`, `_edit_entry`, `_edit_desc_text`, `_edit_save_btn`, `_edit_cancel_btn`, `_open_edit_dialog`, `_close_edit_dialog` via delegation.
- **R5 (S):** extract the entry-placeholder mechanism into `todo_md/placeholders.py`; `TodoApp` keeps `_placeholders`, `_entry_value`, `_restore_placeholder` as thin wrappers.
- **R6 (S):** extract shared dialog helpers into `todo_md/dialogs.py` (window centering, dock-icon apply — must call `todo_md.app.dock_icon_path` via dynamic lookup since tests monkeypatch it).
- **R7 (S):** move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py`; re-export both from `app.py`; pure move, no behavior change.
- **R8 (S):** final complexity pass on remaining `app.py`: collapse the repeated `current_list is None` guards, remove the controller `nonlocal` closure pattern, dedupe any remaining kwargs patterns, slim `__init__`; target `app.py` ≈ 400 lines or fewer.

## Active Blockers
None.

## Recently Completed
- R1 — Extract Settings window (construction + save flow) into `todo_md/settings_window.py`: DONE (Implementer commit e8f3f37; merged to main at 495e9d5).
- 47 — Center modal dialogs on the main window (edit + settings): DONE (v1.0.0 released; Implementer commit d547cbf).
- 46 — Persist settings.json on every change: DONE (Implementer commit c9f9711).
- 45 — Fix dark-theme unreadable gray text: DONE (Implementer commit 0c9e64b).
- 44 — Theme system with live switching and dock icon: DONE (Implementer commit 893d7a9).
