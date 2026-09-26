"""GUI tests: muted placeholder hints on the two ttk.Entry fields.

Covered:
- both entries show their placeholder on build (unfocused, empty);
- focusing an entry clears the placeholder;
- typed text survives focus-out (no placeholder residue);
- focus-out on an empty entry restores the placeholder;
- after a theme toggle the displayed placeholder uses the new theme's
  muted gray (winfo_rgb probe: differs from entry background and main text);
- Return in a placeholder-showing new-list entry is a no-op (no list created).
"""

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore

NAME_PLACEHOLDER = "Insert the name of a new list here"
ITEM_PLACEHOLDER = "Add a new todo item here"


def _build(tmp_path) -> TodoApp:
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    return TodoApp(controller, config_dir=str(tmp_path / "config"))


def test_placeholders_displayed_on_build(tmp_path):
    app = _build(tmp_path)
    try:
        app.root.update()
        assert app.new_name_entry.get() == NAME_PLACEHOLDER
        assert app.new_item_entry.get() == ITEM_PLACEHOLDER
    finally:
        app.root.destroy()


def test_focus_in_clears_placeholder(tmp_path):
    app = _build(tmp_path)
    try:
        app.root.update()
        app.new_name_entry.focus_set()
        app.root.update()
        assert app.new_name_entry.get() == ""
        app.new_item_entry.focus_set()
        app.root.update()
        assert app.new_item_entry.get() == ""
    finally:
        app.root.destroy()


def test_typed_text_survives_focus_out(tmp_path):
    app = _build(tmp_path)
    try:
        app.root.update()
        entry = app.new_item_entry
        entry.focus_set()
        app.root.update()
        entry.delete(0, "end")
        entry.insert(0, "buy milk")
        app.new_name_entry.focus_set()
        app.root.update()
        assert entry.get() == "buy milk"
    finally:
        app.root.destroy()


def test_focus_out_on_empty_entry_restores_placeholder(tmp_path):
    app = _build(tmp_path)
    try:
        app.root.update()
        entry = app.new_name_entry
        entry.focus_set()
        app.root.update()
        assert entry.get() == ""  # placeholder removed on focus
        app.new_item_entry.focus_set()
        app.root.update()
        assert entry.get() == NAME_PLACEHOLDER
    finally:
        app.root.destroy()


def test_placeholder_color_follows_theme_toggle(tmp_path):
    app = _build(tmp_path)
    try:
        app.root.update()
        for _ in range(2):  # visit both themes
            app.root.update()
            palette = app._palette
            assert palette is not None  # clam fallback path
            # The entry still shows its placeholder (unfocused, empty).
            entry = app.new_name_entry
            assert entry.get() == NAME_PLACEHOLDER
            shown = app.root.winfo_rgb(entry.cget("foreground"))
            expect = app.root.winfo_rgb(palette["placeholder_fg"])
            assert shown == expect
            # Muted gray: distinct from both the entry background and the
            # main text color of the current theme.
            assert shown != app.root.winfo_rgb(palette["entry_bg"])
            assert shown != app.root.winfo_rgb(palette["fg"])
            app._on_toggle_theme()
            app.root.update()
    finally:
        app.root.destroy()


def test_return_on_empty_new_list_entry_creates_nothing(tmp_path):
    app = _build(tmp_path)
    try:
        app.root.update()
        # Entry shows its placeholder and is unfocused: Return must no-op.
        assert app.new_name_entry.get() == NAME_PLACEHOLDER
        app.new_name_entry.event_generate("<Return>")
        app.root.update()
        assert app.controller.list_names() == []
        assert not list(tmp_path.glob("*.md"))
        # Placeholder must still be displayed (never consumed as content).
        assert app.new_name_entry.get() == NAME_PLACEHOLDER
    finally:
        app.root.destroy()