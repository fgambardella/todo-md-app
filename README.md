# todo-md-app

A small **desktop TODO application for macOS**, written in Python (stdlib only, no runtime dependencies). Its defining trait: **every list is persisted as its own plain Markdown file** using GitHub-flavored checkbox syntax, so your data is human-readable, diffable, and portable — no database.

Lists are stored by default in `~/.todo-md-app/lists/`, one file per list, e.g. `Shopping.md` (an item's optional multi-line description is stored as two-space-indented lines under its checkbox line):

```markdown
# Shopping
- [x] Buy milk
- [ ] Buy bread
  2% if available
- [ ] Coffee beans
```

App settings (theme, completed-item visibility, lists directory) persist as `settings.json` in a dedicated config directory (e.g. `~/.todo-md-app/config`), separate from the Markdown lists.

## Architecture

The code lives in `src/todo_md/` and is layered so that all business logic is testable headlessly (no display required):

```
src/
├── todo_md/
│   ├── __init__.py     # package exports (domain, storage, settings, version)
│   ├── models.py       # Domain layer: TodoItem, TodoList dataclasses
│   ├── storage.py      # Persistence layer: MarkdownListStore
│   ├── settings.py     # Headless settings (Settings, load/save, theme resolution)
│   ├── version.py      # Headless version loader (get_version)
│   ├── VERSION         # App version (X.Y.Z), auto-bumped by the git hook
│   ├── assets/         # Dock/Finder icon source (dock_icon.png)
│   ├── app.py          # TodoController (UI-agnostic view-model) + TodoApp (tkinter GUI)
│   ├── settings_window.py # Settings Toplevel GUI (construction + save flow), lazy-imported by app.py
│   └── __main__.py     # Entry point: python -m todo_md
├── requirements-dev.txt # Dev-only pins (PyInstaller)
├── scripts/
│   ├── build_app.sh    # PyInstaller build → self-contained dist/todo-md.app (Apple Silicon only)
│   ├── release_package.sh # Builds the bundle + versioned release zip
│   └── bump_version.sh # version bump + pre-commit hook installer
└── tests/              # pytest suite (headless core + GUI tests on a real display)
```

- **Domain — `models.py`**: `TodoItem` (text, done flag, creation timestamp, optional multi-line description) and `TodoList` (name, items) with validated operations: `add_item`, `edit` (title + description), `toggle`, `remove`, `rename`.
- **Persistence — `storage.py`**: `MarkdownListStore` reads/writes each list as `<Name>.md` (`- [ ]` / `- [x]` checkbox lines under a `# Name` header; an item description is stored as two-space-indented continuation lines directly under its checkbox line — legacy files parse as empty description, empty descriptions write no extra lines). Writes are **atomic** (temp file + `os.replace`, no partial content on failure); list names are sanitized to filesystem-safe characters.
- **View-model — `app.py` (`TodoController`)**: pure logic bridging domain and storage: create/delete lists, open a list, add/toggle/edit/remove items — every mutation is persisted immediately. No tkinter imports, so it is fully unit-testable without a display.
- **Versioning — `version.py` + `VERSION`**: headless `get_version()` reads `todo_md/VERSION` (falls back to `0.0.0`); the GUI displays it as a small low-contrast badge in the bottom-right corner. A git pre-commit hook (installed via `implementer/src/scripts/bump_version.sh --install-hook`) bumps the patch version on every commit.
- **Presentation — `app.py` (`TodoApp`)**: a native-feeling **Tkinter** GUI (list sidebar with create/delete — button or Enter in the new-list entry, checkbutton-backed item rows with a trash-bin delete icon and an edit icon opening a pre-populated modal dialog (title entry + multi-line description box, both persisted on Save) — double-clicking an unfinished item's text opens the same dialog —, an entry + button for adding items, refresh after each mutation). Completed items retain completion order above unfinished items and only the newest configured count is shown (hidden items are never deleted from disk). A settings window changes theme, completed-item visibility and the lists directory (with optional list movement) live, persisting the full payload on Save. Modal dialogs (settings window, item-edit dialog) open vertically and horizontally centered on the main window. Deleting a list or an item first asks for confirmation (Yes/No popup). Tkinter is imported lazily so the package stays importable on display-less machines/CI.
- **Entry point — `__main__.py`**: launches controller + GUI via `run()`.
- **Build tooling — `scripts/build_app.sh`**: freezes the app into a self-contained `todo-md.app` bundle for Apple Silicon macOS (see “Building a self-contained app bundle” below).

Data flow: **GUI → Controller → (Models) → MarkdownListStore → `.md` files**, with the store re-read after each mutation to drive the UI refresh.

## Prerequisites

- Python 3.x (macOS)
- Tk support for your Python. With Homebrew Python you must install the matching glue formula, e.g. `brew install python-tk@3.14` (otherwise `ModuleNotFoundError: No module named '_tkinter'`)
- A virtualenv (the system Python is PEP-668 externally managed)

```bash
cd src
python3 -m venv .venv
.venv/bin/pip install pytest
```

### Installing the version-bump git hook (developers)

The app version lives in `src/todo_md/VERSION` and is auto-incremented (patch) on every commit by a git pre-commit hook. Hooks are not stored in the repository, so on a freshly cloned repo install it once from the repo root:

```bash
./implementer/src/scripts/bump_version.sh --install-hook
```

## Running the tests

All core tests run headless (they never launch the GUI); the `test_gui_*.py` tests require a display (available on macOS):

```bash
cd src
.venv/bin/python -m pytest tests -v
```

Expected: 344 passing tests (plus 2 skipped gated integration tests: full build with `RUN_BUILD_TESTS=1`, release packaging with `RUN_RELEASE_TESTS=1`) across `test_storage.py`, `test_models.py`, `test_controller.py`, `test_settings.py`, `test_version.py`, `test_gui_headless.py` (the latter also includes an end-to-end session that asserts the exact Markdown produced on disk), `test_build_script.py`, `test_release_package.py`, `test_startup.py`, `test_visible_items.py`, `test_dialog_guard.py`, `test_gui_lifecycle.py`, plus GUI tests `test_gui_toggle.py`, `test_gui_layout.py`, `test_gui_delete.py`, `test_gui_delete_icon.py`, `test_gui_trash_icon.py`, `test_gui_edit.py`, `test_gui_double_click.py`, `test_gui_contrast.py`, `test_gui_theme.py`, `test_gui_theme_switch.py`, `test_gui_hover.py`, `test_gui_new_list.py`, `test_gui_version.py`, `test_gui_version_colors.py`, `test_gui_placeholders.py`, `test_gui_confirm.py`, `test_gui_dock_icon.py`, `test_gui_settings.py`, `test_gui_centering.py`.

## Running the app

From the `src/` directory, using the venv:

```bash
.venv/bin/python -m todo_md
```

This opens the Tkinter window. Your lists are created and edited in `~/.todo-md-app/lists/` as plain Markdown files, which you can also edit by hand and see reflected on the next refresh.

## Building a self-contained app bundle (macOS, Apple Silicon)

On an Apple Silicon Mac, the build script freezes the app into a self-contained `todo-md.app` bundle using PyInstaller (a dev-only build dependency — the app itself stays stdlib-only):

```bash
cd implementer/src
bash scripts/build_app.sh
```

- Also works from the repo root: `bash implementer/src/scripts/build_app.sh` (all paths resolve relative to the script).
- Aborts with a clear error on non-arm64 hosts.
- If PyInstaller is missing it is installed into `.venv` automatically (pinned in `implementer/src/requirements-dev.txt`).
- Output: `implementer/src/dist/todo-md.app` — open it in Finder or run `dist/todo-md.app/Contents/MacOS/todo-md`. `build/` and `dist/` are local artifacts and are never committed.
- The bundle shows a custom Finder icon: the script generates a `.icns` from `todo_md/assets/dock_icon.png` via macOS `sips`/`iconutil` at build time.
- The script ends with a smoke check: the bundle must launch, stay alive ~3s without any traceback in stderr, then it is terminated.
- The full build is also covered by a gated integration test (skipped by default to keep the suite fast): from `implementer/src`, `RUN_BUILD_TESTS=1 .venv/bin/python -m pytest tests/test_build_script.py -v`.

## Packaging and release

One command builds the bundle and packages the distributable release zip:

```bash
cd implementer/src
bash scripts/release_package.sh
```

- Reuses `build_app.sh` (arm64-only guard, launch smoke check), validates `todo_md/VERSION` is a strict `X.Y.Z`, then zips `dist/todo-md.app` via `ditto -c -k --noextattr --noqtn` into `dist/todo-md-<version>-arm64.zip` with `todo-md.app` at the zip root (no wrapper dir, no `__MACOSX` entries); prints the zip path, size, and SHA-256.
- A GitHub Release is not a repo folder: the zip travels as a **release asset**. Create the release in the GitHub web UI (repo → **Releases** → **Draft a new release**), set the tag to `v<version>` matching the zip, and attach the zip as an asset.
- Artifacts stay in the gitignored `dist/`; never commit them.
- Gated end-to-end test (real build + zip assertions), from `implementer/src`: `RUN_RELEASE_TESTS=1 .venv/bin/python -m pytest tests/test_release_package.py -v`.
