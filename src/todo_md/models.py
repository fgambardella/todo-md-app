"""Data models for the todo_md package."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class TodoItem:
    """A single todo entry."""

    text: str
    done: bool = False
    created: float = 0.0

    def __post_init__(self) -> None:
        if self.created == 0.0:
            self.created = time.time()


@dataclass
class TodoList:
    """A named collection of TodoItems."""

    name: str
    items: list[TodoItem] = field(default_factory=list)

    def add_item(self, text: str) -> TodoItem:
        """Append a new item with the given text.

        The text is stripped; a ValueError is raised if the resulting
        text is empty.
        """
        stripped = text.strip()
        if not stripped:
            raise ValueError("todo item text must not be empty")
        item = TodoItem(text=stripped)
        self.items.append(item)
        return item

    def toggle(self, index: int) -> TodoItem:
        """Flip the done state of the item at ``index`` and return it."""
        item = self.items[index]
        item.done = not item.done
        return item

    def remove(self, index: int) -> TodoItem:
        """Remove and return the item at ``index``."""
        return self.items.pop(index)

    def rename(self, new_name: str) -> None:
        """Rename this list."""
        self.name = new_name
