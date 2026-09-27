# TASKS.md

## Project Goal

Build a macOS desktop TODO app in Python (stdlib only, no runtime dependencies). Every list is persisted as its own plain Markdown file using GitHub-flavored checkbox syntax — no database. The Tkinter GUI is layered above a headless, fully testable domain/persistence/controller core. Support light/dark themes with a persisted user setting and a sensible system default.

## Test Policy

- Framework: pytest (selected as the standard Python framework).
- Full suite, from `implementer/src`: `.venv/bin/python -m pytest tests -v`
- Targeted: `.venv/bin/python -m pytest tests/<file>.py -v`
- GUI tests require a display (available on this Mac): destroy `root` in `finally`, call `root.update()` after building, probe effective colors via `winfo_rgb`. Headless tests must never launch the GUI.

## Current Implementation Summary

- Markdown persistence: each list stored as its own `.md` file with GFM checkboxes, atomic writes, filename-safe names.
- Domain layer: validated add/toggle/remove/rename of items with clear errors.
- Headless controller: create/delete lists, add/toggle/remove items; every mutation persisted immediately.
- GUI: list sidebar (create via button or Enter, delete), checkbutton item rows, add-item entry, per-item trash-icon delete; destructive actions require a modal Yes/No confirmation.
- Both input fields (new list, new item) show muted-gray placeholder hints that disappear on focus, are restored only when the entry has genuinely lost focus (never re-inserted into a still-focused field after submit), and are treated as empty on submit.
- Readability: item label foreground adapts to background luminance in both themes; entry fills follow the palette and sit slightly lighter than the list background in dark mode.
- Theming: persisted light/dark setting with system-default detection on first start; switcher applied at startup and on toggle; stored in `~/.todo-md-app/config/settings.json`.
- Theme switch flips the whole window including item rows; buttons use a darker hover/press fill for readable text.
- Versioning: version lives in `todo_md/VERSION`, auto-incremented (patch) by a git pre-commit hook; GUI shows it as a small low-contrast badge in the bottom-right whose background matches the window and whose toned-down gray text adapts on theme toggle.
- Dock icon: on macOS the app sets a custom dock icon from a bundled PNG (committed alongside its JPEG source); missing/unsupported icons fail soft so startup is unaffected.

## Active Task

**Task 26 (M)** — macOS arm64 self-contained build script + README usage docs
- Branch: `implementer/task-26-build-script` (base and integration branch: `main`; not yet created)
- Decomposition (sequential):
  - **26a (delegated, S):** `implementer/src/scripts/build_app.sh` + dev dependency + build tests (prompt below).
  - **26b (architect-owned, at closeout):** update repo-root `README.md` with precise instructions for using the build script (immutable build/run/test sections untouched; keep DRY; check the 3,500-word compaction threshold).
- Technical notes: PyInstaller is the standard tool; it is dev-only (runtime stays stdlib-only). `.venv` is the project interpreter. Prefer `--onedir --windowed` producing `todo-md.app`; guard non-arm64 hosts with a clear error. `implementer/src/scripts/bump_version.sh` is the in-repo style reference.
- Acceptance criteria (26a):
  1. `scripts/build_app.sh` (bash, `set -euo pipefail`) builds a self-contained `dist/todo-md.app` (macOS, arm64) of `python -m todo_md` using PyInstaller from `.venv` (installing it into `.venv` if missing).
  2. The script fails with a clear message on non-arm64 hosts; works when invoked from the repo root and from `implementer/src`.
  3. Smoke check: the built binary starts and stays alive (GUI opens, no import traceback) — verified by launching with a short timeout and checking liveness + clean stderr.
  4. No runtime dependency added to the `todo_md` package; no changes outside `implementer/src/`.
  5. Tests: fast by default (script exists/executable/`bash -n` clean, arm64 guard present); full build+launch integration test skipped unless `RUN_BUILD_TESTS=1`.
- Commands (from `implementer/src`):
  - `.venv/bin/python -m pytest tests -v`
  - `bash scripts/build_app.sh` (implementer must run once; bundle must build and launch)
  - `RUN_BUILD_TESTS=1 .venv/bin/python -m pytest tests/test_build_script.py -v` (implementer must run once)

Prompt for the Implementer (microtask 26a):
```
You are the Implementer. Base/integration branch: `main`. Your assigned implementation branch is `implementer/task-26-build-script` (already checked out).

Task 26 (M, microtask 1 of 2): add a build script that produces a self-contained macOS (Apple Silicon/arm64) executable of the application.

Before editing: verify the branch is `implementer/task-26-build-script` and `git status --short` is clean; if not, stop and report.

Scope — you may modify/create ONLY:
- implementer/src/scripts/build_app.sh (new; follow the conventions of the sibling scripts/bump_version.sh: bash, set -euo pipefail, executable bit, header comments documenting how to invoke it; robust to being run from the repo root or from implementer/src — resolve paths relative to the script location)
- implementer/src/requirements-dev.txt (new: dev-only build dependency, pin PyInstaller)
- implementer/src/tests/test_build_script.py (new)
Do not change anything outside implementer/src/. Changes anywhere under architect/ or at the repository root are forbidden.

Requirements:
1. build_app.sh builds the GUI app entry point (`python -m todo_md`) with PyInstaller into a self-contained `dist/todo-md.app` bundle (PyInstaller `--onedir --windowed --name todo-md`, workpath/specpath under `implementer/src/build/`). Use the project venv `.venv` (interpreter `implementer/src/.venv/bin/python`); if PyInstaller is not installed in it, install it first (`.venv/bin/python -m pip install pyinstaller`). PyInstaller is dev-only: the todo_md package itself must keep importing stdlib only — do not add runtime imports.
2. Host guard: if `uname -m` is not `arm64`, abort with a clear message stating the build targets Apple Silicon/arm64.
3. Smoke check at the end of the build: launch `dist/todo-md.app/Contents/MacOS/todo-md` in the background, wait ~3s, assert the process is still alive and no traceback appears in its stderr, then terminate it. On failure, exit non-zero with the captured stderr.
4. Do not commit build artifacts: make sure the final commit contains no files under dist/ or build/ (check `git status` before committing and report how you guaranteed this).

Tests (tests/test_build_script.py; keep the default suite fast):
- fast tests (always run): the script exists and is executable; `bash -n` passes; it contains the arm64 guard.
- integration test: full `bash scripts/build_app.sh` run + bundle launch check, skipped unless the environment variable RUN_BUILD_TESTS=1 is set.

Verify (from implementer/src):
- .venv/bin/python -m pytest tests -v   (all green)
- bash scripts/build_app.sh             (build succeeds, bundle launches; run it once for real)
- RUN_BUILD_TESTS=1 .venv/bin/python -m pytest tests/test_build_script.py -v   (all green)

Commit your work to `implementer/task-26-build-script`. Forbid: creating/switching/merging/rebasing/renaming/deleting branches, pushing, committing to main, broad staging or destructive working-tree operations.

Handoff must end with: RESULT: SUCCESS or RESULT: FAILURE; BRANCH: implementer/task-26-build-script; COMMIT: <full commit hash>; one-line test summary including the real build run outcome; blockers if any.
```

## Queue

- Analyse the Known Architectural Debt in 'architect/DESIGN.md' and make a plan to reduce it.

## Active Blockers

None.

## Recently Completed

- Task 25 — placeholder re-entry bug: `_restore_placeholder` no-ops while the entry still holds focus; old buggy `test_gui_new_list.py` contract aligned; 4 new regression tests; after one child timeout, finished from uncommitted checkpoint; verified 80/80, merged (d511d85).
- Task 24 — custom macOS dock icon: bundled PNG (450×450, from the kept jpg) applied via `iconphoto` at startup, reference kept on the instance, fail-soft on missing/unsupported icon; new `test_gui_dock_icon.py`; verified 76/76, merged (bd043dc, at VERSION 0.1.27).
- Task 23 — deterministic focus tests: placeholder/new-list GUI tests use `event_generate("<FocusIn>")`/`"<FocusOut>"` instead of WM focus (fixes post-merge flakiness); after one child timeout, completed from uncommitted checkpoint; two consecutive 73/73 runs; merged (0c46f37).
- Task 22 — input placeholders: muted-gray hints on both entries (placeholder_fg), cleared on focus-in, restored on empty focus-out, counted as empty on submit; new `test_gui_placeholders.py` + minimal `test_gui_new_list.py` contract alignment; merged (3c26e92).
- Task 21 — version badge colors: fallback-path label bg pinned to window palette bg, muted-gray fg in both themes, bg+fg refreshed on toggle; new `test_gui_version_colors.py`; verified, merged (4c03028).
