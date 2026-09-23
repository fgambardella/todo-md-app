"""Tests for todo_md.models."""

import time

import pytest

from todo_md.models import TodoItem, TodoList


def test_add_item_happy_path():
    tl = TodoList(name="test")
    item = tl.add_item("buy milk")
    assert isinstance(item, TodoItem)
    assert item.text == "buy milk"
    assert item.done is False
    assert tl.items == [item]


def test_add_item_strips_whitespace():
    tl = TodoList(name="test")
    item = tl.add_item("  spaced text  ")
    assert item.text == "spaced text"


def test_add_item_empty_raises_value_error():
    tl = TodoList(name="test")
    with pytest.raises(ValueError):
        tl.add_item("")
    with pytest.raises(ValueError):
        tl.add_item("   ")


def test_toggle_happy_path():
    tl = TodoList(name="test")
    item = tl.add_item("task")
    toggled = tl.toggle(0)
    assert toggled is item
    assert toggled.done is True
    toggled = tl.toggle(0)
    assert toggled.done is False


def test_toggle_out_of_range_raises_index_error():
    tl = TodoList(name="test")
    tl.add_item("task")
    with pytest.raises(IndexError):
        tl.toggle(1)
    with pytest.raises(IndexError):
        tl.toggle(-2)


def test_remove_happy_path():
    tl = TodoList(name="test")
    tl.add_item("one")
    item = tl.add_item("two")
    tl.add_item("three")
    removed = tl.remove(1)
    assert removed is item
    assert [i.text for i in tl.items] == ["one", "three"]


def test_remove_out_of_range_raises_index_error():
    tl = TodoList(name="test")
    tl.add_item("one")
    with pytest.raises(IndexError):
        tl.remove(5)


def test_item_ordering_preserved():
    tl = TodoList(name="test")
    tl.add_item("first")
    tl.add_item("second")
    tl.add_item("third")
    assert [i.text for i in tl.items] == ["first", "second", "third"]
    tl.toggle(1)
    assert [i.text for i in tl.items] == ["first", "second", "third"]
    tl.remove(0)
    assert [i.text for i in tl.items] == ["second", "third"]


def test_rename():
    tl = TodoList(name="old")
    tl.add_item("task")
    tl.rename("new")
    assert tl.name == "new"


def test_created_defaults_to_recent_timestamp():
    before = time.time()
    item = TodoItem(text="x")
    after = time.time()
    assert before <= item.created <= after
    assert abs(item.created - time.time()) < 10


def test_explicit_created_is_kept():
    item = TodoItem(text="x", created=1234.5)
    assert item.created == 1234.5
