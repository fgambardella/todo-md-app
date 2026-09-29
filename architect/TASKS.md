# TASKS.md

## Project Goal

Build a macOS desktop TODO app in Python with a stdlib-only runtime. Persist each list as a portable Markdown file with GFM checkboxes. Keep domain, persistence, and controller logic headlessly testable beneath the Tkinter GUI, with persistent settings and light/dark themes.

## Test Policy

- Framework: pytest, already used throughout `implementer/src/tests/`.
- Full suite from `implementer/`: `(cd src && .venv/bin/python -m pytest tests -v)`.
- Targeted convention from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/<file>.py -v)`.
- Tests require `implementer/src/` as working directory for existing relative asset paths; tools may set that workdir directly and run the inner command.
- Build/release changes also require the corresponding gated tests from `implementer/src/`: `RUN_BUILD_TESTS=1 .venv/bin/python -m pytest tests/test_build_script.py -v`; `RUN_RELEASE_TESTS=1 .venv/bin/python -m pytest tests/test_release_package.py -v`.
- GUI tests run on the local display with isolated data/config directories. Owned roots are updated and unconditionally destroyed, including failure paths; headless tests never launch the GUI.
- Automated tests must never require human input. Mock expected dialog choices explicitly; unexpected dialogs must fail immediately or at teardown when swallowed by Tk. Shared facilities: `implementer/src/tests/conftest.py`. Negative subprocess tests assert expected inner failures while the outer suite remains green. Never blanket-answer Yes, suppress failures, or add skips/xfails to hide regressions.

## Current Implementation Summary

- Lists persist as separate Markdown files with atomic writes and filesystem-safe names; validated item operations are persisted immediately.
- The GUI supports list creation, item toggles, per-item deletion, placeholder hints, and confirmation of destructive actions.
- Light/dark themes include readable controls, a theme-aware version badge, and custom dock/Finder icons.
- Settings validate and save the full payload, apply theme and completed-item filtering live, and discard unsaved controls on window Cancel. Filtering never changes stored content.
- Directory changes apply live with optional list movement; popup Cancel retains the directory while saving other settings. Populated destinations are rejected, equivalent paths are harmless, and configuration stays fixed.
- Relocation failures preserve recoverable files and refresh the active view. Failed settings persistence keeps the destination usable and supports retry without repeating completed moves; pending theme/filter edits remain unapplied.
- Automated GUI tests intercept unexpected dialogs and verify cleanup after failures without human interaction.
- Build and release scripts produce a launch-tested Apple Silicon app bundle and versioned distributable ZIP.

## Active Task

None.

## Queue

- Functional change request: now it is forbidden to the user to select a non empty destination directory for lists. The user receives the following message:
"Could not switch lists folder from '...' to '...': destination already contains Markdown files: ...". I want that the user can select a not empty destination directory and, if it decide to proceed copying list files from the source directory, the operation fails only if in the destination directory there is already a file with the same name of a file in the source directory. No file overwrite permitted.
Some files may already be at the destination. Completed moves have not been undone. The active lists folder is '/Users/flavio/.todo-md-app/lists'. The directory preference is not saved for restart.
- GUI BUG: when the app main window opens, the setting button is partially hidden.
- GUI BUG: when the setting window opens, the cancel/save buttons are partially hidden.
- GUI BUG: in the setting window, the cancel/save buttons must be orizzontally centered.
- GUI BUG: in the setting window the "theme" section has a too bright background in dark mode and too tanned background in light mode.
- GUI BUG: in the setting window the "theme" section lacks of left and right margin.
- GUI BUG: in the setting window the confirmation message: "You are about to change the directory where your lists are stored from '...' to '...' but there are already lists in it." misses a foundamental final part: the question! It should be: "You are about to change the directory where your lists are stored from '...' to '...' but there are already lists in it. Do you want to copy them in the new path?"
- GUI BUG: in the todolist, the completed list items must be always shown on top, in order of completion (from least recently completed on the very top and the last recently completed just before the first uncompleted one). Only the least recently completed list item must be hidden when a list item is completed.
- GUI BUG: in light mode, the cursor disappear in all input fields (probably white over white).

## Active Blockers

None.

## Recently Completed

- 36b2: GUI relocation and unattended test harness; independently verified and approved; `a0fc76918d5424334a1116176838013115eaed84`.
- 36b1: Headless controller directory switching; verified and merged; `9612b3b`.
- 36a: Headless lists-directory relocation; verified and merged; `f543275`.
- 35b: Settings Save/Cancel; verified and merged; `9c45b49`.
