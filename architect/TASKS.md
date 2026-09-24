# TASKS.md

## Project Goal

Build a macOS desktop TODO app in Python (stdlib only, no runtime dependencies). Every list is persisted as its own plain Markdown file using GitHub-flavored checkbox syntax — no database. The Tkinter GUI is layered above a headless, fully testable domain/persistence/controller core. Support light/dark themes with a persisted user setting and a sensible system default.

## Test Policy

- Framework: pytest (selected as the standard Python framework).
- Full suite, from `implementer/src`: `.venv/bin/python -m pytest tests -v`
- Targeted: `.venv/bin/python -m pytest tests/<file>.py -v`
- GUI tests require a display (available on this Mac): destroy `root` in `finally`, call `root.update()` after building, probe effective colors via `winfo_rgb`. Headless tests must never launch the GUI.

## Current Implementation Summary

- Markdown persistence: each list stored as its own `.md` file with GFM checkboxes, atomic writes, filename-safe list names.
- Domain layer: validated add, toggle, remove, and rename of items with clear errors for empty text or bad indexes.
- Headless controller: create/delete lists and add/toggle/remove items; every mutation is persisted to disk immediately.
- GUI: list sidebar with create/delete, checkbutton item rows, entry to add items, per-item trash-icon delete control.
- Readability: item label foreground adapts to the effective background luminance, readable in both light and dark.
- Theming: persisted light/dark setting with macOS system-default detection on first start; GUI theme switcher applied at startup and on toggle, and persisted.
- Theme switches flip the whole window including item rows, verified in both switch directions.

## Active Task

**Task 14: Move the persisted theme setting from `<lists>/config.json` to `<app-root>/config/settings.json` with one-time migration**

- Branch: `implementer/14-config-dir` (base and integration branch: `main`)
- Scope: `implementer/src/todo_md/theme.py` (config functions operate on a `config_dir` containing `settings.json`; new `migrate_legacy_config`), `implementer/src/todo_md/app.py` (`TodoApp` gains `config_dir` parameter, default `os.path.dirname(os.path.abspath(data_dir))/config`), and the test files listed below. No other production behavior changes.
- Acceptance criteria:
  1. Theme setting lives at `<app-root>/config/settings.json`; production default `~/.todo-md-app/lists` → `~/.todo-md-app/config/settings.json` (verify by scratch check; commit no scratch files).
  2. `migrate_legacy_config(config_dir, legacy_path)`: if the legacy `<lists>/config.json` exists AND the new settings file does not, a valid legacy theme is copied atomically to the new file and the legacy file is deleted; a corrupt/invalid legacy file is left untouched and first-start detection still applies. Never touches list `.md` files.
  3. Existing semantics preserved at the new path: startup load, first-start system-default detection + write, toggle persistence, `save_theme` `ValueError` on invalid value, atomic writes.
  4. Full test suite passes (existing + updated + new).
- Required tests: update `tests/test_theme.py` (switch all cases to `config_dir = tmp_path/'config'`; add: migration happy path, migration no-op when new file exists, migration no-op on corrupt legacy + subsequent `load_theme` falls back to system default and rewrites a valid file). Update `tests/test_gui_theme.py` (new settings path for pre-written configs and first-start assertion; add GUI migration test: legacy dark config → app starts dark, `config/settings.json` written, legacy file deleted). Grep ALL of `tests/` for `TodoApp(` and make every instantiation that would otherwise write config into a shared tmp dir pass an isolated `config_dir`. Do not weaken any assertion except the moved file paths.
- Test commands (from `implementer/src`): `.venv/bin/python -m pytest tests -v`
- Delegated prompt:

> Assigned task (Task 14): move the persisted theme setting from the lists directory to a dedicated config directory, with a one-time legacy migration.
>
> Git rules: work ONLY on branch `implementer/14-config-dir` (base: `main`). Before editing, verify your current branch (`git branch --show-current`) and working tree (`git status --short`); if you are not on that branch with a clean tree, stop and report. Do NOT create/switch/merge/rebase/rename/delete/push any branch, do NOT commit to `main`, do NOT use broad staging (`git add -A`), and do NOT use destructive working-tree operations. Restrict all changes to files under `implementer/`; do not touch `implementer/AGENTS.md`, anything under `architect/`, or the repository root. Commit completed work (and stabilized partial work) on your branch, and end with a handoff stating the branch name and commit hash. If you are near ~1000 seconds of work, enter Wrap-Up mode: commit a checkpoint, report status/blockers/remaining work.
>
> Current state: `todo_md/theme.py` (your code is under `implementer/src/`) has `CONFIG_FILENAME = 'config.json'` and `load_theme(data_dir)` / `save_theme(data_dir, theme)` reading/writing `<lists-dir>/config.json` atomically (temp file + os.replace; first start detects the system default and writes it; corrupt/invalid → fallback + rewrite; save validates against `("light", "dark")`). `todo_md/app.py`: `TodoApp.__init__(self, controller, data_dir=None)` (defaults `data_dir` to `controller.store.data_dir`) calls `load_theme(self.data_dir)`; `_on_toggle_theme` calls `save_theme(self.data_dir, new)`.
>
> Work: (1) Refactor `todo_md/theme.py` (stdlib only, NO tkinter): rename the constant to `SETTINGS_FILENAME = 'settings.json'`; all config functions now take `config_dir: str` = the directory that will contain `settings.json`: `_settings_path(config_dir)`, `_write_atomic(config_dir, payload)` (makedirs config_dir; mkstemp temp INSIDE config_dir; os.replace), `load_theme(config_dir)`, `save_theme(config_dir, theme)` — semantics otherwise unchanged. Add `migrate_legacy_config(config_dir: str, legacy_path: str) -> None`: if `legacy_path` exists AND `<config_dir>/settings.json` does NOT — read the legacy file; if it parses and its `theme` value is valid, atomically write `{"theme": t}` to the new file AND delete the legacy file (os.remove); if corrupt or invalid, do nothing (leave legacy in place). Must never touch list `.md` files. (2) In `todo_md/app.py`: change the signature to `TodoApp.__init__(self, controller, data_dir=None, config_dir=None)`; default `config_dir = os.path.join(os.path.dirname(os.path.abspath(data_dir)), 'config')`; store as `self.config_dir`. BEFORE the `load_theme` call, run `migrate_legacy_config(self.config_dir, os.path.join(os.path.abspath(self.data_dir), 'config.json'))`. Use `load_theme(self.config_dir)`; `_on_toggle_theme` must `save_theme(self.config_dir, new)`. (3) Tests as specified in the task: update `tests/test_theme.py` (all cases use `config_dir = tmp_path/'config'`; new cases: migration happy path — legacy dark → new file written, legacy gone; no-op when new settings file already exists; no-op on corrupt legacy + subsequent `load_theme` returns `system_default_theme()` and creates a valid file). Update `tests/test_gui_theme.py` (display available; destroy root in `finally`; pre-written configs move to `tmp_path/'config'/'settings.json'`; first-start asserts the new path; add GUI migration test: legacy `{"theme": "dark"}` in `tmp_path/'lists'/'config.json'` → build `TodoApp(TodoController(MarkdownListStore(tmp_path/'lists')), config_dir=str(tmp_path/'config'))` → assert `app.theme == 'dark'`, new file parses to dark, legacy deleted). Grep ALL of `tests/` for `TodoApp(` — every instantiation that does not pass `config_dir` would write config into a shared tmp parent dir; update those to pass an isolated `config_dir`. Do not weaken any existing assertion except the moved file paths.
>
> Acceptance: criteria 1–4 of Task 14 in TASKS.md (new path with production default `~/.todo-md-app/lists` → `~/.todo-md-app/config`; one-time migration with legacy deletion; corrupt legacy untouched; toggle persists to `config/settings.json`; full suite green).
>
> Run from `implementer/src`: `.venv/bin/python -m pytest tests -v`. ALL tests must pass before finishing. Then reply with exactly `RESULT: SUCCESS` (or `RESULT: FAILURE` plus a short error summary if you cannot).

## Queue

None.

## Active Blockers

None.

## Recently Completed

- Task 13 — item rows kept dark background after dark→light theme switch: fixed, verified, merged (0edf5b2).
- Tasks 12/12a — GUI theme switcher + startup theme application persisted to config.json: completed, verified, merged (8e8bf73).
- Tasks 1–11 — storage, models, controller, GUI, toggle bug, row layout, trash-icon delete, adaptive contrast, headless theme module: completed, verified, merged (pre-reorganization history; see `git log`).
