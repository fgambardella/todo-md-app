"""Headless tests for the pure display filter ``visible_items``."""

import pytest

from todo_md.app import TodoController, visible_items
from todo_md.models import TodoItem
from todo_md.storage import MarkdownListStore


def _item(text: str, done: bool = False) -> TodoItem:
    return TodoItem(text=text, done=done)


# -- keep all when completed <= N -----------------------------------------


def test_keeps_all_when_completed_within_limit():
    items = [
        _item("a", done=True),
        _item("b"),
        _item("c", done=True),
        _item("d"),
    ]
    assert [i.text for i in visible_items(items, 2)] == ["a", "c", "b", "d"]


def test_keeps_all_when_completed_exactly_at_limit():
    items = [
        _item("a", done=True),
        _item("b", done=True),
        _item("c"),
    ]
    assert [i.text for i in visible_items(items, 2)] == ["a", "b", "c"]


# -- excess hidden from the TOP when completed > N -------------------------


def test_hides_excess_completed_from_top():
    items = [
        _item("c1", done=True),  # top-most completed -> hidden
        _item("todo1"),
        _item("c2", done=True),  # hidden
        _item("c3", done=True),  # bottom-most completed -> kept
        _item("todo2"),
    ]
    visible = visible_items(items, 1)
    assert [i.text for i in visible] == ["c3", "todo1", "todo2"]


def test_hides_multiple_excess_completed_from_top():
    items = [_item(f"c{n}", done=True) for n in range(5)] + [_item("todo")]
    visible = visible_items(items, 2)
    assert [i.text for i in visible] == ["c3", "c4", "todo"]


# -- 0 hides every completed item ------------------------------------------


def test_zero_hides_all_completed():
    items = [
        _item("a", done=True),
        _item("b"),
        _item("c", done=True),
    ]
    visible = visible_items(items, 0)
    assert [i.text for i in visible] == ["b"]
    assert all(not i.done for i in visible)


# -- incomplete items always stay ------------------------------------------


def test_incomplete_items_always_visible():
    items = [_item(f"c{n}", done=True) for n in range(5)]
    items += [_item(f"todo{n}") for n in range(3)]
    for limit in (0, 1, 2, 10):
        visible = visible_items(items, limit)
        for n in range(3):
            assert f"todo{n}" in [i.text for i in visible]


# -- relative order preserved within completed/incomplete groups ------------


@pytest.mark.parametrize(
    "limit,expected_indexes",
    [(0, [0, 2, 4]), (1, [5, 0, 2, 4]), (2, [3, 5, 0, 2, 4]),
     (10, [1, 3, 5, 0, 2, 4])],
)
def test_visible_groups_preserve_order_identity_and_input(limit, expected_indexes):
    items = [
        _item("t1"),
        _item("c1", done=True),
        _item("t2"),
        _item("c2", done=True),
        _item("t3"),
        _item("c3", done=True),
    ]
    original_ids = [id(item) for item in items]
    original_fields = [vars(item).copy() for item in items]
    visible = visible_items(items, limit)
    assert visible is not items
    assert [id(item) for item in visible] == [original_ids[i] for i in expected_indexes]
    assert [id(item) for item in items] == original_ids
    assert [vars(item) for item in items] == original_fields


def test_equal_duplicates_keep_distinct_identities():
    items = [TodoItem("same", done=done, created=1) for done in (True, False, True, False)]
    assert items[0] == items[2] and items[0] is not items[2]
    assert items[1] == items[3] and items[1] is not items[3]
    visible = visible_items(items, 1)
    assert [id(item) for item in visible] == [id(items[i]) for i in (2, 1, 3)]


@pytest.mark.parametrize("limit", [0, 1, 10])
def test_empty_list(limit):
    items = []
    visible = visible_items(items, limit)
    assert visible == []
    assert visible is not items


def test_returns_new_list_not_input():
    items = [_item("a"), _item("b", done=True)]
    visible = visible_items(items, 0)
    assert visible is not items
    assert [i.text for i in items] == ["a", "b"]  # input untouched


def test_negative_limit_rejected():
    with pytest.raises(ValueError):
        visible_items([], -1)


# -- storage untouched: the filter must never lose items on disk ------------


@pytest.mark.parametrize(
    "limit,expected",
    [(0, ["todo1"]), (1, ["c3", "todo1"]),
     (2, ["c2", "c3", "todo1"]), (10, ["c1", "c2", "c3", "todo1"])],
)
def test_storage_unaffected_by_filter(tmp_path, limit, expected):
    store = MarkdownListStore(tmp_path / "data")
    controller = TodoController(store)
    # A legacy file may interleave completed and incomplete rows.
    store.save("work", [("c1", True), ("todo1", False), ("c2", True), ("c3", True)])

    before = (tmp_path / "data" / "work.md").read_bytes()

    todo_list = controller.open_list("work")
    visible = visible_items(todo_list.items, limit)
    assert [i.text for i in visible] == expected

    after = (tmp_path / "data" / "work.md").read_bytes()
    assert before == after  # disk file byte-identical

    reloaded = controller.open_list("work")
    assert [i.text for i in reloaded.items] == ["c1", "todo1", "c2", "c3"]
    assert [i.done for i in reloaded.items] == [True, False, True, True]
