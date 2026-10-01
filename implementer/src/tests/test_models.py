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


def test_toggle_tracks_completion_order_not_source_order():
    tl = TodoList(name="test")
    first, second, third, fourth = [
        tl.add_item(text) for text in ("first", "second", "third", "fourth")
    ]

    assert tl.toggle(2) is third
    assert tl.items == [third, first, second, fourth]
    assert tl.toggle(1) is first
    assert tl.items == [third, first, second, fourth]
    assert tl.toggle(3) is fourth
    assert tl.items == [third, first, fourth, second]
    assert tl.toggle(3) is second
    assert tl.items == [third, first, fourth, second]
    assert all(item.done for item in tl.items)


@pytest.mark.parametrize("done", [False, True])
def test_toggle_stably_groups_interleaved_legacy_items(done):
    pending_first = TodoItem("pending first")
    oldest = TodoItem("oldest", done=True)
    selected = TodoItem("selected", done=done)
    pending_second = TodoItem("pending second")
    newer = TodoItem("newer", done=True)
    tl = TodoList("test", [pending_first, oldest, selected, pending_second, newer])

    assert tl.toggle(2) is selected

    assert tl.items == [oldest, newer, selected, pending_first, pending_second]
    assert [item.done for item in tl.items] == [True, True, not done, False, False]


def test_undo_moves_to_front_of_incomplete_and_recompletion_is_newest():
    oldest = TodoItem("oldest", done=True)
    newer = TodoItem("newer", done=True)
    pending_first = TodoItem("pending first")
    pending_second = TodoItem("pending second")
    tl = TodoList("test", [oldest, newer, pending_first, pending_second])

    assert tl.toggle(0) is oldest
    assert tl.items == [newer, oldest, pending_first, pending_second]
    assert oldest.done is False
    assert tl.toggle(2) is pending_first
    assert tl.items == [newer, pending_first, oldest, pending_second]
    assert tl.toggle(2) is oldest
    assert tl.items == [newer, pending_first, oldest, pending_second]
    assert [item.done for item in tl.items] == [True, True, True, False]


@pytest.mark.parametrize("done", [False, True])
def test_toggle_moves_exact_duplicate_object(done):
    first = TodoItem("same", done=done, created=1234.5)
    selected = TodoItem("same", done=done, created=1234.5)
    pending = TodoItem("pending", created=9876.5)
    tl = TodoList("test", [first, pending, selected])
    assert first == selected and first is not selected

    assert tl.toggle(2) is selected

    expected = [first, selected, pending] if done else [selected, first, pending]
    assert [id(item) for item in tl.items] == [id(item) for item in expected]
    assert first.done is done
    assert selected.done is not done
    assert first.created == selected.created == 1234.5
    assert pending.created == 9876.5


def test_toggle_retains_python_negative_indexing():
    first = TodoItem("first")
    completed = TodoItem("completed", done=True)
    last = TodoItem("last")
    tl = TodoList("test", [first, completed, last])

    assert tl.toggle(-1) is last
    assert tl.items == [completed, last, first]
    assert last.done is True
    assert tl.toggle(-3) is completed
    assert tl.items == [last, completed, first]
    assert completed.done is False


@pytest.mark.parametrize("index", [3, -4, 10**100, -(10**100), 1.5, "1", None])
def test_toggle_invalid_index_does_not_mutate(index):
    items = [TodoItem("first"), TodoItem("done", done=True), TodoItem("last")]
    tl = TodoList("test", list(items))
    error = IndexError if isinstance(index, int) else TypeError

    with pytest.raises(error):
        tl.toggle(index)

    assert [id(item) for item in tl.items] == [id(item) for item in items]
    assert [item.done for item in tl.items] == [False, True, False]


@pytest.mark.parametrize("index", [0, -1])
def test_toggle_empty_list_raises_index_error(index):
    tl = TodoList("test")
    with pytest.raises(IndexError):
        tl.toggle(index)
    assert tl.items == []


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


def test_add_and_remove_preserve_item_order():
    tl = TodoList(name="test")
    tl.add_item("first")
    tl.add_item("second")
    tl.add_item("third")
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
