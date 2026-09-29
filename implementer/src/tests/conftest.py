"""Shared test infrastructure for GUI tests."""

import pytest


class UnexpectedDialogError(AssertionError):
    """Raised when an unmocked dialog would open during a test."""


class DialogGuard:
    """Records intercepted native dialogs for the current test."""

    def __init__(self) -> None:
        self.attempts: list[dict] = []

    def acknowledge(self) -> None:
        """Mark recorded attempts as intentionally triggered and caught."""
        self.attempts.clear()

    def expect_unexpected(self, func, *args, **kwargs):
        """Run func expecting it to raise UnexpectedDialogError, then acknowledge.

        Returns the exception instance for further assertion.
        """
        with pytest.raises(UnexpectedDialogError) as exc_info:
            func(*args, **kwargs)
        self.acknowledge()
        return exc_info.value


@pytest.fixture(autouse=True)
def dialog_guard(monkeypatch):
    """Block real modal dialogs from opening in GUI tests.

    Patches tkinter.commondialog.Dialog.show to intercept all messageboxes
    and file pickers. Tests that expect dialogs must mock the public API
    (messagebox.askyesnocancel, showerror, etc.) with expected return values.
    Unexpected dialogs raise before opening anything; attempts that survive
    to teardown (e.g., swallowed by a Tk callback) fail the test there.

    This fixture never creates a Tk root, so it is safe for headless tests.
    """
    guard = DialogGuard()

    try:
        from tkinter.commondialog import Dialog
    except ImportError:
        # Headless environment without tkinter; nothing to guard.
        yield guard
        return

    def guarded_show(self, **options):
        guard.attempts.append({
            "options": options,
            "class": self.__class__.__name__,
        })
        raise UnexpectedDialogError(
            f"Unexpected dialog would open: {self.__class__.__name__} "
            f"with options {options!r}. "
            f"Tests must mock the public dialog function (e.g., "
            f"messagebox.askyesnocancel) explicitly."
        )

    monkeypatch.setattr(Dialog, "show", guarded_show)

    yield guard

    # If a Tk callback swallowed the raised error, the dialog attempt never
    # surfaced to the test; fail now so the run stays unattended.
    if guard.attempts:
        raise AssertionError(
            f"Dialog was opened without test assertion: {guard.attempts!r}"
        )
