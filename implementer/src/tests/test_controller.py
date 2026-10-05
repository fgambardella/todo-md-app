"""Tests for TodoController (todo_md/app.py)."""

from unittest.mock import Mock

import pytest

from todo_md import app as app_module
from todo_md.app import TodoController
from todo_md.models import TodoItem, TodoList
from todo_md.storage import MarkdownListStore


@pytest.fixture
def controller(tmp_path):
    store = MarkdownListStore(tmp_path / "data")
    return TodoController(store)


def _file(tmp_path, name):
    return tmp_path / "data" / f"{name}.md"


def test_create_then_add_item_persists_markdown(controller, tmp_path):
    controller.create_list("work")
    controller.add_item("work", "write tests")
    content = _file(tmp_path, "work").read_text(encoding="utf-8")
    assert "- [ ] write tests" in content


def test_toggle_item_flips_checkbox_on_disk(controller, tmp_path):
    controller.create_list("work")
    controller.add_item("work", "task one")

    controller.toggle_item("work", 0)
    content = _file(tmp_path, "work").read_text(encoding="utf-8")
    assert "- [x] task one" in content
    assert "- [ ] task one" not in content

    controller.toggle_item("work", 0)
    content = _file(tmp_path, "work").read_text(encoding="utf-8")
    assert "- [ ] task one" in content
    assert "- [x] task one" not in content


def test_toggle_completion_order_persists_through_undo_recompletion_and_reload(
    controller, tmp_path
):
    controller.create_list("work")
    for text in ("first", "second", "third", "fourth"):
        controller.add_item("work", text)

    third = controller.toggle_item("work", 2)
    assert (third.text, third.done) == ("third", True)
    first = controller.toggle_item("work", 1)
    assert (first.text, first.done) == ("first", True)
    fourth = controller.toggle_item("work", 3)
    assert (fourth.text, fourth.done) == ("fourth", True)
    path = _file(tmp_path, "work")
    assert path.read_text(encoding="utf-8") == (
        "# work\n- [x] third\n- [x] first\n- [x] fourth\n- [ ] second\n"
    )

    reloaded = TodoController(MarkdownListStore(path.parent))
    assert [(item.text, item.done) for item in reloaded.open_list("work").items] == [
        ("third", True), ("first", True), ("fourth", True), ("second", False)
    ]
    undone = reloaded.toggle_item("work", 0)
    assert (undone.text, undone.done) == ("third", False)
    assert path.read_text(encoding="utf-8") == (
        "# work\n- [x] first\n- [x] fourth\n- [ ] third\n- [ ] second\n"
    )

    reloaded = TodoController(MarkdownListStore(path.parent))
    recompleted = reloaded.toggle_item("work", 2)
    assert (recompleted.text, recompleted.done) == ("third", True)
    assert path.read_text(encoding="utf-8") == (
        "# work\n- [x] first\n- [x] fourth\n- [x] third\n- [ ] second\n"
    )
    reloaded = TodoController(MarkdownListStore(path.parent))
    assert [(item.text, item.done) for item in reloaded.open_list("work").items] == [
        ("first", True), ("fourth", True), ("third", True), ("second", False)
    ]
    assert list(path.parent.iterdir()) == [path]


def test_toggle_groups_legacy_items_without_load_time_writes(
    controller, tmp_path, monkeypatch
):
    path = _file(tmp_path, "work")
    original = (
        "# work\n- [ ] pending first\n- [x] oldest\n- [ ] selected\n"
        "- [x] newer\n- [ ] pending second\n"
    )
    path.write_text(original, encoding="utf-8")
    save = Mock(wraps=controller.store.save)
    monkeypatch.setattr(controller.store, "save", save)

    loaded = controller.open_list("work")

    save.assert_not_called()
    assert [item.text for item in loaded.items] == [
        "pending first", "oldest", "selected", "newer", "pending second"
    ]
    assert path.read_text(encoding="utf-8") == original

    selected = controller.toggle_item("work", 2)

    assert (selected.text, selected.done) == ("selected", True)
    save.assert_called_once_with("work", [
        ("oldest", True, ""), ("newer", True, ""), ("selected", True, ""),
        ("pending first", False, ""), ("pending second", False, ""),
    ])
    assert path.read_text(encoding="utf-8") == (
        "# work\n- [x] oldest\n- [x] newer\n- [x] selected\n"
        "- [ ] pending first\n- [ ] pending second\n"
    )


@pytest.mark.parametrize("done", [False, True])
@pytest.mark.parametrize("index", [2, -1])
def test_toggle_returns_exact_duplicate_object_after_reordering(
    controller, monkeypatch, done, index
):
    first = TodoItem("same", done=done, created=1234.5)
    selected = TodoItem("same", done=done, created=1234.5)
    pending = TodoItem("pending")
    todo_list = TodoList("work", [first, pending, selected])
    assert first == selected and first is not selected
    monkeypatch.setattr(controller, "open_list", lambda name: todo_list)

    assert controller.toggle_item("work", index) is selected

    expected = [first, selected, pending] if done else [selected, first, pending]
    assert [id(item) for item in todo_list.items] == [id(item) for item in expected]
    assert first.done is done
    assert selected.done is not done
    reloaded = TodoController(MarkdownListStore(controller.store.data_dir))
    assert [(item.text, item.done) for item in reloaded.open_list("work").items] == [
        (item.text, item.done) for item in expected
    ]


@pytest.mark.parametrize("index", [2, -3, 1.5, "1", None])
def test_toggle_invalid_index_does_not_save(controller, tmp_path, monkeypatch, index):
    controller.store.save("work", [("pending", False, ""), ("completed", True, "")])
    path = _file(tmp_path, "work")
    original = path.read_bytes()
    save = Mock(wraps=controller.store.save)
    monkeypatch.setattr(controller.store, "save", save)
    error = IndexError if isinstance(index, int) else TypeError

    with pytest.raises(error):
        controller.toggle_item("work", index)

    save.assert_not_called()
    assert path.read_bytes() == original


def test_remove_item_deletes_line_from_disk(controller, tmp_path):
    controller.create_list("work")
    controller.add_item("work", "keep me")
    controller.add_item("work", "remove me")

    controller.remove_item("work", 1)
    content = _file(tmp_path, "work").read_text(encoding="utf-8")
    assert "remove me" not in content
    assert "- [ ] keep me" in content


def test_edit_item_persists_new_text_and_is_reloaded(controller, tmp_path):
    controller.create_list("work")
    controller.add_item("work", "task one")
    controller.add_item("work", "task two")

    edited = controller.edit_item("work", 0, "  renamed task  ")

    assert (edited.text, edited.done) == ("renamed task", False)
    content = _file(tmp_path, "work").read_text(encoding="utf-8")
    assert "- [ ] renamed task" in content
    assert "task one" not in content
    assert "- [ ] task two" in content
    # The controller re-reads the persisted list (same reload pattern as other mutations).
    reloaded = TodoController(MarkdownListStore(controller.store.data_dir))
    assert [item.text for item in reloaded.open_list("work").items] == [
        "renamed task",
        "task two",
    ]


@pytest.mark.parametrize("new_text", ["", "   "])
def test_edit_item_empty_text_persists_nothing(controller, tmp_path, monkeypatch, new_text):
    controller.create_list("work")
    controller.add_item("work", "task one")
    path = _file(tmp_path, "work")
    original = path.read_bytes()
    save = Mock(wraps=controller.store.save)
    monkeypatch.setattr(controller.store, "save", save)

    with pytest.raises(ValueError):
        controller.edit_item("work", 0, new_text)

    save.assert_not_called()
    assert path.read_bytes() == original
    assert [item.text for item in controller.open_list("work").items] == ["task one"]


@pytest.mark.parametrize("new_text", ["task one", "  task one  "])
def test_edit_item_unchanged_text_is_harmless_noop(controller, tmp_path, monkeypatch, new_text):
    controller.create_list("work")
    controller.add_item("work", "task one")
    path = _file(tmp_path, "work")
    original = path.read_bytes()
    save = Mock(wraps=controller.store.save)
    monkeypatch.setattr(controller.store, "save", save)

    edited = controller.edit_item("work", 0, new_text)

    assert (edited.text, edited.done) == ("task one", False)
    save.assert_not_called()
    assert path.read_bytes() == original


def test_open_list_restores_persisted_descriptions(controller, tmp_path):
    controller.create_list("work")
    path = _file(tmp_path, "work")
    path.write_text(
        "# work\n- [ ] task one\n  details here\n"
        "- [x] task two\n  first line\n  second line\n",
        encoding="utf-8",
    )

    loaded = controller.open_list("work")

    assert [(item.text, item.done, item.description) for item in loaded.items] == [
        ("task one", False, "details here"),
        ("task two", True, "first line\nsecond line"),
    ]


def test_add_toggle_remove_preserve_existing_descriptions(controller, tmp_path):
    path = _file(tmp_path, "work")
    path.write_text(
        "# work\n- [ ] task one\n  details one\n- [ ] task two\n  details two\n",
        encoding="utf-8",
    )

    controller.add_item("work", "task three")
    content = path.read_text(encoding="utf-8")
    assert "details one" in content
    assert "details two" in content

    controller.toggle_item("work", 1)
    content = path.read_text(encoding="utf-8")
    assert "- [x] task two" in content
    assert "details one" in content
    assert "details two" in content

    controller.remove_item("work", 1)
    content = path.read_text(encoding="utf-8")
    assert "task one" not in content
    assert "details one" not in content
    assert "task two" in content
    assert "details two" in content
    assert "task three" in content


def test_edit_item_with_description_persists(controller, tmp_path):
    controller.create_list("work")
    controller.add_item("work", "task one")

    edited = controller.edit_item("work", 0, "task one", "  some details  ")

    assert (edited.text, edited.description) == ("task one", "some details")
    content = _file(tmp_path, "work").read_text(encoding="utf-8")
    assert content == "# work\n- [ ] task one\n  some details\n"
    reloaded = controller.open_list("work")
    assert reloaded.items[0].description == "some details"


def test_edit_item_same_text_changed_description_persists(
    controller, tmp_path, monkeypatch
):
    controller.create_list("work")
    controller.add_item("work", "task one")
    controller.edit_item("work", 0, "task one", "first version")
    path = _file(tmp_path, "work")
    original = path.read_bytes()
    save = Mock(wraps=controller.store.save)
    monkeypatch.setattr(controller.store, "save", save)

    edited = controller.edit_item("work", 0, "task one", "second version")

    assert (edited.text, edited.description) == ("task one", "second version")
    save.assert_called_once_with("work", [("task one", False, "second version")])
    assert path.read_bytes() != original
    content = path.read_text(encoding="utf-8")
    assert "second version" in content
    assert "first version" not in content


@pytest.mark.parametrize("new_desc", ["details", "  details  "])
def test_edit_item_same_text_and_description_is_noop(
    controller, tmp_path, monkeypatch, new_desc
):
    controller.create_list("work")
    controller.add_item("work", "task one")
    controller.edit_item("work", 0, "task one", "details")
    path = _file(tmp_path, "work")
    original = path.read_bytes()
    save = Mock(wraps=controller.store.save)
    monkeypatch.setattr(controller.store, "save", save)

    edited = controller.edit_item("work", 0, "  task one  ", new_desc)

    assert (edited.text, edited.description) == ("task one", "details")
    save.assert_not_called()
    assert path.read_bytes() == original


def test_list_names_reflects_created_and_deleted_lists(controller):
    assert controller.list_names() == []

    controller.create_list("alpha")
    controller.create_list("beta")
    assert controller.list_names() == ["alpha", "beta"]

    controller.delete_list("alpha")
    assert controller.list_names() == ["beta"]


def test_duplicate_create_list_raises(controller):
    controller.create_list("work")
    with pytest.raises(FileExistsError):
        controller.create_list("work")


def test_empty_text_add_item_raises(controller):
    controller.create_list("work")
    with pytest.raises(ValueError):
        controller.add_item("work", "")
    with pytest.raises(ValueError):
        controller.add_item("work", "   ")


def test_data_dir_defaults_to_store_data_dir(tmp_path):
    store = MarkdownListStore(tmp_path / "data")
    controller = TodoController(store)
    assert controller.data_dir == store.data_dir


def test_data_dir_explicit_override_wins(tmp_path):
    store = MarkdownListStore(tmp_path / "data")
    override = str(tmp_path / "override")
    controller = TodoController(store, data_dir=override)
    assert controller.data_dir == override
    assert controller.data_dir != store.data_dir


@pytest.mark.parametrize("populated_target", [True, False])
def test_change_lists_dir_moves_contents_and_future_writes(
    controller, tmp_path, populated_target
):
    original_store = controller.store
    source = controller.store.data_dir
    target = tmp_path / "nested" / "lists"
    contents = {
        "work.md": b"# Custom heading\r\n- [ ] task one\r\n",
        "other.md": b"# Other\n\nhandwritten notes without a final newline",
    }
    for name, content in contents.items():
        (source / name).write_bytes(content)
    (source / "notes.txt").write_bytes(b"leave here")
    target_contents = {}
    if populated_target:
        target.mkdir(parents=True)
        target_contents = {"existing.md": b"# Existing\r\n- [x] target task\r\n"}
        for name, content in target_contents.items():
            (target / name).write_bytes(content)

    controller.change_lists_dir(target, move=True)

    assert controller.store is not original_store
    assert original_store.data_dir == source
    assert controller.data_dir == controller.store.data_dir == target
    assert controller.list_names() == sorted(
        name[:-3] for name in contents | target_contents
    )
    for name, content in contents.items():
        assert (target / name).read_bytes() == content
        assert not (source / name).exists()
    assert [(item.text, item.done) for item in controller.open_list("work").items] == [
        ("task one", False)
    ]

    controller.toggle_item("work", 0)
    controller.add_item("work", "task two")

    assert (target / "work.md").read_bytes() == b"# work\n- [x] task one\n- [ ] task two\n"
    assert (target / "other.md").read_bytes() == contents["other.md"]
    for name, content in target_contents.items():
        assert (target / name).read_bytes() == content
    assert {p.name: p.read_bytes() for p in source.iterdir()} == {"notes.txt": b"leave here"}


def test_change_lists_dir_without_move_uses_empty_destination(controller, tmp_path):
    source = controller.store.data_dir
    original_store = controller.store
    original = b"# work\r\n- [ ] old task\r\n"
    (source / "work.md").write_bytes(original)
    target = tmp_path / "nested" / "lists"

    controller.change_lists_dir(str(target), move=False)

    assert controller.data_dir == controller.store.data_dir == str(target)
    assert original_store.data_dir == source
    assert controller.list_names() == []
    controller.create_list("work")
    controller.add_item("work", "new task")

    assert (source / "work.md").read_bytes() == original
    assert (target / "work.md").read_bytes() == b"# work\n- [ ] new task\n"
    assert controller.list_names() == ["work"]


@pytest.mark.parametrize("existing_name", ["work.md", "existing.md"])
def test_change_lists_dir_without_move_uses_populated_target(
    controller, tmp_path, existing_name
):
    original_store = controller.store
    original_dir = controller.data_dir
    original = b"# work\r\n- [ ] source task\r\n"
    (original_dir / "work.md").write_bytes(original)
    target = tmp_path / "target"
    target.mkdir()
    existing = b"# Existing\r\n- [x] target task\r\n"
    (target / existing_name).write_bytes(existing)

    controller.change_lists_dir(target, move=False)

    assert controller.store is not original_store
    assert original_store.data_dir == original_dir
    assert controller.data_dir == controller.store.data_dir == target
    assert controller.list_names() == [existing_name[:-3]]
    items = controller.open_list(existing_name[:-3]).items
    assert [(item.text, item.done) for item in items] == [("target task", True)]
    assert {p.name: p.read_bytes() for p in original_dir.iterdir()} == {"work.md": original}
    assert {p.name: p.read_bytes() for p in target.iterdir()} == {existing_name: existing}


def test_change_lists_dir_transfer_conflict_keeps_bindings(controller, tmp_path):
    original_store = controller.store
    original_dir = controller.data_dir
    source_contents = {
        "first.md": b"# First\n- [ ] first task\n",
        "work.md": b"# work\r\n- [ ] source task\r\n",
    }
    for name, content in source_contents.items():
        (original_dir / name).write_bytes(content)
    target = tmp_path / "target"
    target.mkdir()
    existing = b"# Existing\r\n- [x] target task\r\n"
    (target / "work.md").write_bytes(existing)

    with pytest.raises(FileExistsError):
        controller.change_lists_dir(target, move=True)

    assert controller.store is original_store
    assert controller.data_dir == controller.store.data_dir == original_dir
    assert controller.list_names() == ["first", "work"]
    assert {p.name: p.read_bytes() for p in original_dir.iterdir()} == source_contents
    assert {p.name: p.read_bytes() for p in target.iterdir()} == {"work.md": existing}


@pytest.mark.parametrize("move", [True, False])
@pytest.mark.parametrize("invalid_kind", ["file", "file_parent", "empty"])
def test_change_lists_dir_invalid_path_keeps_bindings(
    controller, tmp_path, move, invalid_kind
):
    original_store = controller.store
    original_dir = controller.data_dir
    original = b"# work\n- [ ] task\n"
    (original_dir / "work.md").write_bytes(original)
    blocker = tmp_path / "not_a_directory"
    blocker.write_bytes(b"not a directory")
    targets = {"file": blocker, "file_parent": blocker / "lists", "empty": ""}

    with pytest.raises(OSError):
        controller.change_lists_dir(targets[invalid_kind], move=move)

    assert controller.store is original_store
    assert controller.data_dir == controller.store.data_dir == original_dir
    assert (original_dir / "work.md").read_bytes() == original
    assert blocker.read_bytes() == b"not a directory"


@pytest.mark.parametrize("move", [True, False])
def test_change_lists_dir_relocation_error_keeps_bindings(tmp_path, monkeypatch, move):
    store = MarkdownListStore(tmp_path / "source")
    override = str(tmp_path / "override")
    controller = TodoController(store, data_dir=override)
    controller.create_list("work")
    original = (store.data_dir / "work.md").read_bytes()
    target = tmp_path / "target"
    failure = OSError("injected relocation failure")

    def fail_relocation(old_dir, new_dir, should_move):
        assert old_dir == store.data_dir
        assert new_dir == target
        assert should_move is move
        raise failure

    monkeypatch.setattr(app_module, "relocate_lists", fail_relocation)

    with pytest.raises(OSError, match="injected relocation failure") as exc:
        controller.change_lists_dir(target, move=move)

    assert exc.value is failure
    assert controller.store is store
    assert controller.store.data_dir == tmp_path / "source"
    assert controller.data_dir == override
    assert (store.data_dir / "work.md").read_bytes() == original
    assert not target.exists()


@pytest.mark.parametrize("move", [True, False])
@pytest.mark.parametrize("path_kind", ["same", "normalized", "relative", "symlink"])
def test_change_lists_dir_equivalent_path_is_noop(tmp_path, monkeypatch, move, path_kind):
    source = tmp_path / "data"
    store = MarkdownListStore(source)
    override = str(tmp_path / "override")
    controller = TodoController(store, data_dir=override)
    original = b"# work\r\n- [ ] unchanged\r\n"
    (source / "work.md").write_bytes(original)
    if path_kind == "same":
        target = source
    elif path_kind == "normalized":
        target = str(source / ".." / "data") + "/."
    elif path_kind == "relative":
        monkeypatch.chdir(tmp_path)
        target = "data"
    else:
        target = tmp_path / "alias"
        target.symlink_to(source, target_is_directory=True)

    def unexpected_relocation(*args, **kwargs):
        pytest.fail("same-directory requests must not call relocation")

    monkeypatch.setattr(app_module, "relocate_lists", unexpected_relocation)

    controller.change_lists_dir(target, move=move)

    assert controller.store is store
    assert controller.store.data_dir == source
    assert controller.data_dir == override
    assert controller.list_names() == ["work"]
    assert (source / "work.md").read_bytes() == original


def test_change_lists_dir_uses_store_not_constructor_override(tmp_path):
    source = tmp_path / "source"
    store = MarkdownListStore(source)
    override = tmp_path / "override"
    override.mkdir()
    (override / "unrelated.md").write_bytes(b"not the active store")
    controller = TodoController(store, data_dir=str(override))
    original = b"# work\r\n- [ ] actual source\r\n"
    (source / "work.md").write_bytes(original)
    target = tmp_path / "target"

    controller.change_lists_dir(target, move=True)

    assert controller.data_dir == controller.store.data_dir == target
    assert controller.list_names() == ["work"]
    assert (target / "work.md").read_bytes() == original
    assert list(source.iterdir()) == []
    assert (override / "unrelated.md").read_bytes() == b"not the active store"
