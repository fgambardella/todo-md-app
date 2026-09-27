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

None

## Queue

- The self-contained launchable `dist/todo-md.app` application file, built by`scripts/build_app.sh` (PyInstaller, arm64), shows a default icon in finder. Use instead `implementer/src/todo_md/assets/dock_icon.png` as the application file icon.
- Analyse the Known Architectural Debt in 'architect/DESIGN.md' and make a plan to reduce it.

## Active Blockers

None.

## Recently Completed

- Task 26 — arm64 build script: `scripts/build_app.sh` (PyInstaller `--onedir --windowed` + `--collect-data`, arm64 guard, post-build launch smoke check) + pinned dev dep + gated build tests + README usage docs; verified (83 passed/1 skipped, real bundle built and launched from repo root), merged (011e048; README c9f0829).
- Task 25 — placeholder re-entry bug: `_restore_placeholder` no-ops while the entry still holds focus; old buggy `test_gui_new_list.py` contract aligned; 4 new regression tests; after one child timeout, finished from uncommitted checkpoint; verified 80/80, merged (d511d85).
- Task 24 — custom macOS dock icon: bundled PNG (450×450, from the kept jpg) applied via `iconphoto` at startup, reference kept on the instance, fail-soft on missing/unsupported icon; new `test_gui_dock_icon.py`; verified 76/76, merged (bd043dc, at VERSION 0.1.27).
- Task 23 — deterministic focus tests: placeholder/new-list GUI tests use `event_generate("<FocusIn>")`/`"<FocusOut>"` instead of WM focus (fixes post-merge flakiness); after one child timeout, completed from uncommitted checkpoint; two consecutive 73/73 runs; merged (0c46f37).
- Task 22 — input placeholders: muted-gray hints on both entries (placeholder_fg), cleared on focus-in, restored on empty focus-out, counted as empty on submit; new `test_gui_placeholders.py` + minimal `test_gui_new_list.py` contract alignment; merged (3c26e92).
