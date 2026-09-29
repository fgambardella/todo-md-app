"""Shared test infrastructure for GUI tests."""

from contextlib import contextmanager
from pathlib import Path

import pytest

pytest_plugins = ["pytester"]


@contextmanager
def managed_tk_roots():
    """Own only roots created here, draining each before unconditional destroy."""
    from tkinter import Tk

    roots = []
    errors = []

    def create(*args, **kwargs):
        root = Tk(*args, **kwargs)
        roots.append(root)
        return root

    try:
        yield create
    except BaseException as error:
        errors.append(error)
    finally:
        for root in reversed(roots):
            try:
                root.update()
            except BaseException as error:
                errors.append(error)
            finally:
                try:
                    root.destroy()
                except BaseException as error:
                    errors.append(error)
        if len(errors) == 1:
            raise errors[0]
        if errors:
            raise BaseExceptionGroup("Tk root lifecycle failures", errors)


@pytest.fixture
def isolated_pytest(pytester):
    """Run the real shared fixtures in a bounded, separate pytest process."""
    source_dir = str(Path(__file__).resolve().parents[1])
    pytester.makeconftest(
        f"import sys\nsys.path.insert(0, {source_dir!r})\n"
        "from tests.conftest import dialog_guard\n"
    )

    def run(source):
        pytester.makepyfile(test_isolated=source)
        # TimeoutExpired propagates: a hung native dialog is never a pass.
        return pytester.runpytest_subprocess("-v", "--tb=short", timeout=30)

    return run


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
