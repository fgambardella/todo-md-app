# TASKS.md

## Project Goal

Build a macOS desktop TODO app in Python (stdlib only, no runtime dependencies). Every list is persisted as its own plain Markdown file using GitHub-flavored checkbox syntax — no database. The Tkinter GUI is layered above a headless, fully testable domain/persistence/controller core. Support light/dark themes with a persisted user setting and a sensible system default.

## Test Policy

- Framework: pytest (selected as the standard Python framework).
- Full suite, from `implementer/src`: `.venv/bin/python -m pytest tests -v`
- Targeted: `.venv/bin/python -m pytest tests/<file>.py -v`
- Gated: `RUN_BUILD_TESTS=1 .venv/bin/python -m pytest tests/test_build_script.py -v` (full build + launch); `RUN_RELEASE_TESTS=1 .venv/bin/python -m pytest tests/test_release_package.py -v` (full release packaging: build + zip assertions).
- GUI tests require a display (available on this Mac): destroy `root` in `finally`, call `root.update()` after building, probe effective colors via `winfo_rgb`. Headless tests must never launch the GUI.

## Current Implementation Summary

- Markdown persistence: each list stored as its own `.md` file with GFM checkboxes, atomic writes, filename-safe names.
- Domain layer: validated add/toggle/remove/rename of items with clear errors.
- Headless controller: create/delete lists, add/toggle/remove items; every mutation persisted immediately.
- GUI: list sidebar (create via button or Enter, delete), checkbutton item rows, add-item entry, per-item trash-icon delete; destructive actions gated by a Yes/No popup.
- Both input fields (new list, new item) show muted-gray placeholder hints: cleared on focus-in, counted as empty on submit.
- Readability: item label colors adapt to background luminance in both themes; entry fills follow the palette (slightly lighter than list background in dark mode).
- Versioning: version lives in `todo_md/VERSION`, auto-incremented (patch) by a pre-commit hook; GUI shows it as a small low-contrast bottom-right badge that adapts on theme toggle.
- Dock icon: macOS startup sets a custom dock icon from a bundled PNG (JPEG source kept); missing/unsupported icons fail soft.
- Settings: headless `settings.json` core (theme light/dark/system — system detected live at startup, never persisted; lists_dir; completed-visible count) with legacy-compat load and atomic save; theme switcher flips the whole window including item rows; buttons use darker hover/press fills; stored in `~/.todo-md-app/config/`.
- Build: `scripts/build_app.sh` (PyInstaller, arm64) builds a self-contained launchable `dist/todo-md.app` with post-build smoke check and custom Finder icon (`.icns` generated at build time); PyInstaller is dev-only (runtime stays stdlib-only).
- Release packaging: `scripts/release_package.sh` builds, validates strict `X.Y.Z`, and zips the bundle as `dist/todo-md-<version>-arm64.zip` (app at zip root, no `__MACOSX`); gated end-to-end test.

## Active Task

None.

## Queue

- **Task 33 (S)** — Startup wiring for user settings: `run()` loads settings from a FIXED config dir `~/.todo-md-app/config/` (config dir must no longer be derived from the lists dir, otherwise changing the lists path would move the settings file); data dir derived from `settings.lists_dir` (default `~/.todo-md-app/lists/`, created on demand); list-dir location in the GUI/README wording unaffected; headless tests incl. temp config/data dirs.
- **Task 34 (S)** — Completed-items display filter: controller/view-model logic `visible_items(items, completed_visible)` — when completed count exceeds N, hide the excess starting from the top of the list (bottom-most completed stay); 0 hides all completed; storage on disk always keeps every item. Headless tests only; no GUI change.
- **Task 35 (M)** — Settings window (break down into sequential micro-tasks):
  - 35a: `"Settings"` button in the main window opening a Toplevel with: lists-folder row (Entry + `Browse…` via `filedialog.askdirectory` + `Reset to default`), theme radiobuttons (System default / Light / Dark), completed-visible Spinbox (0–999, 0 = hide all), Save/Cancel; window pre-filled from current settings; GUI tests for construction and pre-fill.
  - 35b: Save flow — persist via `save_settings`; on Save re-apply: theme (`_apply_theme` + `_refresh_items`), lists dir (relocation per Task 36 + sidebar reload), completed filter (items refresh); Cancel = full no-op; GUI tests incl. live theme change and sidebar reload after dir change.
- **Task 36 (M)** — Lists-dir relocation with user-decided file move (break down into sequential micro-tasks):
  - 36a: headless relocation (controller/storage): `relocate_lists(old_dir, new_dir, move)` — new dir created on demand; `move=True` moves every `.md` from old to new (non-`.md` files untouched); `move=False` leaves them in place; raises a clear error if the new dir already contains `.md` files (no silent overwrite); headless tests.
  - 36b: GUI + validation — on Save with a changed lists dir, show a popup only when the old dir contains at least one list: `messagebox.askyesnocancel` with text “You are about to change the directory where your lists are stored from 'old' to 'new' but there are already lists in it.” (Yes = proceed and move; No = proceed without moving; Cancel = keep old dir, other settings still apply); no popup when old dir is empty — dedicated GUI test required; lists path is an existing file, target dir already has lists, or invalid completed-visible → error dialog, that change not persisted; empty path entry → default.

## Active Blockers

None.

## Recently Completed

- Task 32 — settings core: `todo_md/settings.py` (`Settings` dataclass, legacy-compat `load_settings`, validating atomic `save_settings`, `resolve_theme` with live never-persisted system detection); `theme.py` removed, GUI/tests migrated; verified 101 passed/2 skipped (b0c3be2).
- Task 31b — v0.2.1 release cut (Architect-direct per user): VERSION commit lands at `0.2.1` (ecd4eb7); package rebuilt on `main` → `dist/todo-md-0.2.1-arm64.zip` (sha256 2ba5021d…); tagged `v0.2.1`, pushed per explicit request; user attaches zip in GitHub web release UI.
- Task 31a — one-command release packaging: `scripts/release_package.sh` (build → strict X.Y.Z validation → ditto zip, app at zip root) + static/gated tests; verified 90 passed/2 skipped + `RUN_RELEASE_TESTS=1` 5/5 (3be777e, merged c35805c).
- Task 30 — pre-sized trash icon: 18×18 RGBA `assets/trash_18.png` (sips from the 512×512 source, which is kept); GUI loads it directly, `.subsample(28)` gone; 2 GUI tests updated; verified 86/1-skip (d2f6964).
- Task 29 — explicit `TodoController.data_dir` (optional override, defaults to store's); `TodoApp` derives from the controller, no more store reach-in; 2 new headless tests; verified 86/1-skip (790ee86).