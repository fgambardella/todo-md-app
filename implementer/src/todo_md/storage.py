"""Markdown-based TODO list storage (stdlib only)."""

from __future__ import annotations

import os
import re
import shutil
import tempfile

__all__ = ["MarkdownListStore", "relocate_lists"]

_CHECKBOX_RE = re.compile(r"^- \[( |x|X)\](?: (.*))?$")
_HEADER_RE = re.compile(r"^#")
_CONTINUATION_INDENT = "  "
_BAD_NAME_RE = re.compile(r"[^A-Za-z0-9_-]")


def relocate_lists(old_dir, new_dir, move: bool) -> None:
    """Create new_dir and optionally move top-level .md files there verbatim.

    Without moves, existing files are untouched. Before moving, any same-name
    destination path (including a dangling symlink) raises FileExistsError.
    Moves never overwrite files, including ones created after validation. On I/O
    failure, already moved files stay in new_dir; the failing source remains
    intact, possibly with a complete copy if deleting the source failed.
    """
    os.makedirs(new_dir, exist_ok=True)
    if not move:
        return

    try:
        with os.scandir(old_dir) as entries:
            sources = sorted(
                entry.path
                for entry in entries
                if entry.name.endswith(".md") and entry.is_file()
            )
    except FileNotFoundError:
        return

    for source in sources:
        target = os.path.join(new_dir, os.path.basename(source))
        if os.path.lexists(target):
            raise FileExistsError(f"destination already exists: {target}")

    for source in sources:
        target = os.path.join(new_dir, os.path.basename(source))
        created = False
        try:
            with open(source, "rb") as incoming:
                with open(target, "xb") as outgoing:
                    created = True
                    shutil.copyfileobj(incoming, outgoing)
        except BaseException:
            if created:
                try:
                    os.unlink(target)
                except OSError:
                    pass
            raise
        # Close the complete copy before deleting the source, even across devices.
        os.unlink(source)


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

    def load(self, name: str) -> list[tuple[str, bool, str]]:
        """Parse `<name>.md` into (text, done, description) tuples; [] if missing.

        A checkbox line starts an item; following lines indented by two or
        more spaces (up to the next checkbox or header line, or any other
        non-indented line) form the item's description, de-indented, joined
        with newlines, and stripped. Continuation lines before the first
        checkbox are ignored.
        """
        path = self._path(name)
        if not os.path.isfile(path):
            return []
        items: list[tuple[str, bool, str]] = []
        current: tuple[str, bool, list[str]] | None = None
        collecting = False

        def close_current() -> None:
            nonlocal current, collecting
            if current is not None:
                text, done, desc_lines = current
                items.append((text, done, "\n".join(desc_lines).strip()))
            current = None
            collecting = False

        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\r\n")
                m = _CHECKBOX_RE.match(line)
                if m:
                    close_current()
                    current = (m.group(2) or "", m.group(1).lower() == "x", [])
                    collecting = True
                    continue
                if _HEADER_RE.match(line):
                    close_current()
                    continue
                if collecting and line.startswith(_CONTINUATION_INDENT):
                    current[2].append(line[len(_CONTINUATION_INDENT):])
                else:
                    collecting = False
        close_current()
        return items

    def save(self, name: str, items: list[tuple[str, bool, str]]) -> None:
        """Write items atomically as a markdown file (temp + os.replace).

        Each non-empty description line is written as two spaces + line
        directly under its checkbox line; an empty description adds no lines.
        """
        path = self._path(name)
        lines = ["# " + name]
        for text, done, description in items:
            lines.append("- [x] " + text if done else "- [ ] " + text)
            for desc_line in description.split("\n"):
                if desc_line:
                    lines.append(_CONTINUATION_INDENT + desc_line)
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
