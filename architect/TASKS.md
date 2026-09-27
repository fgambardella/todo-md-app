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
- Dock icon: on macOS the app sets a custom dock icon from a bundled PNG (committed alongside its JPEG source); missing/unsupported icons fail soft so startup is unaffected.

## Active Task

**Task 25 (S)** — Placeholder bug: hint re-enters a still-focused input after submit
- Branch: `implementer/task-25-placeholder-focus` (base and integration branch: `main`; not yet created)
- Scope: `implementer/src/todo_md/app.py` (placeholder focus logic); `implementer/src/tests/test_gui_placeholders.py` (new regression tests; minimal alignment of other placeholder-related GUI tests if needed).
- Bug report: after creating a todo item or a new list by typing the name and pressing Enter, the typed text in the input field is replaced by the placeholder text, which then does not disappear when the user starts typing again — because the focus never actually left the field, the focus-in clear never re-fires.
- Technical notes: the focus-out placeholder-restore path must verify the entry actually lost focus (e.g. `root.focus_get() is not entry`) before writing the placeholder; submit must leave the entry cleared. Follow the Task 23 deterministic-focus convention (`event_generate("<FocusIn>")`/`"<FocusOut>")` plus `focus_set()` where a real focus state is asserted).
- Acceptance criteria:
  1. After typing a name and pressing Enter (or clicking the button) to create an item/list, the entry is cleared and contains no placeholder text; further typing in the still-focused field works normally.
  2. The placeholder hint is still restored on a genuine focus-out (focus moved to another widget) when the field content is empty.
  3. Focus-in still clears a visible placeholder (existing behavior unchanged).
  4. No changes beyond the placeholder focus handling (themes, layout, handlers untouched).
- Required tests: with the entry focused and a submit performed, the field holds no placeholder text; a simulated real focus-out on an empty entry restores the placeholder; existing placeholder/new-list tests keep passing.
- Commands (from `implementer/src`):
  - `.venv/bin/python -m pytest tests/test_gui_placeholders.py -v`
  - `.venv/bin/python -m pytest tests -v`

Prompt for the Implementer:
```
You are the Implementer. Base/integration branch: `main`. Your assigned implementation branch is `implementer/task-25-placeholder-focus` (already checked out).

Task 25 (S): fix the placeholder bug where the hint re-enters a still-focused input after submit.

Bug: after creating a todo item or a new list by typing the name and pressing Enter, the typed text in the input field is replaced by the placeholder hint text, which then does not disappear when the user starts typing again. Cause: the focus-out placeholder-restore path runs even though the focus never actually left the entry, so the placeholder is written into a field that still has focus (the focus-in clear never re-fires).

Before editing: verify the current branch is `implementer/task-25-placeholder-focus` and `git status --short` is clean; if not, stop and report.

Scope — you may modify/create ONLY:
- implementer/src/todo_md/app.py
- implementer/src/tests/test_gui_placeholders.py (regression tests; extend or add as needed)
- minimal alignment of other placeholder-related GUI tests ONLY if their asserted contract conflicts with the fix
Do not change anything outside implementer/src/. Changes anywhere under architect/ or at the repository root are forbidden.

Requirements:
1. The placeholder-restore path must only write the placeholder when the entry has genuinely lost focus (e.g. check `self.root.focus_get() is not entry`); a submit while the field still has focus must leave the entry cleared and placeholder-free.
2. Genuine focus-out (focus moved to another widget) on an empty entry must still restore the muted-gray placeholder hint.
3. Focus-in must still clear a visible placeholder (existing behavior unchanged).
4. No other behavior changes (themes, layout, handlers untouched).

Tests (tests/test_gui_placeholders.py; GUI tests on a real display: destroy root in finally, call root.update() after building; use the deterministic-focus convention from the existing placeholder tests — `event_generate("<FocusIn>")`/`"<FocusOut>")` for events, `focus_set()` when a real focus state must be asserted):
- entry focused + submit performed (Enter in the entry): the field is cleared and does NOT contain the placeholder text, while still focused;
- focus genuinely moved away then `<FocusOut>` on an empty entry: the placeholder text is restored;
- focus-in on a field showing the placeholder clears it (regression guard).

Run from implementer/src:
- .venv/bin/python -m pytest tests/test_gui_placeholders.py -v
- .venv/bin/python -m pytest tests -v

Commit your work to `implementer/task-25-placeholder-focus`. Forbid: creating/switching/merging/rebasing/renaming/deleting branches, pushing, committing to main, broad staging or destructive working-tree operations.

Handoff must end with: RESULT: SUCCESS or RESULT: FAILURE; BRANCH: implementer/task-25-placeholder-focus; COMMIT: <full commit hash>; one-line test summary; blockers if any.
```

## Queue

- Implement a build script in bash/zsh that builds the application in a self contained executable file for MacOS (Apple Silicon/arm64). Update 'README.md' file with precise instructions on how to use that script.
- Analyse the Known Architectural Debt in 'architect/DESIGN.md' and make a plan to reduce it.

## Active Blockers

None.

## Recently Completed

- Task 24 — custom macOS dock icon: bundled PNG (450×450, from the kept jpg) applied via `iconphoto` at startup, reference kept on the instance, fail-soft on missing/unsupported icon; new `test_gui_dock_icon.py`; verified 76/76, merged (bd043dc, at VERSION 0.1.27).
- Task 23 — deterministic focus tests: placeholder/new-list GUI tests use `event_generate("<FocusIn>")`/`"<FocusOut>"` instead of WM focus (fixes post-merge flakiness); after one child timeout, completed from uncommitted checkpoint; two consecutive 73/73 runs; merged (0c46f37).
- Task 22 — input placeholders: muted-gray hints on both entries (placeholder_fg), cleared on focus-in, restored on empty focus-out, counted as empty on submit; new `test_gui_placeholders.py` + minimal `test_gui_new_list.py` contract alignment; merged (3c26e92).
- Task 21 — version badge colors: fallback-path label bg pinned to window palette bg, muted-gray fg in both themes, bg+fg refreshed on toggle; new `test_gui_version_colors.py`; verified, merged (4c03028).
- Task 20 — Yes/No confirmation popups (messagebox.askyesno) gate both delete-list and delete-item GUI handlers; No = full no-op; verified, merged (8d07a84).
- Task 19 — versioning: `bump_version.sh` + pre-commit hook auto-increments `todo_md/VERSION` (patch); headless `get_version()`; bottom-right GUI version badge; verified, merged (4fd69737, at VERSION 0.1.3).
