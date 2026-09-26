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
- Versioning: version lives in `todo_md/VERSION`, auto-incremented (patch) by a git pre-commit hook; GUI shows it as a small low-contrast badge in the bottom-right whose background matches the window and whose toned-down gray text adapts on theme toggle.

## Active Task

**Task 22 (S)** — Input field placeholders
- Branch: `implementer/task-22-input-placeholders` (base and integration branch: `main`)
- Scope: `implementer/src/todo_md/app.py` (placeholder behavior for `new_name_entry` and `new_item_entry`); new `implementer/src/tests/test_gui_placeholders.py`.
- Acceptance criteria:
  1. Both input fields show placeholder text when empty and unfocused: new-list entry → "Insert the name of a new list here"; add-item entry → "Add a new todo item here".
  2. The placeholder disappears as soon as the field receives focus (FocusIn), even when empty.
  3. On focus-out the placeholder reappears only if the field is empty; typed text is never overwritten or corrupted.
  4. Placeholder text is a muted gray distinguishable from real text, correct in both themes and refreshed on theme toggle.
  5. The placeholder can never be submitted as content (empty Enter/button presses remain no-ops, existing empty-input guards intact).
- Required tests: both entries show placeholders on build; focus-in clears placeholder; typed text survives focus-out; empty focus-out restores placeholder; placeholder fg follows the palette on theme toggle; empty Enter in the new-list entry does not create a list.
- Commands (from `implementer/src`):
  - `.venv/bin/python -m pytest tests/test_gui_placeholders.py -v`
  - `.venv/bin/python -m pytest tests -v`

Prompt for the Implementer:
```
You are the Implementer. Base/integration branch: `main`. Your assigned implementation branch is `implementer/task-22-input-placeholders` (already checked out).

Task 22 (S): add placeholders to both input fields.

Context: `TodoApp` in `implementer/src/todo_md/app.py` has two ttk.Entry widgets: `self.new_name_entry` (new list name) and `self.new_item_entry` (new item text). The GUI runs on the clam fallback palette path (`self._palette` dict with keys bg/fg/btn_bg/entry_bg/list_bg/version_fg) set in `_apply_theme`; theme toggles go through `_on_toggle_theme` → `_apply_theme`.

Before editing: verify the current branch is `implementer/task-22-input-placeholders` and `git status --short` is clean; if not, stop and report.

Scope — you may modify ONLY these files:
- `implementer/src/todo_md/app.py`
- `implementer/src/tests/test_gui_placeholders.py` (new)
Do not change anything outside `implementer/src/`. Changes anywhere under `architect/` or at the repository root are forbidden.

Requirements:
1. Placeholder text: new-list entry → "Insert the name of a new list here"; add-item entry → "Add a new todo item here".
2. Show the placeholder when the entry is empty and unfocused. On `<FocusIn>` remove the placeholder (only if it is currently the displayed content) so the field starts clean the instant the user focuses it.
3. On `<FocusOut>`, restore the placeholder only if the entry is empty; never overwrite typed text. A small shared helper on TodoApp for both entries is preferred over duplicated logic.
4. Placeholder text must be a muted gray distinguishable from real text in BOTH themes (e.g. a gray palette value per theme); when the theme toggles and the placeholder is displayed, its color must update. Use a dedicated palette entry (e.g. `placeholder_fg`) rather than reusing version_fg.
5. The placeholder must never be submitted as content: with an empty (placeholder-showing) entry, Enter or the corresponding button must behave exactly as today (no-op / validation error, no list or item created). Do not weaken existing empty-input guards.

Tests (new file `tests/test_gui_placeholders.py`; GUI tests on a real display: destroy `root` in `finally`, call `root.update()` after building/simulating, probe state via widget cget/entry get and `winfo_rgb` where colors are checked):
- both entries display their placeholder text on build (unfocused, empty);
- focusing an entry (focus_set + update) clears the placeholder;
- typing text then moving focus away keeps the text intact (no placeholder residue);
- moving focus away from an empty entry restores the placeholder;
- after a theme toggle, the displayed placeholder color matches the new theme's muted gray (probe via winfo_rgb, assert it differs from both the entry background and the main text color);
- pressing Return in an empty new-list entry does not create any list.

Run from `implementer/src`:
- `.venv/bin/python -m pytest tests/test_gui_placeholders.py -v`
- `.venv/bin/python -m pytest tests -v`

Commit your work to `implementer/task-22-input-placeholders`. Forbid: creating/switching/merging/rebasing/renaming/deleting branches, pushing, committing to `main`, broad staging or destructive working-tree operations.

Handoff must end with: RESULT: SUCCESS or RESULT: FAILURE; BRANCH: implementer/task-22-input-placeholders; COMMIT: <full commit hash>; one-line test summary; blockers if any.
```

## Queue

- Now the application is shown with a standard icon in the MacOS dock, but I want it uses the following image: 'implementer/src/todo_md/assets/dock_icon.jpg'
- Implement a build script in bash/zsh that builds the application in a self contained executable file for MacOS (Apple Silicon/arm64). Update 'README.md' file with precise instructions on how to use that script.
- Analyse the Known Architectural Debt in 'architect/DESIGN.md' and make a plan to reduce it.

## Active Blockers

None.

## Recently Completed

- Task 21 — version badge colors: fallback-path label bg pinned to window palette bg, muted-gray fg in both themes, bg+fg refreshed on toggle; new `test_gui_version_colors.py`; verified, merged (4c03028).
- Task 20 — Yes/No confirmation popups (messagebox.askyesno) gate both delete-list and delete-item GUI handlers; No = full no-op; verified, merged (8d07a84).
- Task 19 — versioning: `bump_version.sh` + pre-commit hook auto-increments `todo_md/VERSION` (patch); headless `get_version()`; bottom-right GUI version badge; verified, merged (4fd69737, at VERSION 0.1.3).
- Task 18 — Enter in new-list entry creates the list (Return bind on `new_name_entry` + `test_gui_new_list.py`): verified, merged (82d5271).
- Task 17 — dark-mode entry fills lighter than list widget (TEntry `#383838` vs listbox `#2d2d2d`, separate `list_bg` palette value): verified, merged (3512857).