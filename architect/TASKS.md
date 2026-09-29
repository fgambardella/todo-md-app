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

None.

## Queue

- **36b: GUI lists-directory relocation**, remaining micro-task of 36-M after 36a merges. Size before promotion; split further if medium. On changed-directory Save, prompt only if the old directory has lists using `messagebox.askyesnocancel` and exact text: "You are about to change the directory where your lists are stored from '<old>' to '<new>' but there are already lists in it." Yes moves; No changes directory without moving; Cancel retains the old directory while applying other settings. No popup for empty source (dedicated GUI test). Reject target containing lists and invalid completed-visible without persisting that change; empty path selects default. Keep the live store consistent with any moved files.

## Active Blockers

None.

## Recently Completed

- 36a: Headless lists-directory relocation; independently verified, approved for merge; `f543275d8ed131dce5e0359ccf4f00aa847c0e3a`.
- 35b: Settings Save/Cancel; verified and merged; `9c45b49`.
- 35a: Settings window construction; verified and merged; `895bfb5`.
- 34: Completed-item display filter; verified and merged; `bf3ab84`.
- 33: Startup settings wiring; verified and merged; `998778c`.
