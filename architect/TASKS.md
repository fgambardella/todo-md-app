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
- Theme switches flip the whole window including item rows, verified in both switch directions; buttons use a slightly darker fill on hover/press in both themes so their text stays readable (dark-mode hover regression fixed).

## Active Task

None.

## Queue

None.

## Active Blockers

None.

## Recently Completed

- Task 16 — dark-mode button hover: `style.map` active/pressed TButton to darker fill (#2e2e2e dark / #d0d0d0 light) so text stays visible; verified, merged (f0f5125).
- Task 15 — dark-mode entry fields kept light fill: fixed by setting clam `TEntry` `fieldbackground` in `_apply_theme`, verified, merged (1ca5aca).
- Task 14 — theme setting moved to `~/.todo-md-app/config/settings.json` with one-time legacy `<lists>/config.json` migration: completed, verified, merged (17e3461).
- Task 13 — item rows kept dark background after dark→light theme switch: fixed, verified, merged (0edf5b2).
- Tasks 12/12a — GUI theme switcher + startup theme application persisted to config.json: completed, verified, merged (8e8bf73).
