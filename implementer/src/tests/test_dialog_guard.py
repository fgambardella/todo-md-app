"""Regression tests for the dialog guard fixture."""

import pytest
from unittest.mock import patch

from tests.conftest import UnexpectedDialogError


def test_guard_blocks_unmocked_askyesnocancel(tmp_path, dialog_guard):
    """An unmocked askyesnocancel raises before opening."""
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    try:
        exc = dialog_guard.expect_unexpected(
            messagebox.askyesnocancel, "Title", "Message"
        )
        assert "Unexpected dialog would open" in str(exc)
    finally:
        root.update()
        root.destroy()


def test_guard_blocks_unmocked_showerror(tmp_path, dialog_guard):
    """An unmocked showerror raises before opening."""
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    try:
        exc = dialog_guard.expect_unexpected(
            messagebox.showerror, "Error", "Something failed"
        )
        assert "Unexpected dialog would open" in str(exc)
    finally:
        root.update()
        root.destroy()


def test_guard_blocks_unmocked_file_dialog(tmp_path, dialog_guard):
    """An unmocked file dialog raises before opening."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    try:
        exc = dialog_guard.expect_unexpected(
            filedialog.askdirectory, parent=root, initialdir="/tmp"
        )
        assert "Unexpected dialog would open" in str(exc)
    finally:
        root.update()
        root.destroy()


def test_guard_allows_explicit_askyesnocancel_mock(tmp_path):
    """Explicitly mocked askyesnocancel returns expected value."""
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    try:
        with patch("tkinter.messagebox.askyesnocancel", return_value=True) as mocked:
            result = messagebox.askyesnocancel("Title", "Message")
            assert result is True
            assert mocked.called
    finally:
        root.update()
        root.destroy()


def test_guard_allows_explicit_showerror_mock(tmp_path):
    """Explicitly mocked showerror can be asserted."""
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    try:
        with patch("tkinter.messagebox.showerror") as mocked:
            messagebox.showerror("Error", "Message")
            assert mocked.called
    finally:
        root.update()
        root.destroy()


def test_guard_catches_swallowed_dialog_at_teardown(tmp_path, dialog_guard):
    """Dialog attempt swallowed by a callback is recorded by the guard."""
    import tkinter as tk

    root = tk.Tk()
    try:
        from tkinter import messagebox

        def swallowed_callback():
            try:
                messagebox.showinfo("Info", "Hidden dialog")
            except Exception:
                pass  # Swallowed; guard must still record the attempt

        swallowed_callback()
        assert dialog_guard.attempts, "guard must record the swallowed attempt"
        dialog_guard.acknowledge()  # acknowledged here; teardown stays green
    finally:
        root.update()
        root.destroy()
