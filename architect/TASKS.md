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
- Headless relocation can move Markdown lists without overwriting destination files, or prepare a new folder while leaving lists in place; non-Markdown content is preserved.
- The GUI supports list creation, item toggles, per-item deletion, placeholder hints, and confirmation of destructive actions.
- Light/dark themes include readable item text, entry fills, button states, and a theme-aware version badge; custom dock and Finder icons are supported.
- Settings support theme, lists directory, and completed-item visibility, with tolerant loading and atomic saving. Startup honors the saved directory while configuration stays fixed.
- A single-instance settings window validates and saves the full payload, applies theme/filter live, and leaves all settings unchanged on Cancel. Directory changes currently apply at restart.
- Completed-item filtering is display-only and preserves stored content.
- Build and release scripts produce a launch-tested Apple Silicon app bundle and versioned distributable ZIP.

## Active Task

**36b1: Headless controller directory switching (S).**

- Parent estimate: 36b is M, covering runtime store rebinding plus GUI decisions, validation, and persistence. Split sequentially into 36b1 (controller) and 36b2 (settings Save integration).
- Branch: `implementer/task-36b1-relocate-controller`; base and integration: `main`.
- Status: prepared for user-interactive delegation; no child process running.
- Scope: `implementer/src/todo_md/app.py` imports and `TodoController` only; `implementer/src/tests/test_controller.py`; automatic VERSION hook change allowed.
- Acceptance: a headless controller operation reuses storage relocation and binds future reads/writes to the destination only on success. No GUI/settings behavior changes. Same-directory requests are no-ops; failures propagate without changing the controller binding.
- Required tests: moved lists remain editable at destination; no-move preserves old files and redirects new writes; populated/invalid destination and injected relocation failure retain old binding; same directory and equivalent paths do not relocate.
- Commands from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/test_controller.py tests/test_storage.py tests/test_gui_headless.py -v)`; `(cd src && .venv/bin/python -m pytest tests -v)`.

### Delegated Prompt

You are the Implementer for Task 36b1. Work only on assigned branch implementer/task-36b1-relocate-controller; main is its base and integration branch. First verify git branch --show-current and git status --short from implementer/. Stop without changes if the branch is wrong, is main, or the tree is dirty. Follow implementer/AGENTS.md, including the 1,200-second time budget and stabilized-checkpoint wrap-up.

Measure ../architect/DESIGN.md before reading it, then use its Controller/Persistence components, Data Models and Flow, and Known Architectural Debt. Never read TASKS.md. Only edit imports and TodoController in src/todo_md/app.py, plus src/tests/test_controller.py, under implementer/. The normal automatic VERSION hook change is allowed. Never modify any AGENTS.md, any architect/ file, or repository-root files. Do not create, switch, merge, rebase, rename, delete, or push branches. Never commit to main; no broad staging or destructive working-tree operations.

Add one headless TodoController operation to change the lists directory, taking the new directory and whether to move existing lists. Reuse storage.relocate_lists, without reimplementing copying or changing storage.py. Use the currently bound store directory as the source of truth, not a potentially different constructor data_dir override. After successful relocation, bind the controller store and controller.data_dir consistently to the destination so all future list/item operations use it. With move=False, old lists remain on disk and the active destination starts without lists. Treat the same directory, including normalized or symlink-equivalent paths, as a no-op rather than rejecting its existing lists. If validation or relocation fails, propagate the error and leave the original store binding and controller.data_dir unchanged. Do not add batch rollback; the existing documented per-file failure semantics remain. Keep GUI, startup, and settings persistence behavior untouched, and keep imports headless.

Add isolated temp-directory tests proving: move=True preserves contents and list discovery, then toggle/add writes only to the destination; move=False leaves old bytes intact and new list creation uses the destination; a populated destination and an invalid path leave bindings unchanged; an injected relocation error does not rebind; same-directory and equivalent-path requests preserve files without calling relocation; an explicit controller data_dir override does not cause relocation from the wrong source. Avoid new abstractions or unrelated refactoring.

Exact commands from implementer/: (cd src && .venv/bin/python -m pytest tests/test_controller.py tests/test_storage.py tests/test_gui_headless.py -v) and (cd src && .venv/bin/python -m pytest tests -v). Prefer setting tool workdir to implementer/src/ and running the inner commands. Both must pass; the two gated integration tests may remain skipped. Commit completed or stabilized partial work with explicit file staging and normal hooks. Report BRANCH, COMMIT, completed/remaining work, commands/results, blockers, and final working-tree status; end with RESULT: SUCCESS or RESULT: FAILURE. A commit is a checkpoint, not approval. Do not merge or push.

## Queue

- **36b2: GUI lists-directory relocation**, after 36b1. On changed-directory Save, prompt only if the old directory has lists using `messagebox.askyesnocancel` and exact text: "You are about to change the directory where your lists are stored from '<old>' to '<new>' but there are already lists in it." Yes moves; No switches without moving; Cancel retains the old directory while applying other settings. No popup for empty source (dedicated test); unchanged/equivalent paths bypass relocation. Validate completed-visible before disk changes; reject populated targets without persisting changes; empty path selects default. Reuse controller switching, refresh live state, and test relocation/settings-save failures with explicit recovery guidance for retained files. Isolate all GUI test directories.

## Active Blockers

- Interactive Implementer launch and handoff are required for 36b1; do not launch an unattended child while user approvals are inaccessible.

## Recently Completed

- 36a: Headless lists-directory relocation; independently verified and merged; `f543275d8ed131dce5e0359ccf4f00aa847c0e3a`.
- 35b: Settings Save/Cancel; verified and merged; `9c45b49`.
- 35a: Settings window construction; verified and merged; `895bfb5`.
- 34: Completed-item display filter; verified and merged; `bf3ab84`.
- 33: Startup settings wiring; verified and merged; `998778c`.
