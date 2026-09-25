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
- Readability: item label foreground adapts to the effective background luminance, readable in both light and dark; entry field fills follow the palette in both themes (via the clam `fieldbackground` element option), so entry text stays legible. In dark mode entry fills are deliberately slightly lighter than the list widget background to correct the optical effect of identical colors.
- Theming: persisted light/dark setting with macOS system-default detection on first start; GUI theme switcher applied at startup and on toggle, and persisted to `~/.todo-md-app/config/settings.json` (dedicated config dir, with one-time migration from the legacy `<lists>/config.json`).
- Theme switches flip the whole window including item rows, verified in both switch directions; buttons use a slightly darker fill on hover/press in both themes so their text stays readable (dark-mode hover regression fixed).

## Active Task

- **ID/Title:** Task 18 — Enter key in new-list entry creates the list
- **Branch:** `implementer/18-new-list-enter-key` (base: `main`)
- **Scope:** `implementer/src/todo_md/app.py` only: bind `<Return>` on `self.new_name_entry` to `self._on_create_list`, mirroring the existing `self.new_item_entry.bind("<Return>", …)` pattern (line ~203). No other behavior changes; empty/invalid names must behave exactly as the Create button does.
- **Acceptance criteria:**
  1. Enter in the new-list entry creates the list via the same code path as the Create button: persisted to disk, shown in the sidebar, entry cleared.
  2. Enter with an empty entry is a no-op (same guard as the button).
  3. Item-entry `<Return>` behavior is unchanged.
- **Required tests:** new `tests/test_gui_new_list.py` (real display, follow existing `test_gui_*.py` conventions: `root.update()` after build, destroy `root` in `finally`): fire `<Return>` on `new_name_entry` → assert list created on disk and present in listbox; fire `<Return>` on empty entry → assert no list created.
- **Test commands (from `implementer/src`):**
  - Targeted: `.venv/bin/python -m pytest tests/test_gui_new_list.py -v`
  - Full: `.venv/bin/python -m pytest tests -v`

**Delegated prompt:**
```
You are the Implementer for the todo-md-app project. Work from /Users/flavio/LocalAi/todo-md-app/implementer.

ASSIGNED BRANCH: implementer/18-new-list-enter-key (base and integration branch: main). FIRST verify you are on this branch and that `git status --short` is clean before editing.

TASK (Task 18): Let the user create a new todo list by pressing Enter in the new-list input box.
- In src/todo_md/app.py, bind "<Return>" on self.new_name_entry to self._on_create_list, mirroring the existing pattern: self.new_item_entry.bind("<Return>", lambda _e: self._on_add_item()).
- Change nothing else. Empty/invalid names must behave exactly as the Create button does (existing guards in _on_create_list stay as-is).

TESTS: create src/tests/test_gui_new_list.py following the conventions of the existing test_gui_*.py files (real display available: build the app, call root.update() after building, destroy root in finally). Cover: (1) firing <Return> on new_name_entry creates the list — assert it exists on disk in the store's data dir, appears in the listbox, and the entry is cleared; (2) firing <Return> with an empty entry creates nothing.

COMMANDS (run from implementer/src): .venv/bin/python -m pytest tests/test_gui_new_list.py -v and .venv/bin/python -m pytest tests -v

BOUNDARIES: modify only files under implementer/ (this task: src/todo_md/app.py and src/tests/test_gui_new_list.py). Do NOT modify anything under architect/ or the repository root, and do NOT modify implementer/AGENTS.md. Do NOT create/switch/merge/rebase/rename/delete/push branches, commit to main, stage broadly (stage only the exact files you changed), or run destructive git operations.

TIME MANAGEMENT: after ~1000 seconds, stop new work, wrap up, and commit whatever stabilized state exists.

HANDOFF: commit your work on implementer/18-new-list-enter-key and end with RESULT: SUCCESS or RESULT: FAILURE plus COMMIT: <hash> (or COMMIT: NONE) and a short summary.
```

## Queue

None.

## Active Blockers

None.

## Recently Completed

- Task 17 — dark-mode entry fills lighter than list widget (TEntry `#383838` vs listbox `#2d2d2d`, separate `list_bg` palette value): verified, merged (3512857).
- Task 16 — dark-mode button hover: `style.map` active/pressed TButton to darker fill (#2e2e2e dark / #d0d0d0 light) so text stays visible; verified, merged (f0f5125).
- Task 15 — dark-mode entry fields kept light fill: fixed by setting clam `TEntry` `fieldbackground` in `_apply_theme`, verified, merged (1ca5aca).
- Task 14 — theme setting moved to `~/.todo-md-app/config/settings.json` with one-time legacy `<lists>/config.json` migration: completed, verified, merged (17e3461).
- Task 13 — item rows kept dark background after dark→light theme switch: fixed, verified, merged (0edf5b2).
