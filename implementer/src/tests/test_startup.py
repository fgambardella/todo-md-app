"""Headless tests for the startup flow (settings -> data dir -> store).

No display required: exercises ``todo_md.app.startup_dirs`` and the
default wiring only. All temp dirs are pytest fixtures; real user data
under ``~/.todo-md-app`` is never written.
"""

import os

import pytest

from todo_md.app import (
    DEFAULT_CONFIG_DIR,
    DEFAULT_DATA_DIR,
    TodoController,
    startup_dirs,
)
from todo_md.settings import SETTINGS_FILENAME, Settings, save_settings
from todo_md.storage import MarkdownListStore


# -- fixed config dir --------------------------------------------------------


def test_default_config_dir_is_fixed():
    # The config dir is a constant location, independent of any lists dir.
    assert DEFAULT_CONFIG_DIR == os.path.join(
        os.path.expanduser("~"), ".todo-md-app", "config"
    )
    # Config dir is never inside the default lists dir (nor vice versa).
    assert not DEFAULT_CONFIG_DIR.startswith(DEFAULT_DATA_DIR + os.sep)
    assert not DEFAULT_DATA_DIR.startswith(DEFAULT_CONFIG_DIR + os.sep)


def test_saved_lists_dir_does_not_move_config_dir(tmp_path):
    # A saved lists_dir points elsewhere; startup must still use the
    # fixed config dir passed in and never derive one from the lists dir.
    config_dir = tmp_path / "config"
    lists_dir = tmp_path / "elsewhere" / "lists"
    save_settings(str(config_dir), Settings(theme="light", lists_dir=str(lists_dir)))

    cfg, data_dir, settings = startup_dirs(str(config_dir))
    assert cfg == str(config_dir)
    assert data_dir == str(lists_dir)
    assert settings.lists_dir == str(lists_dir)
    # The settings file stays in the fixed config dir.
    assert (config_dir / SETTINGS_FILENAME).exists()
    # Config dir is not inside the (saved) lists dir.
    assert not cfg.startswith(data_dir + os.sep)


# -- effective data dir ------------------------------------------------------


def test_effective_data_dir_from_saved_lists_dir_created_on_demand(tmp_path):
    config_dir = tmp_path / "config"
    lists_dir = tmp_path / "custom" / "lists"  # does not exist yet
    save_settings(str(config_dir), Settings(theme="dark", lists_dir=str(lists_dir)))

    cfg, data_dir, _settings = startup_dirs(str(config_dir))
    assert data_dir == str(lists_dir)
    assert os.path.isdir(lists_dir)  # created on demand

    # Store/controller built with the derived dir work end-to-end.
    store = MarkdownListStore(data_dir)
    controller = TodoController(store, data_dir=data_dir)
    assert controller.data_dir == str(lists_dir)
    controller.create_list("Work")
    controller.add_item("Work", "Ship it")
    assert (lists_dir / "Work.md").exists()


def test_default_data_dir_on_fresh_run(tmp_path, monkeypatch):
    # Fresh (missing) config dir: settings are all defaults, so the
    # effective data dir is DEFAULT_DATA_DIR — overridden to a temp dir
    # here so no real user data is ever touched.
    fake_default = tmp_path / "default-lists"
    monkeypatch.setattr("todo_md.app.DEFAULT_DATA_DIR", str(fake_default))
    config_dir = tmp_path / "fresh-config"

    cfg, data_dir, settings = startup_dirs(str(config_dir))
    assert settings.lists_dir is None
    assert data_dir == str(fake_default)
    assert os.path.isdir(fake_default)
    assert cfg == str(config_dir)
    # Default config dir is not inside the derived data dir.
    assert not cfg.startswith(data_dir + os.sep)


def test_config_dir_override_default_argument(tmp_path, monkeypatch):
    # run()/startup_dirs default (no override) must use the FIXED
    # ~/.todo-md-app/config, never something derived from the data dir.
    monkeypatch.setattr("todo_md.app.DEFAULT_CONFIG_DIR", str(tmp_path / "fixed-cfg"))
    fake_default = tmp_path / "default-lists"
    monkeypatch.setattr("todo_md.app.DEFAULT_DATA_DIR", str(fake_default))

    cfg, data_dir, _settings = startup_dirs()
    assert cfg == str(tmp_path / "fixed-cfg")
    assert data_dir == str(fake_default)