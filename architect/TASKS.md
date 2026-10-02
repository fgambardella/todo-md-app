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
- **Checkpoint:** `d2469ac` (44a complete and independently verified: `TodoList.edit` + headless `TodoController.edit_item` with empty-text rejection and unchanged-text no-op; `tests/test_controller.py` extended; full suite 309 passed / 2 gated skips; commit also includes hook-staged VERSION bump).
- **Current status:** 44a done and verified on the branch; 44b (GUI icon + modal + GUI tests + LICENSE/asset commit) now delegating.
- **Revised approach:** split into sequential micro-tasks after the first timeout; 44a done, 44b next.
- **Micro-task 44a (done, verified `d2469ac`):** headless `TodoController.edit_item` + domain `TodoList.edit`; empty/whitespace rejected, unchanged text no-op; headless tests green.
- **Micro-task 44b (now delegating, same branch):** add the `edit_18.png` icon strictly left of the trash icon on each item row (themed like `trash_18.png` in `implementer/src/todo_md/app.py`; reference `tests/test_gui_trash_icon.py` / `tests/test_gui_delete_icon.py`); clicking opens a modal styled like the existing confirmation dialogs (theme-aware colors) with an entry pre-populated with the item text and `cancel` / `save` buttons below it; Save calls the 44a controller path and refreshes, Cancel closes unchanged, empty/whitespace Save persists nothing. New `tests/test_gui_edit.py` per `tests/test_gui_confirm.py` + `tests/conftest.py` conventions (isolated dirs, dialog guards, owned roots updated and destroyed). Fix the mislabeled pencil block in `implementer/src/todo_md/assets/LICENSE.txt` to name the real files `edit.png` / `edit_18.png` (keep the Flaticon CC-BY 4.0 attribution). Include the three pre-existing asset files in the 44b commit.
  - **Acceptance criteria (44b):** icon placement left of trash; modal pre-populated; Save persists to the `.md` file and closes; Cancel no-change; empty Save no-persistence; LICENSE fixed; full suite green.
  - **Test commands (from `implementer/`):** `(cd src && .venv/bin/python -m pytest tests/test_gui_edit.py -v)` then `(cd src && .venv/bin/python -m pytest tests -v)`.
- **Prompt (44b):**

```
Task 44b (GUI micro-task of task 44): add the edit icon and edit modal.

The headless method `TodoController.edit_item(name, index, text)` already exists on this branch (raises ValueError on empty/whitespace text; no-op on unchanged text). Do not modify controller/domain logic.

BRANCH: you MUST work on branch `implementer/task-44-edit-todo-item` (already checked out, based on integration branch `main`).

Start by following the Implementer Mandatory Execution Clock phase rules:
1. Your FIRST tool call MUST run `../architect/tools/implementer-run.sh` with no arguments (read-only harness; execute it, never modify it).
2. Every subsequent Bash command MUST use that wrapper.
3. Verify the current branch and inspect the working tree (`git status --short`) before editing. Pre-existing state belonging to this micro-task that MUST be included in your commit: untracked `implementer/src/todo_md/assets/edit.png`, untracked `implementer/src/todo_md/assets/edit_18.png`, and the user-modified `implementer/src/todo_md/assets/LICENSE.txt`.

FEATURE (work under `implementer/` only, GUI layer of `implementer/src/todo_md/app.py`):
- Add a pencil/edit icon on each todo item row, positioned strictly LEFT of the existing trash bin icon. Use `implementer/src/todo_md/assets/edit_18.png`, loaded and themed exactly like the existing `trash_18.png` usage (reference: the trash-icon code in `app.py` plus `tests/test_gui_trash_icon.py` / `tests/test_gui_delete_icon.py`).
- Clicking the edit icon opens a modal dialog styled like the existing confirmation dialogs (theme-aware colors, same window style as the other dialogs): one entry pre-populated with the item's current text, and below it two buttons: `cancel` (close the modal, no changes) and `save` (call the existing controller `edit_item` for this item, then close the modal and refresh the list).
- Save with empty/whitespace-only input persists nothing (modal still closes; the controller raises ValueError on such input, handle it gracefully); saving unchanged text is harmless.
- Fix the pencil block in `implementer/src/todo_md/assets/LICENSE.txt`: it mislabels the asset as `trash.png`/`pencil.png`; reference the real files `edit.png` and `edit_18.png`, keeping the Flaticon CC-BY 4.0 attribution as written.

TESTS (working directory `implementer/src/`):
- New `tests/test_gui_edit.py` per `tests/test_gui_trash_icon.py`, `tests/test_gui_confirm.py`, and `tests/conftest.py` conventions: edit icon present on item rows and positioned left of the trash icon; modal opens with the entry pre-populated with the item text; Save persists the new text to the `.md` file and closes; Cancel closes without change; Save on empty/whitespace input persists nothing. No test may need human input.

Commands from `implementer/`:
- Targeted: `(cd src && .venv/bin/python -m pytest tests/test_gui_edit.py -v)`
- Full: `(cd src && .venv/bin/python -m pytest tests -v)`

RULES:
- Only modify files under `implementer/`; never touch `architect/` or the repository root; do not change controller/domain logic already committed for 44a.
- Never create/switch/merge/rebase/rename/delete/push branches; never commit to `main`; no broad staging or destructive operations; stage only this micro-task's files (including the three pre-existing asset files).
- Commit completed work. End with: RESULT (SUCCESS/FAILURE), branch, commit hash, test results, blockers.
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
