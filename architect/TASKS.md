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

**36b2: GUI relocation recovery (M); current micro-task R2: directory decisions (S).**

- Branch: `implementer/task-36b2-settings-relocation`; base/integration: `main`. Keep this branch through all recovery; no merge until 36b2 is complete.
- Latest checkpoint: `7940adbf8e678e43e0515d2d4c238967cad3c478`, unapproved. Verified: guard 6, focused 96, full suite 180 passed/2 skipped twice, unattended.
- Review: popup interruption resolved; app.py changed outside R1's tests-only scope. Default/filter assertions weakened; guard teardown proof missing.
- Confirmed defects: stale sidebar/rows, default Cancel persists non-null, invalid abandoned target blocks Cancel, missing source raises FileNotFoundError.
- Revised approach: sequential interactive R2 decisions, R3 live/error state, R4 final harness coverage; preserve checkpoint and keep branch unmerged.
- R2 scope: settings-related code in `implementer/src/todo_md/app.py` and `implementer/src/tests/test_gui_settings.py`, plus normal VERSION hook change.
- R2 acceptance: correct validated Yes/No/Cancel/default/missing/equivalent-path decisions with meaningful transition tests; preserve dialog guard. Exact tests/commands are in the delegated prompt. R3/R4 remain required for full approval.

### Delegated Prompt

Implement Task 36b2 recovery R2: directory-decision correctness. Assigned branch: implementer/task-36b2-settings-relocation; main is base/integration. Start from checkpoint 7940adbf8e678e43e0515d2d4c238967cad3c478 plus Architect planning commits. Verify git branch --show-current, git status --short, and checkpoint ancestry first. Stop if branch is wrong/main or tree dirty. Follow implementer/AGENTS.md, its 1,200-second limit, and checkpoint wrap-up.

Measure ../architect/DESIGN.md before reading its Presentation, Data Models and Flow, and Known Architectural Debt sections. Never read TASKS.md. Only edit settings-related GUI code in src/todo_md/app.py and src/tests/test_gui_settings.py under implementer/. The normal VERSION hook update is allowed. Do not change controller/storage/settings.py, dialog_guard, other tests, manifests, AGENTS.md, architect/, or repository-root files. No branch create/switch/merge/rebase/rename/delete/push, main commits, broad staging, or destructive operations. Preserve existing changes; do not revert the checkpoint.

Correct Save decisions using the existing controller API. Validate theme and integer completed-visible 0-999 before any filesystem checks, prompts, creation, relocation, or persistence. Blank/whitespace means the actual DEFAULT_DATA_DIR; normalize user paths to stable absolute paths and normalize the effective default to lists_dir=null, including after popup Cancel. Compare against controller.store.data_dir. Equivalent paths, including symlinks, must not prompt or call relocation.

For a changed target and nonempty Markdown source, ask Yes/No/Cancel with exact message: "You are about to change the directory where your lists are stored from '<old>' to '<new>' but there are already lists in it." Yes moves, No switches without moving, Cancel retains the active directory but persists/applies other valid settings. Only validate the chosen target after the decision: Cancel must ignore an unusable abandoned target and must not create it. Preserve null when cancelling from the default directory. Keep settings-window Cancel a full no-op for unsaved controls.

Treat empty, missing, and non-Markdown-only sources as no-popup cases, creating the selected target through change_lists_dir. Directory inspection/equivalence errors must not escape as Tk callback exceptions: missing source is supported, other filesystem errors are reported. Keep populated-target refusal for Yes/No with original files/bindings/settings unchanged. Update stale Save documentation. Do not implement batch rollback or the separate sidebar/live-state/persistence-failure work; those remain R3.

Repair settings fixture alignment rather than adjusting every entry to compensate: actual store follows explicit data_dir or saved lists_dir or the patched default, with configuration under tmp_path. Preserve initially absent settings and caller dictionaries. Open Settings before using controls; guarantee root update/destroy even on setup failures. Keep native dialog guard active and mock expected dialogs explicitly. Restore meaningful blank-entry coverage: begin with a non-default source containing a list, clear the entry, choose Yes, and assert exact moved bytes, active default directory, null payload, and subsequent destination-only writes. Also test No, populated default rejection, Cancel from default (null preserved), Cancel with an invalid abandoned target (other edits applied), missing source, normalized/symlink-equivalent paths, exact message equality, and invalid theme/count blocking filesystem and relocation calls. Assert no uncaught Tk callback errors. No skips, xfails, blanket dialog responses, or weakened transition assertions.

Run from implementer/: (cd src && .venv/bin/python -m pytest tests/test_dialog_guard.py tests/test_gui_settings.py tests/test_controller.py tests/test_storage.py tests/test_settings.py -v) and (cd src && .venv/bin/python -m pytest tests -v) twice as separate runs. Prefer tool workdir implementer/src/ with inner commands. All must pass without human input. Commit completed or stabilized partial changes with explicit staging and normal hooks. Report BRANCH, COMMIT, completed/remaining scope, exact test results, blockers, and final tree status; end RESULT: SUCCESS only for completed delegated scope with all required suites passing, otherwise RESULT: FAILURE. Do not claim R3/R4 complete; no merge or push.

## Queue

- **36b2-R3 (S):** synchronize app/controller directory, sidebar, selection, and rows on success and relocation/save errors. Use populated sources in tests; No clears stale lists, partial moves refresh source state, failed persistence keeps destination editable and reports unsaved restart preference, retry does not move again. Restore actual theme/count edits in failure test and verify unchanged palette/filter until saved. Same branch; no batch rollback.
- **36b2-R4 (S):** close harness verification gaps: isolated pytest regression must fail when a real Tk callback swallows an unmocked dialog and teardown sees the attempt; do not acknowledge it away. Verify root cleanup after setup/update failures and finish full unattended acceptance coverage. No merge until all 36b2 requirements pass independent review.

## Active Blockers

- Product defects and weakened/missing regressions remain despite a green suite; checkpoint is not mergeable.
- R1 app.py edits exceeded delegated scope; retained unmerged for corrective review, not silently approved.
- Recovery awaits user-interactive Implementer execution; no unattended child launch.

## Recently Completed

- 36b1: Headless controller directory switching; verified and merged; `9612b3b`.
- 36a: Headless lists-directory relocation; verified and merged; `f543275`.
- 35b: Settings Save/Cancel; verified and merged; `9c45b49`.
- 35a: Settings window construction; verified and merged; `895bfb5`.
- 34: Completed-item display filter; verified and merged; `bf3ab84`.
