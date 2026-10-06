"""Regression: modal dialogs open centered on the main window."""

from unittest.mock import patch

import pytest

from tests.conftest import managed_tk_roots
from todo_md.app import TodoApp, TodoController
from todo_md.settings import Settings, save_settings
from todo_md.storage import MarkdownListStore

TOLERANCE_PX = 8
FIRST_POS = (200, 100)
SECOND_POS = (480, 280)


@pytest.fixture
def make_app(tmp_path):
    callback_errors = []

    def build():
        def create_app_root():
            return create_root()

        config_dir = str(tmp_path / "config")
        save_settings(config_dir, Settings(theme="light"))
        controller = TodoController(MarkdownListStore(tmp_path / "lists"))
        controller.create_list("work")
        controller.add_item("work", "task")
        with patch("tkinter.Tk", create_app_root):
            app = TodoApp(controller, config_dir=config_dir)
        app.root.report_callback_exception = (
            lambda exc, val, tb: callback_errors.append(val)
        )
        app.root.update()
        return app

    with managed_tk_roots() as create_root:
        yield build

    assert callback_errors == [], f"uncaught Tk callback errors: {callback_errors!r}"


def _move_root(root, x, y):
    root.geometry(f"+{x}+{y}")
    root.update()
    assert root.winfo_ismapped()
    # The window manager may offset by the frame; be lenient, but the
    # requested position must be roughly honored on the real display.
    assert abs(root.winfo_rootx() - x) <= 40
    assert abs(root.winfo_rooty() - y) <= 40


def _assert_centered(win, root, label):
    assert win.winfo_ismapped(), f"{label} dialog is not mapped"
    win.update_idletasks()
    wx, wy = win.winfo_rootx(), win.winfo_rooty()
    ww, wh = win.winfo_width(), win.winfo_height()
    rx, ry = root.winfo_rootx(), root.winfo_rooty()
    rw, rh = root.winfo_width(), root.winfo_height()
    expected_x, expected_y = rx + rw // 2, ry + rh // 2
    got_x, got_y = wx + ww // 2, wy + wh // 2
    assert abs(got_x - expected_x) <= TOLERANCE_PX, (
        f"{label} dialog horizontal center {got_x} is not within "
        f"{TOLERANCE_PX}px of main window center {expected_x}"
    )
    assert abs(got_y - expected_y) <= TOLERANCE_PX, (
        f"{label} dialog vertical center {got_y} is not within "
        f"{TOLERANCE_PX}px of main window center {expected_y}"
    )


def test_settings_dialog_centered_on_main_window(make_app):
    app = make_app()
    root = app.root

    _move_root(root, *FIRST_POS)
    app._open_settings()
    root.update()
    win = app.settings_window
    assert win is not None
    assert win.master is root
    try:
        _assert_centered(win, root, "settings")
    finally:
        app._close_settings()

    # Recomputed on every open: move the main window, reopen, re-assert.
    first_center = (root.winfo_rootx(), root.winfo_rooty())
    _move_root(root, *SECOND_POS)
    moved = (root.winfo_rootx(), root.winfo_rooty())
    assert abs(moved[0] - first_center[0]) + abs(moved[1] - first_center[1]) > 100, (
        f"main window did not move: {first_center} -> {moved}"
    )
    app._open_settings()
    root.update()
    win = app.settings_window
    assert win is not None
    try:
        _assert_centered(win, root, "settings (after move)")
    finally:
        app._close_settings()


def test_edit_dialog_centered_on_main_window(make_app):
    app = make_app()
    root = app.root
    assert app.current_list is not None

    _move_root(root, *FIRST_POS)
    app._open_edit_dialog(0)
    root.update()
    win = app._edit_window
    assert win is not None
    assert win.master is root
    try:
        _assert_centered(win, root, "edit")
    finally:
        app._close_edit_dialog()

    first_center = (root.winfo_rootx(), root.winfo_rooty())
    _move_root(root, *SECOND_POS)
    moved = (root.winfo_rootx(), root.winfo_rooty())
    assert abs(moved[0] - first_center[0]) + abs(moved[1] - first_center[1]) > 100, (
        f"main window did not move: {first_center} -> {moved}"
    )
    app._open_edit_dialog(0)
    root.update()
    win = app._edit_window
    assert win is not None
    try:
        _assert_centered(win, root, "edit (after move)")
    finally:
        app._close_edit_dialog()