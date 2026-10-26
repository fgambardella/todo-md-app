"""GUI tests: the edit dialog opens at 50% of the main window, centered.

Covers (C4): with the main root at a known 800x600 geometry the edit
dialog opens at ~400x300 (50% of each axis, a few pixels of tolerance for
Tk content clamping) and its on-screen position centers it on the live
main window on BOTH axes (same center math as test_gui_centering); the
size is recomputed on every open; and the 200/150 floors apply when the
main window is smaller than 400x300.
"""

from unittest.mock import patch

import pytest

from tests.conftest import managed_tk_roots
from todo_md.app import TodoApp, TodoController
from todo_md.settings import Settings, save_settings
from todo_md.storage import MarkdownListStore

TOLERANCE_PX = 8
POS = (200, 100)


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


def _place_root(root, geom, x, y):
    root.geometry(geom)
    root.geometry(f"+{x}+{y}")
    root.update()
    assert root.winfo_ismapped()
    assert abs(root.winfo_rootx() - x) <= 40
    assert abs(root.winfo_rooty() - y) <= 40


def _assert_half_size(win, root, label):
    win.update_idletasks()
    rw, rh = root.winfo_width(), root.winfo_height()
    ww, wh = win.winfo_width(), win.winfo_height()
    assert abs(ww - rw // 2) <= TOLERANCE_PX, (
        f"{label} dialog width {ww} is not ~50% of main width {rw} (expect {rw // 2})"
    )
    assert abs(wh - rh // 2) <= TOLERANCE_PX, (
        f"{label} dialog height {wh} is not ~50% of main height {rh} (expect {rh // 2})"
    )


def _assert_centered(win, root, label):
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


def test_edit_dialog_opens_at_half_of_main_window(make_app):
    app = make_app()
    root = app.root
    assert app.current_list is not None

    _place_root(root, "800x600", *POS)
    app._open_edit_dialog(0)
    root.update()
    win = app._edit_window
    assert win is not None
    assert win.master is root
    try:
        assert win.winfo_ismapped()
        # For an 800x600 main window: ~400x300.
        assert win.winfo_width() == pytest.approx(400, abs=TOLERANCE_PX)
        assert win.winfo_height() == pytest.approx(300, abs=TOLERANCE_PX)
        _assert_half_size(win, root, "edit")
        _assert_centered(win, root, "edit")
    finally:
        app._close_edit_dialog()


def test_edit_dialog_size_recomputed_on_every_open(make_app):
    app = make_app()
    root = app.root
    assert app.current_list is not None

    # First open at 800x600 -> ~400x300.
    _place_root(root, "800x600", *POS)
    app._open_edit_dialog(0)
    root.update()
    win = app._edit_window
    try:
        assert win.winfo_width() == pytest.approx(400, abs=TOLERANCE_PX)
        assert win.winfo_height() == pytest.approx(300, abs=TOLERANCE_PX)
    finally:
        app._close_edit_dialog()

    # Resize the main window, reopen: the dialog is rebuilt, so it
    # resizes to ~50% of the new size and re-centers on both axes.
    _place_root(root, "1200x700", *POS)
    app._open_edit_dialog(0)
    root.update()
    win = app._edit_window
    try:
        assert win.winfo_width() == pytest.approx(600, abs=TOLERANCE_PX)
        assert win.winfo_height() == pytest.approx(350, abs=TOLERANCE_PX)
        _assert_half_size(win, root, "edit (reopened)")
        _assert_centered(win, root, "edit (reopened)")
    finally:
        app._close_edit_dialog()


def test_edit_dialog_size_floors_on_tiny_main_window(make_app):
    app = make_app()
    root = app.root
    assert app.current_list is not None

    # Main window well below 400x300: the 200/150 floors must apply
    # (Tk may clamp upward to the content minimum; never smaller).
    _place_root(root, "300x200", *POS)
    app._open_edit_dialog(0)
    root.update()
    win = app._edit_window
    try:
        assert win.winfo_ismapped()
        assert win.winfo_width() >= 200
        assert win.winfo_height() >= 150
        # Centering is position-based (live dialog size), so it still
        # holds even when the floor/content clamping exceeds 50%.
        _assert_centered(win, root, "edit (floored)")
    finally:
        app._close_edit_dialog()
