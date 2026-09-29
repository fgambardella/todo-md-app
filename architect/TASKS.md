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
- Versioning: version lives in `todo_md/VERSION`, auto-incremented (patch) by a pre-commit hook; shown as a low-contrast bottom-right badge that adapts on theme toggle.
- Dock icon: macOS sets a custom dock icon at startup (bundled PNG; JPEG source kept); fails soft.
- Settings: headless `settings.json` core (theme light/dark/system, detected live and never persisted; lists_dir; completed-visible count), legacy-compat load, atomic save; startup honors a saved lists dir; config dir fixed at `~/.todo-md-app/config/`; theme switcher flips the whole window; darker hover/press button fills; item view hides completed beyond the count (top-first, 0 hides all); settings Toplevel pre-filled, Save/Cancel stubs.
- Build: `scripts/build_app.sh` (PyInstaller, dev-only) builds a launchable `dist/todo-md.app` with post-build smoke check and custom Finder icon (`.icns` at build time); runtime stays stdlib-only.
- Release packaging: `scripts/release_package.sh` builds, validates strict `X.Y.Z`, and zips the bundle as `dist/todo-md-<version>-arm64.zip` (app at zip root, no `__MACOSX`); gated end-to-end test.

## Active Task

- **Task 35b (S, micro of 35-M)** — Settings window Save/Cancel behavior. *Second recovery after timeout; implementation verified complete, only the commit remains.*
  - Branch: `implementer/task-35b-settings-save` (base `main`).
  - Latest state: no child commit exists. The second run (also timed out, uncommitted) left **complete, Architect-verified** working-tree work: `implementer/src/todo_md/app.py` (`_valid_lists_dir_path`; `_settings_on_save` validation, full-payload `save_settings`, default-dir entry normalized to `lists_dir: null`, live `resolve_theme` → `_apply_theme` → `_refresh_items`; Cancel close-only) and `implementer/src/tests/test_gui_settings.py` (all five required GUI tests; 11 passed). Architect independently ran the full suite: 127 passed / 2 skipped; no boundary violations, no file outside `implementer/src` touched.
  - Remaining scope (micro-task): verify state and **commit** the finished working-tree changes on this branch. No new code.
  - Prompt:
    - You are the Implementer. Work ONLY on branch `implementer/task-35b-settings-save`; base and integration branch is `main`. From `implementer/` first verify `git branch --show-current` and `git status --short`. Boundaries: only files under `implementer/`; never touch `architect/` or the repo root; never modify `implementer/src/AGENTS.md`; no branch create/switch/merge/rename/delete/push; no commit to `main`; no broad staging and no destructive working-tree operations (no reset/clean/stash/checkout of paths).
    - The task 35b work is already complete in the working tree (a prior run timed out before committing): `src/todo_md/app.py` (Save/Cancel implementation) and `src/tests/test_gui_settings.py` (five GUI tests). Do **not** write or edit code. Verify state: from `implementer/src` run `.venv/bin/python -m pytest tests/test_gui_settings.py -v` then `.venv/bin/python -m pytest tests -v` (expect all passing; the 2 gated integration tests may be skipped). If the suite is green, stage exactly `src/todo_md/app.py` and `src/tests/test_gui_settings.py` and commit them on the branch with a clear message describing task 35b (Save validation + full-payload persistence + live theme/filter re-apply, Cancel full no-op, GUI tests); the pre-commit hook may additionally stage the auto `VERSION` bump, which is expected. If the suite is red, do NOT commit; hand off RESULT: FAILURE with a concise diagnosis.
    - Acceptance criteria: one commit on the branch containing the implementation changes (plus the hook-staged VERSION bump); full suite green at that commit; nothing else changed by the commit.
    - Hand off with RESULT / BRANCH / COMMIT.

## Queue

- **Task 36 (M)** — Lists-dir relocation with user-decided file move (break down into sequential micro-tasks):
  - 36a: headless relocation (controller/storage): `relocate_lists(old_dir, new_dir, move)` — new dir created on demand; `move=True` moves every `.md` from old to new (non-`.md` files untouched); `move=False` leaves them in place; raises a clear error if the new dir already contains `.md` files (no silent overwrite); headless tests.
  - 36b: GUI + validation — on Save with a changed lists dir, show a popup only when the old dir contains at least one list: `messagebox.askyesnocancel` with text “You are about to change the directory where your lists are stored from 'old' to 'new' but there are already lists in it.” (Yes = proceed and move; No = proceed without moving; Cancel = keep old dir, other settings still apply); no popup when old dir is empty — dedicated GUI test required; lists path is an existing file, target dir already has lists, or invalid completed-visible → error dialog, that change not persisted; empty path entry → default.

## Active Blockers

None.

## Recently Completed

- Task 35a — settings window construction: main-window `Settings` button opens a single-instance pre-filled Toplevel (lists-folder Entry + Browse/Reset, theme radiobuttons, completed-visible Spinbox, Save/Cancel stubs writing nothing); verified 123 passed/2 skipped (895bfb5).
- Task 34 — completed-items display filter: pure `visible_items(items, completed_visible)` (top-first hiding, 0 hides all, order preserved, storage untouched) + GUI row wiring via id-based visibility; recovered from committed checkpoint after timeout; verified 116 passed/2 skipped (bf3ab84, merged fcb7abb).
- Task 33 — startup settings wiring: fixed config dir `~/.todo-md-app/config` (never derived from the lists dir, overridable for tests), headless `startup_dirs` derives data dir from saved `lists_dir` (default created on demand), store/controller built with it; verified 106 passed/2 skipped (998778c, merged 25f743a).
- Task 32 — settings core: `todo_md/settings.py` (`Settings` dataclass, legacy-compat `load_settings`, validating atomic `save_settings`, `resolve_theme` with live never-persisted system detection); `theme.py` removed, GUI/tests migrated; verified 101 passed/2 skipped (b0c3be2, merged adbedc4).
- Task 31b — v0.2.1 release cut (Architect-direct per user): VERSION commit lands at `0.2.1` (ecd4eb7); package rebuilt on `main` → `dist/todo-md-0.2.1-arm64.zip` (sha256 2ba5021d…); tagged `v0.2.1`, pushed per explicit request; user attaches zip in GitHub web release UI.