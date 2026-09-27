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
- Branch: `implementer/task-25-placeholder-focus` (base and integration branch: `main`; checked out)
- Checkpoint: `COMMIT: NONE` — first attempt timed out. The core fix exists as uncommitted working-tree changes: focus guard in `_restore_placeholder` (`implementer/src/todo_md/app.py`: early return when `root.focus_get() is entry`) + 4 new regression tests in `implementer/src/tests/test_gui_placeholders.py` (10/10 pass). Never discard or rewrite these uncommitted changes.
- Current blocker: `tests/test_gui_new_list.py::test_return_creates_list` fails — it asserts the pre-fix buggy contract (placeholder text present in the still-focused entry after submit).
- Remaining scope:
  1. Align only the post-submit assertion in `test_gui_new_list.py::test_return_creates_list` with the fixed behavior (still-focused entry cleared and placeholder-free, `== ""`); keep its on-disk/listbox/`current_list` assertions.
  2. Full suite green.
  3. Commit `app.py` + both test files on the branch.
- Acceptance criteria:
  1. Submit with focus on the field leaves the entry cleared, no placeholder text; further typing works normally.
  2. Genuine focus-out on an empty entry restores the placeholder; focus-in clears a visible placeholder.
  3. No changes beyond placeholder focus handling.
- Commands (from `implementer/src`):
  - `.venv/bin/python -m pytest tests/test_gui_placeholders.py tests/test_gui_new_list.py -v`
  - `.venv/bin/python -m pytest tests -v`

Prompt for the Implementer:
```
You are the Implementer. Base/integration branch: `main`. Your assigned implementation branch is `implementer/task-25-placeholder-focus` (already checked out). This is a follow-up after a timeout; the previous attempt left the core fix uncommitted in the working tree.

Before editing: verify the branch is `implementer/task-25-placeholder-focus` and `git status --short` shows exactly these two modified files:
- implementer/src/todo_md/app.py
- implementer/src/tests/test_gui_placeholders.py
If anything else is modified or these are missing, stop and report. Do NOT discard, revert, or rewrite the existing uncommitted changes.

Task 25 (S, follow-up): finish the fix for the placeholder bug where the hint re-enters a still-focused input after submit.

Already in place (do not redo): `_restore_placeholder` in todo_md/app.py returns early when `self.root.focus_get() is entry`; 4 new regression tests in tests/test_gui_placeholders.py (10/10 pass).

Remaining work:
1. tests/test_gui_new_list.py::test_return_creates_list currently asserts the old buggy contract: after Enter it expects `app.new_name_entry.get() == "Insert the name of a new list here"`. Update ONLY that post-submit assertion (and its comment) to the fixed behavior: while the entry still has focus it must be cleared and placeholder-free (`== ""`). Leave the rest of the test (on-disk file, listbox selection, current_list) untouched.
2. Verify from implementer/src: `.venv/bin/python -m pytest tests/test_gui_placeholders.py tests/test_gui_new_list.py -v`, then `.venv/bin/python -m pytest tests -v` — all green.
3. Stage exactly the three files (todo_md/app.py, tests/test_gui_placeholders.py, tests/test_gui_new_list.py) and commit them to `implementer/task-25-placeholder-focus` with a clear message.

Scope — you may modify ONLY the three files above. Do not change anything outside implementer/src/. Changes anywhere under architect/ or at the repository root are forbidden. Forbid: creating/switching/merging/rebasing/renaming/deleting branches, pushing, committing to main, destructive working-tree operations.

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
