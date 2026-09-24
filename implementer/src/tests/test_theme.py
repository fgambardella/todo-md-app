"""Headless tests for todo_md.theme (pytest + tmp_path, no display needed)."""

import json

import pytest

from todo_md.storage import MarkdownListStore
from todo_md.theme import (
    SETTINGS_FILENAME,
    VALID_THEMES,
    load_theme,
    migrate_legacy_config,
    save_theme,
    system_default_theme,
)


def _settings_path(config_dir):
    return config_dir / SETTINGS_FILENAME


def test_first_start_creates_config_matching_system_default(tmp_path):
    config_dir = tmp_path / "config"
    expected = system_default_theme()
    assert expected in VALID_THEMES
    got = load_theme(str(config_dir))
    assert got == expected
    with open(_settings_path(config_dir), encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": expected}


def test_persisted_choice_honored_and_untouched(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _settings_path(config_dir).write_text(
        json.dumps({"theme": "light"}), encoding="utf-8"
    )
    assert load_theme(str(config_dir)) == "light"
    with open(_settings_path(config_dir), encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": "light"}


def test_round_trip_save_then_load(tmp_path):
    config_dir = tmp_path / "config"
    save_theme(str(config_dir), "dark")
    assert load_theme(str(config_dir)) == "dark"
    with open(_settings_path(config_dir), encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": "dark"}


def test_save_invalid_theme_raises_and_leaves_file_untouched(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _settings_path(config_dir).write_text(
        json.dumps({"theme": "light"}), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        save_theme(str(config_dir), "neon")
    with open(_settings_path(config_dir), encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": "light"}


def test_corrupt_config_falls_back_and_rewrites(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _settings_path(config_dir).write_bytes(b"not json")
    expected = system_default_theme()
    assert load_theme(str(config_dir)) == expected
    with open(_settings_path(config_dir), encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": expected}


def test_invalid_theme_value_falls_back_and_rewrites(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _settings_path(config_dir).write_text(
        json.dumps({"theme": "blue"}), encoding="utf-8"
    )
    expected = system_default_theme()
    assert load_theme(str(config_dir)) == expected
    with open(_settings_path(config_dir), encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": expected}


def test_settings_json_coexists_with_lists(tmp_path):
    lists_dir = tmp_path / "lists"
    lists_dir.mkdir()
    config_dir = tmp_path / "config"
    store = MarkdownListStore(str(lists_dir))
    store.create("Shopping")
    load_theme(str(config_dir))
    assert store.lists() == ["Shopping"]


def test_no_temp_file_litter(tmp_path):
    config_dir = tmp_path / "config"
    load_theme(str(config_dir))
    save_theme(str(config_dir), "dark")
    assert not [e for e in config_dir.iterdir() if e.name.startswith(".tmp-")]


def test_migrate_legacy_happy_path_deletes_legacy(tmp_path):
    lists_dir = tmp_path / "lists"
    lists_dir.mkdir()
    config_dir = tmp_path / "config"
    legacy = lists_dir / "config.json"
    legacy.write_text(json.dumps({"theme": "dark"}), encoding="utf-8")

    migrate_legacy_config(str(config_dir), str(legacy))

    with open(_settings_path(config_dir), encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": "dark"}
    assert not legacy.exists()
    assert load_theme(str(config_dir)) == "dark"


def test_migrate_legacy_noop_when_settings_already_exists(tmp_path):
    lists_dir = tmp_path / "lists"
    lists_dir.mkdir()
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _settings_path(config_dir).write_text(
        json.dumps({"theme": "light"}), encoding="utf-8"
    )
    legacy = lists_dir / "config.json"
    legacy.write_text(json.dumps({"theme": "dark"}), encoding="utf-8")

    migrate_legacy_config(str(config_dir), str(legacy))

    assert legacy.exists(), "legacy must be left in place when settings.json exists"
    with open(_settings_path(config_dir), encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": "light"}


def test_migrate_legacy_corrupt_left_in_place_and_load_falls_back(tmp_path):
    lists_dir = tmp_path / "lists"
    lists_dir.mkdir()
    config_dir = tmp_path / "config"
    legacy = lists_dir / "config.json"
    legacy.write_bytes(b"not json")

    migrate_legacy_config(str(config_dir), str(legacy))

    assert legacy.exists(), "corrupt legacy file must be left in place"
    assert not _settings_path(config_dir).exists()
    expected = system_default_theme()
    assert load_theme(str(config_dir)) == expected
    with open(_settings_path(config_dir), encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": expected}


def test_migrate_legacy_invalid_theme_left_in_place(tmp_path):
    lists_dir = tmp_path / "lists"
    lists_dir.mkdir()
    config_dir = tmp_path / "config"
    legacy = lists_dir / "config.json"
    legacy.write_text(json.dumps({"theme": "neon"}), encoding="utf-8")

    migrate_legacy_config(str(config_dir), str(legacy))

    assert legacy.exists()
    assert not _settings_path(config_dir).exists()