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
- **Checkpoint:** `996faf0` (branch tip; first delegation timed out at 20 min with `COMMIT: NONE` and no working-tree changes beyond the three pre-existing user asset files: untracked `implementer/src/todo_md/assets/edit.png`, `edit_18.png`, modified `LICENSE.txt`).
- **Current status:** nothing implemented; starting state is the branch tip.
- **Current blocker (resolved by split):** single-shot delegation exceeded the 20-minute child limit without producing a commit.
- **Revised approach:** 44a = headless controller edit path + headless tests (no GUI). 44b = edit icon left of trash, edit modal, GUI tests, LICENSE/asset commit.
- **Micro-task 44a (now delegating):** add `TodoController.edit_item` updating item text through domain/storage, persisting immediately with the same re-read/refresh as other mutations; no tkinter in controller/domain. Empty/whitespace-only new text is rejected (no persistence); unchanged text is harmless. Extend `tests/test_controller.py` accordingly.
  - **Acceptance criteria (44a):** controller method persists the new text to the `.md` file and re-reads; empty/whitespace input persists nothing; no tkinter imports introduced outside GUI layer; headless tests pass.
  - **Test commands (from `implementer/`):** `(cd src && .venv/bin/python -m pytest tests/test_controller.py -v)` then `(cd src && .venv/bin/python -m pytest tests -v)`.
- **Micro-task 44b (queued after 44a, same branch):** add the `edit_18.png` icon strictly left of the trash icon on each item row (themed like `trash_18.png` in `implementer/src/todo_md/app.py`; reference `tests/test_gui_trash_icon.py` / `tests/test_gui_delete_icon.py`); clicking opens a modal styled like the existing confirmation dialogs (theme-aware colors) with an entry pre-populated with the item text and `cancel` / `save` buttons below it; Save calls the 44a controller path and refreshes, Cancel closes unchanged, empty/whitespace Save persists nothing. New `tests/test_gui_edit.py` per `tests/test_gui_confirm.py` + `tests/conftest.py` conventions (isolated dirs, dialog guards, owned roots updated and destroyed). Fix the mislabeled pencil block in `implementer/src/todo_md/assets/LICENSE.txt` to name the real files `edit.png` / `edit_18.png` (keep the Flaticon CC-BY 4.0 attribution). Include the three pre-existing asset files in the 44b commit.
  - **Acceptance criteria (44b):** icon placement left of trash; modal pre-populated; Save persists to the `.md` file and closes; Cancel no-change; empty Save no-persistence; LICENSE fixed; full suite green.
  - **Test commands (from `implementer/`):** `(cd src && .venv/bin/python -m pytest tests/test_gui_edit.py -v)` then `(cd src && .venv/bin/python -m pytest tests -v)`.
- **Prompt (44a):**

```
Task 44a (headless micro-task of task 44): add a controller method to edit a single todo item's text.

BRANCH: you MUST work on branch `implementer/task-44-edit-todo-item` (already checked out, based on integration branch `main`). No GUI work in this micro-task.

Start by following the Implementer Mandatory Execution Clock phase rules:
1. Your FIRST tool call MUST run `../architect/tools/implementer-run.sh` with no arguments (read-only harness; execute it, never modify it).
2. Every subsequent Bash command MUST use that wrapper.
3. Verify the current branch and inspect the working tree (`git status --short`) before editing. Pre-existing untracked asset files and a modified `LICENSE.txt` under `implementer/src/todo_md/assets/` are NOT part of this micro-task: do not stage, modify, or delete them.

SCOPE (work under `implementer/` only):
- Read `implementer/src/todo_md/app.py` (TodoController) and `implementer/src/todo_md/models.py`, `storage.py` to follow the existing mutation pattern (add/toggle/remove).
- Add a headless `TodoController.edit_item` (name may follow existing conventions) that updates a single item's text through domain/storage and persists immediately with the same re-read/refresh behavior as other mutations. No tkinter imports in controller/domain code.
- Semantics: empty or whitespace-only new text is rejected (nothing persisted, no crash); saving the unchanged text is a harmless no-op.

TESTS (working directory `implementer/src/`):
- Extend `tests/test_controller.py`: edit persists the new text to the `.md` file and the controller re-reads it; empty/whitespace input persists nothing; unchanged text is harmless. Headless only; no display required.

Commands from `implementer/`:
- Targeted: `(cd src && .venv/bin/python -m pytest tests/test_controller.py -v)`
- Full: `(cd src && .venv/bin/python -m pytest tests -v)`

RULES:
- Only modify files under `implementer/`; never touch `architect/` or the repository root.
- Never create/switch/merge/rebase/rename/delete/push branches; never commit to `main`; no broad staging or destructive operations; stage only this micro-task's files.
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
