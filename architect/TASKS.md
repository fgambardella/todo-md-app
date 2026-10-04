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

- Lists persist as separate Markdown files with atomic writes and filesystem-safe names; validated operations persist immediately.
- The GUI supports list creation, item toggles, per-item deletion, placeholder hints, and confirmation of destructive actions. Main-window sizing keeps sidebar controls accessible. Completed items retain completion order above unfinished items, showing only the newest configured count without deleting hidden items.
- Light/dark themes include readable controls and insertion cursors, a theme-aware version badge, and custom dock/Finder icons. Settings theme controls have consistent palette colors and symmetric margins, including during live changes.
- Settings use fully visible, centered Save/Cancel actions, validate and save the full payload, apply theme and completed-item filtering live, and discard unsaved controls on window Cancel. Filtering never changes stored content.
- Directory changes apply live with optional list movement and an explicit confirmation; popup Cancel retains the directory while saving other settings. Populated destinations are accepted, collisions are rejected without overwriting, equivalent paths are harmless, and configuration stays fixed.
- Relocation failures preserve recoverable files and refresh the active view; failed settings persistence keeps the destination usable and supports retry without repeating moves, pending theme/filter edits remain unapplied.
- Automated GUI tests intercept unexpected dialogs and verify cleanup after failures without human interaction.
- Item rows have an edit icon left of the trash; the pre-populated modal persists text to the `.md` file on Save, while Cancel or empty input is a no-op. Double-clicking an unfinished item's text opens the same modal; completed items ignore double-clicks.
- Build and release scripts produce a launch-tested Apple Silicon app bundle and versioned distributable ZIP.

## Active Task

- **Task 46 (M)** — Description field for todo items.
- Branch: `implementer/46-item-description` (base and integration: `main`).
- Scope: `TodoItem.description` (str, default `""`); `TodoList.edit` sets title + description; storage round-trips description as two-space-indented continuation lines under each checkbox line (legacy files parse as empty description; empty description writes no extra lines); controller persists description through `edit_item`; edit modal gains a pre-populated description text box (Save persists both fields; Cancel or empty title stays a no-op).
- Micro-tasks (sequential, same branch, prior commit as start state): 46.1 domain (done, `080f035`); 46.2a storage only (done, `427a3b5`); 46.2b controller only (`todo_md/app.py` TodoController, `tests/test_controller.py`); 46.3 GUI modal description box (`tests/test_gui_edit.py`, `tests/test_gui_double_click.py`).
- Acceptance: title remains required non-empty after strip; description stored stripped, `""` when blank, internal newlines preserved; legacy `.md` without descriptions loads unchanged; no spurious lines written for empty descriptions; every mutation persists immediately; full suite green.
- Required tests: full suite plus targeted `tests/test_models.py`, `tests/test_storage.py`, `tests/test_controller.py`, `tests/test_gui_edit.py`, `tests/test_gui_double_click.py` (subset per micro-task).
- Test commands from `implementer/`: full `(cd src && .venv/bin/python -m pytest tests -v)`; targeted `(cd src && .venv/bin/python -m pytest tests/<files>.py -v)`.
- Checkpoint: 46.1 verified at `080f035`; 46.2a verified at `427a3b5` (3-tuple storage contract; `test_storage.py` green, 35 passed; full suite expectedly red until 46.2b: 115 failed / 214 passed / 2 errors). Next: 46.2b controller micro-task, prompt below.
- Prompt (current micro-task 46.2b, controller only):
  > Task 46, micro-task 46.2b (controller only): adapt `TodoController` in `implementer/src/todo_md/app.py` to the new 3-tuple store contract (`load` returns and `save` accepts `(text, done, description)` tuples). You are on branch `implementer/46-item-description` (base and integration branch: `main`), starting from commit `427a3b5` with a clean tree. Verify with `git branch --show-current` and `git status --short` before editing. First tool call: run `../architect/tools/implementer-run.sh` without arguments; use that wrapper for every subsequent Bash command and follow the Mandatory Execution Clock phase rules; the harness is read-only, never modify it. Changes, restricted to `implementer/src/todo_md/app.py` and `implementer/src/tests/test_controller.py`: (1) every `store.load` call site (~line 172) must unpack the 3-tuple and pass the description into the constructed `TodoItem`; (2) every `store.save` call site (~lines 191, 234) must include `item.description` as the third tuple element; (3) extend `TodoController.edit_item(name, index, text)` with an optional `description: str = ''` parameter passed through to `TodoList.edit` (model semantics: description is stripped, blank becomes `''` and overwrites); existing callers not passing it must keep working; (4) update `tests/test_controller.py` to the 3-tuple contract: loading a list with descriptions restores them on the model; add/edit/toggle/remove/rename all persist descriptions; `edit_item` with a description persists it. Do NOT change the controller public surface beyond the new optional parameter; do NOT touch GUI code, `storage.py`, `models.py`, or their tests. Never modify anything under `../architect/` or the repo root. No branch creation/switching/merging/pushing; never commit to `main`; no broad staging or destructive git operations. Completion gates from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/test_controller.py -v)` fully green, then `(cd src && .venv/bin/python -m pytest tests -v)` fully green (the full suite must be green again at the end of this micro-task). Commit with message `Adapt controller to 3-tuple store contract with description (46.2b)`; the handoff must state RESULT: SUCCESS/FAILURE, the branch name, and the commit hash (COMMIT: NONE only if nothing changed).
- Files in /tmp from previous executions:
  1) implementer-46.2.log
  2) implementer-prompt-46.2.txt
  3) implementer-prompt-46.2a.txt
  4) implementer-prompt-46.2a-v2.txt
  5) implementer-46.2a-v2.log
  Check the content and delete them after a successful completion.
  
## Queue

None.

## Active Blockers

- `pi` child launches repeatedly hit memory limits (macOS free-page floor / GPU OOM); one attempt lost work by dying after editing but before committing (recovered via verify-and-commit follow-up). Mitigate with narrower micro-tasks and commit early; verify handoff hashes against `git rev-parse`.

## Recently Completed

- 45: Double-click on unfinished item text opens the modal edit dialog (GUI-only, stored-index safe); independently verified and approved; `160c423ff1a933a5f67975dbdb9f7fc7d37008e3`.
- 44: Per-item edit icon left of trash and modal edit dialog (headless `edit_item` + GUI); independently verified and approved; `3181f134a4f3f25b0ba2cd0fb3a8c8a5c04db406`.
- 43: Withdrawn structural long-label test and lifecycle regression; independently verified and approved; `47020e50c32afa52fb32296b87bc9991d18b3989`.
- 42: Input caret contrast across themes; independently verified and approved; `dceb909362fb036ec69712139c27492d86c9b5d3`.
- 41: Persisted completion order and safe filtered GUI callbacks; independently verified and approved; `5b9c4457bf25fc6b682ffd1e14e243577789e81c`.
