# TASKS.md

## Project Goal

Build a macOS desktop TODO app in Python with a stdlib-only runtime. Persist each list as a portable Markdown file with GFM checkboxes. Keep domain, persistence, and controller logic headlessly testable beneath the Tkinter GUI, with persistent settings and light/dark themes.

## Test Policy

- Framework: pytest, already used throughout `implementer/src/tests/`.
- Full suite from `implementer/`: `(cd src && .venv/bin/python -m pytest tests -v)`.
- Targeted convention from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/<file>.py -v)`.
- Tests require `implementer/src/` as working directory for existing relative asset paths; tools may set that workdir directly and run the inner command.
- Build/release changes also require the corresponding gated tests from `implementer/src/`: `RUN_BUILD_TESTS=1 .venv/bin/python -m pytest tests/test_build_script.py -v`; `RUN_RELEASE_TESTS=1 .venv/bin/python -m pytest tests/test_release_package.py -v`.
- GUI tests use isolated data/config directories. Geometry tests map windows on the local display; structural-only label checks keep roots withdrawn before construction-time idle processing. Owned roots are updated and unconditionally destroyed, including failure paths; headless tests never launch the GUI.
- Automated tests must never require human input. Mock expected dialog choices explicitly; unexpected dialogs must fail immediately or at teardown when swallowed by Tk. Shared facilities: `implementer/src/tests/conftest.py`. Negative subprocess tests assert expected inner failures while the outer suite remains green. Never blanket-answer Yes, suppress failures, or add skips/xfails to hide regressions.

## Current Implementation Summary

- Lists persist as separate Markdown files with atomic writes and filesystem-safe names; validated item operations are persisted immediately.
- The GUI supports list creation, item toggles, per-item deletion, placeholder hints, and confirmation of destructive actions. Main-window sizing keeps sidebar controls fully accessible. Completed items retain completion order above unfinished items, showing only the newest configured count without deleting hidden items.
- Light/dark themes include readable controls and insertion cursors, a theme-aware version badge, and custom dock/Finder icons. Settings theme controls have consistent palette colors and symmetric margins, including during live theme changes.
- Settings use fully visible, centered Save/Cancel actions, validate and save the full payload, apply theme and completed-item filtering live, and discard unsaved controls on window Cancel. Filtering never changes stored content.
- Directory changes apply live with optional list movement and an explicit confirmation question; popup Cancel retains the directory while saving other settings. Populated destinations are accepted, transfers reject filename collisions without overwriting, equivalent paths are harmless, and configuration stays fixed.
- Relocation failures preserve recoverable files and refresh the active view. Failed settings persistence keeps the destination usable and supports retry without repeating completed moves; pending theme/filter edits remain unapplied.
- Automated GUI tests intercept unexpected dialogs and verify cleanup after failures without human interaction. Structural label checks avoid unnecessary native-window presentation.
- Build and release scripts produce a launch-tested Apple Silicon app bundle and versioned distributable ZIP.

## Active Task

- **ID:** 44
- **Title:** Edit a single todo item (pencil icon + edit modal)
- **Size:** S (decomposed after timeout; sequential micro-tasks 44a → 44b)
- **Branch:** `implementer/task-44-edit-todo-item` (base and integration: `main`)
- **Checkpoint:** last commit `a3b91b6` plus uncommitted working-tree changes from the timed-out 44b run (architect-inspected): `app.py` GUI implementation (edit icon left of trash, modal with pre-filled entry, save/cancel, graceful empty-text handling), `LICENSE.txt` fix, two untracked PNGs; no `tests/test_gui_edit.py`, no 44b commit. 44a remains complete at `d2469ac`.
- **Current status:** 44b feature code present but uncommitted and regressing ~39 existing GUI tests: `_item_rows` is now a 5-tuple `(var, cb, label, del_ctrl, edit_ctrl)` while several tests unpack 4-tuples.
- **Current blocker:** 44b run #2 timed out at 20 min after implementing the feature but before tests/commit; full suite red from the tuple-unpack breakage.
- **Revised approach:** narrowed 44b' run: fix the tuple unpacks in existing tests, add `tests/test_gui_edit.py`, get the full suite green, commit all 44b files including the three asset files. No new feature code.
- **Micro-task 44a (done, verified `d2469ac`):** headless `TodoController.edit_item` + domain `TodoList.edit`; empty/whitespace rejected, unchanged text no-op; headless tests green.
- **Acceptance criteria (44b'):** icon left of trash; modal pre-populated; Save persists and closes; Cancel no-change; empty Save no-persistence; LICENSE names `edit.png`/`edit_18.png`; full suite green; single 44b commit includes the asset files.
- **Test commands (from `implementer/`):** `(cd src && .venv/bin/python -m pytest tests/test_gui_edit.py -v)` then `(cd src && .venv/bin/python -m pytest tests -v)`.
- **Prompt (44b'):**

```
Task 44b' (narrowed completion micro-task of task 44): fix test regressions, add the edit GUI tests, commit.

The GUI feature (edit icon left of the trash icon + edit modal) is already implemented on this branch but UNCOMMITTED in the working tree, along with the `LICENSE.txt` fix and untracked `implementer/src/todo_md/assets/edit.png`, `edit_18.png`. The headless `TodoController.edit_item(name, index, text)` is already committed. Do NOT add or change feature code in `app.py`, `models.py`, or `storage.py`.

BRANCH: you MUST work on branch `implementer/task-44-edit-todo-item` (already checked out, based on integration branch `main`).

Start by following the Implementer Mandatory Execution Clock phase rules:
1. Your FIRST tool call MUST run `../architect/tools/implementer-run.sh` with no arguments (read-only harness; execute it, never modify it).
2. Every subsequent Bash command MUST use that wrapper.
3. Verify the current branch and inspect the working tree (`git status --short`) before editing.

KNOWN REGRESSION (architect-verified): `app._item_rows` elements are now 5-tuples `(var, cb, label, del_ctrl, edit_ctrl)`; existing tests still unpack 4-tuples and ~39 GUI tests fail with `ValueError: too many values to unpack` (e.g. `test_gui_contrast.py`, `test_gui_layout.py`, `test_gui_settings.py`, `test_gui_theme.py`, `test_gui_theme_switch.py`, `test_gui_toggle.py`).

SCOPE (work under `implementer/` only):
- Fix the 4-tuple unpacks of `app._item_rows` in the affected existing tests minimally (append an extra `_edit` variable). If the full suite reveals other regressions caused by the uncommitted 44b change, fix those test-side issues the same minimal way.
- New `tests/test_gui_edit.py` per `tests/test_gui_trash_icon.py`, `tests/test_gui_confirm.py`, and `tests/conftest.py` conventions: edit icon present on item rows and positioned left of the trash icon; modal opens with the entry pre-populated with the item text; Save persists the new text to the `.md` file and closes; Cancel closes without change; Save on empty/whitespace input persists nothing. No test may need human input.

Commands from `implementer/`:
- Targeted: `(cd src && .venv/bin/python -m pytest tests/test_gui_edit.py -v)`
- Full: `(cd src && .venv/bin/python -m pytest tests -v)`

COMMIT: stage and commit exactly: `implementer/src/todo_md/app.py`, `implementer/src/todo_md/assets/LICENSE.txt`, `implementer/src/todo_md/assets/edit.png`, `implementer/src/todo_md/assets/edit_18.png`, `implementer/src/tests/test_gui_edit.py`, and the modified existing test files.

RULES:
- Only modify files under `implementer/`; never touch `architect/` or the repository root.
- Never create/switch/merge/rebase/rename/delete/push branches; never commit to `main`; no broad staging or destructive operations.
- End with: RESULT (SUCCESS/FAILURE), branch, commit hash, test results, blockers.
```

## Queue

None.

## Active Blockers

None.

## Recently Completed

- 43: Withdrawn structural long-label test and lifecycle regression; independently verified and approved; `47020e50c32afa52fb32296b87bc9991d18b3989`.
- 42: Input caret contrast across themes; independently verified and approved; `dceb909362fb036ec69712139c27492d86c9b5d3`.
- 41: Persisted completion order and safe filtered GUI callbacks; independently verified and approved; `5b9c4457bf25fc6b682ffd1e14e243577789e81c`.
- 40: Settings Theme palette and margins; independently verified and approved; `9d785ef23b8b9778645936b5e7f42113a8ae9434`.
- 39: Visible centered Settings actions; independently verified and approved; `7c69eb2413098f97ffa91d5e2507578c07aac669`.
