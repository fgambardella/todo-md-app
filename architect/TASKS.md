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
- Both input fields (new list, new item) show muted-gray placeholder hints that disappear on focus and are treated as empty on submit.
- Readability: item label foreground adapts to background luminance in both themes; entry fills follow the palette and sit slightly lighter than the list background in dark mode.
- Theming: persisted light/dark setting with system-default detection on first start; switcher applied at startup and on toggle; stored in `~/.todo-md-app/config/settings.json`.
- Theme switch flips the whole window including item rows; buttons use a darker hover/press fill for readable text.
- Versioning: version lives in `todo_md/VERSION`, auto-incremented (patch) by a git pre-commit hook; GUI shows it as a small low-contrast badge in the bottom-right whose background matches the window and whose toned-down gray text adapts on theme toggle.

## Active Task

**Task 24 (S)** — Custom macOS dock icon
- Branch: `implementer/task-24-dock-icon` (base and integration branch: `main`; not yet created)
- Scope: `implementer/src/todo_md/app.py` (dock icon wiring); new PNG asset derived from `implementer/src/todo_md/assets/dock_icon.jpg` (450x450 JPEG, keep the original jpg); new `implementer/src/tests/test_gui_dock_icon.py`.
- Technical notes: Tk `PhotoImage` cannot decode JPEG natively, so a PNG version of the icon must be produced once (e.g. macOS `sips -s format png`) and committed alongside the jpg. On macOS, `root.iconphoto(True, photo)` sets the app's dock icon; the `PhotoImage` must be kept alive in an instance attribute to avoid GC. Runtime stays stdlib-only.
- Acceptance criteria:
  1. `TodoApp` loads a PNG dock icon package-relative (via the `todo_md` package path, like other assets) and applies it with `root.iconphoto(True, photo)`, storing the reference on the instance.
  2. The PNG asset exists in `todo_md/assets/` and is a valid multi-color PNG derived from the provided jpg (lossless format conversion, no redesign).
  3. A missing/unreadable icon must not break app startup (fail soft: skip `iconphoto`, app runs normally).
  4. No changes to theme, layout, or behavior beyond the icon wiring.
- Required tests: the PNG asset loads as a `PhotoImage` with width and height > 0; `TodoApp` stores the icon reference and `iconphoto` is applied without error (icon set at startup); a corrupted/missing icon path (simulated) leaves the app functional.
- Commands (from `implementer/src`):
  - `.venv/bin/python -m pytest tests/test_gui_dock_icon.py -v`
  - `.venv/bin/python -m pytest tests -v`

Prompt for the Implementer:
```
You are the Implementer. Base/integration branch: `main`. Your assigned implementation branch is `implementer/task-24-dock-icon` (already checked out).

Task 24 (S): use a custom macOS dock icon.

Context: the icon source is implementer/src/todo_md/assets/dock_icon.jpg (450x450 JPEG). Tk PhotoImage cannot decode JPEG natively, so generate a PNG version once using macOS `sips -s format png` (or equivalent lossless format conversion) and commit it as implementer/src/todo_md/assets/dock_icon.png; keep the original jpg. On macOS, `root.iconphoto(True, photo)` sets the app's dock icon; keep the PhotoImage alive in an instance attribute. Runtime stays stdlib-only (no Pillow or other deps).

Before editing: verify the current branch is `implementer/task-24-dock-icon` and `git status --short` is clean; if not, stop and report.

Scope — you may modify/create ONLY:
- implementer/src/todo_md/app.py
- implementer/src/todo_md/assets/dock_icon.png (new, derived from the existing jpg)
- implementer/src/tests/test_gui_dock_icon.py (new)
Do not change anything outside implementer/src/. Changes anywhere under architect/ or at the repository root are forbidden.

Requirements:
1. TodoApp loads the PNG dock icon package-relative (resolve the path via the todo_md package location, like other assets) and applies it with self.root.iconphoto(True, photo) at startup; store the PhotoImage on self (e.g. self._dock_icon) so it is not garbage-collected.
2. The PNG is a faithful format conversion of the provided jpg (no resizing beyond what sips does by default is required; keep it simple, e.g. original 450x450).
3. Fail soft: if the icon file is missing or unreadable, catch the error, skip iconphoto, and the app must start and run normally.
4. No other behavior changes (themes, layout, handlers untouched).

Tests (new file tests/test_gui_dock_icon.py; GUI tests on a real display: destroy root in finally, call root.update() after building):
- the PNG asset loads as a tk.PhotoImage with width() > 0 and height() > 0;
- building TodoApp leaves the icon reference stored on the instance and iconphoto applied without error (the app can assert the stored reference is a PhotoImage with non-zero size);
- with the icon path simulated to a missing file (monkeypatch the path resolution or the asset lookup used by TodoApp), TodoApp still builds and the app is usable (no exception, root alive), with no stored icon reference.

Run from implementer/src:
- .venv/bin/python -m pytest tests/test_gui_dock_icon.py -v
- .venv/bin/python -m pytest tests -v

Commit your work to `implementer/task-24-dock-icon`. Forbid: creating/switching/merging/rebasing/renaming/deleting branches, pushing, committing to main, broad staging or destructive working-tree operations.

Handoff must end with: RESULT: SUCCESS or RESULT: FAILURE; BRANCH: implementer/task-24-dock-icon; COMMIT: <full commit hash>; one-line test summary; blockers if any.
```

## Queue

- Fix a GUI bug: after creating a todo item or a new list by typing the name and pressing enter, in the input field the typed text is replaced by the palceholder text that doesn't diappear when you start typing again, because the focus is already on the input field. You need to implement a check so that if the focus is already on the input field no plecholder text in added into the field.
- Implement a build script in bash/zsh that builds the application in a self contained executable file for MacOS (Apple Silicon/arm64). Update 'README.md' file with precise instructions on how to use that script.
- Analyse the Known Architectural Debt in 'architect/DESIGN.md' and make a plan to reduce it.

## Active Blockers

None.

## Recently Completed

- Task 23 — deterministic focus tests: placeholder/new-list GUI tests use `event_generate("<FocusIn>")`/`"<FocusOut>"` instead of WM focus (fixes post-merge flakiness); after one child timeout, completed from uncommitted checkpoint; two consecutive 73/73 runs; merged (0c46f37).
- Task 22 — input placeholders: muted-gray hints on both entries (placeholder_fg), cleared on focus-in, restored on empty focus-out, counted as empty on submit; new `test_gui_placeholders.py` + minimal `test_gui_new_list.py` contract alignment; merged (3c26e92).
- Task 21 — version badge colors: fallback-path label bg pinned to window palette bg, muted-gray fg in both themes, bg+fg refreshed on toggle; new `test_gui_version_colors.py`; verified, merged (4c03028).
- Task 20 — Yes/No confirmation popups (messagebox.askyesno) gate both delete-list and delete-item GUI handlers; No = full no-op; verified, merged (8d07a84).
- Task 19 — versioning: `bump_version.sh` + pre-commit hook auto-increments `todo_md/VERSION` (patch); headless `get_version()`; bottom-right GUI version badge; verified, merged (4fd69737, at VERSION 0.1.3).
