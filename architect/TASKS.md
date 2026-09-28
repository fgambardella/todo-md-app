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

- **Task 32 (S)** — Settings core module (macro: user settings page, overall size L, ordered queue 32→36).
  - Branch: `implementer/task-32-settings-core` (base `main`).
  - Scope: `implementer/src/todo_md/settings.py` (replaces `theme.py`), `implementer/src/todo_md/app.py`, `implementer/src/todo_md/__init__.py`, `implementer/src/tests/` only.
  - Prompt:
    - You are the Implementer. Work ONLY on branch `implementer/task-32-settings-core`; base and integration branch is `main`. First verify `git branch --show-current` and `git status --short` from `implementer/`. You may change only files under `implementer/`; never touch `architect/` or the repo root, never modify `implementer/src/AGENTS.md`, never create/switch/merge/push branches, never commit to `main`.
    - Read `architect/DESIGN.md` (Theme config / Data models sections) and existing `src/todo_md/theme.py`, `tests/test_theme.py`.
    - Create `src/todo_md/settings.py` replacing `theme.py`:
      - `Settings` dataclass: `lists_dir: str | None` (None = default `~/.todo-md-app/lists/`), `theme: str` (one of `"light"`, `"dark"`, `"system"`), `completed_visible: int` (>= 0; how many completed items stay visible; 0 hides all completed; default 10).
      - `load_settings(config_dir)`: reads `settings.json`; fully backward-compatible with the legacy `{"theme": "light"|"dark"}` file (missing keys → defaults); missing/corrupt file → all defaults; no exceptions on read.
      - `save_settings(config_dir, settings)`: atomic write (temp + `os.replace`, same pattern as theme.py), UTF-8, keys `theme`, `lists_dir` (omit/null when default), `completed_visible`.
      - `resolve_theme(settings)`: returns `"light"`/`"dark"`; for `"system"` uses the existing macOS `defaults read -g AppleInterfaceStyle` detection with graceful fallback to `"light"`. Do NOT persist the resolved system value.
      - Keep the module headless (no tkinter).
    - Delete `theme.py`; update all imports (`app.py`, `__init__.py`, tests); rename `tests/test_theme.py` → `tests/test_settings.py` preserving all existing theme-behavior coverage, and add tests for: all-defaults load, legacy JSON compatibility, round-trip save/load, `"system"` resolution (mock the detection), `completed_visible` negative/invalid rejected on save input, `lists_dir` passthrough.
    - No GUI changes; existing theme switcher behavior must be unchanged.
    - Acceptance criteria: `settings.py` exposes `Settings`/`load_settings`/`save_settings`/`resolve_theme`; `theme.py` gone with zero remaining references; full suite green.
    - Commands (from `implementer/src`): `.venv/bin/python -m pytest tests/test_settings.py -v` then full `.venv/bin/python -m pytest tests -v`.
    - Commit finished work (and any stabilized partial work) on `implementer/task-32-settings-core`; hand off with RESULT / BRANCH / COMMIT. If blocked, commit a `RESULT: FAILURE` checkpoint with the blocker instead.

## Queue

- **Task 33 (S)** — Startup wiring for user settings: `run()` loads settings from a FIXED config dir `~/.todo-md-app/config/` (config dir must no longer be derived from the lists dir, otherwise changing the lists path would move the settings file); data dir derived from `settings.lists_dir` (default `~/.todo-md-app/lists/`, created on demand); list-dir location in the GUI/README wording unaffected; headless tests incl. temp config/data dirs.
- **Task 34 (S)** — Completed-items display filter: controller/view-model logic `visible_items(items, completed_visible)` — when completed count exceeds N, hide the excess starting from the top of the list (bottom-most completed stay); 0 hides all completed; storage on disk always keeps every item. Headless tests only; no GUI change.
- **Task 35 (M)** — Settings window (break down into sequential micro-tasks):
  - 35a: `"Settings"` button in the main window opening a Toplevel with: lists-folder row (Entry + `Browse…` via `filedialog.askdirectory` + `Reset to default`), theme radiobuttons (System default / Light / Dark), completed-visible Spinbox (0–999, 0 = hide all), Save/Cancel; window pre-filled from current settings; GUI tests for construction and pre-fill.
  - 35b: Save flow — persist via `save_settings`; on Save re-apply: theme (`_apply_theme` + `_refresh_items`), lists dir (controller/store data-dir switch + sidebar reload, existing files in the old dir are left in place, no auto-move), completed filter (items refresh); Cancel = full no-op; GUI tests incl. live theme change and sidebar reload after dir change.
- **Task 36 (S)** — Settings edge cases and validation: empty entry → default; existing path is a file → error dialog, settings not persisted; nonexistent dir → created when first list is written; unreadable/invalid value in Save for completed-visible → error dialog, no persist; headless validation tests + one GUI test for the error path.

## Active Blockers

None.

## Recently Completed

- Task 31b — v0.2.1 release cut (Architect-direct per user): VERSION commit lands at `0.2.1` (ecd4eb7); package rebuilt on `main` → `dist/todo-md-0.2.1-arm64.zip` (sha256 2ba5021d…); tagged `v0.2.1`, pushed per explicit request; user attaches zip in GitHub web release UI.
- Task 31a — one-command release packaging: `scripts/release_package.sh` (build → strict X.Y.Z validation → ditto zip, app at zip root) + static/gated tests; verified 90 passed/2 skipped + `RUN_RELEASE_TESTS=1` 5/5 (3be777e, merged c35805c).
- Task 30 — pre-sized trash icon: 18×18 RGBA `assets/trash_18.png` (sips from the 512×512 source, which is kept); GUI loads it directly, `.subsample(28)` gone; 2 GUI tests updated; verified 86/1-skip (d2f6964).
- Task 29 — explicit `TodoController.data_dir` (optional override, defaults to store's); `TodoApp` derives from the controller, no more store reach-in; 2 new headless tests; verified 86/1-skip (790ee86).
- Task 28 — debt triage and reduction plan (Architect): 4 debt items analysed; 2 accepted as constraints with rationale in `decisions/2026-09-27-debt-triage.md`; 2 executed as tasks 29/30.