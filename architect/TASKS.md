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

- **ID/Title:** Task 19 — Git-hook version bumping + in-GUI version label (split into sequential micro-tasks after child timeout at `2076d28`; branch state: only untracked `src/todo_md/VERSION` = 0.1.0, no commits yet).
- **Branch:** `implementer/19-versioning-hook` (base `main`; integrate back into `main`). Continue on this branch.
- **Shared constraints (all micro-tasks):** only touch files under `implementer/` except `.git/hooks/pre-commit` (git-internal, allowed in 19b); never touch `architect/`, root README, `implementer/AGENTS.md`; no pushing; no branch ops; stage only task files; VERSION format `X.Y.Z`, patch bump, final branch state must end at `0.1.1` (hook bumps it in 19b's commit).
- **Micro-task 19a (next): bump script.** Ensure `src/todo_md/VERSION` = `0.1.0`+newline; create executable `src/scripts/bump_version.sh` (bash): locate repo root via `git rev-parse --show-toplevel`, read/validate VERSION (`^[0-9]+\.[0-9]+\.[0-9]+$`, fail loudly otherwise), increment patch, write back, `git add implementer/src/todo_md/VERSION`; support `--install-hook` flag that writes `<root>/.git/hooks/pre-commit` (`#!/bin/sh`, executable, resolves script path from repo root) — but do NOT run it in 19a. Verify: `sh -n`, and a dry logic check (e.g. copy script logic test via temp dir or `bash -x` on a temp VERSION copy — no git side effects on the real tree). Tests: none required yet. Commit.
- **Micro-task 19b: install hook.** Run `bump_version.sh --install-hook` from repo root; verify hook exists, executable, `sh -n` clean; commit — the hook must fire and that commit itself must contain VERSION = `0.1.1` (verify with `git show HEAD --stat` / `git show HEAD -- implementer/src/todo_md/VERSION`). If the hook fails to fire, fix it (still inside implementer/ boundaries for the script) and re-commit.
- **Micro-task 19c: headless version loader.** New `src/todo_md/version.py` (no tkinter): read VERSION relative to package (`Path(__file__).resolve().parent / 'VERSION'`), return stripped string, fall back to `0.0.0` if missing/unreadable; export from `src/todo_md/__init__.py` as appropriate. New `tests/test_version.py`: returns current file content (should be `0.1.1` from 19b), fallback `0.0.0` with monkeypatched/missing path, tolerant of surrounding whitespace/newlines. Run targeted test; commit.
- **Micro-task 19d: GUI version label.** `TodoApp` in `src/todo_md/app.py`: non-interactive `tk.Label` bottom-right, text `v<version>`, small font (size 8), low-contrast fg via new `version_fg` palette entry in `self._palette` applied in `_apply_theme` (subtle gray, ~`#9a9a9a` light / `#555555` dark, refine to taste); place via `pack(side='bottom', anchor='e')` or grid without breaking existing layout. New `tests/test_gui_version.py`: label exists, text matches `v` + current VERSION, font size <= 10. Run FULL suite from `implementer/src`: `.venv/bin/python -m pytest tests -v` — all must pass. Commit.
- **Acceptance criteria (whole task):** VERSION file exists and reads `0.1.1`; hook auto-bumps future commits; headless loader + tests; GUI label bottom-right with small low-contrast font + GUI test; full suite green; `sh -n` clean on hook and script; nothing left uncommitted.
- **Commands:** from `implementer/src`: `.venv/bin/python -m pytest tests/test_version.py -v`, `.venv/bin/python -m pytest tests/test_gui_version.py -v`, `.venv/bin/python -m pytest tests -v`; from repo root: `sh -n .git/hooks/pre-commit`, `sh -n implementer/src/scripts/bump_version.sh`, `git log -1 --stat`.
- **Blocker (from timeout):** previous single-shot child exceeded 1,200s; revised approach = four sequential micro-tasks above, one child each.

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
