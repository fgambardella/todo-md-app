"""Tests for TodoController (todo_md/app.py)."""

import pytest

from todo_md.app import TodoController
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


def test_remove_item_deletes_line_from_disk(controller, tmp_path):
    controller.create_list("work")
    controller.add_item("work", "keep me")
    controller.add_item("work", "remove me")

    controller.remove_item("work", 1)
    content = _file(tmp_path, "work").read_text(encoding="utf-8")
    assert "remove me" not in content
    assert "- [ ] keep me" in content


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
