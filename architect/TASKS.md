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
- Both input fields (new list, new item) show muted-gray placeholder hints: cleared on focus-in, restored only when the entry has genuinely lost focus (never re-inserted after submit while still focused), counted as empty on submit.
- Readability: item label foreground adapts to background luminance in both themes; entry fills follow the palette (slightly lighter than list background in dark mode).
- Theming: persisted light/dark setting with system-default detection on first start; switcher applied at startup and on toggle; stored in `~/.todo-md-app/config/`.
- Theme switch flips the whole window including item rows; buttons use a darker hover/press fill for readable text.
- Versioning: version lives in `todo_md/VERSION`, auto-incremented (patch) by a git pre-commit hook; GUI shows it as a small low-contrast bottom-right badge (window-matching bg, toned-down gray text) that adapts on theme toggle.
- Dock icon: on macOS the app sets a custom dock icon from a bundled PNG (committed alongside its JPEG source); missing/unsupported icons fail soft so startup is unaffected.
- Build: `scripts/build_app.sh` (PyInstaller, arm64) builds a self-contained launchable `dist/todo-md.app` from `python -m todo_md` with post-build smoke check; PyInstaller is dev-only (runtime stays stdlib-only).

## Active Task

- **Task 27 (S)** — App bundle Finder icon: `dist/todo-md.app` currently shows the default PyInstaller icon in Finder; it must display the app icon from `implementer/src/todo_md/assets/dock_icon.png`.
- **Branch:** `implementer/task-27-app-bundle-icon` (base: `main`).
- **Scope:** only `implementer/src/scripts/build_app.sh` and `implementer/src/tests/test_build_script.py`.
- **Approach:** in `build_app.sh`, before invoking PyInstaller, generate a `.icns` from `todo_md/assets/dock_icon.png` using standard macOS tools (`sips` + `iconutil`) into the untracked `build/` dir, and pass it via `--icon` to PyInstaller. No new runtime/dev dependencies; `.icns` is a build artifact, never committed. Update the script header comment accordingly.
- **Acceptance criteria:**
  1. `bash scripts/build_app.sh` from repo root succeeds (existing smoke check unchanged and passing).
  2. The built bundle contains the icon resource (`dist/todo-md.app/Contents/Resources/` holds a `.icns`) and `Contents/Info.plist` references it (`CFBundleIconFile`).
  3. `test_build_script.py` static assertions extended to require the script to reference `dock_icon.png`, `.icns` generation, and `--icon`.
  4. Full suite still green.
- **Required tests:** update `tests/test_build_script.py` (static assertions; the gated real build covers end-to-end); run full suite.
- **Commands (from `implementer/src`):**
  - `.venv/bin/python -m pytest tests/test_build_script.py -v`
  - `.venv/bin/python -m pytest tests -v`
  - `RUN_BUILD_TESTS=1 .venv/bin/python -m pytest tests/test_build_script.py -v` (real build, verifies bundle icon artifact)
  - `bash scripts/build_app.sh` and inspect `dist/todo-md.app/Contents/Resources/` + `plutil -p dist/todo-md.app/Contents/Info.plist | grep -i icon`
- **Prompt for Implementer:**
  You are the Implementer for todo-md-app. Work in `implementer/` (repo root is `../`).
  1. Verify you are on branch `implementer/task-27-app-bundle-icon` and that the working tree is clean (`git status --short`); do not proceed otherwise.
  2. Modify `implementer/src/scripts/build_app.sh`: before the PyInstaller invocation, use macOS `sips` + `iconutil` to build a valid `.icns` from `implementer/src/todo_md/assets/dock_icon.png` (an app-icon set with the standard sizes, e.g. 16/32/128/256/512 @1x and @2x; the PNG is 450×450 so `sips` may upscale larger sizes — that is acceptable, or cap the set at sizes ≤ 450). Place the `.icns` under the existing untracked `build/` dir and pass it to PyInstaller via `--icon`. Keep the arm64 guard, venv guard, PyInstaller guard, existing PyInstaller flags, and the launch smoke check exactly as they are. Update the script's header comment to mention the icon. Do not commit `build/` or `dist/` (already gitignored).
  3. Extend `implementer/src/tests/test_build_script.py` static assertions to require the script to reference `dock_icon.png`, the `.icns` generation step, and the `--icon` flag.
  4. Run from `implementer/src`: `.venv/bin/python -m pytest tests/test_build_script.py -v` (default skip path), then the real build: `RUN_BUILD_TESTS=1 .venv/bin/python -m pytest tests/test_build_script.py -v`, then the full suite `.venv/bin/python -m pytest tests -v`.
  5. Verify the built bundle: `plutil -p dist/todo-md.app/Contents/Info.plist | grep -i icon` must show `CFBundleIconFile`, and `ls dist/todo-md.app/Contents/Resources/` must contain the `.icns`.
  6. Commit all changes on `implementer/task-27-app-bundle-icon` (never on `main`).
  7. Handoff: report `RESULT: SUCCESS|FAILURE`, `COMMIT: <hash>`, branch name, test results, and any blockers.
  Constraints: only touch `implementer/src/scripts/build_app.sh` and `implementer/src/tests/test_build_script.py`; do not modify anything under `implementer/AGENTS.md`, `architect/`, or repo root; do not create/switch/merge/push branches; no destructive git operations; commit staged paths only.

## Queue

- Analyse the Known Architectural Debt in 'architect/DESIGN.md' and make a plan to reduce it (Architect-owned analysis; no implementation).

## Active Blockers

None.

## Recently Completed

- Task 26 — arm64 build script: `scripts/build_app.sh` (PyInstaller `--onedir --windowed` + `--collect-data`, arm64 guard, post-build launch smoke check) + pinned dev dep + gated build tests + README usage docs; verified (83 passed/1 skipped, real bundle built and launched from repo root), merged (011e048; README c9f0829).
- Task 25 — placeholder re-entry bug: `_restore_placeholder` no-ops while the entry still holds focus; old buggy `test_gui_new_list.py` contract aligned; 4 new regression tests; after one child timeout, finished from uncommitted checkpoint; verified 80/80, merged (d511d85).
- Task 24 — custom macOS dock icon: bundled PNG (450×450, from the kept jpg) applied via `iconphoto` at startup, reference kept on the instance, fail-soft on missing/unsupported icon; new `test_gui_dock_icon.py`; verified 76/76, merged (bd043dc, at VERSION 0.1.27).
- Task 23 — deterministic focus tests: placeholder/new-list GUI tests use `event_generate("<FocusIn>")`/`"<FocusOut>"` instead of WM focus (fixes post-merge flakiness); after one child timeout, completed from uncommitted checkpoint; two consecutive 73/73 runs; merged (0c46f37).
- Task 22 — input placeholders: muted-gray hints on both entries (placeholder_fg), cleared on focus-in, restored on empty focus-out, counted as empty on submit; new `test_gui_placeholders.py` + minimal `test_gui_new_list.py` contract alignment; merged (3c26e92).
