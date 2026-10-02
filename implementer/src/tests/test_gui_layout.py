"""Real-display geometry and item label layout regressions."""

from unittest.mock import patch

import pytest

from tests.conftest import managed_tk_roots
from todo_md.app import TodoApp, TodoController
from todo_md.settings import Settings, save_settings
from todo_md.storage import MarkdownListStore


LONG_TEXT = (
    "This is an intentionally very long todo item text that is over one hundred "
    "and twenty characters long so we can verify it stays fully visible on a "
    "single line in the tkinter row widget"
)


@pytest.fixture
def make_app(tmp_path):
    callback_errors = []

    def build(theme="light", item_text="task", *, mapped=True):
        def create_app_root():
            root = create_root()
            if not mapped:
                # TodoApp updates idle tasks during construction, so withdraw now.
                root.withdraw()
            return root

        config_dir = str(tmp_path / "config")
        save_settings(config_dir, Settings(theme=theme))
        controller = TodoController(MarkdownListStore(tmp_path / "lists"))
        controller.create_list("work")
        controller.add_item("work", item_text)
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


def _assert_fully_visible(widget, root):
    assert widget.winfo_ismapped(), f"{widget} is not mapped"
    width, height = widget.winfo_width(), widget.winfo_height()
    assert width >= widget.winfo_reqwidth(), f"{widget} width is clipped"
    assert height >= widget.winfo_reqheight(), f"{widget} height is clipped"
    x, y = widget.winfo_rootx(), widget.winfo_rooty()
    ancestor = widget.master
    while ancestor is not None:
        assert ancestor.winfo_ismapped(), f"{ancestor} is not mapped"
        ax, ay = ancestor.winfo_rootx(), ancestor.winfo_rooty()
        assert ax <= x and x + width <= ax + ancestor.winfo_width(), (
            f"{widget} extends outside {ancestor} horizontally"
        )
        assert ay <= y and y + height <= ay + ancestor.winfo_height(), (
            f"{widget} extends outside {ancestor} vertically"
        )
        if ancestor is root:
            break
        ancestor = ancestor.master
    else:
        pytest.fail(f"{widget} is not inside the main window")


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("size", ["initial", "minimum"])
def test_main_window_controls_fit_and_settings_opens(make_app, theme, size):
    app = make_app(theme=theme)
    root = app.root
    assert app.theme == theme
    if size == "minimum":
        initial_width, initial_height = root.winfo_width(), root.winfo_height()
        root.geometry(f"{initial_width + 80}x{initial_height + 80}")
        root.update()
        assert root.winfo_width() > initial_width
        assert root.winfo_height() > initial_height
        width, height = root.minsize()
        root.geometry(f"{width}x{height}")
        root.update()
        assert (root.winfo_width(), root.winfo_height()) == (width, height)
        # A smaller resize request must not bypass the supported minimum.
        root.geometry(f"{max(1, width - 40)}x{max(1, height - 40)}")
        root.update()
        assert (root.winfo_width(), root.winfo_height()) == (width, height)

    sidebar = app.listbox.master
    right = app.items_frame.master
    assert sidebar.pack_info()["side"] == "left"
    assert right.pack_info()["side"] == "right"
    assert sidebar.winfo_rootx() + sidebar.winfo_width() <= right.winfo_rootx()
    buttons = []
    for child in sidebar.winfo_children():
        for widget in (child, *child.winfo_children()):
            _assert_fully_visible(widget, root)
            if widget.winfo_class() == "TButton":
                buttons.append(widget.cget("text"))
    assert buttons == ["Create", "Delete", app._theme_button_text(), "Settings"]
    for widget in (app.title_label, app.items_frame, app.version_label,
                   *app.new_item_entry.master.winfo_children()):
        _assert_fully_visible(widget, root)
    assert app.version_label.pack_info()["side"] == "bottom"
    assert len(app._item_rows) == 1
    for widget in app._item_rows[0][1:]:
        _assert_fully_visible(widget, root)
    assert app._item_rows[0][2].cget("text") == "task"

    assert app.settings_window is None
    app._settings_btn.invoke()
    root.update()
    assert app.settings_window is not None
    assert app.settings_window.winfo_ismapped()
    assert app.settings_window.master is root
    assert app.settings_window.title() == "Settings"


def test_item_label_layout(make_app):
    """Check full text and packing metadata without presenting a native window."""
    assert len(LONG_TEXT) >= 120, "test text must be 120+ chars"

    app = make_app(item_text=LONG_TEXT, mapped=False)
    assert app._item_rows, "expected at least one item row"
    _var, checkbutton, label, _del, _edit = app._item_rows[0]

    # Label anchored left
    assert label.cget("anchor") == "w"

    # Label stretches across the row
    info = label.pack_info()
    assert "x" in info.get("fill", "")
    assert info.get("expand") == 1

    # No truncation in the label's text: retain the complete 120+ char value.
    assert label.cget("text") == LONG_TEXT

    # Checkbutton packed left with modest padding
    cb_info = checkbutton.pack_info()
    assert cb_info.get("side") == "left"
    assert cb_info.get("padx") != 0

    # Row frame packed with anchor w, fill x in items_frame
    row = label.master
    row_info = row.pack_info()
    assert row_info.get("anchor") == "w"
    assert "x" in row_info.get("fill", "")
