# TASKS.md

## Project Goal

Build a macOS desktop TODO app in Python (stdlib only, no runtime dependencies). Every list is persisted as its own plain Markdown file using GitHub-flavored checkbox syntax — no database. The Tkinter GUI is layered above a headless, fully testable domain/persistence/controller core. Support light/dark themes with a persisted user setting and a sensible system default.

## Test Policy

- Framework: pytest (selected as the standard Python framework).
- Full suite, from `implementer/src`: `.venv/bin/python -m pytest tests -v`
- Targeted: `.venv/bin/python -m pytest tests/<file>.py -v`
- GUI tests require a display (available on this Mac): destroy `root` in `finally`, call `root.update()` after building, probe effective colors via `winfo_rgb`. Headless tests must never launch the GUI.

## Current Implementation Summary

- Markdown persistence: each list stored as its own `.md` file with GFM checkboxes, atomic writes, filename-safe names.
- Domain layer: validated add/toggle/remove/rename of items with clear errors.
- Headless controller: create/delete lists, add/toggle/remove items; every mutation persisted immediately.
- GUI: list sidebar (create via button or Enter, delete), checkbutton item rows, add-item entry, per-item trash-icon delete; destructive actions require a modal Yes/No confirmation.
- Readability: item label foreground adapts to background luminance in both themes; entry fills follow the palette and sit slightly lighter than the list background in dark mode.
- Theming: persisted light/dark setting with system-default detection on first start; switcher applied at startup and on toggle; stored in `~/.todo-md-app/config/settings.json`.
- Theme switch flips the whole window including item rows; buttons use a darker hover/press fill for readable text.
- Versioning: version lives in `todo_md/VERSION`, auto-incremented (patch) by a git pre-commit hook; GUI shows it as a small low-contrast bottom-right badge.

## Active Task

**Task 21 (S)** — Fix version badge colors in light mode
- Branch: `implementer/task-21-version-badge-colors` (base and integration branch: `main`)
- Scope: `implementer/src/todo_md/app.py` (version label creation in `_build_ui`, palette handling in `_apply_theme`); `implementer/src/tests/test_gui_version.py` (extend, or add `tests/test_gui_version_colors.py`).
- Acceptance criteria:
  1. Version label background equals the main window background in both themes on the clam fallback path (effective colors equal via `winfo_rgb`).
  2. Version text is a visible muted gray in both themes (light: clearly darker than bg, not black; dark: clearly lighter than bg, not white), still unobtrusive.
  3. Colors stay correct after a theme toggle (`_apply_theme` refreshes label bg and fg).
  4. Native `tk appappearance` path behavior unchanged (label background may stay unset there).
- Required tests: label bg == root bg in light and dark; fg gray intermediate (not pure white/black); colors refreshed after toggle; existing `test_gui_version.py` tests still pass.
- Commands (from `implementer/src`):
  - `.venv/bin/python -m pytest tests/test_gui_version.py -v`
  - `.venv/bin/python -m pytest tests -v`

Prompt for the Implementer:
```
You are the Implementer. Base/integration branch: `main`. Your assigned implementation branch is `implementer/task-21-version-badge-colors` (already checked out).

Task 21 (S): fix the version badge colors.

Bug: in light mode the version display component (bottom-right version `tk.Label` in `TodoApp`, `implementer/src/todo_md/app.py`) has a dark background instead of matching the main window. In the clam fallback path the label is created without an explicit background and stays pinned to the system default color.

Before editing: verify the current branch is `implementer/task-21-version-badge-colors` and `git status --short` is clean; if not, stop and report.

Scope — you may modify ONLY these files:
- `implementer/src/todo_md/app.py`
- `implementer/src/tests/test_gui_version.py` (or add `implementer/src/tests/test_gui_version_colors.py`)
Do not change anything outside `implementer/src/`. Changes anywhere under `architect/` or at the repository root are forbidden.

Requirements:
1. Set the version label background explicitly so it equals the main window background (`self.root` bg) in both light and dark mode on the fallback (clam) path; use the palette `bg`.
2. Version text: a visible muted gray in both themes — light: clearly darker than the background but not black; dark: clearly lighter than the background but not white. Keep it unobtrusive (small font, low contrast vs background).
3. Refresh the label background AND foreground in `_apply_theme` so a theme toggle keeps the colors correct.
4. Do not change behavior on the native `tk appappearance` path (early return, `self._palette = None`); an unset label background is acceptable there.

Tests to add/update (GUI tests on a real display: destroy `root` in `finally`, call `root.update()` after building, probe effective colors via `winfo_rgb`):
- label effective background equals root effective background in light and in dark mode;
- label foreground is a gray intermediate between background and main text (not pure white/black in either theme);
- after toggling the theme, label background/foreground match the new theme values;
- all pre-existing `test_gui_version.py` tests still pass.

Run from `implementer/src`:
- `.venv/bin/python -m pytest tests/test_gui_version.py -v`
- `.venv/bin/python -m pytest tests -v`

Commit your work to `implementer/task-21-version-badge-colors`. Forbid: creating/switching/merging/rebasing/renaming/deleting branches, pushing, committing to `main`, broad staging or destructive working-tree operations.

Handoff must end with: RESULT: SUCCESS or RESULT: FAILURE; BRANCH: implementer/task-21-version-badge-colors; COMMIT: <full commit hash>; one-line test summary; blockers if any.
```

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
- Task 18 — Enter in new-list entry creates the list (Return bind on `new_name_entry` + `test_gui_new_list.py`): verified, merged (82d5271).
- Task 17 — dark-mode entry fills lighter than list widget (TEntry `#383838` vs listbox `#2d2d2d`, separate `list_bg` palette value): verified, merged (3512857).
- Task 16 — dark-mode button hover: `style.map` active/pressed TButton to darker fill (#2e2e2e dark / #d0d0d0 light) so text stays visible; verified, merged (f0f5125).