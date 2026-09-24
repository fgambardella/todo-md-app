# todo-md-app

A small **desktop TODO application for macOS**, written in Python (stdlib only, no runtime dependencies). Its defining trait: **every list is persisted as its own plain Markdown file** using GitHub-flavored checkbox syntax, so your data is human-readable, diffable, and portable — no database.

Lists are stored by default in `~/.todo-md-app/lists/`, one file per list, e.g. `Shopping.md`:

```markdown
# Shopping
- [x] Buy milk
- [ ] Buy bread
- [ ] Coffee beans
```

## Architecture

The code lives in `src/todo_md/` and is layered so that all business logic is testable headlessly (no display required):

```
src/
├── todo_md/
│   ├── __init__.py     # package exports (MarkdownListStore)
│   ├── models.py       # Domain layer: TodoItem, TodoList dataclasses
│   ├── storage.py      # Persistence layer: MarkdownListStore
│   ├── app.py          # TodoController (UI-agnostic view-model) + TodoApp (tkinter GUI)
│   └── __main__.py     # Entry point: python -m todo_md
└── tests/              # pytest suite (run headless, never launches the GUI)
```

- **Domain — `models.py`**: `TodoItem` (text, done flag, creation timestamp) and `TodoList` (name, items) with validated operations: `add_item`, `toggle`, `remove`, `rename`.
- **Persistence — `storage.py`**: `MarkdownListStore` reads/writes each list as `<Name>.md` (`- [ ]` / `- [x]` checkbox lines under a `# Name` header). Writes are **atomic** (temp file + `os.replace`, no partial content on failure); list names are sanitized to filesystem-safe characters.
- **View-model — `app.py` (`TodoController`)**: pure logic bridging domain and storage: create/delete lists, open a list, add/toggle/remove items — every mutation is persisted immediately. No tkinter imports, so it is fully unit-testable without a display.
- **Presentation — `app.py` (`TodoApp`)**: a native-feeling **Tkinter** GUI (list sidebar with create/delete, checkbutton-backed item rows, an entry + button for adding items, refresh after each mutation). Tkinter is imported lazily so the package stays importable on display-less machines/CI.
- **Entry point — `__main__.py`**: launches controller + GUI via `run()`.

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

## Running the tests

All tests run headless (the GUI is never launched):

```bash
cd src
.venv/bin/python -m pytest tests -v
```

Expected: 63 passing tests across `test_storage.py`, `test_models.py`, `test_controller.py`, `test_theme.py`, `test_gui_headless.py` (the latter also includes an end-to-end session that asserts the exact Markdown produced on disk), plus GUI tests `test_gui_toggle.py`, `test_gui_layout.py`, `test_gui_delete.py`, `test_gui_delete_icon.py`, `test_gui_trash_icon.py`, `test_gui_contrast.py`, `test_gui_theme.py`, and `test_gui_hover.py`.

## Running the app

From the `src/` directory, using the venv:

```bash
.venv/bin/python -m todo_md
```

This opens the Tkinter window. Your lists are created and edited in `~/.todo-md-app/lists/` as plain Markdown files, which you can also edit by hand and see reflected on the next refresh.
