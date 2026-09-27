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

- **Task 30 (S)** — Pre-sized trash icon (removes debt item 1: 28× runtime subsample of the 512×512 source).
- **Branch:** `implementer/task-30-trash-icon-presize` (base: `main`).
- **Scope:** new binary asset `implementer/src/todo_md/assets/trash_18.png`; `implementer/src/todo_md/app.py`; `implementer/src/tests/test_gui_trash_icon.py`; `implementer/src/tests/test_gui_delete_icon.py`.
- **Acceptance criteria:**
  1. `todo_md/assets/trash_18.png` committed: exactly 18×18, transparent PNG (IHDR color type 4 or 6), generated with `sips -z 18 18` from the 512×512 `trash.png` (source asset retained).
  2. `TodoApp` loads `trash_18.png` directly; no `.subsample` call remains in `todo_md/app.py`; the displayed icon is still 18px.
  3. Both GUI tests updated to reference `trash_18.png` (size range and transparency assertions kept).
  4. Full suite green.
- **Required tests:** update the two GUI tests above; run full suite.
- **Commands (from `implementer/src`):** `sips -z 18 18 todo_md/assets/trash.png --out todo_md/assets/trash_18.png`; `.venv/bin/python -m pytest tests/test_gui_trash_icon.py tests/test_gui_delete_icon.py -v`; `.venv/bin/python -m pytest tests -v`; verify asset: `.venv/bin/python -c "from PIL import Image"` is NOT required — check IHDR via `xxd`/Python stdlib (bytes 16–24).
- **Prompt for Implementer:**
  You are the Implementer for todo-md-app. Work in the implementer/ workspace (this directory).
  1. Verify you are on branch 'implementer/task-30-trash-icon-presize' and the working tree is clean (git status --short); do not proceed otherwise.
  2. From src/: generate the pre-sized asset with 'sips -z 18 18 todo_md/assets/trash.png --out todo_md/assets/trash_18.png' (downscale keeps the alpha channel). Verify the output PNG header: width/height in bytes 16–24 must be 18×18 and IHDR color type (byte 25) must be 4 or 6. Keep the original 512×512 trash.png as the source asset; do not delete it.
  3. In src/todo_md/app.py: make TodoApp load assets/trash_18.png directly (no .subsample call); update the nearby comment. No other behavioral changes.
  4. Update src/tests/test_gui_trash_icon.py and src/tests/test_gui_delete_icon.py to reference trash_18.png (keep the 14–22px size range and transparency assertions; the displayed width/height of the PhotoImage must remain exactly 18).
  5. Run from src/: '.venv/bin/python -m pytest tests/test_gui_trash_icon.py tests/test_gui_delete_icon.py -v' then the full suite '.venv/bin/python -m pytest tests -v'.
  6. Commit all changes (including the new binary asset) on implementer/task-30-trash-icon-presize (NEVER on main).
  7. Handoff: report RESULT: SUCCESS|FAILURE, COMMIT: <hash>, branch name, test results, blockers.
  Constraints: only touch src/todo_md/app.py, src/todo_md/assets/trash_18.png (new file), src/tests/test_gui_trash_icon.py, src/tests/test_gui_delete_icon.py; do not modify AGENTS.md, ../architect/, or the repo root; do not create/switch/merge/push/rebase branches; no destructive git operations; commit only staged paths.

## Queue

(empty — remaining debt plan fully queued as executed; next items come from future user requests)

## Active Blockers

None.

## Recently Completed

- Task 29 — explicit `TodoController.data_dir` (optional override, defaults to store's); `TodoApp` derives from the controller, no more store reach-in; 2 new headless tests; verified 86/1-skip (790ee86).
- Task 28 — debt triage and reduction plan (Architect): 4 debt items analysed; items 2/3 accepted as constraints with rationale in `decisions/2026-09-27-debt-triage.md`; items 1/4 turned into queued tasks 29/30 (S each).
- Task 27 — app bundle Finder icon: `build_app.sh` generates `build/todo_md.icns` from `dock_icon.png` via sips/iconutil and passes `--icon` to PyInstaller; static test extended; verified 84/1-skip + real bundle with valid `.icns`/`CFBundleIconFile` (4c09751).
- Task 26 — arm64 build script: `scripts/build_app.sh` (PyInstaller `--onedir --windowed` + `--collect-data`, arm64 guard, post-build launch smoke check) + pinned dev dep + gated build tests + README usage docs; verified (83 passed/1 skipped, real bundle built and launched from repo root), merged (011e048; README c9f0829).
- Task 25 — placeholder re-entry bug: `_restore_placeholder` no-ops while the entry still holds focus; old buggy `test_gui_new_list.py` contract aligned; 4 new regression tests; after one child timeout, finished from uncommitted checkpoint; verified 80/80, merged (d511d85).
- Task 24 — custom macOS dock icon: bundled PNG (450×450, from the kept jpg) applied via `iconphoto` at startup, reference kept on the instance, fail-soft on missing/unsupported icon; new `test_gui_dock_icon.py`; verified 76/76, merged (bd043dc, at VERSION 0.1.27).
- Task 23 — deterministic focus tests: placeholder/new-list GUI tests use `event_generate("<FocusIn>")`/`"<FocusOut>"` instead of WM focus (fixes post-merge flakiness); after one child timeout, completed from uncommitted checkpoint; two consecutive 73/73 runs; merged (0c46f37).
- Task 22 — input placeholders: muted-gray hints on both entries (placeholder_fg), cleared on focus-in, restored on empty focus-out, counted as empty on submit; new `test_gui_placeholders.py` + minimal `test_gui_new_list.py` contract alignment; merged (3c26e92).
