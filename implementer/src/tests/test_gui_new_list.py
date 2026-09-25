"""GUI test: pressing Enter in the new-list entry creates the list."""

import tkinter.ttk  # noqa: F401  (ensure ttk available)

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def test_return_creates_list(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)

    app = TodoApp(controller, config_dir=str(tmp_path / "config"))
    try:
        app.root.update()

        app.new_name_entry.insert(0, "enter-list")
        app.new_name_entry.focus_force()
        app.new_name_entry.event_generate("<Return>")
        app.root.update()

        # List exists on disk in the store's data dir
        assert (tmp_path / "enter-list.md").exists()
        # List appears in the listbox
        assert "enter-list" in list(app.listbox.get(0, "end"))
        # Entry is cleared
        assert app.new_name_entry.get() == ""
        # Newly created list is selected
        assert app.current_list == "enter-list"
    finally:
        app.root.destroy()


def test_return_with_empty_entry_creates_nothing(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)

    app = TodoApp(controller, config_dir=str(tmp_path / "config"))
    try:
        app.root.update()

        assert app.new_name_entry.get() == ""
        app.new_name_entry.focus_force()
        app.new_name_entry.event_generate("<Return>")
        app.root.update()

        # No list was created
        assert store.lists() == []
        assert app.listbox.size() == 0
    finally:
        app.root.destroy()