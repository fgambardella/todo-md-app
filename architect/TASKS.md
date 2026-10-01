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

### 37: Populated lists destinations (M)

- Branch: `implementer/task-37-populated-lists-dir`; base/integration: `main`.
- Scope: allow populated destinations without overwriting any existing path; preserve existing optional transfer behavior. Complete sequential S micro-tasks: 37a headless collision policy, then 37b settings integration and explicit confirmation question. Merge only after both pass.
- Status: ready for 37a; baseline full suite verified (219 passed, 2 gated skips).
- Acceptance: switching without transfer accepts any populated directory and preserves both sides. Transfers accept unrelated destination lists, reject same-name target paths before moving any source, and retain exclusive creation against races. Filesystem failures preserve recoverability. Settings switch/persist/refresh correctly for Yes/No/Cancel, and the prompt ends with `Do you want to copy them in the new path?`. Existing unrelated behavior remains unchanged.
- Required tests: storage/controller success and conflict cases, no-transfer same-name files, preflight conflicts later in sorted order, destination directories/symlinks, and existing copy/race/deletion-failure regressions. GUI coverage and full suite follow in 37b.
- 37a command from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/test_storage.py tests/test_controller.py -v)`.
- Complete current Implementer prompt: Implement only 37a. Edit `src/todo_md/storage.py`, `src/tests/test_storage.py`, and `src/tests/test_controller.py` (normal hook VERSION change allowed). Remove the blanket populated-directory rejection. Without transfer, leave all existing files alone and permit switching. With transfer, enumerate source Markdown files, reject any existing same-name destination path before moving anything (including directories and dangling symlinks), and preserve exclusive creation and current partial-I/O-failure behavior. Do not change move-versus-copy semantics or the storage format. Update contradictory storage/controller tests and cover non-conflicting populated targets, same-name conflicts, and no-transfer switching with colliding names. Preserve all failure/race tests. Follow DESIGN Component Architecture and Data Models and Flow; this task replaces the old blanket rejection policy. Run the exact targeted command above. Existing GUI rejection tests are deliberately updated by 37b before the task is merged; do not edit GUI files in this micro-task.

## Queue

- 38: Main-window Settings button must be fully visible on opening.
- 39: Settings Save/Cancel buttons must be fully visible on opening and horizontally centered.
- 40: Settings Theme section needs palette-matched light/dark backgrounds and left/right margins.
- 41: Completed items must appear above incomplete items in completion order (oldest first); completing another item should evict only the oldest visible completed item when the configured limit is exceeded.
- 42: Input-field insertion cursors must remain visible in light mode.

## Active Blockers

None.

## Recently Completed

- 36b2: GUI relocation and unattended test harness; independently verified and approved; `a0fc76918d5424334a1116176838013115eaed84`.
- 36b1: Headless controller directory switching; verified and merged; `9612b3b`.
- 36a: Headless lists-directory relocation; verified and merged; `f543275`.
- 35b: Settings Save/Cancel; verified and merged; `9c45b49`.
