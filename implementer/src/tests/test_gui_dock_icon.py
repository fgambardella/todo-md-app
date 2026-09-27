"""GUI tests for the macOS dock icon (require a real display)."""

import os

import tkinter as tk

import todo_md.app as app_module
from todo_md.app import TodoApp, TodoController, dock_icon_path
from todo_md.storage import MarkdownListStore


def _make_app(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    controller = TodoController(store)
    return TodoApp(controller, data_dir=str(tmp_path))


def test_png_asset_loads_as_photoimage():
    assert os.path.isfile(dock_icon_path())
    root = tk.Tk()
    try:
        img = tk.PhotoImage(file=dock_icon_path())
        assert img.width() > 0
        assert img.height() > 0
        # Update before destroy: on this Tk build, a root that is destroyed
        # without ever being updated corrupts the next Tk instance in the
        # process (subsequent update() traps).
        root.update()
    finally:
        root.destroy()


def test_todoapp_stores_dock_icon(tmp_path):
    app = _make_app(tmp_path)
    try:
        app.root.update()
        assert isinstance(app._dock_icon, tk.PhotoImage)
        assert app._dock_icon.width() > 0
        assert app._dock_icon.height() > 0
    finally:
        app.root.destroy()


def test_missing_icon_fails_soft(tmp_path, monkeypatch):
    monkeypatch.setattr(
        app_module, "dock_icon_path", lambda: str(tmp_path / "does_not_exist.png")
    )
    app = _make_app(tmp_path)
    try:
        app.root.update()
        assert app._dock_icon is None
        assert app.root.winfo_exists()
    finally:
        app.root.destroy()
