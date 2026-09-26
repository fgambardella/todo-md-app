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

**Task 23 (S)** — Make placeholder focus tests deterministic (corrective follow-up to task 22)
- Branch: `implementer/task-23-deterministic-focus-tests` (base and integration branch: `main`)
- Status: first Implementer run TIMED OUT at 1200s with no commit. Checkpoint: uncommitted working-tree edits already converting `tests/test_gui_placeholders.py` and `tests/test_gui_new_list.py` from real focus (`focus_set`/`focus_force`) to `entry.event_generate("<FocusIn>")`/`"<FocusOut>"` (see latest uncommitted diff); looks complete but unverified.
- Remaining scope: verify the uncommitted test edits, run the required tests (full suite twice), commit to the branch, hand off.
- Blocker: child timeout (likely slow/hung test run or handoff stall); no production bug identified.
- Revised approach: new Implementer continues on the same branch from the uncommitted state — review the existing edits (do not rewrite from scratch), fix only what fails, commit, hand off. If a test exposes a genuine production bug, stop and report instead of patching around it.
- Acceptance criteria:
  1. Focus in/out simulated via `event_generate` (plus `root.update()`); no reliance on the WM delivering real FocusIn/FocusOut (a `focus_force` solely to route a synthetic `<Return>` is acceptable in `test_gui_new_list.py`).
  2. All placeholder tests and `test_gui_new_list.py` pass; assertions preserved.
  3. Full suite passes twice in a row consecutively.
- Commands (from `implementer/src`):
  - `.venv/bin/python -m pytest tests/test_gui_placeholders.py tests/test_gui_new_list.py -v`
  - `.venv/bin/python -m pytest tests -q` (run twice)

Prompt for the Implementer:
```
You are the Implementer. Base/integration branch: `main`. Your assigned implementation branch is `implementer/task-23-deterministic-focus-tests` (already checked out).

Task 23 (S, follow-up after a timed-out run): finish making the placeholder focus tests deterministic.

Context: a previous run on this branch TIMED OUT without committing. The working tree contains its uncommitted edits: implementer/src/tests/test_gui_placeholders.py and implementer/src/tests/test_gui_new_list.py have already been converted from real focus (focus_set/focus_force) to entry.event_generate("<FocusIn>")/entry.event_generate("<FocusOut>") + app.root.update(). That conversion addresses the post-merge failures of task 22's placeholder tests (they previously relied on the window manager emitting real FocusIn events, which do not fire when the test window is not the active app).

Before editing: verify the current branch is `implementer/task-23-deterministic-focus-tests`; run `git status --short` — the two test files above should show as modified (uncommitted). If the tree does not match, stop and report.

Scope — you may modify ONLY:
- implementer/src/tests/test_gui_placeholders.py
- implementer/src/tests/test_gui_new_list.py
No production-code changes. Do NOT rewrite the existing uncommitted conversion from scratch; review it and fix only what is wrong or failing.
Do not change anything outside implementer/src/. Changes anywhere under architect/ or at the repository root are forbidden.

Work order:
1. Review the uncommitted diff (`git diff -- implementer/src/tests/`): confirm every assertion from the previous version is preserved and the focus simulation is deterministic.
2. Run from implementer/src: `.venv/bin/python -m pytest tests/test_gui_placeholders.py tests/test_gui_new_list.py -v`
3. Fix failures minimally (tests only), re-run until green.
4. Run `.venv/bin/python -m pytest tests -q` twice back-to-back; both runs must pass.
5. Commit the two test files to `implementer/task-23-deterministic-focus-tests` (message summarizing the deterministic-focus fix).

If a test exposes a genuine production bug, do NOT work around it: stop and report it.

Forbid: creating/switching/merging/rebasing/renaming/deleting branches, pushing, committing to `main`, broad staging (e.g. `git add -A`) or destructive working-tree operations (do not discard the existing uncommitted edits).

Handoff must end with: RESULT: SUCCESS or RESULT: FAILURE; BRANCH: implementer/task-23-deterministic-focus-tests; COMMIT: <full commit hash>; one-line test summary (include both full-suite runs); blockers if any.
```

## Queue

- Now the application is shown with a standard icon in the MacOS dock, but I want it uses the following image: 'implementer/src/todo_md/assets/dock_icon.jpg'
- Implement a build script in bash/zsh that builds the application in a self contained executable file for MacOS (Apple Silicon/arm64). Update 'README.md' file with precise instructions on how to use that script.
- Analyse the Known Architectural Debt in 'architect/DESIGN.md' and make a plan to reduce it.

## Active Blockers

None.

## Recently Completed

- Task 22 — input placeholders: muted-gray hints on both entries (placeholder_fg), cleared on focus-in, restored on empty focus-out, counted as empty on submit; new `test_gui_placeholders.py` + minimal `test_gui_new_list.py` contract alignment; merged (3c26e92); post-merge flaky real-focus tests being fixed in Task 23.
- Task 21 — version badge colors: fallback-path label bg pinned to window palette bg, muted-gray fg in both themes, bg+fg refreshed on toggle; new `test_gui_version_colors.py`; verified, merged (4c03028).
- Task 20 — Yes/No confirmation popups (messagebox.askyesno) gate both delete-list and delete-item GUI handlers; No = full no-op; verified, merged (8d07a84).
- Task 19 — versioning: `bump_version.sh` + pre-commit hook auto-increments `todo_md/VERSION` (patch); headless `get_version()`; bottom-right GUI version badge; verified, merged (4fd69737, at VERSION 0.1.3).
- Task 18 — Enter in new-list entry creates the list (Return bind on `new_name_entry` + `test_gui_new_list.py`): verified, merged (82d5271).
