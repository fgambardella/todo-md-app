"""GUI test: toggling an item updates the row UI (check state, gray, strikethrough)."""

from contextlib import ExitStack
import tkinter.font as tkfont
import tkinter.ttk  # noqa: F401  (ensure ttk available)
from unittest.mock import patch

import pytest

from tests.conftest import managed_tk_roots
from todo_md.app import TodoApp, TodoController
from todo_md.settings import Settings, save_settings
from todo_md.storage import MarkdownListStore


@pytest.fixture
def make_app(tmp_path):
    apps = []

    def build(items=None, completed_visible=2):
        store = MarkdownListStore(tmp_path / "data")
        if items is not None:
            store.save("work", items)
        config_dir = tmp_path / "config"
        if not (config_dir / "settings.json").exists():
            save_settings(config_dir, Settings(theme="light", completed_visible=completed_visible))
        # A restart must drain/destroy the old root before Tk picks a new default.
        roots.close()
        create_root = roots.enter_context(managed_tk_roots())
        with patch("tkinter.Tk", create_root):
            app = TodoApp(TodoController(store), config_dir=str(config_dir))
        app.callback_errors = []
        app.root.report_callback_exception = (
            lambda exc, val, tb: app.callback_errors.append(val)
        )
        apps.append(app)
        app.root.update()
        return app

    with ExitStack() as roots:
        yield build
    errors = [error for app in apps for error in app.callback_errors]
    assert errors == [], f"uncaught Tk callback errors: {errors!r}"


def _rows(app):
    return [(label.cget("text"), bool(var.get())) for var, _, label, _del, _edit in app._item_rows]


def _stored(rows, description=""):
    """Lift displayed ``(text, done)`` rows to the stored 3-tuple contract."""
    return [(text, done, description) for text, done in rows]


def _parse_rgb(value: str) -> tuple:
    """Parse a tkinter color string into an (r, g, b) int tuple."""
    value = value.strip().lstrip("#")
    assert len(value) == 6, f"expected hex color, got {value!r}"
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _overstrike(label) -> bool:
    font = tkfont.Font(font=label.cget("font"))
    return bool(font.actual("overstrike"))


def test_toggle_updates_gui(make_app):
    app = make_app([("first item", False, ""), ("second item", False, "")])
    assert len(app._item_rows) == 2
    var, cb, label, _del, _edit = app._item_rows[0]

    # Initially undone
    assert var.get() == 0
    assert not _overstrike(label)

    cb.invoke()
    app.root.update()

    var, cb, label, _del, _edit = app._item_rows[0]
    assert var.get() == 1
    r, g, b = _parse_rgb(label.cget("foreground"))
    assert max(r, g, b) - min(r, g, b) <= 10, "foreground should be gray"
    assert _overstrike(label)
    assert label.cget("text") == "first item"

    # Second row untouched
    var2, _cb2, label2, _del2, _edit2 = app._item_rows[1]
    assert var2.get() == 0
    assert not _overstrike(label2)

    cb.invoke()
    app.root.update()
    var, _cb, label, _del, _edit = app._item_rows[0]
    assert var.get() == 0
    assert not _overstrike(label)


@pytest.mark.parametrize(
    "limit,expected",
    [(0, [("first", False), ("second", False)]),
     (1, [("latest", True), ("first", False), ("second", False)]),
     (2, [("middle", True), ("latest", True), ("first", False), ("second", False)]),
     (10, [("oldest", True), ("middle", True), ("latest", True),
           ("first", False), ("second", False)])],
)
def test_legacy_rows_group_without_writes_on_load(make_app, tmp_path, limit, expected):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    path = data_dir / "work.md"
    original = (
        b"# work\n\n- [ ] first\n- [x] oldest\n- [ ] second\n"
        b"- [x] middle\n- [X] latest\nretained formatting\n"
    )
    path.write_bytes(original)
    with patch.object(MarkdownListStore, "save", side_effect=AssertionError("display wrote data")):
        app = make_app(completed_visible=limit)
        assert _rows(app) == expected
        app._refresh_items()
        app.root.update()
        assert _rows(app) == expected
        reloaded = make_app()
        assert _rows(reloaded) == expected
    assert path.read_bytes() == original


def test_completion_order_eviction_undo_recompletion_and_reload(make_app, tmp_path):
    app = make_app([(text, False, "") for text in ("first", "second", "third", "fourth", "fifth")])

    # Complete out of source order; each callback must use its stored index.
    app._item_rows[2][1].invoke()
    app.root.update()
    assert _rows(app) == [
        ("third", True), ("first", False), ("second", False), ("fourth", False), ("fifth", False)
    ]
    app._item_rows[1][1].invoke()
    app.root.update()
    assert _rows(app) == [
        ("third", True), ("first", True), ("second", False), ("fourth", False), ("fifth", False)
    ]
    app._item_rows[3][1].invoke()
    app.root.update()
    assert _rows(app) == [("first", True), ("fourth", True), ("second", False), ("fifth", False)]
    assert app.controller.store.load("work") == [
        ("third", True, ""), ("first", True, ""), ("fourth", True, ""),
        ("second", False, ""), ("fifth", False, ""),
    ]

    # Undo restores the previously hidden completion and leads the incomplete group.
    app._item_rows[0][1].invoke()
    app.root.update()
    assert _rows(app) == [
        ("third", True), ("fourth", True), ("first", False), ("second", False), ("fifth", False)
    ]
    assert app.controller.store.load("work") == _stored(_rows(app))

    # Re-completion makes first newest, evicting third, never an incomplete row.
    app._item_rows[2][1].invoke()
    app.root.update()
    expected = [("fourth", True), ("first", True), ("second", False), ("fifth", False)]
    assert _rows(app) == expected
    persisted = _stored([("third", True)] + expected)
    assert app.controller.store.load("work") == persisted
    before = (tmp_path / "data" / "work.md").read_bytes()
    reloaded = make_app()
    assert reloaded.settings.completed_visible == 2
    assert _rows(reloaded) == expected
    assert reloaded.controller.store.load("work") == persisted
    assert (tmp_path / "data" / "work.md").read_bytes() == before


@pytest.mark.parametrize("action", ["toggle", "delete"])
@pytest.mark.parametrize("display_index,stored_index", [(0, 3), (1, 1), (3, 4)])
def test_callbacks_use_identity_for_reordered_equal_duplicates(
    make_app, monkeypatch, action, display_index, stored_index
):
    # Equal dataclass values must not alias a hidden completion or an earlier todo.
    monkeypatch.setattr("todo_md.models.time.time", lambda: 1)
    items = [("same", True, ""), ("same", False, ""), ("between", False, ""),
             ("same", True, ""), ("same", False, ""), ("tail", False, "")]
    app = make_app(items, completed_visible=1)
    loaded = app.controller.open_list("work").items
    assert loaded[0] == loaded[3] and loaded[0] is not loaded[3]
    assert loaded[1] == loaded[4] and loaded[1] is not loaded[4]
    assert _rows(app) == [items[i][:2] for i in (3, 1, 2, 4, 5)]
    expected = list(items)
    text, done, description = expected.pop(stored_index)

    if action == "toggle":
        with patch.object(app.controller, "toggle_item", wraps=app.controller.toggle_item) as toggle:
            app._item_rows[display_index][1].invoke()
            app.root.update()
        toggle.assert_called_once_with("work", stored_index)
        expected = ([item for item in expected if item[1]] + [(text, not done, description)]
                    + [item for item in expected if not item[1]])
    else:
        with patch("tkinter.messagebox.askyesno", return_value=True) as ask:
            with patch.object(app.controller, "remove_item", wraps=app.controller.remove_item) as remove:
                app._item_rows[display_index][3].event_generate("<Button-1>")
                app.root.update()
        ask.assert_called_once_with("Confirm deletion", 'Delete item "same"?')
        remove.assert_called_once_with("work", stored_index)

    assert app.controller.store.load("work") == expected
    assert _rows(app) == ([item[:2] for item in expected if item[1]][-1:]
                          + [item[:2] for item in expected if not item[1]])
