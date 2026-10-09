"""Headless controller layer for the todo_md package.

This module holds ``TodoController``, the UI-agnostic view-model that
mediates between the user (or UI) and the ``MarkdownListStore``. It has no
tkinter dependency, so the controller can be imported and tested on
headless machines without a display. ``todo_md.app`` re-exports the class
for compatibility with existing importers.
"""

from __future__ import annotations

import os

from .models import TodoItem, TodoList
from .storage import MarkdownListStore, relocate_lists


class TodoController:
    """Mediates between the user (or UI) and the MarkdownListStore.

    All methods that load/mutate a list follow the pattern:
    load -> mutate -> persist via ``store.save``.
    """

    def __init__(
        self, store: MarkdownListStore, data_dir: str | None = None
    ) -> None:
        self.store = store
        self.data_dir = data_dir if data_dir is not None else store.data_dir

    def change_lists_dir(self, new_dir: str | os.PathLike[str], move: bool) -> None:
        """Switch storage after relocation succeeds; equivalent paths are a no-op.

        Errors propagate without changing either binding. Relocation is per-file,
        so an error can still leave some lists at the destination; no rollback is
        attempted. Settings persistence is the caller's responsibility.
        """
        old_dir = self.store.data_dir
        try:
            if os.path.samefile(old_dir, new_dir):
                return
        except FileNotFoundError:
            pass  # Relocation handles missing source/destination directories.

        from . import app  # compat: frozen tests patch relocate_lists on todo_md.app

        app.relocate_lists(old_dir, new_dir, move)
        new_store = MarkdownListStore(new_dir)
        self.store = new_store
        self.data_dir = new_store.data_dir

    # -- list-level operations -------------------------------------------

    def list_names(self) -> list[str]:
        """Return the names of all stored lists, sorted."""
        return self.store.lists()

    def open_list(self, name: str) -> TodoList:
        """Load a list into a TodoList of TodoItem objects."""
        todo_list = TodoList(name=name)
        for text, done, description in self.store.load(name):
            todo_list.items.append(
                TodoItem(text=text, done=done, description=description)
            )
        return todo_list

    def create_list(self, name: str) -> None:
        """Create an empty list; the name must be non-empty."""
        if not name or not name.strip():
            raise ValueError("list name must not be empty")
        self.store.create(name)

    def delete_list(self, name: str) -> None:
        """Delete a list."""
        self.store.delete(name)

    # -- item-level operations (load -> mutate -> save) -------------------

    def add_item(self, name: str, text: str) -> TodoItem:
        """Add an item to the list and persist the change."""
        if not text or not text.strip():
            raise ValueError("todo item text must not be empty")
        todo_list = self.open_list(name)
        todo_list.add_item(text)
        self.store.save(
            name, [(i.text, i.done, i.description) for i in todo_list.items]
        )
        return todo_list.items[-1]

    def toggle_item(self, name: str, index: int) -> TodoItem:
        """Flip the done state of the item at ``index`` and persist it."""
        todo_list = self.open_list(name)
        toggled = todo_list.toggle(index)
        self.store.save(
            name, [(i.text, i.done, i.description) for i in todo_list.items]
        )
        return toggled

    def edit_item(
        self, name: str, index: int, text: str, description: str = ''
    ) -> TodoItem:
        """Replace the text (and optionally the description) at ``index``.

        Empty or whitespace-only text is rejected before anything is
        loaded or persisted. Saving unchanged text *and* unchanged
        description (ignoring surrounding whitespace) is a no-op: nothing
        is written; a description-only change is still persisted.
        """
        stripped = (text or "").strip()
        if not stripped:
            raise ValueError("todo item text must not be empty")
        stripped_desc = (description or "").strip()

        todo_list = self.open_list(name)
        item = todo_list.items[index]
        if item.text == stripped and item.description == stripped_desc:
            return item

        todo_list.edit(index, stripped, stripped_desc)
        self.store.save(
            name, [(i.text, i.done, i.description) for i in todo_list.items]
        )
        return todo_list.items[index]

    def remove_item(self, name: str, index: int) -> TodoItem:
        """Remove the item at ``index`` and persist the change."""
        todo_list = self.open_list(name)
        removed = todo_list.remove(index)
        self.store.save(
            name, [(i.text, i.done, i.description) for i in todo_list.items]
        )
        return removed
