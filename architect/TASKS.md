# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional `<!-- Description: -->` line). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -v)` (346 pass, 2 skip, ~26s baseline).
- Targeted: `.venv/bin/python -m pytest tests/<file> -v` from `implementer/src/`.
- Refactor series R1-R8: **test files are frozen** — implementers may not add, modify, or remove any test; every task is verified against the existing suite only.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together, and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; in the dark theme the settings spinbox arrows are pinned to the theme text color so they stay visible (B1); it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` hosts the Tkinter GUI shell, while its settings window, item rows, theme engine, edit dialog, placeholders, dialog helpers, controller, and visible-items filter now live in dedicated modules. All 346 tests pass.

## Active Task
**B2 — Spinbox arrows disappear on hover (dark theme)** (size S, branch `implementer/b2-spinbox-hover`)

- **Scope:** `implementer/src/todo_md/theme.py` (`apply_theme`) + extend `implementer/src/tests/test_gui_spinbox_arrows.py`. No other production files.
- **Bug (architect-verified from user screenshot + Tk 9 source/library analysis):** on the clam-fallback path, `TSpinbox` *inherits* `TCombobox`'s `-background` state map (`active/pressed → #eeebe7`, the theme "lighter" color — `ttk::style lookup TSpinbox -background {active}` returns `#eeebe7`; the clam `Arrow` C element draws its button box from `-background`). On hover the arrow buttons fill light while B1's `arrowcolor` chevron stays light → invisible.
- **Fix:** in the clam path of `apply_theme()`, after the B1 `arrowcolor` configure, add `style.map("TSpinbox", background=[("active", btn_active),("pressed", btn_active)], arrowcolor=[("active", fg),("pressed", fg),("disabled", fg_disabled)])` so both interactive states keep a dark button fill with a light chevron in dark mode (consistent values in light; `btn_active`/`fg`/`fg_disabled` already exist in `palette_for`). Do NOT map `fieldbackground`/`bordercolor` (inherited entries must stay).
- **Acceptance criteria (from `implementer/src/`):**
  1. Dark theme: `root.tk.call("ttk::style","lookup","TSpinbox","-background","active")` equals the dark `btn_active` (#484848); the `-arrowcolor` active lookup equals `fg`; luminance(arrowcolor) − luminance(background) in the active state > 0.35 (dark) and the light theme's active lookups use its `btn_active` with `fg` black.
  2. Inherited `fieldbackground`/`bordercolor` maps unchanged (readonly/disabled/focus entries still resolve as before).
  3. Native-path guard: skip when `app._palette is None`.
- **Tests:** extend `tests/test_gui_spinbox_arrows.py` (parametrized dark/light) with the state-map assertions above; do not touch other test files.
- **Test commands:** `.venv/bin/python -m pytest tests/test_gui_spinbox_arrows.py -v` then `.venv/bin/python -m pytest tests -v` (baseline 346 pass / 2 skip).

**Prompt for Implementer:**
  You are assigned task **B2 — Spinbox arrows disappear on hover** on branch `implementer/b2-spinbox-hover` (base and integration branch: `main`).
  1. First tool call: run `../architect/tools/implementer-run.sh` (no arguments) from your workspace. Use this wrapper for ALL subsequent Bash commands and follow the Mandatory Execution Clock phase rules.
  2. Verify you are on branch `implementer/b2-spinbox-hover` and inspect the working tree before editing. Restrict every change to `implementer/`; NEVER touch `architect/` or repository-root files.
  3. Bug (architect-verified): on the clam-fallback theme, hovering the settings spinbox up/down buttons makes the arrows disappear. Root cause: Tk 9's C `Arrow` element draws its button box from the `-background` element option (a 3D fill) and the chevron from `-arrowcolor`; `TSpinbox` *inherits* `TCombobox`'s style maps, and the clam theme maps `-background` to the theme's light "-lighter" color in the `active` state — confirmed by `ttk::style lookup TSpinbox -background {active}` returning `#eeebe7` in dark mode, so the light chevron on the light hover fill is invisible. B1 (already merged) set the *base* `arrowcolor`; B2 fixes the *state maps*. For rationale see the `theme.py` entry in `architect/DESIGN.md`.
  4. Implement in `todo_md/theme.py` `apply_theme()` (clam-fallback path, right after the existing `style.configure("TSpinbox", arrowcolor=fg)` line): `style.map("TSpinbox", background=[("active", btn_active), ("pressed", btn_active)], arrowcolor=[("active", fg), ("pressed", fg), ("disabled", fg_disabled)])` with a comment explaining the inherited TCombobox `-background` map. `btn_active`, `fg`, `fg_disabled` already exist in `palette_for`. Do not map `fieldbackground`/`bordercolor`; do not alter `settings_window.py` or anything else.
  5. Extend `tests/test_gui_spinbox_arrows.py` (parametrized dark/light, same guard pattern: skip when `app._palette is None`) asserting: the active-state lookups of `-background` and `-arrowcolor` equal the palette `btn_active`/`fg` (call the Tcl command directly via `root.tk.call("ttk::style","lookup","TSpinbox","-background","active")` — note: `ttk.Style.lookup` mishandles the state argument, so do not use it for state lookups), the active-state luminance contrast between the two > 0.35, and that the inherited `-fieldbackground` map still resolves its `readonly`/`disabled` entry to a non-None value.
  6. Run from `implementer/src/`: `.venv/bin/python -m pytest tests/test_gui_spinbox_arrows.py -v` then the full suite `.venv/bin/python -m pytest tests -v` (baseline 346 passed, 2 skipped — no failures allowed).
  7. Commit completed work on the current branch (if the pre-commit hook auto-bumps `src/todo_md/VERSION`, include it). NEVER create/switch/merge/rebase/rename/delete/push branches; committing to `main` is forbidden; no destructive working-tree operations.
  8. Handoff: report RESULT, branch name, commit hash, tests run with outcomes, and any blockers.

## Queue
- **Backlog (non-blocking):** `TodoApp` still builds the sidebar (listbox, entries, buttons) and owns the edit-dialog open/save flow in `_build_ui`/`_open_edit_dialog`; extract to dedicated modules if `app.py` grows again.

## Active Blockers
None.

## Recently Completed
- B1 — Dark-theme spinbox arrows: `apply_theme` pins `TSpinbox -arrowcolor` to palette fg (Tk 9 C Arrow element otherwise defaults near-black); new `test_gui_spinbox_arrows.py`: DONE (Implementer commit eb3cd40).
- R9 — Remove both compat shims: `dock_icon_path` canonical in `dialogs.py` + `apply_dock_icon(root, icon_path)` param, `relocate_lists` called directly in controller, authorized 2-line test repatch: DONE (Implementer commit 6d81255).
- R8 — Final complexity pass: no `nonlocal` in controller, row rebuild moved to `item_row.rebuild_rows`, compressed wrappers/slimmed `__init__`; app.py 713 → 589 lines: DONE (Implementer commit bd38aa1).
- R7 — Move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py` (re-exported by `app.py`; `relocate_lists` resolved via app for frozen-test compat): DONE (Implementer commit f4f87c3).
- R5 — Extract entry-placeholder mechanism into `todo_md/placeholders.py` (PlaceholderBinder) + `self._ph` holder: DONE (Implementer commit 8ff404b).
