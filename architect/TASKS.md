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
- **Checkpoint:** `6b84fa0a31ea7900d024dc73672b449d25c21f01` (helper added and wired to both dialogs; new `tests/test_gui_centering.py`).
- **Status:** first delegation timed out at the 20-minute hard limit; checkpoint independently verified: boundaries OK, but the new GUI tests FAIL — the dialog's vertical center lands ~31 px below the main window's center on macOS (horizontal centering is within tolerance). Remaining scope: correct the vertical offset so both modals are truly centered.
- **Blocker:** on macOS, `win.geometry("+x+y")` placement and `winfo_rootx/rooty` measurement disagree by ~one title-bar height (~31 px), so a single placement pass is off vertically.
- **Revised approach (narrow micro-task):** make centering self-correcting: after the first `geometry("+x+y")` and `win.update()`, re-measure the dialog's actual `winfo_rootx/rooty/width/height` and the parent rectangle, and apply one corrective `geometry("+dx+dy")` that closes the measured centering error (compute dx/dy from measured values, not assumptions about decorations). No hardcoded title-bar heights. Then make `tests/test_gui_centering.py` pass as written (±8 px both axes, including the moved-main-window re-open case).
- **Acceptance criteria:** unchanged from original: both dialogs centered within ±8 px on both axes; recomputed on every open; no behavior change to transient/grab/single-instance; targeted and full suites pass.
- **Required tests:** new GUI test (e.g. `tests/test_gui_centering.py` or extend `tests/test_gui_layout.py`) that on a real display: positions the main window at a known `+x+y`, opens the settings window, asserts its on-screen position is centered within tolerance; closes it, opens the edit dialog for an item, asserts the same; optionally moves the main window and re-asserts. Owned roots updated and unconditionally destroyed, including failure paths.
- **Test commands (from `implementer/`):** `(cd src && .venv/bin/python -m pytest tests/test_gui_layout.py tests/test_gui_settings.py tests/test_gui_edit.py -v)` and the full suite `(cd src && .venv/bin/python -m pytest tests -v)`.
- **Prompt for Implementer (corrective micro-task, starts from checkpoint `6b84fa0`):**
  > Task 47 (correction): fix the vertical centering offset.
  > You are continuing on branch `implementer/task-47-dialog-centering`, starting from commit `6b84fa0a31ea7900d024dc73672b449d25c21f01`. First verify the branch and clean `git status --short`. Restrict changes to `implementer/src/`; never touch `architect/`, `implementer/AGENTS.md`, or the repository root.
  > Your first tool call MUST run `../architect/tools/implementer-run.sh` with no arguments; every subsequent Bash command MUST go through that wrapper, following your Mandatory Execution Clock phase rules. The wrapper is read-only: execute, never modify.
  > Known failure from independent verification: `tests/test_gui_centering.py` fails on macOS — the dialog's vertical center is ~31 px (one title-bar height) below the main window's center; horizontal centering is fine. Cause: on macOS, `win.geometry("+x+y")` placement and the subsequent `winfo_rootx/rooty` reading disagree by ~one title-bar height, so a single placement pass is off.
  > Fix `TodoApp._center_window_on_parent` (implementer/src/todo_md/app.py) to be self-correcting: after the initial `geometry("+x+y")` and `win.update()`, re-measure the dialog's actual `winfo_rootx/rooty/width/height` and the parent's rectangle, compute the residual centering error, and apply one corrective `geometry("+dx+dy")`. Do not hardcode title-bar heights. Then make `tests/test_gui_centering.py` pass as written (±8 px on both axes, including the moved-main-window re-open case). Do not weaken the test's assertions; do not add skips/xfails.
  > Run from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/test_gui_centering.py tests/test_gui_layout.py tests/test_gui_settings.py tests/test_gui_edit.py -v)` then the full suite `(cd src && .venv/bin/python -m pytest tests -v)`. All must pass.
  > Commit to the branch (never `main`; no branch creation/switching/merging/pushing, no destructive git ops). Hand off with branch name and commit hash, RESULT: SUCCESS/FAILURE, tests run, and any blockers.

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
