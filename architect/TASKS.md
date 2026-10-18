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
**B1 — Fix invisible spinbox arrows in dark theme** (size S, branch `implementer/b1-spinbox-arrows`)

- **Scope:** `implementer/src/todo_md/theme.py` (`apply_theme`) + new GUI test file `implementer/src/tests/test_gui_spinbox_arrows.py`. No other production files.
- **Bug (architect-verified from user screenshot + pixel analysis):** on the clam-fallback dark theme, the settings `ttk.Spinbox` up/down arrow glyphs render near-black (#0e0e0e = anti-aliased black) on the dark field fill (#383838) — contrast ≈ 1.3:1, effectively invisible. Root cause: `apply_theme()` configures TEntry/TSpinbox `background`/`foreground`/`fieldbackground`/`insertcolor` but never `-arrowcolor`; on Tcl/Tk 9.1 the C `Arrow` element then falls back to a black default. Light theme works only by luck (black on white).
- **Fix:** in `apply_theme()`, configure `arrowcolor` = palette `fg` on the `TSpinbox` style (light arrows in dark, black in light) with a comment explaining the Tk 9 C Arrow-element black default. Do not alter `settings_window.py` or other styling.
- **Acceptance criteria:**
  1. Dark theme: `ttk.Style().lookup("TSpinbox", "arrowcolor")` equals the palette `fg` and its luminance differs from the field background by > 0.35.
  2. Light theme: same lookup equals the light `fg`; existing behavior unchanged.
  3. Guarded skip when the native `appappearance` path is active (`app._palette is None`), following `test_gui_theme_switch.py` conventions.
- **Tests:** new `tests/test_gui_spinbox_arrows.py` only (existing test files stay untouched); use the `lum()` helper pattern and conftest fixtures from `test_gui_theme_switch.py`.
- **Test commands (from `implementer/src/`):** `.venv/bin/python -m pytest tests/test_gui_spinbox_arrows.py -v` then `.venv/bin/python -m pytest tests -v` (baseline 344 pass / 2 skip, plus the new tests).
- **Prompt for Implementer:**
  You are assigned task **B1** on branch `implementer/b1-spinbox-arrows` (base and integration branch: `main`).
  1. First tool call: run `../architect/tools/implementer-run.sh` (no arguments) from your workspace. Use this wrapper for ALL subsequent Bash commands and follow the Mandatory Execution Clock phase rules.
  2. Verify you are on branch `implementer/b1-spinbox-arrows` and inspect the working tree before editing. Restrict every change to `implementer/`; NEVER touch `architect/` or repository-root files.
  3. Bug context: read `architect/DESIGN.md` (section *Component Architecture* → `theme.py`) and the *Known Architectural Debt* note; the bug and root cause are stated in this prompt (see TASKS.md Active Task for the verified pixel-level analysis): the clam-fallback dark theme leaves `TSpinbox -arrowcolor` unset, so the Tk 9 C Arrow element draws near-black arrows on the #383838 field — invisible.
  4. Implement: in `todo_md/theme.py` `apply_theme()`, set `arrowcolor` to the palette `fg` on the `TSpinbox` style (document why in a comment). Keep light-theme output unchanged (its `fg` is already black).
  5. Add `tests/test_gui_spinbox_arrows.py` asserting the acceptance criteria above (dark + light lookups, luminance-contrast check, native-path guard). Do not modify existing tests or production files.
  6. Run from `implementer/src/`: `.venv/bin/python -m pytest tests/test_gui_spinbox_arrows.py -v` then the full suite `.venv/bin/python -m pytest tests -v`.
  7. Commit completed work (if the pre-commit hook auto-bumps `src/todo_md/VERSION`, include that file). NEVER create/switch/merge/rename/delete/push branches; never commit to `main`; no destructive working-tree operations.
  8. Handoff: report RESULT, branch `implementer/b1-spinbox-arrows`, commit hash, tests run, and any blockers.

## Queue
- **Backlog (non-blocking):** `TodoApp` still builds the sidebar (listbox, entries, buttons) and owns the edit-dialog open/save flow in `_build_ui`/`_open_edit_dialog`; extract to dedicated modules if `app.py` grows again.

## Active Blockers
None.

## Recently Completed
- R9 — Remove both compat shims: `dock_icon_path` canonical in `dialogs.py` + `apply_dock_icon(root, icon_path)` param, `relocate_lists` called directly in controller, authorized 2-line test repatch: DONE (Implementer commit 6d81255).
- R8 — Final complexity pass: no `nonlocal` in controller, row rebuild moved to `item_row.rebuild_rows`, compressed wrappers/slimmed `__init__`; app.py 713 → 589 lines: DONE (Implementer commit bd38aa1).
- R7 — Move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py` (re-exported by `app.py`; `relocate_lists` resolved via app for frozen-test compat): DONE (Implementer commit f4f87c3).
- R5 — Extract entry-placeholder mechanism into `todo_md/placeholders.py` (PlaceholderBinder) + `self._ph` holder: DONE (Implementer commit 8ff404b).
