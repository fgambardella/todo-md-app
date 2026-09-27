# TASKS.md

## Project Goal

Build a macOS desktop TODO app in Python (stdlib only, no runtime dependencies). Every list is persisted as its own plain Markdown file using GitHub-flavored checkbox syntax — no database. The Tkinter GUI is layered above a headless, fully testable domain/persistence/controller core. Support light/dark themes with a persisted user setting and a sensible system default.

## Test Policy

- Framework: pytest (selected as the standard Python framework).
- Full suite, from `implementer/src`: `.venv/bin/python -m pytest tests -v`
- Targeted: `.venv/bin/python -m pytest tests/<file>.py -v`
- Gated: `RUN_BUILD_TESTS=1 .venv/bin/python -m pytest tests/test_build_script.py -v` enables the full build+launch integration test (skipped by default).
- GUI tests require a display (available on this Mac): destroy `root` in `finally`, call `root.update()` after building, probe effective colors via `winfo_rgb`. Headless tests must never launch the GUI.

## Current Implementation Summary

- Markdown persistence: each list stored as its own `.md` file with GFM checkboxes, atomic writes, filename-safe names.
- Domain layer: validated add/toggle/remove/rename of items with clear errors.
- Headless controller: create/delete lists, add/toggle/remove items; every mutation persisted immediately.
- GUI: list sidebar (create via button or Enter, delete), checkbutton item rows, add-item entry, per-item trash-icon delete; destructive actions gated by a Yes/No popup.
- Both input fields (new list, new item) show muted-gray placeholder hints: cleared on focus-in, restored only when the entry has genuinely lost focus, counted as empty on submit.
- Readability: item label colors adapt to background luminance in both themes; entry fills follow the palette (slightly lighter than list background in dark mode).
- Theming: persisted light/dark setting with system-default detection on first start; switcher applied at startup and on toggle; stored in `~/.todo-md-app/config/`.
- Theme switch flips the whole window including item rows; buttons use darker hover/press fills.
- Versioning: version lives in `todo_md/VERSION`, auto-incremented (patch) by a pre-commit hook; GUI shows it as a small low-contrast bottom-right badge that adapts on theme toggle.
- Dock icon: on macOS a custom dock icon is set at startup from a bundled PNG (JPEG source kept); missing/unsupported icons fail soft so startup is unaffected.
- Build: `scripts/build_app.sh` (PyInstaller, arm64) builds a self-contained launchable `dist/todo-md.app` from `python -m todo_md` with post-build smoke check; the bundle carries a custom Finder icon (`.icns` generated at build time from the dock icon PNG); PyInstaller is dev-only (runtime stays stdlib-only).

## Active Task

**Task 31a (S) — `scripts/release_package.sh`: one-command release packaging**
Branch: `implementer/task-31a-release-package-script` (base: `main`)

Scope:
- New executable `implementer/src/scripts/release_package.sh` (`set -euo pipefail`, paths resolved relative to the script, same style as `scripts/build_app.sh`):
  1. Runs `scripts/build_app.sh` → fresh `dist/todo-md.app` (inherits arm64 host guard + launch smoke check).
  2. Reads `todo_md/VERSION`; validates `X.Y.Z`, exits with a clear error if malformed.
  3. Removes any pre-existing artifact, then zips the bundle with macOS `ditto -c -k --noextattr --noqtn` → `dist/todo-md-<version>-arm64.zip`, `todo-md.app` at the zip root (no wrapper dir, no `__MACOSX` entries).
  4. Prints zip path, size, `sha256`, and one line pointing to the README "Packaging and release" section for the GitHub upload.
- New `tests/test_release_package.py` mirroring the static + gated pattern of `tests/test_build_script.py`:
  - Static (always run): script exists + executable; `bash -n` OK; references `build_app.sh`, `VERSION`, `ditto`, `-arm64`.
  - Gated by `RUN_RELEASE_TESTS=1`: runs the script end-to-end; asserts zip name matches current VERSION; `unzip -l` shows `todo-md.app` at zip root, no `__MACOSX`; stdout contains sha256.
- Nothing is ever committed; artifacts stay in gitignored `dist/`.

Acceptance criteria:
1. Static tests pass; full suite green (existing 86 + new static pass; gated tests skipped by default).
2. `RUN_RELEASE_TESTS=1` run passes (real build + zip assertions).
3. `git status --short` clean after a run.
4. No changes outside `implementer/src/` (no root `README.md`, no `../architect/`, no `implementer/AGENTS.md`).

Test commands (from `implementer/src`):
- `.venv/bin/python -m pytest tests/test_release_package.py -v`
- `.venv/bin/python -m pytest tests -v`
- `RUN_RELEASE_TESTS=1 .venv/bin/python -m pytest tests/test_release_package.py -v` (slow: real build)

Implementer prompt:
"Assigned branch: `implementer/task-31a-release-package-script` (base and integration branch: `main`). Preflight: `git branch --show-current` must exactly match the assigned branch and `git status --short` must be clean; otherwise return RESULT: FAILURE before editing. Validate `../architect/DESIGN.md` per your protocol for context; mirror the conventions of `scripts/build_app.sh` and `tests/test_build_script.py`. Deliver: (1) executable `implementer/src/scripts/release_package.sh` (`set -euo pipefail`, all paths resolved relative to the script) that: runs `bash <scriptdir>/build_app.sh`; reads and validates `X.Y.Z` in `todo_md/VERSION` (clear error on malformed); removes any existing `dist/todo-md-<version>-arm64.zip`; zips `dist/todo-md.app` via `ditto -c -k --noextattr --noqtn` into `dist/todo-md-<version>-arm64.zip` with `todo-md.app` at the zip root; prints zip path, size, sha256, and a one-line pointer to the README 'Packaging and release' section for the GitHub upload. (2) `tests/test_release_package.py` mirroring `tests/test_build_script.py`: static tests (exists+executable, `bash -n`, references to `build_app.sh`/`VERSION`/`ditto`/`-arm64`) plus one end-to-end test gated by `RUN_RELEASE_TESTS=1` asserting the zip name matches the current VERSION, `todo-md.app` at zip root via `unzip -l`, no `__MACOSX` entries, sha256 in stdout. Constraints: modify only files under `implementer/src/`; never touch `implementer/AGENTS.md`, anything under `../architect/`, or repo-root files (including `README.md`); do not create/switch/merge/rename/delete branches, do not push, do not commit to `main`, no destructive git operations; stage only explicit paths you changed. Run from `implementer/src`: `.venv/bin/python -m pytest tests/test_release_package.py -v`, then `.venv/bin/python -m pytest tests -v`, then the gated `RUN_RELEASE_TESTS=1 .venv/bin/python -m pytest tests/test_release_package.py -v` (slow; last). Commit on the assigned branch with a concise message. Handoff: branch + commit hash, what changed, each test command + result, final `git status --short`, then `RESULT: SUCCESS` or `RESULT: FAILURE`."

## Queue

- **Task 31b (S) — cut the v0.2.x release package** (branch `implementer/task-31b-release-v0-2`): set `todo_md/VERSION` to `0.2.0` and commit (pre-commit hook bumps patch → commit lands at 0.2.1, the accepted release version); run `bash scripts/release_package.sh` → `dist/todo-md-0.2.1-arm64.zip`; no code changes beyond the VERSION bump; full suite + zip verification (name matches committed version, `todo-md.app` at zip root, sha256 reported). After merge: Architect rebuilds the package on `main`, tags `v0.2.1`, pushes `main` + tag (explicit user request), user attaches the zip in the GitHub web release.
- Release channel finding (web research, 2026-09-27): a GitHub Release is not a repo folder — the executable travels as a release asset attached in the web UI (or `gh`/Actions); pushing files into folders cannot create a downloadable release.
- Architect follow-up (not Implementer work): after 31a is verified and merged, add a "Packaging and release" section to the root `README.md` (script usage + GitHub web release steps) before the 31b promotion commit.

## Active Blockers

None.

## Recently Completed

- Task 30 — pre-sized trash icon: 18×18 RGBA `assets/trash_18.png` (sips from the 512×512 source, which is kept); GUI loads it directly, `.subsample(28)` gone; 2 GUI tests updated; verified 86/1-skip (d2f6964).
- Task 29 — explicit `TodoController.data_dir` (optional override, defaults to store's); `TodoApp` derives from the controller, no more store reach-in; 2 new headless tests; verified 86/1-skip (790ee86).
- Task 28 — debt triage and reduction plan (Architect): 4 debt items analysed; 2 accepted as constraints with rationale in `decisions/2026-09-27-debt-triage.md`; 2 executed as tasks 29/30.
- Task 27 — app bundle Finder icon: `build_app.sh` generates `build/todo_md.icns` from `dock_icon.png` via sips/iconutil and passes `--icon` to PyInstaller; static test extended; verified 84/1-skip + real bundle with valid `.icns`/`CFBundleIconFile` (4c09751).
- Task 26 — arm64 build script: `scripts/build_app.sh` (PyInstaller `--onedir --windowed` + `--collect-data`, arm64 guard, post-build launch smoke check) + pinned dev dep + gated build tests + README usage docs; verified (83 passed/1 skipped, real bundle built and launched from repo root), merged (011e048; README c9f0829).
