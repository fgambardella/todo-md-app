# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional `<!-- Description: -->` line). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -v)` (344 pass, 2 skip, ~25s baseline).
- Targeted: `.venv/bin/python -m pytest tests/<file> -v` from `implementer/src/`.
- Refactor series R1-R8: **test files are frozen** — implementers may not add, modify, or remove any test; every task is verified against the existing suite only.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together, and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` also hosts the Tkinter GUI — its settings window and item-row rendering now live in dedicated modules while the rest stays in `app.py`, the target of refactor series R1-R8. All 344 tests pass.

## Active Task
**R3 (S)** — Extract the theme engine (palette construction, `_apply_theme`, luminance `_text_colors`, `_theme_button_text`) into `todo_md/theme.py`; `TodoApp` keeps `_palette`, `_apply_theme`, `_theme_button_text`, `_text_colors` as thin wrappers.
- Branch: `implementer/r3-theme` (base `main`; integration branch `main`).
- Scope: create `implementer/src/todo_md/theme.py`; modify `implementer/src/todo_md/app.py` only.
- Acceptance: all theme logic lives in `theme.py`; the `app._palette` attribute and `_apply_theme`/`_theme_button_text`/`_text_colors` methods keep identical behavior; zero test edits; full suite green; headless import intact.
- Required tests: full suite; targeted `tests/test_gui_theme.py tests/test_gui_theme_switch.py tests/test_gui_contrast.py tests/test_gui_version_colors.py tests/test_gui_headless.py tests/test_startup.py`.
- Commands (from `implementer/src/`): targeted `.venv/bin/python -m pytest tests/test_gui_theme.py tests/test_gui_theme_switch.py tests/test_gui_contrast.py tests/test_gui_version_colors.py tests/test_gui_headless.py tests/test_startup.py -v`; full `.venv/bin/python -m pytest tests -v`.

### Implementer Prompt (R3)
Task R3 — Extract the theme engine into `todo_md/theme.py`.
Branch: work only on `implementer/r3-theme` (already checked out); base and integration branch is `main`. Never create/switch/merge/rebase/rename/delete/push branches; never commit to `main`; no broad `git add -A`, `reset`, or `clean` — stage only the files you changed.
First tool call: run `../architect/tools/implementer-run.sh` with no arguments; use that wrapper for ALL later Bash commands; follow the Mandatory Execution Clock phase rules. Executing it is permitted; modifying it is forbidden.
Before editing: verify the current branch (`git rev-parse --abbrev-ref HEAD`) and inspect the working tree (`git status --short`).
Scope — you may create/modify ONLY: `implementer/src/todo_md/theme.py` (new) and `implementer/src/todo_md/app.py`.
Forbidden: every file under `implementer/src/tests/` (tests are frozen — zero modifications), all other `todo_md` modules, everything under `architect/`, repository root.
Work:
1. Create `implementer/src/todo_md/theme.py` containing exactly the theme logic moved out of `TodoApp` (preserve all explanatory comments):
   - `button_text(theme: str) -> str` — from `TodoApp._theme_button_text` ("🌙 Dark" when `theme == "light"` else "☀️ Light").
   - `palette_for(theme: str) -> dict` — the dark/light clam-fallback palette dict currently built inline in `_apply_theme` (keys bg, fg, btn_bg, entry_bg, list_bg, version_fg, placeholder_fg).
   - `text_colors(root, reference_widget) -> tuple[str, str]` — the luminance logic currently in `TodoApp._text_colors` (uses `root.winfo_rgb`; identical thresholds and return values).
   - `apply_theme(root, app) -> dict | None` — the body of `TodoApp._apply_theme` with `self` replaced by the `app` parameter (duck-typed; it reads/sets `app._palette` via the caller, and accesses `app.settings_window`, `app.items_frame`, `app.listbox`, `app.version_label`, `app._placeholders` exactly as the current code does, including the `getattr(..., None)` guards). Native path (`tk appappearance` succeeds): return `None` (meaning "no fallback palette"). Fallback path: return the `palette_for(theme)` dict. tkinter imports only inside functions.
2. In `app.py`, replace the three method bodies with thin wrappers (lazy `from .theme import ...` inside each method):
   - `_theme_button_text(self)` → `return button_text(self.theme)`
   - `_apply_theme(self, theme)` → `self._palette = apply_theme(self.root, self)` (keep the current docstring)
   - `_text_colors(self, reference_widget)` → `return text_colors(self.root, reference_widget)`
   Remove the palette/style/luminance code that moved to `theme.py`; no other `app.py` changes.
Hard invariants:
- Zero test modifications.
- `import todo_md.app` must stay headless; `theme.py` must have no top-level tkinter import and must NOT import `todo_md.app` (everything arrives as parameters).
- `app._palette` must keep the exact same lifecycle (None on the native path, the same dict on the fallback path — tests read `app._palette["fg"]`, `["entry_bg"]`, `["placeholder_fg"]`, `["version_fg"]`) and call `app._apply_theme(theme)`.
- Identical styling side effects (ttk clam styles, state maps, widget bg/fg updates, settings-window bg, placeholder refresh) and order; identical user-visible behavior.
- All `todo_md.app` module-level names and `__all__` must remain untouched.
Acceptance: theme engine lives in `theme.py`; the three wrappers behave identically; full suite green with zero test edits.
Commands (from `implementer/src/`): targeted `.venv/bin/python -m pytest tests/test_gui_theme.py tests/test_gui_theme_switch.py tests/test_gui_contrast.py tests/test_gui_version_colors.py tests/test_gui_headless.py tests/test_startup.py -v`; then full `.venv/bin/python -m pytest tests -v`.
On completion: commit BOTH files on `implementer/r3-theme` (the pre-commit hook may auto-stage a VERSION bump — expected, leave it), then hand off: RESULT: SUCCESS|FAILURE, SUMMARY (3-5 bullets), BRANCH, COMMIT hash, test totals. Keep edits minimal and commit early; the clock is the known risk.

## Queue
- **R4 (S):** extract the modal edit dialog into `todo_md/edit_dialog.py` (`EditItemDialog`); `TodoApp` keeps `_edit_window`, `_edit_entry`, `_edit_desc_text`, `_edit_save_btn`, `_edit_cancel_btn`, `_open_edit_dialog`, `_close_edit_dialog` via delegation.
- **R5 (S):** extract the entry-placeholder mechanism into `todo_md/placeholders.py`; `TodoApp` keeps `_placeholders`, `_entry_value`, `_restore_placeholder` as thin wrappers.
- **R6 (S):** extract shared dialog helpers into `todo_md/dialogs.py` (window centering, dock-icon apply — must call `todo_md.app.dock_icon_path` via dynamic lookup since tests monkeypatch it).
- **R7 (S):** move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py`; re-export both from `app.py`; pure move, no behavior change.
- **R8 (S):** final complexity pass on remaining `app.py`: collapse the repeated `current_list is None` guards, remove the controller `nonlocal` closure pattern, dedupe any remaining kwargs patterns, slim `__init__`; target `app.py` ≈ 400 lines or fewer.

## Active Blockers
None.

## Recently Completed
- R2 — Extract item-row rendering into `todo_md/item_row.py` + `bg_kwargs` helper: DONE (Implementer commit aee8051).
- R1 — Extract Settings window (construction + save flow) into `todo_md/settings_window.py`: DONE (Implementer commit e8f3f37; merged to main at 495e9d5).
- 47 — Center modal dialogs on the main window (edit + settings): DONE (v1.0.0 released; Implementer commit d547cbf).
- 46 — Persist settings.json on every change: DONE (Implementer commit c9f9711).
- 45 — Fix dark-theme unreadable gray text: DONE (Implementer commit 0c9e64b).
