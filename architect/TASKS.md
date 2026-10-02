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
- **Size:** S
- **Branch:** `implementer/task-44-edit-todo-item` (base and integration: `main`)
- **Scope:** Add a pencil/edit icon left of the trash icon on each item row. Clicking it opens a modal with an entry pre-populated with the item text and Cancel/Save buttons below it. Save persists the new text immediately; Cancel closes with no change. Controller gains a headless item-edit path. Existing user-placed assets `implementer/src/todo_md/assets/edit.png`, `edit_18.png`, and the modified `LICENSE.txt` must be included in the task commit.
- **Acceptance criteria:**
  1. Each item row shows the edit icon (from `assets/edit_18.png`, themed like `trash_18.png`) strictly left of the trash icon.
  2. Clicking the edit icon opens a modal dialog containing an entry pre-populated with the current item text and two buttons below it: `cancel` (closes, no action) and `save` (persists new text, closes, list re-read and refreshed).
  3. Headless controller method (e.g. `TodoController.edit_item`) performs the edit through domain/storage, persists immediately, and contains no tkinter imports.
  4. Save with empty/whitespace-only input persists nothing; modal still closes. Saving identical text is harmless.
  5. `LICENSE.txt` pencil-icon attribution block is corrected to name the real files (`edit.png`, `edit_18.png`) instead of the mislabeled `trash.png`/`pencil.png`.
  6. New tests: headless controller edit tests and a GUI test file (pattern: `tests/test_gui_trash_icon.py`, `tests/test_gui_confirm.py`, conftest dialog-guard conventions) covering icon placement, pre-populated entry, save persistence to the Markdown file, cancel no-change, and empty-input rejection.
- **Required tests:** new GUI + controller tests; full suite green.
- **Test commands (from `implementer/`):** `(cd src && .venv/bin/python -m pytest tests/test_gui_edit.py tests/test_controller.py -v)` then `(cd src && .venv/bin/python -m pytest tests -v)`.
- **Prompt:**

```
Task 44 (size S): implement editing of a single todo item.

BRANCH: you MUST work on branch `implementer/task-44-edit-todo-item`, which is already checked out and based on `main` (the integration branch).

Start by following the Implementer Mandatory Execution Clock phase rules:
1. Your FIRST tool call MUST run `../architect/tools/implementer-run.sh` with no arguments (read-only harness; you may execute it but never modify it).
2. Every subsequent Bash command MUST use that same wrapper.
3. Verify the current branch is `implementer/task-44-edit-todo-item` and inspect the working tree (`git status --short`) before editing. Known pre-existing state that belongs to this task and must end up in your commit: untracked `implementer/src/todo_md/assets/edit.png`, untracked `implementer/src/todo_md/assets/edit_18.png`, and the user-modified `implementer/src/todo_md/assets/LICENSE.txt`.

FEATURE (work under `implementer/` only):
- Add a pencil/edit icon on each todo item row, positioned to the LEFT of the existing trash bin icon. Use `implementer/src/todo_md/assets/edit_18.png`, loaded and themed exactly like the existing `trash_18.png` usage in `implementer/src/todo_md/app.py` (read that code and the `tests/test_gui_trash_icon.py` / `tests/test_gui_delete_icon.py` tests as the reference pattern).
- Clicking the edit icon opens a modal dialog: one input (entry) pre-populated with the item's current text, and below it two buttons: `cancel` (close the modal, no changes) and `save` (close the modal after saving the new text to the item). Model the modal on the existing confirmation-dialog style already in `app.py`, including theme-aware colors.
- Add a headless controller method (e.g. `TodoController.edit_item`) that updates the item text through the domain/storage layers and persists immediately with the same re-read/refresh behavior as other mutations. No tkinter imports in controller/domain code.
- Save with empty or whitespace-only input must persist nothing (modal still closes). Saving the unchanged text is harmless.
- Fix the pencil-icon block in `implementer/src/todo_md/assets/LICENSE.txt`: it currently mislabels the asset as `trash.png`/`pencil.png`; rename it to reference the real files `edit.png` and `edit_18.png` (keep the Flaticon CC-BY 4.0 attribution as written).

TESTS to add/update (working directory `implementer/src/`):
- Headless: extend `tests/test_controller.py` for the new edit method (text change persisted to the Markdown file, unchanged/whitespace handling, list re-read).
- New `tests/test_gui_edit.py` following `tests/test_gui_trash_icon.py` and `tests/test_gui_confirm.py` conventions and `tests/conftest.py` (isolated data dirs, dialog guards, owned roots updated and destroyed): edit icon present on item rows and positioned left of the trash icon; modal opens pre-populated with the item text; Save persists the new text to the `.md` file and closes; Cancel closes without change; Save with empty/whitespace input persists nothing.
- No test may require human input.

Commands to run from `implementer/`:
- Targeted: `(cd src && .venv/bin/python -m pytest tests/test_gui_edit.py tests/test_controller.py -v)`
- Full: `(cd src && .venv/bin/python -m pytest tests -v)`

RULES:
- Only modify files under `implementer/`. Never modify anything under `architect/` or at the repository root.
- Never create, switch, merge, rebase, rename, delete, or push branches. Never commit to `main`. No broad staging or destructive working-tree operations; stage only the specific files for this task (including the three pre-existing asset files).
- Commit completed work. End with a handoff stating: RESULT (SUCCESS/FAILURE), branch name, commit hash, test results, and any blockers.
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
