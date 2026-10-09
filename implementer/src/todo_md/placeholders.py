"""Entry-placeholder mechanism for ``TodoApp``.

``PlaceholderBinder`` owns the entry widget -> placeholder hint mapping and
all focus-driven placeholder show/clear/restore behavior. The app is held
duck-typed (only ``app.root`` and ``app._palette`` are used), so this
module has no tkinter dependency and ``todo_md.app`` stays importable
headless.
"""

from __future__ import annotations


class PlaceholderBinder:
    """Owns the muted placeholder text shown in empty entries.

    The hint is removed the instant an entry gains focus (only when it is
    still the displayed content) and restored when focus leaves an empty
    entry. A displayed placeholder is treated as empty by the submit
    handlers, so it can never be created as a list/item.
    """

    def __init__(self, app) -> None:
        # The app is duck-typed: only ``app.root`` (focus query) and
        # ``app._palette`` (theme colors) are ever used.
        self.app = app
        # entry widget -> its placeholder text (empty fields show this muted
        # hint; a displayed placeholder counts as "empty" for submission).
        self.map: dict = {}

    def attach(self, entry, text: str) -> None:
        """Show ``text`` as a muted placeholder on ``entry``.

        The hint is removed the instant the entry gains focus (only when it
        is still the displayed content) and restored when focus leaves an
        empty entry. A displayed placeholder is treated as empty by the
        submit handlers, so it can never be created as a list/item.
        """
        self.map[entry] = text
        entry.insert(0, text)
        entry.configure(foreground=self.fg())
        entry.bind("<FocusIn>", lambda _e, e=entry: self.focus_in(e))
        entry.bind("<FocusOut>", lambda _e, e=entry: self.focus_out(e))

    def fg(self) -> str:
        """Muted gray for placeholder text in the current (fallback) theme."""
        return (self.app._palette or {}).get("placeholder_fg", "#808080")

    def value(self, entry) -> str:
        """Strip the entry's text; a displayed placeholder counts as empty."""
        if entry.get() == self.map.get(entry, ""):
            return ""
        return entry.get().strip()

    def focus_in(self, entry) -> None:
        if entry.get() == self.map.get(entry, ""):
            entry.delete(0, "end")
            entry.configure(foreground=(self.app._palette or {}).get("fg", "#000000"))

    def focus_out(self, entry) -> None:
        if entry.get().strip() == "":
            self.restore(entry)

    def restore(self, entry) -> None:
        """Re-show the placeholder on an empty entry that no longer has focus.

        While the entry still holds the focus (e.g. right after a submit
        that cleared it), writing the hint would leave stale placeholder
        text in a focused field, since no FocusIn will re-fire to clear it.
        """
        if self.app.root.focus_get() is entry:
            return
        entry.delete(0, "end")
        entry.insert(0, self.map[entry])
        entry.configure(foreground=self.fg())
