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
- Item rows have an edit icon left of the trash; items can carry an optional multi-line description stored as indented continuation lines in the list's `.md` file (legacy files parse as empty description). The pre-populated modal edits title and description and persists both on Save, while Cancel or an empty title is a no-op. Double-clicking an unfinished item's text opens the same modal; completed items ignore double-clicks.
- Build and release scripts produce a launch-tested Apple Silicon app bundle and versioned distributable ZIP.

## Active Task

### 47 — Center modal dialogs on the main window (S)

- **Branch:** `implementer/task-47-dialog-centering` (base and integration branch: `main`).
- **Scope:** `implementer/src/todo_md/app.py` (settings Toplevel ~line 644 and item-edit Toplevel ~line 1125) plus a new/updated GUI test. Both modals currently appear at the main window's top-left; they must open vertically and horizontally centered on the main window's *current* on-screen rectangle.
- **Acceptance criteria:**
  1. The settings window and the item-edit dialog both open centered on the main window (center of dialog == center of main window, within a small tolerance, e.g. ±8 px).
  2. Centering is recomputed on every open: moving or resizing the main window before opening a dialog must produce a correctly centered dialog.
  3. Implementation: after the dialog's widgets exist and its size geometry is set, call `update_idletasks()`, measure the dialog's requested size and the parent's `winfo_rootx/rooty/width/height`, then apply `win.geometry(f"+{x}+{y}")` with `x = parent_rootx + (parent_width - dialog_width)//2` and the analogous `y`. Prefer a small shared helper in `TodoApp` used by both dialogs. Do not change transient, grab, or single-instance settings behavior.
  4. Existing behavior and tests unaffected.
- **Required tests:** new GUI test (e.g. `tests/test_gui_centering.py` or extend `tests/test_gui_layout.py`) that on a real display: positions the main window at a known `+x+y`, opens the settings window, asserts its on-screen position is centered within tolerance; closes it, opens the edit dialog for an item, asserts the same; optionally moves the main window and re-asserts. Owned roots updated and unconditionally destroyed, including failure paths.
- **Test commands (from `implementer/`):** `(cd src && .venv/bin/python -m pytest tests/test_gui_layout.py tests/test_gui_settings.py tests/test_gui_edit.py -v)` and the full suite `(cd src && .venv/bin/python -m pytest tests -v)`.
- **Prompt for Implementer:**
  > Task 47: center modal dialogs on the main window.
  > Work on branch `implementer/task-47-dialog-centering` (base: `main`). First verify the checked-out branch and that `git status --short` is clean before editing. Restrict all changes to `implementer/src/` (app.py + tests); never touch `architect/`, `implementer/AGENTS.md`, or the repository root.
  > Your first tool call MUST run `../architect/tools/implementer-run.sh` with no arguments; every subsequent Bash command MUST go through that wrapper, following your Mandatory Execution Clock phase rules. The wrapper is read-only: execute, never modify.
  > In `implementer/src/todo_md/app.py`, make both the settings Toplevel (~line 644) and the item-edit Toplevel (~line 1125) open vertically and horizontally centered on the main window's current on-screen rectangle. Add a small shared helper on `TodoApp` that, after the dialog's size geometry is set, calls `update_idletasks()`, measures the dialog's requested size and the parent's `winfo_rootx`/`winfo_rooty`/`winfo_width`/`winfo_height`, and applies `win.geometry(f"+{x}+{y}")` where `x = parent_rootx + (parent_width - dialog_width)//2` and `y` is analogous. Recompute on every open. Do not change transient, grab, or single-instance settings behavior.
  > Write a GUI test (`tests/test_gui_centering.py` or extend `tests/test_gui_layout.py`) per the acceptance criteria: place the main window at a known `+x+y` on the real display, open each dialog, assert centered position within ±8 px; also move the main window and re-assert. Follow `tests/conftest.py` conventions (isolated dirs, dialog guard, roots updated and unconditionally destroyed).
  > Run from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/test_gui_layout.py tests/test_gui_settings.py tests/test_gui_edit.py -v)` then the full suite `(cd src && .venv/bin/python -m pytest tests -v)`. All must pass; do not add skips/xfails.
  > Commit your work to the branch (never `main`; no branch creation/switching/merging/pushing, no destructive git ops). Hand off with branch name and commit hash.

## Queue

None.

## Active Blockers

None.

## Recently Completed

- 46: Item description field (domain, storage, controller, full test migration, GUI edit modal description box); independently verified and approved; `ca02ac4bad7c5ce6964e85ffec10bd57be65d635`.
- 45: Double-click on unfinished item text opens the modal edit dialog (GUI-only, stored-index safe); independently verified and approved; `160c423ff1a933a5f67975dbdb9f7fc7d37008e3`.
- 44: Per-item edit icon left of trash and modal edit dialog (headless `edit_item` + GUI); independently verified and approved; `3181f134a4f3f25b0ba2cd0fb3a8c8a5c04db406`.
- 43: Withdrawn structural long-label test and lifecycle regression; independently verified and approved; `47020e50c32afa52fb32296b87bc9991d18b3989`.
- 42: Input caret contrast across themes; independently verified and approved; `dceb909362fb036ec69712139c27492d86c9b5d3`.
