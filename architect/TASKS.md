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
- GUI: list sidebar with create/delete, checkbutton item rows, entry to add items, per-item trash-icon delete control; the new-list entry also creates the list on Enter. Destructive actions (delete list, delete item) require a modal Yes/No confirmation before anything is removed.
- Readability: item label foreground adapts to the effective background luminance, readable in both light and dark; entry field fills follow the palette in both themes (via the clam `fieldbackground` element option), so entry text stays legible. In dark mode they sit slightly lighter than the list widget background (identical colors read darker optically).
- Theming: persisted light/dark setting with macOS system-default detection on first start; theme switcher applied at startup and on toggle, persisted to `~/.todo-md-app/config/settings.json`.
- Theme switches flip the whole window including item rows in both directions; buttons use a slightly darker hover/press fill in both themes for readable text.
- Versioning: app version lives in `todo_md/VERSION`, auto-incremented (patch) by a git pre-commit hook via `scripts/bump_version.sh`; the GUI shows it as a small, low-contrast badge in the bottom-right corner.

## Active Task

None.

## Queue

- Add placeholders in all input fields, explaining what that field is supposed to contain: like 'Insert the name of a new list here' or 'Add a new todo item here'. Important: those placeholders must disappear as soon as the user put the focus on it.
- Now the application is shown with a standard icon in the MacOS dock, but I want it uses the following image: 'implementer/src/todo_md/assets/dock_icon.jpg'
- Implement a build script in bash/zsh that builds the application in a self contained executable file for MacOS (Apple Silicon/arm64). Update 'README.md' file with precise instructions on how to use that script.
- Analyse the Known Architectural Debt in 'architect/DESIGN.md' and make a plan to reduce it.

## Active Blockers

None.

## Recently Completed

- Task 20 — Yes/No confirmation popups (messagebox.askyesno) gate both delete-list and delete-item GUI handlers; No = full no-op; verified, merged (8d07a84).
- Task 19 — versioning: `bump_version.sh` + pre-commit hook auto-increments `todo_md/VERSION` (patch); headless `get_version()`; bottom-right GUI version badge; verified, merged (4fd69737, at VERSION 0.1.3).

## Queue

- Now the delete list and delete todo item actions proceed without asking any confirmation to the user: it is dangerous and I want you implement a popup confirmation window (message + yes/no buttons) for both use cases.
- Add placeholders in all input fields, explaining what that field is supposed to contain: like 'Insert the name of a new list here' or 'Add a a new todo item here'. Important: those placeholders must disappear as soon as the user put the focus on it.
- Now the application is shown with a standard icon in the MacOS dock, but I want it uses the following image: 'implementer/src/todo_md/assets/dock_icon.jpg'
- Implement a build script in bash/zsh that builds the application in a self contained executable file for MacOS (Apple Silicon/arm64). Update 'README.md' file with precise instructions on how to use that script.
- Analyse the Known Architectural Debt in 'architect/DESIGN.md' and make a plan to reduce it.
- Now the delete list and delete todo item actions proceed without asking any confirmation to the user: it is dangerous and I want you implement a popup confirmation window (message + yes/no buttons) for both use cases.
- Add placeholders in all input fields, explaining what that field is supposed to contain: like 'Insert the name of a new list here' or 'Add a new todo item here'. Important: those placeholders must disappear as soon as the user put the focus on it.
- Now the application is shown with a standard icon in the MacOS dock, but I want it uses the following image: 'implementer/src/todo_md/assets/dock_icon.jpg'
- Implement a build script in bash/zsh that builds the application in a self contained executable file for MacOS (Apple Silicon/arm64). Update 'README.md' file with precise instructions on how to use that script.
- Analyse the Known Architectural Debt in 'architect/DESIGN.md' and make a plan to reduce it.

## Active Blockers

None.

## Recently Completed

- Task 18 — Enter in new-list entry creates the list (Return bind on `new_name_entry` + `test_gui_new_list.py`): verified, merged (82d5271).
- Task 17 — dark-mode entry fills lighter than list widget (TEntry `#383838` vs listbox `#2d2d2d`, separate `list_bg` palette value): verified, merged (3512857).
- Task 16 — dark-mode button hover: `style.map` active/pressed TButton to darker fill (#2e2e2e dark / #d0d0d0 light) so text stays visible; verified, merged (f0f5125).
- Task 15 — dark-mode entry fields kept light fill: fixed by setting clam `TEntry` `fieldbackground` in `_apply_theme`, verified, merged (1ca5aca).
