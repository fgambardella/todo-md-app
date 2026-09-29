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
- The GUI supports list creation, item toggles, per-item deletion, placeholder hints, and confirmation of destructive actions.
- Light/dark themes include readable item text, entry fills, button states, and a theme-aware version badge; custom dock and Finder icons are supported.
- Settings support theme, lists directory, and completed-item visibility, with tolerant loading and atomic saving. Startup honors the saved directory while configuration stays fixed.
- A single-instance settings window validates and saves the full payload, applies theme/filter live, and leaves all settings unchanged on Cancel. Directory changes currently apply at restart.
- Completed-item filtering is display-only and preserves stored content.
- Build and release scripts produce a launch-tested Apple Silicon app bundle and versioned distributable ZIP.

## Active Task

**36a: Headless lists-directory relocation (S, first micro-task of 36-M).**

- Branch: `implementer/task-36a-relocate-headless`; base and integration: `main`.
- Scope: `implementer/src/todo_md/storage.py` and `implementer/src/tests/test_storage.py`; automatic version-hook update allowed. No GUI changes.
- Acceptance: create destination parents; optionally move only Markdown files without overwriting existing destination lists; preserve non-Markdown files; handle empty/missing source. Remain headless and pass full suite.
- Required tests: moved contents and source cleanup; no-move; target containing Markdown rejected for both modes without source changes; empty/missing source; nested destination creation.
- Exact commands from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/test_storage.py -v)`; `(cd src && .venv/bin/python -m pytest tests -v)`.

### Delegated Prompt

You are the Implementer for Task 36a. Work only on assigned branch implementer/task-36a-relocate-headless; main is its base and integration branch. First verify git branch --show-current and inspect git status --short from implementer/. If the branch is wrong or the tree is dirty, stop without modifying anything. Follow implementer/AGENTS.md, including the 1,200-second limit and checkpoint wrap-up.

After measuring ../architect/DESIGN.md, read its Persistence component and Data Models and Flow context. Never read TASKS.md. Restrict edits to src/todo_md/storage.py and src/tests/test_storage.py under implementer/ (the normal automatic VERSION hook change is allowed). Never change any AGENTS.md, anything under architect/, or repository-root files. Do not create, switch, merge, rebase, rename, delete, or push branches; never commit to main. No broad staging or destructive working-tree operations.

Implement a headless relocate_lists(old_dir, new_dir, move) capability in storage.py. Create the destination including parents. With move=True move each top-level *.md file, retaining its name and exact bytes; leave non-Markdown source content untouched. With move=False leave the source unchanged and create the destination. Reject a destination already containing any Markdown file with a clear exception before moving anything, for either mode. Empty or missing source is successful and still creates the destination. Use stdlib only and no tkinter imports. Do not change the GUI or controller. Preserve content on ordinary move failures and never deliberately overwrite a destination list.

Add temp-directory unit tests for moved contents/non-Markdown preservation, no-move, populated-target rejection in both modes with unchanged source/target bytes, and empty/missing source with parent creation. Exact commands from implementer/: (cd src && .venv/bin/python -m pytest tests/test_storage.py -v) and (cd src && .venv/bin/python -m pytest tests -v). Prefer setting the tool workdir to implementer/src/ and running the inner commands directly. Both must pass; the two existing gated integration tests may remain skipped.

Commit completed work or stabilized partial work on the assigned branch with explicit file staging and normal hooks. Report BRANCH, COMMIT, completed/remaining scope, exact test results, blockers, and final working-tree status; end with RESULT: SUCCESS or RESULT: FAILURE. A commit is a checkpoint, not integration approval. Do not merge or push.

## Queue

- **36b: GUI lists-directory relocation**, remaining micro-task of 36-M after 36a merges. Size before promotion; split further if medium. On changed-directory Save, prompt only if the old directory has lists using `messagebox.askyesnocancel` and exact text: "You are about to change the directory where your lists are stored from '<old>' to '<new>' but there are already lists in it." Yes moves; No changes directory without moving; Cancel retains the old directory while applying other settings. No popup for empty source (dedicated GUI test). Reject target containing lists and invalid completed-visible without persisting that change; empty path selects default. Keep the live store consistent with any moved files.

## Active Blockers

None.

## Recently Completed

- 35b: Settings Save/Cancel; verified and merged; `9c45b49`.
- 35a: Settings window construction; verified and merged; `895bfb5`.
- 34: Completed-item display filter; verified and merged; `bf3ab84`.
- 33: Startup settings wiring; verified and merged; `998778c`.
- 32: Headless settings core; verified and merged; `b0c3be2`.
