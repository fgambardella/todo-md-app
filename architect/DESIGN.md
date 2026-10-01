# DESIGN.md

## System Overview

- macOS desktop TODO application, Python stdlib runtime; Tkinter imports remain lazy for headless use.
- Each list is a portable Markdown file with GFM checkboxes, not a database.
- Domain, persistence, headless controller, and GUI have separate responsibilities.
- Default lists directory: `~/.todo-md-app/lists/`; fixed configuration directory: `~/.todo-md-app/config/`.
- Runtime dependencies remain stdlib-only; development dependencies are defined in `implementer/src/requirements-dev.txt`.

## Component Architecture

Paths below are relative to `implementer/src/`.

- **Domain**, `todo_md/models.py`: validated list/item operations and domain state; no UI or persistence dependencies.
- **Persistence**, `todo_md/storage.py`: Markdown list discovery, name sanitization, parsing, atomic list writes, and headless optional relocation using stdlib filesystem operations.
- **Settings**, `todo_md/settings.py`: headless validated settings, tolerant legacy loading, atomic JSON persistence, and live OS-theme resolution.
- **Controller**, `todo_md/app.py` (`TodoController`): coordinates domain objects and storage; mutations persist immediately; switches the active store through headless relocation and exposes the effective data directory.
- **Presentation**, `todo_md/app.py` (`TodoApp`): Tkinter list/item controls, confirmations, placeholders, completed-item visibility, themes, and single-instance settings dialog. Depends on controller, settings, version, and bundled assets.
- **Startup**, `todo_md/__main__.py` and `todo_md/app.py` (`startup_dirs`, `run`): load settings before constructing store, controller, and GUI; explicit config-directory overrides support isolated tests.
- **Version**, `todo_md/version.py`: package-relative version loading with a safe fallback; GUI displays a theme-aware badge.
- **Assets**, `todo_md/assets/`: presentation icons and attribution in `LICENSE.txt`; dock-icon loading fails softly.
- **Build and release**, `scripts/build_app.sh`, `scripts/release_package.sh`: dev-only PyInstaller bundling, Apple Silicon guard, icon conversion, launch smoke test, and versioned distributable ZIP. Artifacts remain gitignored.
- **Version tooling**, `scripts/bump_version.sh`: optional installed Git hook increments and stages `todo_md/VERSION`.
- **Verification harness**, `tests/conftest.py`: pytest fixtures intercept unexpected native dialogs and own only their created Tk roots. Bounded subprocess proofs in `tests/test_dialog_guard.py` and `tests/test_gui_lifecycle.py` verify error detection and cleanup without user input.

## Data Models and Flow

- Domain ownership and fields are canonical in `todo_md/models.py`; storage maps each list to `<Name>.md`. GUI-only filtering never changes persisted items.
- Toggle mutations persist completed items first in completion order using Markdown row order, without extra metadata; legacy completed rows retain relative order. Undo returns the item to the incomplete-group front, and re-completion makes it newest. Controller returns the selected object even when its position changes.
- GUI actions flow through controller to storage; list mutations are re-read for rendering. Storage writes use temporary files and replacement to avoid partial individual files.
- Window initial/minimum dimensions follow fixed-control requests; main-window sizing precedes loading lists so item text and list length cannot dictate size. Settings actions remain centered as one group.
- Relocation creates the destination and optionally transfers top-level Markdown files verbatim. Populated destinations are allowed; transfers preflight every source filename against existing destination paths, and exclusive creation prevents racing overwrites. Source deletion follows a completed copy, including across filesystems. Non-Markdown content remains in place.
- Controller switching uses the bound store directory as its source of truth and replaces both bindings only after success. Equivalent paths are no-ops; errors retain the original bindings. Settings persistence remains the caller's responsibility.
- Settings schema and validation are canonical in `todo_md/settings.py`. A null lists directory means the application default; legacy theme-only files load compatibly. Configuration never moves with lists.
- Startup resolves the lists directory from saved settings, creates it on demand, and supplies it to storage/controller. System theme is detected live, never persisted as a resolved choice.
- Settings Save validates theme/count before filesystem work, normalizes the directory, asks whether to move existing lists, and switches the controller before persisting the full payload. Relocation-popup Cancel retains the active directory while saving other edits; the settings-window Cancel discards unsaved controls. Theme/filter apply after persistence succeeds.
- Runtime directory preferences and views follow the bound store, not necessarily the last saved JSON. Failed relocation refreshes the remaining source; unreadable views clear safely. Failed preference persistence retains an editable destination and the previous theme/filter, reports the unsaved restart preference, and permits retry without repeating completed moves.

## External Interfaces

- Application entry: `python -m todo_md` from `implementer/src/`; build/run/test instructions remain in the root `README.md`.
- Persistence: UTF-8 Markdown checkbox files and `settings.json`; canonical formats are defined by `todo_md/storage.py` and `todo_md/settings.py`.
- OS integration: macOS system-theme detection uses `defaults read -g AppleInterfaceStyle` with a light fallback; packaging uses native icon/ZIP tooling via the scripts above.
- Tk compatibility: unsupported native appearance falls back to ttk clam with explicit palette colors for fields, sections, dialog backgrounds and interactive button/radio states. Native appearance remains untouched. Image labels use supported compound values. GUI tests must update each Tk root before destroying it.
- Installed version hooks affect every ordinary commit. Architect-only state commits use the user-approved command-scoped hook bypass; implementation commits retain normal hooks.

## Known Architectural Debt

- List batches and configuration cannot commit atomically: earlier moves remain at the destination after a later failure, and source-deletion failure leaves both copies. Automatic batch resume/rollback is unavailable; recovery of files split across directories may require manual intervention.
