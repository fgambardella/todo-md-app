"""Tests for Markdown list storage and headless relocation."""

import builtins

import pytest

from todo_md import MarkdownListStore
from todo_md import storage
from todo_md.storage import relocate_lists


@pytest.fixture
def store(tmp_path):
    return MarkdownListStore(str(tmp_path / "data"))


def test_init_creates_dir(tmp_path):
    target = tmp_path / "nested" / "data"
    assert not target.exists()
    MarkdownListStore(str(target))
    assert target.is_dir()


def test_save_load_round_trip(store):
    items = [("buy milk", False), ("write tests", True), ("  spaced  text  ", False)]
    store.save("groceries", items)
    assert store.load("groceries") == items


def test_load_missing_file_returns_empty(store):
    assert store.load("nope") == []


def test_parse_hand_written_md(store, tmp_path):
    raw = (
        "# Shopping\n"
        "\n"
        "Some intro prose that is not a checkbox.\n"
        "- [ ] eggs\n"
        "\n"
        "* not a checkbox line\n"
        "  - [x] indented, so ignored\n"
        "- [X] uppercase done\n"
        "- [ ]\n"  # empty text still a valid checkbox line
        "1. numbered item ignored\n"
        "\n"
    )
    (tmp_path / "data" / "todo.md").write_text(raw, encoding="utf-8")
    assert store.load("todo") == [
        ("eggs", False),
        ("uppercase done", True),
        ("", False),
    ]


def test_create_and_delete(store):
    store.create("work")
    assert store.lists() == ["work"]
    assert store.load("work") == []

    store.delete("work")
    assert store.lists() == []


def test_create_existing_raises(store):
    store.create("dup")
    with pytest.raises(FileExistsError):
        store.create("dup")


def test_delete_missing_raises(store):
    with pytest.raises(FileNotFoundError):
        store.delete("ghost")


def test_lists_sorted(store):
    for n in ["zebra", "alpha", "Mango"]:
        store.create(n)
    assert store.lists() == sorted(["zebra", "alpha", "Mango"])


def test_name_sanitization(store, tmp_path):
    weird = "my list (v2)?"
    store.create(weird)
    data_dir = tmp_path / "data"
    files = [p.name for p in data_dir.iterdir()]
    # every char outside [A-Za-z0-9_-] must have become an underscore
    assert files == ["my_list__v2__.md"]
    assert store.lists() == ["my_list__v2__"]
    # original (unsanitized) name must map to the same file
    store.save(weird, [("a", True)])
    assert store.load(weird) == [("a", True)]
    assert files and store.lists() == ["my_list__v2__"]


def test_save_has_header_no_crlf_trailing_newline(store, tmp_path):
    store.save("note", [("one", False)])
    data = (tmp_path / "data" / "note.md").read_bytes()
    assert b"\r" not in data
    assert data.endswith(b"\n")
    assert not data.endswith(b"\n\n")
    assert data.decode("utf-8").splitlines()[0] == "# note"


def test_atomic_replace_no_partial_content(store, tmp_path):
    path = tmp_path / "data" / "big.md"
    store.save("big", [(f"item {i}", i % 2 == 0) for i in range(50)])
    before = path.read_bytes()

    # Overwrite with a much shorter payload: file must swap atomically,
    # never ending up with a partial/truncated mix of the two contents.
    store.save("big", [("only", True)])
    after = path.read_bytes()
    assert after == b"# big\n- [x] only\n"
    assert after != before

    # No leftover temp files in the data directory
    leftovers = [p for p in (tmp_path / "data").iterdir() if p.name.startswith(".tmp-")]
    assert leftovers == []

    # A failed write must leave the old content fully intact.
    class ExplodingWriter:
        def __init__(self, real):
            self._real = real

        def write(self, s):
            if "item 49" in s:
                raise IOError("simulated disk failure")
            self._real.write(s)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return self._real.__exit__(*exc)

    import os
    import todo_md.storage as mod

    original_fdopen = os.fdopen
    os.fdopen = lambda *a, **k: ExplodingWriter(original_fdopen(*a, **k))
    try:
        with pytest.raises(IOError):
            store.save("big", [(f"item {i}", False) for i in range(50)])
    finally:
        os.fdopen = original_fdopen

    assert path.read_bytes() == after  # untouched by the failed write
    leftovers = [p for p in (tmp_path / "data").iterdir() if p.name.startswith(".tmp-")]
    assert leftovers == []


@pytest.mark.parametrize("populated_target", [True, False])
def test_relocate_moves_exact_bytes_and_preserves_other_content(
    tmp_path, populated_target
):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    contents = {
        "my list (v2).md": b"# Manual title\r\n\r\n- [X] done\r\n\xff\x00",
        ".hidden.md": b"no trailing newline",
        "empty.md": b"",
    }
    for name, content in contents.items():
        (source / name).write_bytes(content)
    (source / "settings.json").write_bytes(b'{"untouched": true}\n')
    (source / "nested.md").mkdir()
    nested = source / "nested.md" / "child.md"
    nested.write_bytes(b"nested list")
    target_contents = {"notes.txt": b"keep target notes"}
    if populated_target:
        target_contents["existing.md"] = b"# Existing\r\n- [x] keep this list\r\n"
    for name, content in target_contents.items():
        (target / name).write_bytes(content)

    relocate_lists(source, target, move=True)

    for name, content in contents.items():
        assert (target / name).read_bytes() == content
        assert not (source / name).exists()
    assert {p.name for p in source.iterdir()} == {"settings.json", "nested.md"}
    assert (source / "settings.json").read_bytes() == b'{"untouched": true}\n'
    assert nested.read_bytes() == b"nested list"
    assert {p.name for p in target.iterdir()} == set(contents) | set(target_contents)
    for name, content in target_contents.items():
        assert (target / name).read_bytes() == content


def test_relocate_without_move_leaves_source_unchanged(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    contents = {"tasks.md": b"- [ ] task\r\n", "notes.txt": b"other\x00\xff"}
    for name, content in contents.items():
        (source / name).write_bytes(content)
    target = tmp_path / "parent" / "target"

    relocate_lists(str(source), str(target), move=False)

    assert target.is_dir()
    assert list(target.iterdir()) == []
    assert {p.name: p.read_bytes() for p in source.iterdir()} == contents


@pytest.mark.parametrize("existing_name", ["tasks.md", "different.md"])
def test_relocate_without_move_preserves_populated_target(tmp_path, existing_name):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    source_contents = {"first.md": b"first\r\n", "tasks.md": b"source\xff"}
    target_contents = {existing_name: b"existing\x00\r\n", "notes.txt": b"notes"}
    for name, content in source_contents.items():
        (source / name).write_bytes(content)
    for name, content in target_contents.items():
        (target / name).write_bytes(content)

    relocate_lists(source, target, move=False)

    assert {p.name: p.read_bytes() for p in source.iterdir()} == source_contents
    assert {p.name: p.read_bytes() for p in target.iterdir()} == target_contents


@pytest.mark.parametrize(
    "target_kind", ["file", "directory", "symlink", "dangling_symlink"]
)
def test_relocate_preflights_later_conflict_before_any_transfer(tmp_path, target_kind):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    source_contents = {"first.md": b"first\r\n", "tasks.md": b"source\xff"}
    for name, content in source_contents.items():
        (source / name).write_bytes(content)
    (target / "notes.txt").write_bytes(b"target notes")
    conflict = target / "tasks.md"
    existing = b"existing\x00\r\n"
    referent = tmp_path / "referent"
    if target_kind == "file":
        conflict.write_bytes(existing)
    elif target_kind == "directory":
        conflict.mkdir()
        (conflict / "child.md").write_bytes(existing)
    else:
        if target_kind == "symlink":
            referent.write_bytes(existing)
        conflict.symlink_to(referent)

    with pytest.raises(FileExistsError):
        relocate_lists(source, target, move=True)

    assert {p.name: p.read_bytes() for p in source.iterdir()} == source_contents
    assert {p.name for p in target.iterdir()} == {"tasks.md", "notes.txt"}
    assert (target / "notes.txt").read_bytes() == b"target notes"
    if target_kind == "file":
        assert conflict.read_bytes() == existing
    elif target_kind == "directory":
        assert {p.name: p.read_bytes() for p in conflict.iterdir()} == {"child.md": existing}
    else:
        assert conflict.is_symlink()
        assert conflict.readlink() == referent
        if target_kind == "symlink":
            assert referent.read_bytes() == existing
        else:
            assert not referent.exists()


@pytest.mark.parametrize("move", [True, False])
@pytest.mark.parametrize("source_exists", [True, False])
@pytest.mark.parametrize("populated_target", [True, False])
def test_relocate_empty_or_missing_source_preserves_target(
    tmp_path, move, source_exists, populated_target
):
    source = tmp_path / "source"
    if source_exists:
        source.mkdir()
    target = tmp_path / "one" / "two" / "target"
    target_contents = {"existing.md": b"existing list"} if populated_target else {}
    if populated_target:
        target.mkdir(parents=True)
        (target / "existing.md").write_bytes(target_contents["existing.md"])

    relocate_lists(source, target, move=move)

    assert target.is_dir()
    assert {p.name: p.read_bytes() for p in target.iterdir()} == target_contents
    assert source.exists() == source_exists
    if source_exists:
        assert list(source.iterdir()) == []


def test_relocate_copy_failure_preserves_content(tmp_path, monkeypatch):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "first.md").write_bytes(b"first list")
    (source / "second.md").write_bytes(b"second list\r\n\xff")
    original_copy = storage.shutil.copyfileobj

    def fail_second_copy(incoming, outgoing):
        if incoming.name.endswith("second.md"):
            outgoing.write(incoming.read(3))
            raise OSError("simulated copy failure")
        original_copy(incoming, outgoing)

    monkeypatch.setattr(storage.shutil, "copyfileobj", fail_second_copy)

    with pytest.raises(OSError, match="simulated copy failure"):
        relocate_lists(source, target, move=True)

    assert (target / "first.md").read_bytes() == b"first list"
    assert not (source / "first.md").exists()
    assert (source / "second.md").read_bytes() == b"second list\r\n\xff"
    assert not (target / "second.md").exists()


def test_relocate_source_deletion_failure_preserves_both_copies(tmp_path, monkeypatch):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    content = b"complete list\r\n\xff"
    (source / "tasks.md").write_bytes(content)
    original_unlink = storage.os.unlink

    def fail_source_unlink(path, *args, **kwargs):
        if path == str(source / "tasks.md"):
            raise PermissionError("simulated deletion failure")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(storage.os, "unlink", fail_source_unlink)

    with pytest.raises(PermissionError, match="simulated deletion failure"):
        relocate_lists(source, target, move=True)

    assert (source / "tasks.md").read_bytes() == content
    assert (target / "tasks.md").read_bytes() == content


def test_relocate_never_overwrites_target_created_after_validation(tmp_path, monkeypatch):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "tasks.md").write_bytes(b"source list")

    def create_collision(path, mode):
        if mode == "xb":
            (target / "tasks.md").write_bytes(b"concurrent list")
        return builtins.open(path, mode)

    monkeypatch.setattr(storage, "open", create_collision, raising=False)

    with pytest.raises(FileExistsError):
        relocate_lists(source, target, move=True)

    assert (source / "tasks.md").read_bytes() == b"source list"
    assert (target / "tasks.md").read_bytes() == b"concurrent list"
