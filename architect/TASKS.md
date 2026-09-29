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

**36b2: GUI lists-directory relocation (S, final micro-task of 36b-M).**

- Size rationale: localized settings Save integration using the verified controller operation; no new relocation algorithm, persistence format, or rollback mechanism.
- Branch: `implementer/task-36b2-settings-relocation`; base and integration: `main`.
- Status: prepared for user-interactive delegation; no child process running.
- Scope: settings-related GUI code in `implementer/src/todo_md/app.py` and `implementer/src/tests/test_gui_settings.py`; normal VERSION hook update allowed.
- Acceptance: the prompt/validation/save flow below supports Yes, No, Cancel, empty/default/equivalent directories, immediate store/UI consistency, and explicit safe failure handling. Existing behavior outside directory changes remains intact.
- Required tests: confirmation choices and exact text; empty-source no-popup; populated/invalid target; invalid completed count before effects; default/equivalent paths; subsequent writes, repeat Save, relocation and settings-persistence errors.
- Commands from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/test_gui_settings.py tests/test_controller.py tests/test_storage.py tests/test_settings.py -v)`; `(cd src && .venv/bin/python -m pytest tests -v)`.

### Delegated Prompt

You are the Implementer for Task 36b2. Work only on implementer/task-36b2-settings-relocation; main is its base and integration branch. First verify git branch --show-current and git status --short from implementer/. Stop without changes if the branch is wrong, is main, or the tree is dirty. Follow implementer/AGENTS.md, including the 1,200-second limit and checkpoint wrap-up.

Measure ../architect/DESIGN.md before reading it; use its Presentation/Controller components, Data Models and Flow, and Known Architectural Debt. Never read TASKS.md. Only edit settings-related GUI code in src/todo_md/app.py and src/tests/test_gui_settings.py under implementer/. The normal hook-generated VERSION update is allowed. Never modify any AGENTS.md, architect/ content, repository-root files, storage/controller behavior, or settings.py. No branch creation, switching, merging, rebasing, renaming, deletion, or pushing; no commits to main, broad staging, or destructive working-tree operations.

Wire the settings Save handler to the existing TodoController.change_lists_dir. Compare the requested directory against controller.store.data_dir, not stale settings or constructor overrides. Blank/whitespace entry means DEFAULT_DATA_DIR, persisted as null. Normalize user paths and recognize equivalent existing directories; unchanged/equivalent paths must not prompt or relocate. Validate theme and completed-visible (integer 0-999) before any prompt, directory creation, relocation, or persistence. Invalid input shows an error, leaves the window open, and persists nothing.

When changing directories and the active source contains at least one top-level Markdown file, call messagebox.askyesnocancel with this exact message, substituting paths: "You are about to change the directory where your lists are stored from '<old>' to '<new>' but there are already lists in it." Yes proceeds with move=True; No proceeds with move=False; popup Cancel keeps the old directory and files but still saves/applies other valid settings. Cancel must not validate or create the abandoned destination. Do not show the popup for an empty/missing source or non-Markdown-only source. A chosen destination containing Markdown lists, or an unusable directory, must show an error and not persist the attempted change. Reuse the controller/storage guard rather than duplicate relocation logic.

On success, persist the full settings payload in the unchanged config directory, synchronize live data-directory state, apply theme/filter, refresh sidebar and item selection, and close the dialog. Subsequent edits must write only to the active destination; No must not leave editable stale source rows. Reopening and saving unchanged settings must not prompt or relocate again. The settings-window Cancel button remains a no-op for unsaved control edits.

Catch expected filesystem/settings-save failures instead of leaking Tk callback errors. A relocation error must not persist the proposed settings; refresh from the still-bound source so already moved lists cannot be edited through stale rows. Report both paths and explain that some files may already be at the destination. Do not add rollback or delete retained files. If relocation succeeded but saving settings fails, keep the active destination usable, keep the dialog open, and clearly report that the directory preference is not saved for restart. Keep runtime directory state coherent and permit a Save retry without moving or prompting again; do not claim that an already completed move was undone. Pending theme/filter edits apply only after persistence succeeds.

Update the GUI test fixture to isolate DEFAULT_DATA_DIR as well as data/config paths under tmp_path and align the initial store with saved/default settings. Never access real user lists. Mock all messageboxes, and update/destroy every root in finally. Cover Yes/No/Cancel with exact prompt text, files and persisted payload; a dedicated empty-source no-popup case; populated destination (both choices), invalid path, invalid completed values before side effects; empty entry/default normalization and equivalent paths; live rows and destination-only writes; repeat Save; injected relocation failure including partial progress; and persistence failure followed by a successful retry. Preserve existing theme/filter and settings-window Cancel assertions.

Run from implementer/: (cd src && .venv/bin/python -m pytest tests/test_gui_settings.py tests/test_controller.py tests/test_storage.py tests/test_settings.py -v) and (cd src && .venv/bin/python -m pytest tests -v). Prefer tool workdir implementer/src/ with the inner commands. Both must pass; the two gated integration tests may stay skipped. Commit finished or stabilized partial work with explicit file staging and normal hooks. Report BRANCH, COMMIT, completed/remaining scope, exact commands/results, blockers, and final working-tree status; end with RESULT: SUCCESS or RESULT: FAILURE. Do not merge or push.

## Queue

None.

## Active Blockers

- Interactive Implementer launch and handoff are required for 36b2; do not launch an unattended child while user approvals are inaccessible.

## Recently Completed

- 36b1: Headless controller directory switching; independently verified and merged; `9612b3b0708ffb40b58a407933ba3fdc5b0194e7`.
- 36a: Headless lists-directory relocation; independently verified and merged; `f543275d8ed131dce5e0359ccf4f00aa847c0e3a`.
- 35b: Settings Save/Cancel; verified and merged; `9c45b49`.
- 35a: Settings window construction; verified and merged; `895bfb5`.
- 34: Completed-item display filter; verified and merged; `bf3ab84`.
