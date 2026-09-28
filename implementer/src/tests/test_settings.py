"""Headless tests for todo_md.settings (pytest + tmp_path, no display needed)."""

import json

import pytest

from todo_md.settings import (
    DEFAULT_COMPLETED_VISIBLE,
    DEFAULT_THEME,
    SETTINGS_FILENAME,
    VALID_THEMES,
    Settings,
    load_settings,
    resolve_theme,
    save_settings,
    system_default_theme,
)
from todo_md.storage import MarkdownListStore


def _settings_path(config_dir):
    return config_dir / SETTINGS_FILENAME


# -- load: defaults, legacy compatibility, corrupt input --------------------


def test_missing_file_loads_all_defaults(tmp_path):
    config_dir = tmp_path / "config"
    got = load_settings(str(config_dir))
    assert got == Settings(
        theme=DEFAULT_THEME, lists_dir=None, completed_visible=DEFAULT_COMPLETED_VISIBLE
    )
    assert got.theme == "system"
    assert got.completed_visible == 10


def test_missing_keys_load_defaults(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _settings_path(config_dir).write_text(
        json.dumps({"theme": "dark"}), encoding="utf-8"
    )
    got = load_settings(str(config_dir))
    assert got.theme == "dark"
    assert got.lists_dir is None
    assert got.completed_visible == 10


def test_legacy_theme_file_compatibility(tmp_path):
    # Legacy file shape {"theme": "light"|"dark"} must load exactly as-is.
    for legacy in ("light", "dark"):
        config_dir = tmp_path / f"config-{legacy}"
        config_dir.mkdir()
        _settings_path(config_dir).write_text(
            json.dumps({"theme": legacy}), encoding="utf-8"
        )
        got = load_settings(str(config_dir))
        assert got.theme == legacy
        assert got.lists_dir is None
        assert got.completed_visible == DEFAULT_COMPLETED_VISIBLE


def test_persisted_full_choice_honored_and_untouched(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    raw = json.dumps(
        {"theme": "light", "lists_dir": "/tmp/lists", "completed_visible": 3}
    )
    _settings_path(config_dir).write_text(raw, encoding="utf-8")
    got = load_settings(str(config_dir))
    assert got == Settings(theme="light", lists_dir="/tmp/lists", completed_visible=3)
    # Load must never rewrite the file.
    assert _settings_path(config_dir).read_text(encoding="utf-8") == raw


def test_corrupt_config_falls_back_to_defaults_without_raising(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _settings_path(config_dir).write_bytes(b"not json")
    got = load_settings(str(config_dir))
    assert got == Settings()
    # Load does not rewrite the file.
    assert _settings_path(config_dir).read_bytes() == b"not json"


def test_invalid_theme_value_falls_back_to_default(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _settings_path(config_dir).write_text(
        json.dumps({"theme": "blue"}), encoding="utf-8"
    )
    assert load_settings(str(config_dir)).theme == DEFAULT_THEME


def test_invalid_completed_visible_falls_back_to_default(tmp_path):
    for bad in (-1, "10", None, True):
        config_dir = tmp_path / f"config-{abs(hash(bad))}"
        config_dir.mkdir()
        _settings_path(config_dir).write_text(
            json.dumps({"completed_visible": bad}), encoding="utf-8"
        )
        assert load_settings(str(config_dir)).completed_visible == DEFAULT_COMPLETED_VISIBLE


def test_settings_json_coexists_with_lists(tmp_path):
    lists_dir = tmp_path / "lists"
    lists_dir.mkdir()
    config_dir = tmp_path / "config"
    store = MarkdownListStore(str(lists_dir))
    store.create("Shopping")
    load_settings(str(config_dir))
    assert store.lists() == ["Shopping"]


# -- save: round-trip, validation, atomicity ---------------------------------


def test_round_trip_save_then_load(tmp_path):
    config_dir = tmp_path / "config"
    save_settings(
        str(config_dir),
        Settings(theme="dark", lists_dir="/tmp/lists", completed_visible=3),
    )
    assert load_settings(str(config_dir)) == Settings(
        theme="dark", lists_dir="/tmp/lists", completed_visible=3
    )
    with open(_settings_path(config_dir), encoding="utf-8") as fh:
        assert json.load(fh) == {
            "theme": "dark",
            "lists_dir": "/tmp/lists",
            "completed_visible": 3,
        }


def test_save_default_lists_dir_written_as_null(tmp_path):
    config_dir = tmp_path / "config"
    save_settings(str(config_dir), Settings())
    with open(_settings_path(config_dir), encoding="utf-8") as fh:
        data = json.load(fh)
    assert data == {
        "theme": DEFAULT_THEME,
        "lists_dir": None,
        "completed_visible": DEFAULT_COMPLETED_VISIBLE,
    }
    assert data["lists_dir"] is None


def test_lists_dir_passthrough(tmp_path):
    config_dir = tmp_path / "config"
    save_settings(
        str(config_dir),
        Settings(theme="light", lists_dir="/custom/lists", completed_visible=0),
    )
    with open(_settings_path(config_dir), encoding="utf-8") as fh:
        assert json.load(fh)["lists_dir"] == "/custom/lists"
    assert load_settings(str(config_dir)).lists_dir == "/custom/lists"


def test_save_invalid_theme_raises_and_leaves_file_untouched(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _settings_path(config_dir).write_text(
        json.dumps({"theme": "light"}), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        save_settings(str(config_dir), Settings(theme="neon"))
    with open(_settings_path(config_dir), encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": "light"}


def test_save_negative_completed_visible_raises_and_leaves_file_untouched(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _settings_path(config_dir).write_text(
        json.dumps({"theme": "light"}), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        save_settings(str(config_dir), Settings(completed_visible=-1))
    with open(_settings_path(config_dir), encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": "light"}


def test_save_non_int_completed_visible_raises(tmp_path):
    config_dir = tmp_path / "config"
    for bad in ("10", None, True):
        with pytest.raises(ValueError):
            save_settings(str(config_dir), Settings(completed_visible=bad))


def test_no_temp_file_litter(tmp_path):
    config_dir = tmp_path / "config"
    load_settings(str(config_dir))
    save_settings(str(config_dir), Settings(theme="dark"))
    assert not [e for e in config_dir.iterdir() if e.name.startswith(".tmp-")]


# -- resolve_theme -----------------------------------------------------------


def test_resolve_theme_explicit_values_returned_verbatim():
    assert resolve_theme(Settings(theme="light")) == "light"
    assert resolve_theme(Settings(theme="dark")) == "dark"


def test_resolve_theme_system_uses_detection(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "todo_md.settings.system_default_theme", lambda: "dark"
    )
    assert resolve_theme(Settings(theme="system")) == "dark"
    monkeypatch.setattr(
        "todo_md.settings.system_default_theme", lambda: "light"
    )
    assert resolve_theme(Settings(theme="system")) == "light"


def test_resolve_theme_system_not_persisted(monkeypatch, tmp_path):
    monkeypatch.setattr("todo_md.settings.system_default_theme", lambda: "dark")
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    assert resolve_theme(Settings(theme="system")) == "dark"
    # Resolution must not create or modify any settings file.
    assert not _settings_path(config_dir).exists()


def test_system_default_theme_valid_values(monkeypatch):
    import subprocess

    class _Result:
        def __init__(self, returncode, stdout):
            self.returncode = returncode
            self.stdout = stdout

    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: _Result(0, "dark\n")
    )
    assert system_default_theme() == "dark"
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: _Result(1, "")
    )
    assert system_default_theme() == "light"
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(OSError())
    )
    assert system_default_theme() == "light"