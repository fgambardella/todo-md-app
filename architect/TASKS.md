# TASKS.md

## Project Goal

Build a macOS desktop TODO app in Python with a stdlib-only runtime. Persist each list as a portable Markdown file with GFM checkboxes. Keep domain, persistence, and controller logic headlessly testable beneath the Tkinter GUI, with persistent settings and light/dark themes.

## Test Policy

- Framework: pytest, already used throughout `implementer/src/tests/`.
- Full suite from `implementer/`: `(cd src && .venv/bin/python -m pytest tests -v)`.
- Targeted convention from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/<file>.py -v)`.
- Tests require `implementer/src/` as working directory for existing relative asset paths; tools may set that workdir directly and run the inner command.
- Build/release changes also require the corresponding gated tests from `implementer/src/`: `RUN_BUILD_TESTS=1 .venv/bin/python -m pytest tests/test_build_script.py -v`; `RUN_RELEASE_TESTS=1 .venv/bin/python -m pytest tests/test_release_package.py -v`.
- GUI tests run on the local display, use isolated temporary data/config directories, and update Tk roots before destroying them in `finally`. Headless tests never launch the GUI.
- Automated tests must never require human input: mock expected dialog choices explicitly; unexpected messageboxes/file pickers must fail immediately, including errors swallowed by Tk callbacks. Never blanket-answer Yes or hide failures with skips/xfails.

## Current Implementation Summary

- Lists persist as separate Markdown files with atomic writes and filesystem-safe names; validated item operations are persisted immediately.
- Headless relocation can move Markdown lists without overwriting destination files, or leave old lists in place and direct subsequent operations to a new folder; non-Markdown content is preserved.
- The GUI supports list creation, item toggles, per-item deletion, placeholder hints, and confirmation of destructive actions.
- Light/dark themes include readable item text, entry fills, button states, and a theme-aware version badge; custom dock and Finder icons are supported.
- Settings support theme, lists directory, and completed-item visibility, with tolerant loading and atomic saving. Startup honors the saved directory while configuration stays fixed.
- A single-instance settings window validates and saves the full payload, applies theme/filter live, and leaves all settings unchanged on Cancel. Directory changes currently apply at restart.
- Completed-item filtering is display-only and preserves stored content.
- Build and release scripts produce a launch-tested Apple Silicon app bundle and versioned distributable ZIP.

## Active Task

**36b2: GUI relocation recovery (M); final micro-task R4: harness verification (S).**

- Branch: `implementer/task-36b2-settings-relocation`; base/integration: `main`. Keep this branch through all recovery; no merge until 36b2 is complete.
- Latest checkpoint: `c75f24dd27de82e24e8fe2814086697edfd0f671`; R3 independently verified: 131 focused, 209 passed/2 skipped twice, unattended. Live-state and failure-recovery requirements pass review; integration still pending.
- Remaining: prove swallowed native-dialog attempts fail pytest teardown; verify robust fixture cleanup on setup/update failure without leaked roots. No known unresolved production finding from R3 review.
- Size: S, focused test-harness verification and minimal fixture correction; no production changes.
- Scope: `implementer/src/tests/conftest.py`, `test_dialog_guard.py`, `test_gui_settings.py`, and optional new `test_gui_lifecycle.py`; normal VERSION hook update allowed.
- Acceptance: real Tk callback interception causes an expected isolated pytest teardown failure; explicit dialog mocks pass; all roots are cleaned after injected failures; full acceptance coverage remains green and unattended. Exact tests/commands below.

### Delegated Prompt

Implement Task 36b2 recovery R4: prove unattended test failure detection and root cleanup. Assigned branch: implementer/task-36b2-settings-relocation; main is base/integration. Start from c75f24dd27de82e24e8fe2814086697edfd0f671 plus Architect planning commits. Verify git branch --show-current, git status --short, and checkpoint ancestry first. Stop if branch is wrong/main or tree dirty. Follow implementer/AGENTS.md and its 1,200-second limit/checkpoint wrap-up.

Measure ../architect/DESIGN.md before reading External Interfaces and Data Models and Flow. Never read TASKS.md. Only edit src/tests/conftest.py, src/tests/test_dialog_guard.py, src/tests/test_gui_settings.py, and optionally add src/tests/test_gui_lifecycle.py under implementer/. The normal VERSION hook update is allowed. No production code, manifests, dependencies, other tests, AGENTS.md, architect/, or repository-root changes. No branch create/switch/merge/rebase/rename/delete/push, main commits, broad staging, destructive operations, or unrelated refactoring. Preserve all verified R2/R3 behavior and assertions. If production bugs appear, report them without expanding scope.

Replace or strengthen the current swallowed-dialog regression: it now calls a Python function directly and acknowledges the attempt, so it never proves teardown failure. Use an isolated pytest run with the actual shared dialog_guard fixture, not copied guard logic. Trigger an unmocked messagebox from a real Tk callback (for example, a button invoke) so Tk catches the raised exception and the test body can finish. Leave the recorded attempt unacknowledged. Assert that the inner run fails specifically at fixture teardown with the expected diagnostic and nonzero exit; the outer regression must pass by verifying this expected failure. It must fail if guard teardown detection is removed. Keep a bounded subprocess timeout so a broken guard cannot hang the suite, but timeout itself must not count as success.

Retain direct-dialog and native-file-picker interception and explicit public-function mock coverage. Exercise True/False/None decisions without globally answering dialogs. Prove a clean test after the negative case has no leaked attempt state. The negative test must not create an actual modal popup, call acknowledge to hide its own failure, fake a nonzero exit, or pass because of an unrelated import/display/setup error. Use existing pytest/stdlib facilities, such as pytester, with no new dependency.

Verify cleanup in the settings app fixture and guard tests after app setup/initial-update and teardown-update failures. Ensure every created root is destroyed even if update fails or multiple apps exist, preserve the original failure, and do not destroy an unrelated existing root to hide a leak. Add isolated regressions that exercise the actual fixture, fail for the deliberately injected reason, assert root cleanup, and permit a subsequent clean Tk app with working images. Make only the minimal fixture/helper corrections needed. Keep loading conftest root-free; keep temporary data/config/default paths isolated under tmp_path and all native dialogs guarded.

Run final acceptance coverage without weakening existing tests: Yes/No/popup Cancel, default/null and equivalent paths, validation before effects, empty/missing sources, populated-target rejection, rendered selection/rows, partial relocation, editable destination after failed persistence, unchanged pending theme/filter, retry and close/reopen. These are already covered; preserve them rather than duplicating a new broad suite. No added skips/xfails, suppressed errors, or unconditional success mocks. Distinguish expected failures inside negative subprocess tests from the outer suite result in your handoff.

Run from implementer/: (cd src && .venv/bin/python -m pytest tests/test_dialog_guard.py tests/test_gui_settings.py -v), (cd src && .venv/bin/python -m pytest tests/test_controller.py tests/test_storage.py tests/test_settings.py tests/test_gui_headless.py -v), and (cd src && .venv/bin/python -m pytest tests -v) twice as separate runs. If test_gui_lifecycle.py is added, also run (cd src && .venv/bin/python -m pytest tests/test_gui_lifecycle.py -v). Prefer workdir implementer/src/ with inner commands. All outer suites must pass unattended; only the two existing gated integrations may skip.

Commit completed or stabilized partial changes with explicit staging and normal hooks. Report BRANCH, COMMIT, completed/remaining scope, guard-negative proof, cleanup proof, exact test results, blockers, and final tree status; end RESULT: SUCCESS only if delegated scope and tests pass, otherwise RESULT: FAILURE. A commit remains a review checkpoint; do not merge or push.

## Queue

None.

## Active Blockers

- Final guard-negative and cleanup verification remain incomplete; full branch is not mergeable yet.
- Recovery awaits user-interactive Implementer execution; no unattended child launch.

## Recently Completed

- 36b2-R3: Live-state recovery; independently verified checkpoint, integration pending; `c75f24d`.
- 36b2-R2: Directory decisions; independently verified checkpoint, integration pending; `d859657`.
- 36b1: Headless controller directory switching; verified and merged; `9612b3b`.
- 36a: Headless lists-directory relocation; verified and merged; `f543275`.
- 35b: Settings Save/Cancel; verified and merged; `9c45b49`.
