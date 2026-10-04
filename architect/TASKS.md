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
- Item rows have an edit icon left of the trash; the pre-populated modal persists text to the `.md` file on Save, while Cancel or empty input is a no-op.
- Build and release scripts produce a launch-tested Apple Silicon app bundle and versioned distributable ZIP.

## Active Task

- **Task 45 (S): Open the item edit modal on double-click of an unfinished item**
  - Branch: `implementer/45-double-click-edit` (base and integration branch: `main`).
  - Scope: GUI only, `implementer/src/todo_md/app.py` plus GUI tests. No model, storage, settings, or controller changes; reuse the existing edit-modal path already used by the edit icon.
  - Acceptance criteria:
    1. A double-click (two consecutive `<ButtonPress-1>` events within Tk's double-click window, or Tk's `<Double-Button-1>` binding) on the text of an **unfinished** item opens the existing pre-populated modal edit dialog.
    2. Double-clicking a **completed** item opens no dialog; the existing single-click toggle behavior is unchanged.
    3. The edit icon still opens the modal exactly as before; modal Save/Cancel/empty-input behavior is unchanged.
    4. No persisted content changes occur merely from clicking; edits persist only through the existing modal Save path.
    5. The dialog guard in `tests/conftest.py` remains green: no unexpected dialogs in any existing test.
  - Tests to write/update: new `implementer/src/tests/test_gui_double_click.py` (unfinished item opens modal, completed item does not, single-click toggle still works, Save persists text) and run existing `tests/test_gui_edit.py` to guard regressions.
  - Commands (from `implementer/`):
    - `(cd src && .venv/bin/python -m pytest tests/test_gui_double_click.py tests/test_gui_edit.py -v)`
    - `(cd src && .venv/bin/python -m pytest tests -v)` (full suite before handoff)
  - Prompt for the Implementer:
    > You are the Implementer agent. Assigned branch: `implementer/45-double-click-edit`; base and integration branch: `main`.
    > First tool call: run `../architect/tools/implementer-run.sh` (no arguments). All subsequent Bash commands MUST go through that wrapper, and you MUST follow the Implementer Mandatory Execution Clock phase rules. Executing the read-only harness script is permitted; modifying it is forbidden.
    > Before editing: verify the current branch is `implementer/45-double-click-edit` and inspect the working tree (`git status --short`); stop and report if unexpected.
    > Task: in `implementer/src/todo_md/app.py`, make a double-click on the text of an **unfinished** todo item open the existing pre-populated modal edit dialog (same path the edit icon uses). Double-clicking a **completed** item must open no dialog. Do not change single-click toggle, edit-icon, modal Save/Cancel, storage, models, controller, or settings. Keep changes minimal and within `implementer/src/todo_md/app.py` and new/updated tests under `implementer/src/tests/`.
    > Tests: add `implementer/src/tests/test_gui_double_click.py` covering: double-click on an unfinished item opens the pre-populated modal; Save persists the edited text to the `.md` file; double-click on a completed item opens no dialog (rely on the `tests/conftest.py` dialog guard); single-click toggle still works; the edit icon path is unchanged. Use the shared conftest fixtures, isolated data/config dirs, withdraw/update/destroy owned roots including failure paths; no human input, no skips/xfails.
    > Run from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/test_gui_double_click.py tests/test_gui_edit.py -v)` then the full suite `(cd src && .venv/bin/python -m pytest tests -v)`. All must pass.
    > Commit completed work on `implementer/45-double-click-edit` and report branch name and commit hash in the handoff.
    > Forbidden: creating/switching/merging/rebasing/renaming/deleting/pushing branches; committing to `main`; broad staging or destructive working-tree operations; any change under `../architect/`, `implementer/AGENTS.md`, or the repository root.

## Queue

- Task 46 (M): Description field for todo items — a description text box in the edit modal, stored with the item as a human-readable sub-element in the `.md` file (domain, storage, controller, GUI, tests). Unexpanded; plan and size micro-tasks when promoted.

## Active Blockers

None.

## Recently Completed

- 44: Per-item edit icon left of trash and modal edit dialog (headless `edit_item` + GUI); independently verified and approved; `3181f134a4f3f25b0ba2cd0fb3a8c8a5c04db406`.
- 43: Withdrawn structural long-label test and lifecycle regression; independently verified and approved; `47020e50c32afa52fb32296b87bc9991d18b3989`.
- 42: Input caret contrast across themes; independently verified and approved; `dceb909362fb036ec69712139c27492d86c9b5d3`.
- 41: Persisted completion order and safe filtered GUI callbacks; independently verified and approved; `5b9c4457bf25fc6b682ffd1e14e243577789e81c`.
- 40: Settings Theme palette and margins; independently verified and approved; `9d785ef23b8b9778645936b5e7f42113a8ae9434`.
