# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional `<!-- Description: -->` line). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -v)` (344 pass, 2 skip, ~25s baseline).
- Targeted: `.venv/bin/python -m pytest tests/<file> -v` from `implementer/src/`.
- Refactor series R1-R8: **test files are frozen** — implementers may not add, modify, or remove any test; every task is verified against the existing suite only.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together, and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` hosts the Tkinter GUI, while its settings window, item-row rendering, and theme engine now live in dedicated modules, the rest stays in `app.py`, the target of refactor series R1-R8. All 344 tests pass.

## Active Task
**R4 (S)** — Extract the modal edit dialog into `todo_md/edit_dialog.py` (`EditItemDialog`); `TodoApp` keeps `_edit_window`, `_edit_entry`, `_edit_desc_text`, `_edit_save_btn`, `_edit_cancel_btn`, `_open_edit_dialog`, `_close_edit_dialog` via delegation.
- Branch: `implementer/r4-edit-dialog` (base `main`; integration branch `main`).
- Scope: create `implementer/src/todo_md/edit_dialog.py`; modify `implementer/src/todo_md/app.py` only.
- Acceptance: dialog construction lives in `edit_dialog.py`; `TodoApp` exposes the same attribute/method names with identical behavior; zero test edits; full suite green; headless import intact.
- Required tests: full suite; targeted `tests/test_gui_edit.py tests/test_gui_double_click.py tests/test_gui_centering.py tests/test_gui_headless.py tests/test_startup.py`.
- Commands (from `implementer/src/`): targeted `.venv/bin/python -m pytest tests/test_gui_edit.py tests/test_gui_double_click.py tests/test_gui_centering.py tests/test_gui_headless.py tests/test_startup.py -v`; full `.venv/bin/python -m pytest tests -v`.

### Implementer Prompt (R4)
Task R4 — Extract the modal edit dialog into `todo_md/edit_dialog.py`.
Branch: work only on `implementer/r4-edit-dialog` (already checked out); base and integration branch is `main`. Never create/switch/merge/rebase/rename/delete/push branches; never commit to `main`; no broad `git add -A`, `reset`, or `clean` — stage only the files you changed.
First tool call: run `../architect/tools/implementer-run.sh` with no arguments; use that wrapper for ALL later Bash commands; follow the Mandatory Execution Clock phase rules. Executing it is permitted; modifying it is forbidden.
Before editing: verify the current branch (`git rev-parse --abbrev-ref HEAD`) and inspect the working tree (`git status --short`).
Scope — you may create/modify ONLY: `implementer/src/todo_md/edit_dialog.py` (new) and `implementer/src/todo_md/app.py`.
Forbidden: every file under `implementer/src/tests/` (tests are frozen — zero modifications), all other `todo_md` modules, everything under `architect/`, repository root.
Work:
1. Create `implementer/src/todo_md/edit_dialog.py` with class `EditItemDialog`:
   - `__init__(self, app, item, *, on_save, on_close)`: builds EXACTLY what `TodoApp._open_edit_dialog` builds today, reading `app.root` and `app._palette` (duck-typed; never import `todo_md.app`): the `tk.Toplevel` (palette bg when `app._palette is not None`, title "Edit item", transient over root), the pre-populated `ttk.Entry` title field (item.text), the multi-line `tk.Text` description box (height=5, width=40, wrap WORD, undo, with the same 4-key palette kwargs block and comments, pre-populated with item.description), and the save/cancel `ttk.Button`s wired to the `on_save`/`on_close` callbacks (save also bound to entry `<Return>`; window `WM_DELETE_WINDOW` → `on_close`). Then: `grab_set()`, `update()`, and center via `app._center_window_on_parent(self.window)`. Expose public attributes `window`, `entry`, `desc_text`, `save_btn`, `cancel_btn`.
   - `close(self)`: destroy the window if it still exists.
   - tkinter imports only inside methods; no `todo_md.app` import.
2. In `app.py`:
   - Add an `self._edit = None` holder in `TodoApp.__init__` (fold the existing `_edit_* = None` initializations into it consistently with step 3, or keep them if simpler and still correct).
   - `_open_edit_dialog(self, index)` becomes: guard `current_list is None`, open the list, fetch the item, then instantiate `EditItemDialog(self, item, on_save=self._on_edit_save, on_close=self._close_edit_dialog)` (lazy import from `.edit_dialog`), store it in `self._edit`, and set `self._edit_index = index`.
   - Keep `_edit_index` as a plain `TodoApp` attribute; add delegating `@property` getters so every existing name keeps working: `_edit_window`, `_edit_entry`, `_edit_desc_text`, `_edit_save_btn`, `_edit_cancel_btn` → `self._edit.<attr>` or `None` when no dialog is open.
   - `_close_edit_dialog(self)`: if `self._edit` is not None call `.close()`, then set `self._edit = None` and `self._edit_index = None` (no-op safe when nothing is open). `_on_edit_save` keeps its current body (it reads the properties).
   - Remove the inline dialog-construction code that moved to `edit_dialog.py`; no other `app.py` changes.
Hard invariants:
- Zero test modifications; tests read `app._edit_window` (incl. `.title() == "Edit item"`, `.winfo_exists()`), `app._edit_entry` (`ttk.Entry`), `app._edit_desc_text`, `app._edit_save_btn.invoke()`, `app._edit_cancel_btn`, and call `app._open_edit_dialog(index)` / `app._close_edit_dialog()` (the latter a no-op when no dialog is open) — all must keep working identically.
- `import todo_md.app` must stay headless; `edit_dialog.py` must have no top-level tkinter import and must NOT import `todo_md.app`.
- Identical window styling, pre-population, bindings, grab, and centering; identical user-visible behavior.
- All `todo_md.app` module-level names and `__all__` must remain untouched.
Acceptance: dialog construction lives in `edit_dialog.py`; the delegated names behave identically; full suite green with zero test edits.
Commands (from `implementer/src/`): targeted `.venv/bin/python -m pytest tests/test_gui_edit.py tests/test_gui_double_click.py tests/test_gui_centering.py tests/test_gui_headless.py tests/test_startup.py -v`; then full `.venv/bin/python -m pytest tests -v`.
On completion: commit BOTH files on `implementer/r4-edit-dialog` (the pre-commit hook may auto-stage a VERSION bump — expected, leave it), then hand off: RESULT: SUCCESS|FAILURE, SUMMARY (3-5 bullets), BRANCH, COMMIT hash, test totals. Keep edits minimal and commit early; the clock is the known risk.

## Queue
- **R5 (S):** extract the entry-placeholder mechanism into `todo_md/placeholders.py`; `TodoApp` keeps `_placeholders`, `_entry_value`, `_restore_placeholder` as thin wrappers.
- **R6 (S):** extract shared dialog helpers into `todo_md/dialogs.py` (window centering, dock-icon apply — must call `todo_md.app.dock_icon_path` via dynamic lookup since tests monkeypatch it).
- **R7 (S):** move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py`; re-export both from `app.py`; pure move, no behavior change.
- **R8 (S):** final complexity pass on remaining `app.py`: collapse the repeated `current_list is None` guards, remove the controller `nonlocal` closure pattern, dedupe any remaining kwargs patterns, slim `__init__`; target `app.py` ≈ 400 lines or fewer.

## Active Blockers
None.

## Recently Completed
- R3 — Extract theme engine (palette, apply_theme, text_colors, button_text) into `todo_md/theme.py`: DONE (Implementer commit fda5317).
- R2 — Extract item-row rendering into `todo_md/item_row.py` + `bg_kwargs` helper: DONE (Implementer commit aee8051).
- R1 — Extract Settings window (construction + save flow) into `todo_md/settings_window.py`: DONE (Implementer commit e8f3f37; merged to main at 495e9d5).
- 47 — Center modal dialogs on the main window (edit + settings): DONE (v1.0.0 released; Implementer commit d547cbf).
- 46 — Persist settings.json on every change: DONE (Implementer commit c9f9711).
