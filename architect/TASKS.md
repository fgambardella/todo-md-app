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
- GUI: list sidebar with create/delete, checkbutton item rows, entry to add items, per-item trash-icon delete control; the new-list entry also creates the list on Enter.
- Readability: item label foreground adapts to the effective background luminance, readable in both light and dark; entry field fills follow the palette in both themes (via the clam `fieldbackground` element option), so entry text stays legible. In dark mode they sit slightly lighter than the list widget background (identical colors read darker optically).
- Theming: persisted light/dark setting with macOS system-default detection on first start; theme switcher applied at startup and on toggle, persisted to `~/.todo-md-app/config/settings.json`.
- Theme switches flip the whole window including item rows in both directions; buttons use a slightly darker hover/press fill in both themes for readable text.

## Active Task

- **ID/Title:** Task 19 — Git-hook version bumping + in-GUI version label.
- **Branch:** `implementer/19-versioning-hook` (base `main`; integrate back into `main`).
- **Scope:**
  - New `src/todo_md/VERSION` file containing exactly `0.1.0` (no "v" prefix, no trailing spaces besides newline).
  - New `src/scripts/bump_version.sh` (bash, executable): reads `src/todo_md/VERSION`, increments the PATCH component (X.Y.Z → X.Y.Z+1), writes the new value back, and stages the file (`git add src/todo_md/VERSION`). Idempotent-safe and fails loudly if VERSION is malformed.
  - Install the hook at `.git/hooks/pre-commit` (git-internal, untracked; created by a small install step in `bump_version.sh --install-hook` run once by the Implementer from the repo root so it is not re-created on other machines). Hook content: `#!/bin/sh` + call `"$(git rev-parse --show-toplevel)/src/scripts/bump_version.sh"` relative path from repo root (`implementer/src/scripts/bump_version.sh`), no other logic.
  - The application loads the version dynamically: new helper in `todo_md/app.py` or a small `todo_md/version.py` (either is fine) that reads `VERSION` next to the package at runtime (file-relative via `pathlib.Path(__file__)`, not CWD), falling back to `0.0.0` if the file is missing/unreadable. `TodoApp` displays it in the bottom-right corner of the window: a small font (e.g. size 8), low-contrast foreground (subtle gray on both light and dark palettes — add palette entry in `_apply_theme`, e.g. `#9a9a9a` light / `#555555` dark, refine to taste), non-interactive `tk.Label` placed via `pack(side="bottom", anchor="e")` (or grid in the existing layout) so it does not disrupt existing layout tests. Display as `v<version>`.
  - Do NOT change the version format shown elsewhere; do NOT touch theme/settings logic.
- **Acceptance criteria:**
  1. `src/todo_md/VERSION` exists with `0.1.0`.
  2. After a commit on this branch, `git diff --cached` (or the commit itself) shows `VERSION` incremented by one patch — verify by making one test commit AFTER implementing the hook: the commit's own VERSION must read `0.1.1`, and the final state of the branch must have `VERSION` = `0.1.1` (i.e., the bump is part of normal committing, no special manual commits needed afterwards). If the last commit ends at `0.1.1`, that is the correct final value.
  3. `python -c` from `src` confirms the loader returns the current VERSION content.
  4. GUI shows the version label bottom-right; full test suite passes (label must not break existing layout tests; add a GUI test asserting the label exists, shows `v` + version text, and uses a small font).
- **Required tests:** new `tests/test_version.py` (loader reads VERSION file, falls back to `0.0.0` when missing, parse robustness) and a GUI test (e.g. `tests/test_gui_version.py`) asserting the version label exists in the built window with expected text and small font size.
- **Commands (from `implementer/src`):** `.venv/bin/python -m pytest tests -v` and `.venv/bin/python -m pytest tests/test_version.py tests/test_gui_version.py -v`; from repo root: `sh -n implementer/src/scripts/bump_version.sh` and `git -C .. log -1 --stat` to confirm the hook's effect.
- **Prompt for Implementer:** see Delegation below.

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
- Task 14 — theme setting moved to `~/.todo-md-app/config/settings.json` with one-time legacy `<lists>/config.json` migration: completed, verified, merged (17e3461).
