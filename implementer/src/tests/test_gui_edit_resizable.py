"""GUI tests: the edit dialog's description box has a working scrollbar.

Covers: the dialog opens with a vertical scrollbar paired to the
multi-line description ``tk.Text``; the two-way wiring
(``desc_text`` yscrollcommand drives the scrollbar thumb, the
scrollbar command drives the text view); content longer than the
viewport is reachable (multi-page text scrolls, ``yview()`` and the
scrollbar fraction respond); and the scrollbar renders in both light
and dark themes.
"""

import json

import tkinter as tk
from tkinter import ttk

from todo_md.app import TodoApp, TodoController
from todo_md.storage import MarkdownListStore


def _make_app(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    controller.create_list("Edits")
    controller.add_item("Edits", "Edit me")
    return TodoApp(controller, config_dir=str(tmp_path / "config"))


def _open_edit(app, row_index=0):
    app._item_rows[row_index][4].event_generate("<Button-1>")
    app.root.update()
    assert app._edit_window is not None, "edit dialog should be open"
    return app._edit


def _write_config(tmp_path, theme):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "settings.json").write_text(
        json.dumps({"theme": theme}), encoding="utf-8"
    )


def test_edit_dialog_opens_with_scrollbar(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        app._select_list_name("Edits")
        app.root.update()

        dialog = _open_edit(app)
        win = dialog.window
        assert win.winfo_exists()
        # The existing widget surface is intact.
        assert isinstance(dialog.entry, ttk.Entry)
        assert isinstance(dialog.desc_text, tk.Text)
        assert isinstance(dialog.save_btn, ttk.Button)
        assert isinstance(dialog.cancel_btn, ttk.Button)
        # A vertical scrollbar exists, is a ttk.Scrollbar, and sits
        # inside the description sub-frame at the right edge.
        sb = dialog.desc_scroll
        assert isinstance(sb, ttk.Scrollbar)
        assert sb.winfo_exists()
        app.root.update()
        assert sb.winfo_manager() == "pack"
        assert sb.winfo_height() > 0
        # Text keeps its horizontal expansion, scrollbar pins right.
        assert int(dialog.desc_text.cget("width")) == 40
        assert dialog.desc_text.winfo_x() < sb.winfo_x()
        assert sb.winfo_x() + sb.winfo_width() >= dialog.desc_text.winfo_x()
    finally:
        app._close_edit_dialog()
        app.root.destroy()


def test_scrollbar_wired_both_directions(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        app._select_list_name("Edits")
        app.root.update()

        dialog = _open_edit(app)
        desc, sb = dialog.desc_text, dialog.desc_scroll
        app.root.update()

        # Both sides are wired (registered commands, not defaults).
        assert desc.cget("yscrollcommand")
        assert sb.cget("command")

        # Seed enough text to exceed the 5-line viewport (~20 lines).
        lines = [f"Line {i}" for i in range(1, 21)]
        desc.delete("1.0", "end")
        desc.insert("1.0", "\n".join(lines))
        app.root.update()
        top = desc.yview()
        assert top[0] < top[1] < 1.0  # viewport is a proper window

        # Text -> scrollbar: scrolling the text moves the thumb.
        before = sb.get()
        desc.yview("moveto", 1.0)
        app.root.update()
        after = sb.get()
        assert after[1] > before[1]
        assert abs(after[1] - 1.0) < 0.05

        # Scrollbar -> text: driving the scrollbar moves the view.
        root = app.root
        root.tk.call(str(sb.cget("command")), "moveto", "0.0")
        app.root.update()
        back = desc.yview()
        assert abs(back[0] - 0.0) < 0.05
    finally:
        app._close_edit_dialog()
        app.root.destroy()


def test_content_longer_than_viewport_reachable(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        app._select_list_name("Edits")
        app.root.update()

        dialog = _open_edit(app)
        desc, sb = dialog.desc_text, dialog.desc_scroll
        app.root.update()

        pages = 6  # 6x5 lines = far beyond the 5-line viewport
        lines = [f"detail line {p}.{i}" for p in range(1, pages + 1) for i in range(5)]
        desc.delete("1.0", "end")
        desc.insert("1.0", "\n".join(lines))
        app.root.update()

        # Whole content is present; the tail is not visible at the top.
        assert desc.get("1.0", "end-1c").splitlines() == lines
        top = desc.yview()
        assert top[0] < top[1] < 1.0

        # Scroll to the bottom: yview() and the scrollbar fraction respond.
        desc.yview("moveto", 1.0)
        app.root.update()
        bottom = desc.yview()
        assert bottom[0] > top[0]
        assert abs(bottom[1] - 1.0) < 0.05
        sb_after = sb.get()
        assert sb_after[1] > top[1]  # thumb moved with the content

        # The previously unreachable tail is now the visible window.
        top_idx = desc.index("@0,0")
        assert desc.compare(top_idx, ">", "1.0")  # top of view moved down
        assert desc.get(top_idx, f"{top_idx} lineend").strip() != lines[0]
    finally:
        app._close_edit_dialog()
        app.root.destroy()


def test_scrollbar_renders_in_both_themes(tmp_path):
    for theme in ("light", "dark"):
        case_dir = tmp_path / theme
        case_dir.mkdir()
        _write_config(case_dir, theme)
        app = _make_app(case_dir)
        try:
            app.root.update()
            assert app.theme == theme
            app._select_list_name("Edits")
            app.root.update()

            dialog = _open_edit(app)
            desc, sb = dialog.desc_text, dialog.desc_scroll
            assert isinstance(sb, ttk.Scrollbar)
            app.root.update()
            # The scrollbar renders (mapped, non-empty, still wired).
            assert sb.winfo_exists()
            assert sb.winfo_manager() == "pack"
            assert sb.winfo_height() > 0
            assert sb.winfo_width() > 0
            assert desc.cget("yscrollcommand")
            assert sb.cget("command")
        finally:
            app._close_edit_dialog()
            app.root.destroy()
