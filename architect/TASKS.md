# TASKS.md

## Project Goal

Build a macOS desktop TODO app in Python (stdlib only, no runtime dependencies). Every list is persisted as its own plain Markdown file using GitHub-flavored checkbox syntax — no database. The Tkinter GUI is layered above a headless, fully testable domain/persistence/controller core. Support light/dark themes with a persisted user setting and a sensible system default.

## Test Policy

- Framework: pytest (selected as the standard Python framework).
- Full suite, from `implementer/src`: `.venv/bin/python -m pytest tests -v`
- Targeted: `.venv/bin/python -m pytest tests/<file>.py -v`
- GUI tests require a display (available on this Mac): destroy `root` in `finally`, call `root.update()` after building, probe effective colors via `winfo_rgb`. Headless tests must never launch the GUI.

## Current Implementation Summary

- Markdown persistence: each list stored as its own `.md` file with GFM checkboxes, atomic writes, filename-safe list names.
- Domain layer: validated add, toggle, remove, and rename of items with clear errors for empty text or bad indexes.
- Headless controller: create/delete lists and add/toggle/remove items; every mutation is persisted to disk immediately.
- GUI: list sidebar with create/delete, checkbutton item rows, entry to add items, per-item trash-icon delete control.
- Readability: item label foreground adapts to the effective background luminance, readable in both light and dark; entry field fills follow the palette in both themes (via the clam `fieldbackground` element option), so entry text stays legible.
- Theming: persisted light/dark setting with macOS system-default detection on first start; GUI theme switcher applied at startup and on toggle, and persisted to `~/.todo-md-app/config/settings.json` (dedicated config dir, with one-time migration from the legacy `<lists>/config.json`).
- Theme switches flip the whole window including item rows, verified in both switch directions.

## Active Task

- **ID:** 16
- **Title:** Dark-mode button hover: use slightly darker fill so text stays visible.
- **Branch:** `implementer/16-button-hover-dark` (base: `main`).
- **Scope:** `implementer/src/todo_md/app.py` (add `style.map("TButton", background=[...])` with darker `active`/`pressed` state colors inside `_apply_theme`) plus a GUI test in `implementer/src/tests/` (extend an existing GUI test file or add a small one). No other files; do not touch `implementer/AGENTS.md`, `architect/`, or repo root.
- **Root cause:** in dark mode `TButton` gets `background=#3c3c3c`, `foreground=#f0f0f0`, but clam's default `activeBackground` stays light, so hover fill turns light and the light text vanishes.
- **Acceptance criteria:**
  1. In dark mode, hovering (state `active`) a Create/Delete/theme button shows a fill slightly darker than the normal `#3c3c3c` (e.g. `#2e2e2e`), and foreground stays the light `#f0f0f0`.
  2. In light mode, the `active` state also uses a slightly darker fill than `#e0e0e0` (e.g. `#d0d0d0`) so behavior is consistent.
  3. Normal (non-hover) appearance of all buttons is unchanged in both themes.
- **Required tests:** GUI test that, after applying each theme, puts a `ttk.Button` into `active` state (e.g. via `button.state(["active"])` + `root.update()`), and asserts via `winfo_rgb` that the active background is darker than the normal background and the foreground matches the palette fg. Destroy `root` in `finally`.
- **Test commands (from `implementer/src`):**
  - Targeted: `.venv/bin/python -m pytest tests/test_gui_hover.py -v` (or the chosen test file)
  - Full: `.venv/bin/python -m pytest tests -v`
- **Delegated prompt:** see task body above; Implementer must verify current branch, inspect working tree, commit completed work on `implementer/16-button-hover-dark`, and hand off branch + commit hash. Forbid creating/switching/merging branches, committing to `main`, broad staging, destructive ops, and any change under `architect/` or repo root.

## Queue

None.

## Active Blockers

None.

## Recently Completed

- Task 15 — dark-mode entry fields kept light fill: fixed by setting clam `TEntry` `fieldbackground` in `_apply_theme`, verified, merged (1ca5aca).
- Task 14 — theme setting moved to `~/.todo-md-app/config/settings.json` with one-time legacy `<lists>/config.json` migration: completed, verified, merged (17e3461).
- Task 13 — item rows kept dark background after dark→light theme switch: fixed, verified, merged (0edf5b2).
- Tasks 12/12a — GUI theme switcher + startup theme application persisted to config.json: completed, verified, merged (8e8bf73).
- Tasks 1–11 — storage, models, controller, GUI, toggle bug, row layout, trash-icon delete, adaptive contrast, headless theme module: completed, verified, merged (pre-reorganization history; see `git log`).
