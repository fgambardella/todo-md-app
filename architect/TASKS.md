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

**36b2: GUI relocation recovery (M); current micro-task R1: unattended test harness (S).**

- Branch: `implementer/task-36b2-settings-relocation`; base/integration: `main`. Keep this branch through all recovery; no merge until 36b2 is complete.
- Latest checkpoint: `f1af14c587daaf9165dda08a1fd314913391b889`, not approved; clean tree. Architect verified 76 headless tests and four image tests in isolation. Unsafe settings/full runs deferred.
- Status/blocker: real popups, invalid fixtures, leaked roots, and product acceptance failures.
- Revised approach: sequential interactive R1 tests, R2 decisions, R3 live-state/error recovery; keep partial work unmerged.
- R1 scope: `implementer/src/tests/{conftest,test_dialog_guard,test_gui_settings}.py`; normal VERSION hook update only outside tests.
- R1 acceptance: fail-fast suite-wide dialog protection, explicit expected responses, isolated aligned settings fixtures, reliable root cleanup, and passing guard regression tests. Settings/full suites run unattended and report remaining product failures without weakening assertions.
- Remaining feature acceptance is captured in R2/R3 below. Required tests and exact commands are in the delegated prompt; both full runs must be unattended.

### Delegated Prompt

Implement Task 36b2 recovery R1: unattended GUI tests. Assigned branch: implementer/task-36b2-settings-relocation; main is base/integration. Start from checkpoint f1af14c587daaf9165dda08a1fd314913391b889 plus Architect planning commits. Verify git branch --show-current, git status --short, and checkpoint ancestry first. Stop if branch is wrong/main or tree dirty. Follow implementer/AGENTS.md and its 1,200-second limit/checkpoint wrap-up.

Measure ../architect/DESIGN.md before reading its Presentation, External Interfaces, and Known Architectural Debt sections. Never read TASKS.md. Only change src/tests/test_gui_settings.py and add src/tests/conftest.py and src/tests/test_dialog_guard.py under implementer/. The normal VERSION hook update is allowed. No production, manifests, other tests, AGENTS.md, architect/, or repository-root changes. No branch create/switch/merge/rebase/rename/delete/push, main commits, broad staging, or destructive operations.

Before running settings/full suites, add a function-autouse guard preventing real modal dialogs across tests. Guard the common native-dialog path (tkinter.commondialog.Dialog.show covers current messageboxes/file pickers), record unexpected attempts and raise before opening anything. Also fail at fixture teardown if a Tk callback swallowed the exception. Do not create a Tk root merely by loading the fixture. Leave explicit public-function mocks usable for expected True/False/None choices and error assertions; never globally answer Yes or silently suppress unexpected dialogs. Add focused guard regressions, using isolated pytest runs if useful, proving direct and callback-contained unmocked dialogs fail without blocking, native file pickers are blocked, and explicitly mocked decisions still work.

Repair settings tests without changing intended product assertions. Isolate app.DEFAULT_DATA_DIR under tmp_path and align actual store, saved lists_dir, and dialog prefill. Preserve the distinction between initially absent settings and a preexisting payload; do not mutate caller dictionaries. Open Settings before accessing its variables/buttons. Assert prompt title and exact message separately. Patch todo_md.app.save_settings, where Save looks it up; restore real persistence for retry assertions. Prepare target directories before using them. Register reliable Tk cleanup immediately after app construction, including setup failures, and destroy roots even if update raises. Preserve update-before-destroy ordering. Keep explicit expected askyesnocancel/showerror mocks; do not permit native user interaction.

Do not redefine popup Cancel to match the broken implementation: it must keep the old directory while saving other valid settings. Blank entry must select the actual default directory, not merely save null. Retain tests for live sidebar/rows, destination-only writes, no-popup empty/equivalent paths, validation before effects, populated-target refusal, partial relocation failure, and settings-save failure with retry. Correct bogus setup/assertions but never skip, xfail, delete meaningful coverage, or mock the behavior under test just to turn tests green. Remaining real product failures are expected and belong to later recovery, not this tests-only micro-task.

Run from implementer/: (cd src && .venv/bin/python -m pytest tests/test_dialog_guard.py -v), (cd src && .venv/bin/python -m pytest tests/test_gui_settings.py tests/test_controller.py tests/test_storage.py tests/test_settings.py -v), and (cd src && .venv/bin/python -m pytest tests -v) twice as separate runs even if the first fails. Prefer tool workdir implementer/src/ with inner commands. Guard tests must pass; all runs must finish without human input or native dialogs. Record remaining failures accurately; do not claim full-feature success while they remain.

Commit stabilized test changes with explicit staging and normal hooks; mark the checkpoint partial if product failures remain. Report BRANCH, COMMIT, harness fixes, remaining product failures with test names, exact command results for both full runs, and final tree status. End RESULT: FAILURE if any required suite fails, otherwise RESULT: SUCCESS for this delegated scope only. No merge or push; Architect reviews the checkpoint before the next recovery micro-task.

## Queue

- **36b2-R2 (S):** correct Save decision/default-path flow on the same branch after R1. Yes/No/Cancel semantics; Cancel ignores abandoned destination but applies other settings; normalize blank/default paths and pass an actual path to the controller; validate theme/count first; no popup for empty/missing sources or equivalent paths; reject populated/unusable chosen targets. Exact message: "You are about to change the directory where your lists are stored from '<old>' to '<new>' but there are already lists in it."
- **36b2-R3 (S):** synchronize live directory/sidebar/selection and handle relocation/save failures on the same branch after R2. Preserve retained files, refresh after partial moves, keep destination usable after save failure, report unsaved restart preference, and support retry without moving again. Full unattended suite must pass before approving/merging 36b2.

## Active Blockers

- Unmocked dialogs and broken fixture lifecycle make settings/full-suite runs unsafe until R1 installs the guard.
- Product acceptance failures remain in Cancel, default switching, live refresh, and error recovery; checkpoint is not mergeable.
- Recovery awaits user-interactive Implementer execution; no unattended child launch.

## Recently Completed

- 36b1: Headless controller directory switching; verified and merged; `9612b3b`.
- 36a: Headless lists-directory relocation; verified and merged; `f543275`.
- 35b: Settings Save/Cancel; verified and merged; `9c45b49`.
- 35a: Settings window construction; verified and merged; `895bfb5`.
- 34: Completed-item display filter; verified and merged; `bf3ab84`.
