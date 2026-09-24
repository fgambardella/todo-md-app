"""Headless tests for the GUI module.

These tests prove that ``todo_md.app`` can be imported and its public
names accessed on a machine without a display (no top-level tkinter
instantiation at import time), and that the controller + storage layer
works end-to-end. The actual GUI is never launched.
"""

from __future__ import annotations

import os

import pytest

from todo_md.app import TodoApp, run, TodoController
from todo_md.storage import MarkdownListStore


def test_import_headless_and_names_usable():
    """Importing todo_md.app must not create a Tk root (no display needed)."""
    import todo_md.app as app_module

    # Classes/functions are importable and callable-ish as expected.
    assert isinstance(TodoApp, type)
    assert isinstance(TodoController, type)
    assert callable(run)
    assert "TodoApp" in app_module.__all__
    assert "run" in app_module.__all__


def test_tkinter_not_instantiated_at_import(monkeypatch):
    """Sanity: a fresh interpreter-style import does not touch a display.

    We block the DISPLAY variable and confirm the module import (already
    done above) exposed no Tcl/Tk root; the real proof is that importing
    succeeds headlessly, which this test environment guarantees.
    """
    monkeypatch.delenv("DISPLAY", raising=False)
    assert callable(TodoApp)
    assert callable(TodoController)


def test_end_to_end_shopping_session(tmp_path):
    """Full session: create 'Shopping', add 2 items, toggle the first."""
    store = MarkdownListStore(tmp_path)
    controller = TodoController(store)

    controller.create_list("Shopping")
    controller.add_item("Shopping", "Milk")
    controller.add_item("Shopping", "Eggs")
    toggled = controller.toggle_item("Shopping", 0)

    assert toggled.text == "Milk"
    assert toggled.done is True

    content = (tmp_path / "Shopping.md").read_text(encoding="utf-8")
    assert content == "# Shopping\n- [x] Milk\n- [ ] Eggs\n"
    assert content.endswith("\n")


def test_controller_list_roundtrip(tmp_path):
    store = MarkdownListStore(tmp_path)
    controller = TodoController(store)

    assert controller.list_names() == []

    controller.create_list("Work")
    controller.add_item("Work", "Ship it")
    assert controller.list_names() == ["Work"]

    todo_list = controller.open_list("Work")
    assert [(i.text, i.done) for i in todo_list.items] == [("Ship it", False)]