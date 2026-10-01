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
- The GUI supports list creation, item toggles, per-item deletion, placeholder hints, and confirmation of destructive actions. Main-window sizing keeps sidebar controls fully accessible. Completed items retain completion order above unfinished items, showing only the newest configured count without deleting hidden items.
- Light/dark themes include readable controls and insertion cursors, a theme-aware version badge, and custom dock/Finder icons. Settings theme controls have consistent palette colors and symmetric margins, including during live theme changes.
- Settings use fully visible, centered Save/Cancel actions, validate and save the full payload, apply theme and completed-item filtering live, and discard unsaved controls on window Cancel. Filtering never changes stored content.
- Directory changes apply live with optional list movement and an explicit confirmation question; popup Cancel retains the directory while saving other settings. Populated destinations are accepted, transfers reject filename collisions without overwriting, equivalent paths are harmless, and configuration stays fixed.
- Relocation failures preserve recoverable files and refresh the active view. Failed settings persistence keeps the destination usable and supports retry without repeating completed moves; pending theme/filter edits remain unapplied.
- Automated GUI tests intercept unexpected dialogs and verify cleanup after failures without human interaction.
- Build and release scripts produce a launch-tested Apple Silicon app bundle and versioned distributable ZIP.

## Active Task

### 43: Long-text test apparent stall (S)

- Branch: `implementer/task-43-long-text-test-lifecycle`; base/integration: `main`.
- Scope: diagnose and correct the long-label test's native-window lifecycle, not shorten the text or weaken layout coverage.
- Evidence: layout file passes in 0.88s; long-text call is 0.07s with negligible teardown. Full suite is 303 passed/2 gated skips in 22.28s; following lifecycle subprocess cases cost roughly 0.5-0.7s each. Native probes show Tk destruction can leave pending Cocoa/WindowServer cleanup. No actual text-rendering timeout reproduced.
- Acceptance: root cause is supported by timings/lifecycle evidence; long-label coverage remains meaningful and bounded; its window cannot remain visibly stalled through subsequent blocking subprocess tests. Preserve real mapped geometry tests and owned-root/error-cleanup guarantees. No sleeps, blanket skips, shortened data, or in-process replacement of isolation proofs. Avoid claiming a speedup unsupported by measurement.
- Required tests: regression for the diagnosed lifecycle/isolation issue with actual long text; existing mapped layout and failure-cleanup proofs; comparable targeted/full-suite timing. Prefer deterministic lifecycle assertions over fragile subsecond deadlines.
- Commands from `implementer/`: `(cd src && .venv/bin/python -m pytest tests/test_gui_layout.py tests/test_gui_lifecycle.py tests/test_dialog_guard.py -q --durations=15 -o faulthandler_timeout=10)`; `(cd src && .venv/bin/python -m pytest tests -q --durations=20 -o faulthandler_timeout=10)`.
- Complete Implementer prompt: Diagnose task 43 and implement the smallest evidence-backed correction within `src/tests/test_gui_layout.py`, `src/tests/conftest.py`, `src/tests/test_gui_lifecycle.py`, and `src/tests/test_dialog_guard.py` (normal hook VERSION change allowed). Long-label assertions currently inspect text/pack metadata, while separate tests require actual mapped geometry. Distinguish structural test needs, native window lifetime and the cost of following subprocess proofs; do not presume long-string rendering is slow. Investigate cleanup before choosing a change, retain owned-root teardown even on failure and fail-fast dialogs, and add a deterministic regression demonstrating the corrected behavior. A withdrawn structural-only test is acceptable only if evidence shows mapping is unnecessary and mapped geometry coverage remains intact, not as a way to suppress an actual uninvestigated hang. Do not edit application code or broaden into a suite rewrite. Follow DESIGN Verification harness/Tk compatibility. Run both commands and report precise diagnosis, before/after timing and any remaining platform-specific uncertainty.

## Queue

None.

## Active Blockers

None.

## Recently Completed

- 42: Input caret contrast across themes; independently verified and approved; `dceb909362fb036ec69712139c27492d86c9b5d3`.
- 41: Persisted completion order and safe filtered GUI callbacks; independently verified and approved; `5b9c4457bf25fc6b682ffd1e14e243577789e81c`.
- 40: Settings Theme palette and margins; independently verified and approved; `9d785ef23b8b9778645936b5e7f42113a8ae9434`.
- 39: Visible centered Settings actions; independently verified and approved; `7c69eb2413098f97ffa91d5e2507578c07aac669`.
- 38: Main-window sidebar visibility; independently verified and approved; `ba7e7bbe4fc309c02ed23c099403c292e81256af`.
