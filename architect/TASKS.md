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
- Both input fields show muted-gray placeholder hints: cleared on focus-in, counted as empty on submit.
- Readability: item label colors adapt to background luminance in both themes; entry fills follow the palette.
- Versioning: `todo_md/VERSION` auto-incremented (patch) by a pre-commit hook; shown as a low-contrast bottom-right badge that adapts on theme toggle.
- Dock icon: custom macOS dock icon at startup (bundled PNG; JPEG source kept); fails soft.
- Settings: headless `settings.json` core (theme, lists_dir, completed-visible), legacy-compat load, atomic save; system theme detected live, never persisted; startup honors a saved lists dir; config dir fixed at `~/.todo-md-app/config/`; theme switcher flips the whole window; darker hover/press button fills; item view hides completed beyond the count (top-first, 0 hides all); settings window: apply-on-Save (validate, persist full payload, default dir → null, live theme/filter re-apply), Cancel no-op; new lists dir effective at next startup.
- Build: `scripts/build_app.sh` (PyInstaller, dev-only) builds a launchable `dist/todo-md.app` with post-build smoke check and custom Finder icon (`.icns` at build time); runtime stays stdlib-only.
- Release packaging: `scripts/release_package.sh` zips the built bundle as `dist/todo-md-<version>-arm64.zip` (app at zip root, no `__MACOSX`); gated end-to-end test.

## Active Task

- **Task 36a (S, first micro of 36-M)** — Headless lists-dir relocation.
  - Branch: `implementer/task-36a-relocate-headless` (base `main`).
  - Prompt:
    - You are the Implementer. Work ONLY on branch `implementer/task-36a-relocate-headless`; base and integration branch is `main`. From `implementer/` first verify `git branch --show-current` and `git status --short`. Boundaries: only files under `implementer/`; never touch `architect/` or the repo root; never modify `implementer/src/AGENTS.md`; no branch create/switch/merge/rename/delete/push; no commit to `main`; no destructive working-tree operations.
    - Read `architect/DESIGN.md` (Persistence, Settings config, Data Models & Flow), `src/todo_md/storage.py`, `src/todo_md/app.py` (`TodoController`), and `src/tests/test_storage.py` / `test_controller.py` for patterns.
    - Scope (headless only — no tkinter, no GUI wiring, no Save-handler changes; GUI wiring is the follow-up task): add a `relocate_lists(old_dir, new_dir, move)` capability in the headless layer (storage or controller, your call — keep it tkinter-free and importable for tests): (1) create `new_dir` on demand (including parents); (2) `move=True`: move every `*.md` file from `old_dir` to `new_dir` (e.g. `os.replace`); non-`.md` files in `old_dir` stay untouched; (3) `move=False`: lists stay in `old_dir`, `new_dir` created empty; (4) raise a clear error (never silent overwrite) if `new_dir` already exists and contains at least one `.md` file; (5) empty or missing `old_dir` with `move=True` is a no-op success (new dir still created).
    - Tests (headless, temp dirs): `move=True` relocates `.md` files and leaves a stray non-`.md` file behind; `move=False` leaves all lists in place and creates the new dir; a target dir already containing a `.md` raises the clear error; empty old dir succeeds.
    - Acceptance criteria: relocation is headless and unit-testable; all four behaviors covered; full suite green.
    - Commands (from `implementer/src`): `.venv/bin/python -m pytest tests -v` (no failures/errors; 2 gated integration tests may stay skipped).
    - Commit finished work on the branch; hand off with RESULT / BRANCH / COMMIT; if blocked, commit a `RESULT: FAILURE` checkpoint with the blocker.

## Queue

- **Task 36b (later micro of 36-M, after 36a is merged)** — GUI wiring of lists-dir relocation: on Save with a changed lists dir, show a popup only when the old dir contains at least one list: `messagebox.askyesnocancel` with text "You are about to change the directory where your lists are stored from '<old>' to '<new>' but there are already lists in it." (Yes = proceed and move; No = proceed without moving; Cancel = keep old dir, other settings still apply); no popup when old dir is empty — dedicated GUI test required; target dir already has lists, or invalid completed-visible → error dialog, that change not persisted; empty path entry = default dir.

## Active Blockers

None.

## Recently Completed

- Task 35b — settings Save/Cancel: Save validates (dir / 0–999 / theme), persists full payload (default-dir → null), live re-applies theme + completed filter; Cancel full no-op; 5 GUI tests; recovered across two Implementer timeouts (Architect verified uncommitted tree, then commit-only micro-task); verified 127 passed/2 skipped (9c45b49).
- Task 35a — settings window construction: main-window `Settings` button opens a single-instance pre-filled Toplevel (lists-folder Entry + Browse/Reset, theme radiobuttons, completed-visible Spinbox, Save/Cancel stubs writing nothing); verified 123 passed/2 skipped (895bfb5).
- Task 34 — completed-items display filter: pure `visible_items(items, completed_visible)` (top-first hiding, 0 hides all, order preserved, storage untouched) + GUI row wiring via id-based visibility; recovered from committed checkpoint after timeout; verified 116 passed/2 skipped (bf3ab84, merged fcb7abb).
- Task 33 — startup settings wiring: fixed config dir `~/.todo-md-app/config` (never derived from the lists dir, overridable for tests), headless `startup_dirs` derives data dir from saved `lists_dir` (default created on demand), store/controller built with it; verified 106 passed/2 skipped (998778c, merged 25f743a).
- Task 32 — settings core: `todo_md/settings.py` (`Settings` dataclass, legacy-compat `load_settings`, validating atomic `save_settings`, `resolve_theme` with live never-persisted system detection); `theme.py` removed, GUI/tests migrated; verified 101 passed/2 skipped (b0c3be2, merged adbedc4).