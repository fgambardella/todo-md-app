"""Tests for todo_md.storage.MarkdownListStore."""

import pytest

from todo_md import MarkdownListStore


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