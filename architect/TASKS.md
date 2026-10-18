# Tasks

## Project Goal
macOS desktop TODO app (Python 3, stdlib only): each list is one Markdown file with GFM checkboxes (text + optional `<!-- Description: -->` line). Tkinter GUI with list sidebar, item rows (toggle/edit/trash), completed-item display filter, modal edit dialog, settings window (theme, completed cap, portable lists dir), persisted settings, auto-save. Headless-safe core (models/storage/settings) for testability.

## Test Policy
- Framework: `pytest`.
- Full suite: `(cd implementer/src && .venv/bin/python -m pytest tests -v)` (346 pass, 2 skip, ~26s baseline).
- Targeted: `.venv/bin/python -m pytest tests/<file> -v` from `implementer/src/`.
- Refactor series R1-R8: **test files are frozen** — implementers may not add, modify, or remove any test; every task is verified against the existing suite only.

## Current Implementation Summary
A working macOS TODO application: users create, rename, and delete lists stored as one Markdown file per list; each item is a GFM checkbox with optional text and an HTML-comment description. The GUI provides a list sidebar, per-item toggle/edit/trash rows, and a completed-item display filter; a modal dialog edits text and description together, and double-click opens the same dialog. A settings window offers light/dark/system theme choice (system reacts to macOS appearance changes), a completed-item cap, and an optional portable lists directory; in the dark theme the settings spinbox arrows stay visible in normal, hover, and disabled states (B1/B2); it validates directories with clear error messages and persists choices immediately. Settings live in the fixed config dir, independent of the data dir. A themed dock icon is applied when available. The core (models, storage, settings, controller) is headless and importable without a display; `app.py` hosts the Tkinter GUI shell, while its settings window, item rows, theme engine, edit dialog, placeholders, dialog helpers, controller, and visible-items filter now live in dedicated modules. All 346 tests pass.

## Active Task
**B3 — Spinbox hover too subtle in dark theme** (size S, branch `implementer/b3-spinbox-hover-contrast`)

- **Bug:** B2 pinned the hover fill to the app's button convention `btn_active` (`#2e2e2e`), which is only ~4% luminance away from the normal arrow-box fill (`#383838`) — hover barely perceptible (user-observed).
- **Fix:** add palette key `"spin_hover": "#565656" if dark else "#d0d0d0"` in `palette_for` (light value equals today's `btn_active` → light theme visually unchanged) and point the existing `TSpinbox` `style.map` `background` entries (active/pressed) at `spin_hover` instead of `btn_active`. `btn_active` stays for buttons. Chevron mapping unchanged.
- **Acceptance (from `implementer/src/`):** dark active-state `-background` lookup == `#565656` and `|lum(normal bg) − lum(active bg)| > 0.08`; arrow/background active-state contrast still > 0.35; light active lookup == `#d0d0d0`; inherited `fieldbackground` map intact.
- **Tests:** extend `tests/test_gui_spinbox_arrows.py` with the above (same guard pattern); no other test files.
- **Test commands:** `.venv/bin/python -m pytest tests/test_gui_spinbox_arrows.py -v` then full `.venv/bin/python -m pytest tests -v` (346 pass / 2 skip baseline).

**Prompt for Implementer:**
  You are assigned task **B3 — Spinbox hover too subtle in dark theme** on branch `implementer/b3-spinbox-hover-contrast` (base and integration branch: `main`).
  1. First tool call: run `../architect/tools/implementer-run.sh` (no arguments) from your workspace. Use this wrapper for ALL subsequent Bash commands and follow the Mandatory Execution Clock phase rules.
  2. Verify you are on branch `implementer/b3-spinbox-hover-contrast` and inspect the working tree before editing. Restrict every change to `implementer/`; NEVER touch `architect/` or repository-root files.
  3. Context (architect-verified): B2 (merged) made the spinbox hover work but pinned it to the app's button-hover color `btn_active` (`#2e2e2e` dark), which sits only ~4% luminance away from the normal arrow-box fill `#383838`, so the user perceives no hover. Fix: a dedicated, clearly lighter hover fill for the spinbox only.
  4. Implement in `implementer/src/todo_md/theme.py`: add `"spin_hover": "#565656" if theme == "dark" else "#d0d0d0"` to `palette_for` (comment: dedicated spinbox hover fill — deliberately more contrasting than `btn_active`); in `apply_theme()` read `spin_hover = app._palette["spin_hover"]` and change the existing `style.map("TSpinbox", ...)` `background` entries from `btn_active` to `spin_hover` (keep active and pressed; keep the `arrowcolor` mapping exactly as is). Do not touch `settings_window.py` or other styles.
  5. Extend `implementer/src/tests/test_gui_spinbox_arrows.py` (parametrized dark/light, skip guard `app._palette is None`, state lookups via `root.tk.call("ttk::style","lookup",...)`) asserting: the active-state `-background` equals `app._palette["spin_hover"]`; the absolute luminance difference between the normal-state `-background` and the active-state `-background` is > 0.08 (reuse `lum()`); the arrow/background active-state contrast remains > 0.35; the inherited `-fieldbackground` readonly/disabled entries still resolve non-empty.
  6. Run from `implementer/src/`: `.venv/bin/python -m pytest tests/test_gui_spinbox_arrows.py -v` then `.venv/bin/python -m pytest tests -v` (baseline 346 passed, 2 skipped — no failures).
  7. Commit completed work on the current branch (include the hook's `src/todo_md/VERSION` bump if any). NEVER create/switch/merge/rebase/rename/delete/push branches; committing to `main` is forbidden; no destructive working-tree operations.
  8. Handoff: report RESULT, branch name, commit hash, tests run with outcomes, and any blockers.

## Queue
- **Backlog (non-blocking):** `TodoApp` still builds the sidebar (listbox, entries, buttons) and owns the edit-dialog open/save flow in `_build_ui`/`_open_edit_dialog`; extract to dedicated modules if `app.py` grows again.

## Active Blockers
None.

## Recently Completed
- B2 — Spinbox hover: `TSpinbox` state maps pin `-background`/`-arrowcolor` (active/pressed → palette `btn_active`/`fg`, disabled → `fg_disabled`); `btn_active` promoted into `palette_for`: DONE (Implementer commit cb53a91).
- B1 — Dark-theme spinbox arrows: `apply_theme` pins `TSpinbox -arrowcolor` to palette fg (Tk 9 C Arrow element otherwise defaults near-black); new `test_gui_spinbox_arrows.py`: DONE (Implementer commit eb3cd40).
- R9 — Remove both compat shims: `dock_icon_path` canonical in `dialogs.py` + `apply_dock_icon(root, icon_path)` param, `relocate_lists` called directly in controller, authorized 2-line test repatch: DONE (Implementer commit 6d81255).
- R8 — Final complexity pass: no `nonlocal` in controller, row rebuild moved to `item_row.rebuild_rows`, compressed wrappers/slimmed `__init__`; app.py 713 → 589 lines: DONE (Implementer commit bd38aa1).
- R7 — Move `TodoController` to `todo_md/controller.py` and `visible_items` to `todo_md/models.py` (re-exported by `app.py`; `relocate_lists` resolved via app for frozen-test compat): DONE (Implementer commit f4f87c3).
