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
- Theming: persisted light/dark setting with system-default detection on first start; switcher flips the whole window including item rows at startup and on toggle; buttons use darker hover/press fills; stored in `~/.todo-md-app/config/`.
- Versioning: version lives in `todo_md/VERSION`, auto-incremented (patch) by a pre-commit hook; GUI shows it as a small low-contrast bottom-right badge that adapts on theme toggle.
- Dock icon: on macOS a custom dock icon is set at startup from a bundled PNG (JPEG source kept); missing/unsupported icons fail soft so startup is unaffected.
- Build: `scripts/build_app.sh` (PyInstaller, arm64) builds a self-contained launchable `dist/todo-md.app` with post-build smoke check and custom Finder icon (`.icns` generated at build time); PyInstaller is dev-only (runtime stays stdlib-only).
- Release packaging: `scripts/release_package.sh` builds, validates strict `X.Y.Z`, and zips the bundle as `dist/todo-md-<version>-arm64.zip` (app at zip root, no `__MACOSX`); gated end-to-end test.

## Active Task

**Task 31b (S) — cut the v0.2.1 release package**
Branch: `implementer/task-31b-release-v0-2` (base: `main`)
Executor: Architect directly (explicit user instruction: trivial version bump, no delegation needed). Same branch/verify/merge discipline applies.

Scope:
- Set `implementer/src/todo_md/VERSION` to `0.2.0`; the pre-commit hook bumps the patch, so the single commit lands at `0.2.1` (the accepted release version). No other file changes.
- Run `bash scripts/release_package.sh` from `implementer/src` → `dist/todo-md-0.2.1-arm64.zip`.
- After merge: Architect rebuilds the package on `main`, tags `v0.2.1`, pushes `main` + tag (explicit user request); user attaches the zip as an asset in the GitHub web release UI.

Acceptance criteria:
1. Exactly one commit on the branch touching only `implementer/src/todo_md/VERSION`; committed value is `0.2.1`.
2. Script run produces `dist/todo-md-0.2.1-arm64.zip`; `unzip -l` shows `todo-md.app` at the zip root, no `__MACOSX`; path, size, SHA-256 printed.
3. Full suite green from `implementer/src` (90 passed / 2 skipped).
4. `git status --short` clean; no changes outside `implementer/src/todo_md/VERSION`.

Test commands (from `implementer/src`):
- `bash scripts/release_package.sh`
- `.venv/bin/python -m pytest tests -v`

## Queue

None.

## Active Blockers

None.

## Recently Completed

- Task 31a — one-command release packaging: `scripts/release_package.sh` (build → strict X.Y.Z validation → ditto zip, app at zip root) + static/gated tests; verified 90 passed/2 skipped + `RUN_RELEASE_TESTS=1` 5/5 (3be777e, merged c35805c).
- Task 30 — pre-sized trash icon: 18×18 RGBA `assets/trash_18.png` (sips from the 512×512 source, which is kept); GUI loads it directly, `.subsample(28)` gone; 2 GUI tests updated; verified 86/1-skip (d2f6964).
- Task 29 — explicit `TodoController.data_dir` (optional override, defaults to store's); `TodoApp` derives from the controller, no more store reach-in; 2 new headless tests; verified 86/1-skip (790ee86).
- Task 28 — debt triage and reduction plan (Architect): 4 debt items analysed; 2 accepted as constraints with rationale in `decisions/2026-09-27-debt-triage.md`; 2 executed as tasks 29/30.
- Task 27 — app bundle Finder icon: `build_app.sh` generates `build/todo_md.icns` from `dock_icon.png` via sips/iconutil and passes `--icon` to PyInstaller; static test extended; verified 84/1-skip + real bundle with valid `.icns`/`CFBundleIconFile` (4c09751).