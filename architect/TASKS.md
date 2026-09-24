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
- Readability: item label foreground adapts to the effective background luminance, readable in both light and dark.
- Theming: persisted light/dark setting with macOS system-default detection on first start; GUI theme switcher applied at startup and on toggle, and persisted to `~/.todo-md-app/config/settings.json` (dedicated config dir, with one-time migration from the legacy `<lists>/config.json`).
- Theme switches flip the whole window including item rows, verified in both switch directions.

## Active Task

**Task 15 — Entry fields keep light fill in dark theme (contrast bug)**

- Branch: `implementer/15-entry-dark-contrast` (base `main`).
- Symptom: in dark mode both input boxes (list-name entry, new-item entry) render with a light background, making the light text invisible. Reproduced after light→dark toggle.
- Confirmed root cause: in this Tk build the clam `TEntry` field element (`Entry.field`) consumes the `fieldbackground` style option (element options: `bordercolor`, `lightcolor`, `fieldbackground`), but `_apply_theme` in `src/todo_md/app.py` only configures `background`/`foreground`, so the field keeps its default light fill in dark mode.
- Scope: fix `_apply_theme`'s fallback path so the entry field fill follows the palette in both themes (e.g., set `fieldbackground=entry_bg` on the `TEntry` style); keep light-mode entries white; do not change controller/storage/theme modules.
- Acceptance criteria:
  1. Dark theme (fresh start and after light→dark toggle): both entries' field fill is dark (luminance < 0.5) and entry text is light.
  2. Light theme (fresh start and after dark→light toggle): both entries' field fill is light (luminance > 0.5).
  3. Full suite passes; no regressions.
- Required tests: extend `src/tests/test_gui_theme.py` (existing conventions: probe effective colors via `winfo_rgb` luminance, `root.update()` after building/toggling, `root.destroy()` in `finally`) with a test asserting the `TEntry` field fill option (`ttk.Style(root).lookup("TEntry", "fieldbackground")`) is dark in dark and light in light, after startup and after toggles in both directions.
- Test commands (from `implementer/src`): `.venv/bin/python -m pytest tests/test_gui_theme.py -v` then `.venv/bin/python -m pytest tests -v`.
- Delegated prompt: see Git commit of this file (task text above is the full prompt content plus the generic delegation rules).

## Queue

None.

## Active Blockers

None.

## Recently Completed

- Task 14 — theme setting moved to `~/.todo-md-app/config/settings.json` with one-time legacy `<lists>/config.json` migration: completed, verified, merged (17e3461).
- Task 13 — item rows kept dark background after dark→light theme switch: fixed, verified, merged (0edf5b2).
- Tasks 12/12a — GUI theme switcher + startup theme application persisted to config.json: completed, verified, merged (8e8bf73).
- Tasks 1–11 — storage, models, controller, GUI, toggle bug, row layout, trash-icon delete, adaptive contrast, headless theme module: completed, verified, merged (pre-reorganization history; see `git log`).
