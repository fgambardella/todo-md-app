"""Regression tests for the dialog guard fixture."""

import pytest
from unittest.mock import patch

from tests.conftest import managed_tk_roots


@pytest.fixture
def tk_root():
    with managed_tk_roots() as create_root:
        root = create_root()
        root.update()
        yield root


def test_guard_blocks_unmocked_askyesnocancel(tk_root, dialog_guard):
    """An unmocked askyesnocancel raises before opening."""
    from tkinter import messagebox

    exc = dialog_guard.expect_unexpected(
        messagebox.askyesnocancel, "Title", "Message", parent=tk_root
    )
    assert "Unexpected dialog would open" in str(exc)


def test_guard_blocks_unmocked_showerror(tk_root, dialog_guard):
    """An unmocked showerror raises before opening."""
    from tkinter import messagebox

    exc = dialog_guard.expect_unexpected(
        messagebox.showerror, "Error", "Something failed", parent=tk_root
    )
    assert "Unexpected dialog would open" in str(exc)


def test_guard_blocks_unmocked_file_dialog(tk_root, tmp_path, dialog_guard):
    """An unmocked file dialog raises before opening."""
    from tkinter import filedialog

    exc = dialog_guard.expect_unexpected(
        filedialog.askdirectory, parent=tk_root, initialdir=str(tmp_path)
    )
    assert "Unexpected dialog would open" in str(exc)


@pytest.mark.parametrize("decision", [True, False, None])
def test_guard_allows_explicit_askyesnocancel_mock(tk_root, dialog_guard, decision):
    """Explicitly mocked askyesnocancel returns expected value."""
    from tkinter import messagebox

    with patch("tkinter.messagebox.askyesnocancel", return_value=decision) as mocked:
        result = messagebox.askyesnocancel("Title", "Message", parent=tk_root)
        assert result is decision
        mocked.assert_called_once_with("Title", "Message", parent=tk_root)
    assert dialog_guard.attempts == []


def test_guard_allows_explicit_showerror_mock(tk_root, dialog_guard):
    """Explicitly mocked showerror can be asserted."""
    from tkinter import messagebox

    with patch("tkinter.messagebox.showerror") as mocked:
        messagebox.showerror("Error", "Message", parent=tk_root)
        mocked.assert_called_once_with("Error", "Message", parent=tk_root)
    assert dialog_guard.attempts == []


def test_guard_catches_swallowed_dialog_at_teardown(isolated_pytest):
    """Tk swallows the callback exception; the real guard must fail teardown."""
    result = isolated_pytest('''
        import tkinter as tk
        from tkinter import messagebox
        from tests.test_dialog_guard import tk_root

        previous_guard = None

        def test_unacknowledged_callback(tk_root, dialog_guard, capsys):
            global previous_guard
            previous_guard = dialog_guard
            button = tk.Button(tk_root, command=lambda: messagebox.showinfo(
                "Info", "Hidden dialog", parent=tk_root
            ))
            button.invoke()
            assert "UnexpectedDialogError" in capsys.readouterr().err
            assert len(dialog_guard.attempts) == 1
            assert dialog_guard.attempts[0]["class"] == "Message"

        def test_clean_after_negative(dialog_guard):
            assert dialog_guard is not previous_guard
            assert dialog_guard.attempts == []
            assert len(previous_guard.attempts) == 1
            assert tk._default_root is None
    ''')
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.assert_outcomes(passed=2, errors=1)
    result.stdout.fnmatch_lines([
        "*ERROR at teardown of test_unacknowledged_callback*",
        "*AssertionError: Dialog was opened without test assertion:*Message*",
    ])
