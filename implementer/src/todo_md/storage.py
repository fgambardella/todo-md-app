"""Markdown-based TODO list storage (stdlib only)."""

from __future__ import annotations

import os
import re
import tempfile

__all__ = ["MarkdownListStore"]

_CHECKBOX_RE = re.compile(r"^- \[( |x|X)\](?: (.*))?$")
_BAD_NAME_RE = re.compile(r"[^A-Za-z0-9_-]")


class MarkdownListStore:
    """Stores TODO lists as Markdown checkbox files in a data directory."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _sanitize(name: str) -> str:
        return _BAD_NAME_RE.sub("_", name)

    def _path(self, name: str) -> str:
        return os.path.join(self.data_dir, self._sanitize(name) + ".md")

    # -- public API -------------------------------------------------------

    def lists(self) -> list[str]:
        """Return list names (without extension), sorted."""
        names = []
        for entry in os.listdir(self.data_dir):
            if entry.endswith(".md"):
                names.append(entry[: -len(".md")])
        return sorted(names)

    def load(self, name: str) -> list[tuple[str, bool]]:
        """Parse `<name>.md` into (text, done) tuples; [] if file missing."""
        path = self._path(name)
        if not os.path.isfile(path):
            return []
        items: list[tuple[str, bool]] = []
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\r\n")
                m = _CHECKBOX_RE.match(line)
                if m:
                    items.append((m.group(2) or "", m.group(1).lower() == "x"))
        return items

    def save(self, name: str, items: list[tuple[str, bool]]) -> None:
        """Write items atomically as a markdown file (temp + os.replace)."""
        path = self._path(name)
        lines = ["# " + name]
        for text, done in items:
            lines.append("- [x] " + text if done else "- [ ] " + text)
        content = "\n".join(lines) + "\n"

        dir_name = os.path.dirname(path)
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix=".tmp-", suffix=".md")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(content)
            os.replace(tmp_path, path)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def create(self, name: str) -> None:
        """Create an empty list; raises FileExistsError if it exists."""
        path = self._path(name)
        if os.path.exists(path):
            raise FileExistsError(f"list already exists: {name}")
        self.save(name, [])

    def delete(self, name: str) -> None:
        """Delete a list; raises FileNotFoundError if missing."""
        path = self._path(name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"no such list: {name}")
        os.remove(path)
