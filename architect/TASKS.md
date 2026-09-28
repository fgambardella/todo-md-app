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
- Readability: item label colors adapt to background luminance in both themes; entry fills follow the palette.
- Versioning: version lives in `todo_md/VERSION`, auto-incremented (patch) by a pre-commit hook; GUI shows it as a small low-contrast bottom-right badge that adapts on theme toggle.
- Dock icon: macOS sets a custom dock icon at startup from a bundled PNG (JPEG source kept); fails soft.
- Settings: headless `settings.json` core (theme light/dark/system, detected live and never persisted; lists_dir; completed-visible count), legacy-compat load, atomic save; startup honors a saved lists dir; config dir fixed at `~/.todo-md-app/config/`; theme switcher flips the whole window; darker hover/press button fills; item view hides completed beyond the count (top-first, 0 hides all).
- Build: `scripts/build_app.sh` (PyInstaller, dev-only) builds a launchable `dist/todo-md.app` with post-build smoke check and custom Finder icon (`.icns` at build time); runtime stays stdlib-only.
- Release packaging: `scripts/release_package.sh` builds, validates strict `X.Y.Z`, and zips the bundle as `dist/todo-md-<version>-arm64.zip` (app at zip root, no `__MACOSX`); gated end-to-end test.

## Active Task

- **Task 35a (S, micro of 35-M)** — Settings window (construction + pre-fill only).
  - Branch: `implementer/task-35a-settings-window` (base `main`).
  - Prompt:
    - You are the Implementer. Work ONLY on branch `implementer/task-35a-settings-window`; base and integration branch is `main`. From `implementer/` first verify `git branch --show-current` and `git status --short`. Boundaries: only files under `implementer/`; never touch `architect/` or the repo root; never modify `implementer/src/AGENTS.md`; no branch create/switch/merge/push; no commit to `main`; no destructive working-tree operations.
    - Read `architect/DESIGN.md` (Settings config, Presentation sections), `src/todo_md/app.py` (`TodoApp`, `run`, `startup_dirs`, `visible_items`), `src/todo_md/settings.py`, and the existing GUI tests.
    - Changes: add a `Settings` button in the main window (consistent with the existing button-based UI, NOT a native menu) that opens a Toplevel settings window containing: (1) lists-folder row: read-only-ish Entry showing the current effective data dir + `Browse…` button (`filedialog.askdirectory`) + `Reset to default` (sets Entry to `~/.todo-md-app/lists/`); (2) theme radiobuttons: `System default` / `Light` / `Dark`; (3) completed-visible Spinbox 0–999 (0 = hide all completed); (4) Save and Cancel buttons. The window is pre-filled from the current in-memory settings (`self.settings`); the effective lists dir shown is `self.settings.lists_dir or DEFAULT_DATA_DIR`. THIS TASK ONLY: construction + pre-fill + widget wiring of the entries to a small state holder (e.g. `StringVar`/`IntVar`); Save/Cancel may be no-op stubs or trivially wired — the real apply-on-Save logic is micro-task 35b. Keep the settings window code in `app.py` (or a small helper it uses) with no new dependencies.
    - Tests (GUI, Tk available in CI): settings button exists on the main window; opening it creates a Toplevel that is destroyed cleanly; pre-fill matches the current settings (custom lists_dir, theme `dark`, completed_visible e.g. 5); `Reset to default` sets the Entry to the default dir; radiobutton/Spinbox reflect the selected values. Use the existing GUI test patterns (temp dirs, overrides).
    - Acceptance criteria: settings window opens from a main-window button, is fully pre-filled, has all four control groups; no settings are written by this task alone; full suite green.
    - Commands (from `implementer/src`): `.venv/bin/python -m pytest tests -v` (no failures/errors; 2 gated integration tests may stay skipped).
    - Commit finished work (and stabilized partial work) on the branch; hand off with RESULT / BRANCH / COMMIT; if blocked, commit a `RESULT: FAILURE` checkpoint with the blocker.

## Queue

- **Task 35b (S, micro of 35-M)** — Settings window Save/Cancel behavior: on Save write settings via `save_settings` and re-apply the theme immediately (full-window re-paint as with the toggle); the new lists dir takes effect at next startup in this micro (runtime sidebar reload + relocation is Task 36); Cancel is a full no-op; Save validates the directory path (must be an absolute existing-or-creatable dir) with a clear error dialog otherwise. GUI tests for save/cancel validation paths.
- **Task 36 (M)** — Lists-dir relocation with user-decided file move (break down into sequential micro-tasks):
  - 36a: headless relocation (controller/storage): `relocate_lists(old_dir, new_dir, move)` — new dir created on demand; `move=True` moves every `.md` from old to new (non-`.md` files untouched); `move=False` leaves them in place; raises a clear error if the new dir already contains `.md` files (no silent overwrite); headless tests.
  - 36b: GUI + validation — on Save with a changed lists dir, show a popup only when the old dir contains at least one list: `messagebox.askyesnocancel` with text “You are about to change the directory where your lists are stored from 'old' to 'new' but there are already lists in it.” (Yes = proceed and move; No = proceed without moving; Cancel = keep old dir, other settings still apply); no popup when old dir is empty — dedicated GUI test required; lists path is an existing file, target dir already has lists, or invalid completed-visible → error dialog, that change not persisted; empty path entry → default.

## Active Blockers

None.

## Recently Completed

- Task 34 — completed-items display filter: pure `visible_items(items, completed_visible)` (top-first hiding, 0 hides all, order preserved, storage untouched) + GUI row wiring via id-based visibility; recovered from committed checkpoint after timeout; verified 116 passed/2 skipped (bf3ab84).
- Task 33 — startup settings wiring: fixed config dir `~/.todo-md-app/config` (never derived from the lists dir, overridable for tests), headless `startup_dirs` derives data dir from saved `lists_dir` (default created on demand), store/controller built with it; verified 106 passed/2 skipped (998778c, merged 25f743a).
- Task 32 — settings core: `todo_md/settings.py` (`Settings` dataclass, legacy-compat `load_settings`, validating atomic `save_settings`, `resolve_theme` with live never-persisted system detection); `theme.py` removed, GUI/tests migrated; verified 101 passed/2 skipped (b0c3be2, merged adbedc4).
- Task 31b — v0.2.1 release cut (Architect-direct per user): VERSION commit lands at `0.2.1` (ecd4eb7); package rebuilt on `main` → `dist/todo-md-0.2.1-arm64.zip` (sha256 2ba5021d…); tagged `v0.2.1`, pushed per explicit request; user attaches zip in GitHub web release UI.
- Task 30 — pre-sized trash icon: 18×18 RGBA `assets/trash_18.png` (sips from the 512×512 source, which is kept); GUI loads it directly, `.subsample(28)` gone; 2 GUI tests updated; verified 86/1-skip (d2f6964).