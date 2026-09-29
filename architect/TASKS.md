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

**36b2: GUI relocation recovery (M); current micro-task R3: live-state recovery (S).**

- Branch: `implementer/task-36b2-settings-relocation`; base/integration: `main`. Keep this branch through all recovery; no merge until 36b2 is complete.
- Latest checkpoint: `d8596578b149d6b7b6a5fb55655083b27685c9af`; R2 independently verified: 119 focused, 197 passed/2 skipped twice, unattended. Decision fixes and restored transition tests meet R2 scope; integration still pending.
- Remaining: stale live directory/sidebar/rows and persistence-failure recovery; final harness proof remains R4. Resolved decision-flow findings are removed.
- Size: S, one focused GUI-state synchronization change using existing store/refresh APIs; no new persistence or relocation algorithm.
- Scope: settings/live-view code in `implementer/src/todo_md/app.py` and `implementer/src/tests/test_gui_settings.py`, plus normal VERSION hook change.
- Acceptance: live directory, selection, and rows match the bound store after success or error; retained files remain safe/editable; unsaved preferences and retry are handled accurately. No batch rollback. Exact tests/commands below.

### Delegated Prompt

Implement Task 36b2 recovery R3: live-directory/view synchronization and failure recovery. Assigned branch: implementer/task-36b2-settings-relocation; main is base/integration. Start from d8596578b149d6b7b6a5fb55655083b27685c9af plus Architect planning commits. Verify git branch --show-current, git status --short, and checkpoint ancestry first. Stop if branch is wrong/main or tree dirty. Follow implementer/AGENTS.md and its 1,200-second limit/checkpoint wrap-up.

Measure ../architect/DESIGN.md before reading Presentation, Data Models and Flow, and Known Architectural Debt. Never read TASKS.md. Only edit settings/live-view GUI code in src/todo_md/app.py and src/tests/test_gui_settings.py under implementer/. The normal VERSION hook update is allowed. No controller/storage/settings.py, dialog guard, other tests, manifests, AGENTS.md, architect/, or root-file changes. No branch create/switch/merge/rebase/rename/delete/push, main commits, broad staging, destructive operations, or unrelated refactoring. Preserve R2 behavior and tests.

Make the bound controller store authoritative for runtime state. After a directory operation, synchronize app.data_dir, the effective in-memory directory preference, sidebar contents, selection/current_list, title, and item rows with the actual store. Preserve a selected list only when it still exists and visibly select it in the listbox; otherwise clear selection/title/rows safely. Yes must keep moved lists editable at the destination; No must leave no selectable stale source lists or callbacks targeting them. Use existing refresh mechanisms, with a small shared synchronization helper only if needed. Preserve explicit constructor overrides before any directory operation.

On relocation failure, keep the original controller binding, persist nothing, and refresh from the remaining source files before allowing edits. Report source and target paths and possible partial progress; never delete retained files or pretend completed moves were undone. If refresh itself cannot read the directory, clear stale UI safely and report the failure without an uncaught Tk exception. Cover errors after successful controller switching but before preference persistence too. Batch rollback is explicitly forbidden in this task.

If settings persistence fails after a successful switch, retain the active destination and keep the settings dialog open. Its existing JSON must remain unchanged. Clearly report the active directory, that its preference is not saved for restart, and that Save can be retried. Keep live folder state coherent for further edits; pending theme/completed-count changes must not apply until persistence succeeds. Retry with the same target must neither prompt nor relocate again. Closing/Cancel after such failure discards unsaved controls, not completed file moves; reopening must show the active directory, and subsequent Save or theme persistence must not write an obsolete directory. Keep normal Cancel-without-save behavior and default-null serialization intact.

Strengthen tests with populated sources and actual rendered state, not only controller-path assertions. Required cases: Yes preserves visible selection/rows and UI edits write only to destination; No clears sidebar/selection/title/rows and new UI-created lists stay in destination; partial failure after one real file moves leaves all bytes recoverable, removes stale source rows, and keeps remaining lists editable; persistence failure after real moves keeps destination editable before retry, leaves original JSON unchanged, and reports unpersisted preference; actual pending theme/count edits leave palette/filter unchanged until successful retry; retry and close/reopen do not move/prompt again. Assert file contents, widget state, bindings, and absence of callback errors. Keep tmp_path isolation, expected dialog mocks, native dialog guard, and robust root cleanup. Do not skip, xfail, or weaken existing assertions. R4's guard-negative-test work remains separate.

Run from implementer/: (cd src && .venv/bin/python -m pytest tests/test_gui_settings.py tests/test_controller.py tests/test_storage.py tests/test_settings.py tests/test_dialog_guard.py -v) and (cd src && .venv/bin/python -m pytest tests -v) twice as separate runs. Prefer workdir implementer/src/ with inner commands. All must pass unattended; only the two existing gated integrations may skip. Commit completed or stabilized partial changes with explicit staging and normal hooks. Report BRANCH, COMMIT, completed/remaining scope, exact test results, blockers, and final tree status; end RESULT: SUCCESS only if delegated scope and tests pass, otherwise RESULT: FAILURE. No merge/push or claim that R4 is complete.

## Queue

- **36b2-R4 (S):** close harness verification gaps: isolated pytest regression must fail when a real Tk callback swallows an unmocked dialog and teardown sees the attempt; do not acknowledge it away. Verify root cleanup after setup/update failures and finish full unattended acceptance coverage. No merge until all 36b2 requirements pass independent review.

## Active Blockers

- Live-state/error recovery and final harness proof remain incomplete; full branch is not mergeable.
- Recovery awaits user-interactive Implementer execution; no unattended child launch.

## Recently Completed

- 36b2-R2: Directory decisions; independently verified checkpoint, integration pending; `d859657`.
- 36b1: Headless controller directory switching; verified and merged; `9612b3b`.
- 36a: Headless lists-directory relocation; verified and merged; `f543275`.
- 35b: Settings Save/Cancel; verified and merged; `9c45b49`.
- 35a: Settings window construction; verified and merged; `895bfb5`.
