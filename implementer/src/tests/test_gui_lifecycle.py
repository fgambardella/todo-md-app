"""Subprocess proofs of fixture failure reporting and owned-root cleanup."""

import pytest


@pytest.mark.parametrize(
    "failure,root_count,phase",
    [
        ("before_root", 0, "setup"),
        ("after_root", 1, "setup"),
        ("second_after_root", 2, "setup"),
        ("initial_update", 1, "setup"),
        ("teardown_update", 2, "teardown"),
    ],
)
def test_settings_fixture_cleans_roots_after_failure(
    isolated_pytest, failure, root_count, phase
):
    result = isolated_pytest(f'''
        import tkinter as tk
        import pytest
        from tests.test_gui_settings import default_dir, make_app
        from todo_md.app import TodoApp

        verified_cleanup = False

        @pytest.fixture
        def audit(monkeypatch):
            unrelated = tk.Tk()
            owned = []
            original_init = tk.Tk.__init__

            def track(root, *args, **kwargs):
                original_init(root, *args, **kwargs)
                owned.append(root)

            monkeypatch.setattr(tk.Tk, "__init__", track)
            try:
                yield owned
                assert len(owned) == {root_count}
                for root in owned:
                    with pytest.raises(tk.TclError, match="application has been destroyed"):
                        root.winfo_exists()
                assert unrelated.winfo_exists(), "fixture destroyed an unrelated root"
                global verified_cleanup
                verified_cleanup = True
            finally:
                try:
                    unrelated.update()
                finally:
                    unrelated.destroy()

        @pytest.fixture
        def failing_app(audit, make_app, monkeypatch):
            def fail(*args, **kwargs):
                raise RuntimeError("injected settings {failure}")

            if {failure!r} == "second_after_root":
                make_app()
            if {failure!r} == "before_root":
                monkeypatch.setattr(TodoApp, "__init__", fail)
            elif {failure!r} in ("after_root", "second_after_root"):
                monkeypatch.setattr(TodoApp, "_apply_dock_icon", fail)
            elif {failure!r} == "initial_update":
                original_update = tk.Misc.update
                def fail_once(root):
                    monkeypatch.setattr(tk.Misc, "update", original_update)
                    fail()
                monkeypatch.setattr(tk.Misc, "update", fail_once)

            app = make_app()
            if {failure!r} == "teardown_update":
                second = make_app()
                # Both roots must be destroyed even when both updates fail.
                monkeypatch.setattr(app.root, "update", fail)
                def second_failure():
                    raise ValueError("injected second teardown update")
                monkeypatch.setattr(second.root, "update", second_failure)
            return app

        def test_injected_failure(failing_app):
            assert failing_app.root.winfo_exists()

        def test_clean_app_after_failure(make_app, dialog_guard):
            assert verified_cleanup, "cleanup audit did not finish"
            assert tk._default_root is None
            assert dialog_guard.attempts == []
            app = make_app()
            app.controller.store.save("fresh", [("working image", False)])
            app.refresh_lists(select_first=True)
            app.root.update()
            assert app._trash_image.tk is app.root.tk
            assert app._trash_image.width() > 0
            assert app.root.tk.call("image", "type", str(app._trash_image)) == "photo"
            assert len(app._item_rows) == 1
            assert app._item_rows[0][3].cget("image") == str(app._trash_image)
            assert app.callback_errors == []
    ''')
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.assert_outcomes(passed=2 if phase == "teardown" else 1, errors=1)
    result.stdout.fnmatch_lines([
        f"*ERROR at {phase} of test_injected_failure*",
        f"*RuntimeError: injected settings {failure}*",
    ])
    if failure == "teardown_update":
        result.stdout.fnmatch_lines(["*ValueError: injected second teardown update*"])


@pytest.mark.parametrize("phase", ["setup", "teardown"])
def test_guard_root_fixture_cleans_up_after_update_failure(isolated_pytest, phase):
    result = isolated_pytest(f'''
        import tkinter as tk
        import pytest
        from tests.test_dialog_guard import tk_root

        verified_cleanup = False

        @pytest.fixture
        def inject_update_failure(monkeypatch):
            owned = []
            original_update = tk.Misc.update

            def fail_update(root):
                owned.append(root)
                monkeypatch.setattr(tk.Misc, "update", original_update)
                raise RuntimeError("injected guard {phase} update")

            if {phase!r} == "setup":
                monkeypatch.setattr(tk.Misc, "update", fail_update)
            yield fail_update
            assert len(owned) == 1
            with pytest.raises(tk.TclError, match="application has been destroyed"):
                owned[0].winfo_exists()
            assert tk._default_root is None
            global verified_cleanup
            verified_cleanup = True

        def test_injected_failure(inject_update_failure, tk_root, monkeypatch):
            assert tk_root.winfo_exists()
            monkeypatch.setattr(tk.Misc, "update", inject_update_failure)

        def test_clean_root_after_failure(tk_root, dialog_guard):
            assert verified_cleanup, "cleanup audit did not finish"
            assert dialog_guard.attempts == []
            image = tk.PhotoImage(master=tk_root, width=2, height=2)
            label = tk.Label(tk_root, image=image)
            label.pack()
            tk_root.update()
            assert label.winfo_exists()
            assert tk_root.tk.call("image", "width", str(image)) == 2
    ''')
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.assert_outcomes(passed=2 if phase == "teardown" else 1, errors=1)
    result.stdout.fnmatch_lines([
        f"*ERROR at {phase} of test_injected_failure*",
        f"*RuntimeError: injected guard {phase} update*",
    ])


def test_loading_conftest_is_root_free(isolated_pytest):
    result = isolated_pytest('''
        import importlib
        import tkinter as tk
        from unittest.mock import patch
        from tests import conftest

        def test_import_without_root():
            assert tk._default_root is None
            with patch.object(tk, "Tk", side_effect=AssertionError("root during import")):
                importlib.reload(conftest)
            assert tk._default_root is None
    ''')
    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1)
