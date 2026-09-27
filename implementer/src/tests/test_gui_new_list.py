"""GUI test: pressing Enter in the new-list entry creates the list.

The entry starts showing its muted placeholder (task 22); a simulated
FocusIn event removes the placeholder deterministically (no reliance on
the window manager delivering real focus). Note: Tk routes synthetic key
events to the app's focus window, so the entry still needs focus_force()
before the generated <Return> reaches its binding.
"""

import tkinter.ttk  # noqa: F401  (ensure ttk available)

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def test_return_creates_list(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)

    app = TodoApp(controller, config_dir=str(tmp_path / "config"))
    try:
        app.root.update()

        app.new_name_entry.event_generate("<FocusIn>")
        app.root.update()
        # Focus cleared the placeholder; enter the new list name.
        app.new_name_entry.delete(0, "end")
        app.new_name_entry.insert(0, "enter-list")
        # Give the entry keyboard focus so the synthetic <Return> below is
        # dispatched to its binding (focus_force is the only deterministic
        # way to activate the test app in this environment).
        app.new_name_entry.focus_force()
        app.root.update()
        app.new_name_entry.event_generate("<Return>")
        app.root.update()

        # List exists on disk in the store's data dir
        assert (tmp_path / "enter-list.md").exists()
        # List appears in the listbox
        assert "enter-list" in list(app.listbox.get(0, "end"))
        # Entry is cleared and stays placeholder-free: it still holds
        # focus after submit, so _restore_placeholder must leave it
        # empty instead of re-inserting the hint.
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

        # Unfocused empty entry shows its muted placeholder hint.
        assert app.new_name_entry.get() == "Insert the name of a new list here"
        app.new_name_entry.event_generate("<FocusIn>")
        app.root.update()
        # Focus removed the placeholder: the field is now truly empty.
        assert app.new_name_entry.get() == ""
        # Focus the entry so the generated <Return> actually reaches the
        # handler (the no-op path must be exercised, not skipped).
        app.new_name_entry.focus_force()
        app.root.update()
        app.new_name_entry.event_generate("<Return>")
        app.root.update()

        # No list was created
        assert store.lists() == []
        assert app.listbox.size() == 0
    finally:
        app.root.destroy()