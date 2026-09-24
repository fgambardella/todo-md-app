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

- **ID / Title:** Task 17 — dark-mode entry fields: slightly lighter fill than the list widget to compensate the optical effect.
- **Branch:** `implementer/17-entry-dark-lighter` (base and integration branch: `main`).
- **Scope:** `implementer/src/todo_md/app.py` (`TodoApp._apply_theme` dark palette) + GUI tests under `implementer/src/tests/`. Entry fill and listbox background currently share `entry_bg` (`#2d2d2d` dark); decouple them.
- **Acceptance criteria:**
  1. Dark mode: TEntry `fieldbackground` and `background` = `#383838` (slightly lighter than the list widget); listbox background stays `#2d2d2d`; TEntry foreground stays the palette `fg`.
  2. Light mode unchanged: TEntry fill `#ffffff`, listbox background `#ffffff`.
  3. Separate palette value (e.g. `list_bg`) added so the entry fill no longer drives the listbox background.
  4. New/updated GUI tests assert dark: TEntry fieldbackground `#383838`, entry luminance > listbox luminance, listbox bg `#2d2d2d`; light: both `#ffffff`.
- **Required tests:** GUI assertions in `tests/test_gui_theme.py` (or an adjacent GUI test module) per criteria 4; full suite green.
- **Commands (from `implementer/src`):** `.venv/bin/python -m pytest tests/test_gui_theme.py -v`; `.venv/bin/python -m pytest tests -v`
- **Delegated prompt:** Task 17 — dark-mode entry fields: slightly lighter fill than the list widget. Work on branch `implementer/17-entry-dark-lighter` (base/integration branch: `main`); verify with `git branch --show-current` and `git status --short` before editing. Scope restricted to files under `implementer/src/` (`todo_md/app.py`, `tests/`); forbid changes under `architect/` or at the repository root. In `TodoApp._apply_theme`, the dark-mode TEntry fill and the listbox background both use `entry_bg` (`#2d2d2d`); the entries *look* darker than the list widget even though colors match (optical effect). Fix: add a separate listbox-background palette value (e.g. `list_bg`) and set dark-mode TEntry `background`/`fieldbackground` to `#383838` while the listbox keeps `#2d2d2d`; light mode keeps TEntry `#ffffff` and listbox `#ffffff`. Update the palette dict and the listbox `bg=` accordingly. Add/extend GUI tests (e.g. `tests/test_gui_theme.py`) asserting: dark — `style.lookup("TEntry", "fieldbackground") == "#383838"`, listbox `cget("bg") == "#2d2d2d"`, and entry-field luminance (via `root.winfo_rgb`) strictly greater than listbox luminance; light — both `#ffffff`. Follow existing test conventions (`root.update()` after building, probe colors, destroy `root` in `finally`). Run from `implementer/src`: `.venv/bin/python -m pytest tests/test_gui_theme.py -v` and `.venv/bin/python -m pytest tests -v`. Commit completed work (stage only files under `implementer/src/`) and end the handoff with RESULT: SUCCESS/FAILURE, COMMIT: <hash>, BRANCH: implementer/17-entry-dark-lighter, and a brief summary. Do not create/switch/merge/rebase/rename/delete/push branches, never commit to `main`, no broad staging, no destructive working-tree operations. If you approach ~1000 seconds, stabilize partial work, commit it, and hand off RESULT: FAILURE with remaining work.

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
