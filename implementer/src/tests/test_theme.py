"""Headless tests for todo_md.theme (pytest + tmp_path, no display needed)."""

import json

import pytest

from todo_md.storage import MarkdownListStore
from todo_md.theme import (
    CONFIG_FILENAME,
    VALID_THEMES,
    load_theme,
    save_theme,
    system_default_theme,
)


def test_first_start_creates_config_matching_system_default(tmp_path):
    expected = system_default_theme()
    assert expected in VALID_THEMES
    got = load_theme(str(tmp_path))
    assert got == expected
    with open(tmp_path / CONFIG_FILENAME, encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": expected}


def test_persisted_choice_honored_and_untouched(tmp_path):
    (tmp_path / CONFIG_FILENAME).write_text(
        json.dumps({"theme": "light"}), encoding="utf-8"
    )
    assert load_theme(str(tmp_path)) == "light"
    with open(tmp_path / CONFIG_FILENAME, encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": "light"}


def test_round_trip_save_then_load(tmp_path):
    save_theme(str(tmp_path), "dark")
    assert load_theme(str(tmp_path)) == "dark"
    with open(tmp_path / CONFIG_FILENAME, encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": "dark"}


def test_save_invalid_theme_raises_and_leaves_file_untouched(tmp_path):
    (tmp_path / CONFIG_FILENAME).write_text(
        json.dumps({"theme": "light"}), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        save_theme(str(tmp_path), "neon")
    with open(tmp_path / CONFIG_FILENAME, encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": "light"}


def test_corrupt_config_falls_back_and_rewrites(tmp_path):
    (tmp_path / CONFIG_FILENAME).write_bytes(b"not json")
    expected = system_default_theme()
    assert load_theme(str(tmp_path)) == expected
    with open(tmp_path / CONFIG_FILENAME, encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": expected}


def test_invalid_theme_value_falls_back_and_rewrites(tmp_path):
    (tmp_path / CONFIG_FILENAME).write_text(
        json.dumps({"theme": "blue"}), encoding="utf-8"
    )
    expected = system_default_theme()
    assert load_theme(str(tmp_path)) == expected
    with open(tmp_path / CONFIG_FILENAME, encoding="utf-8") as fh:
        assert json.load(fh) == {"theme": expected}


def test_config_json_coexists_with_lists(tmp_path):
    store = MarkdownListStore(str(tmp_path))
    store.create("Shopping")
    load_theme(str(tmp_path))
    assert store.lists() == ["Shopping"]


def test_no_temp_file_litter(tmp_path):
    load_theme(str(tmp_path))
    save_theme(str(tmp_path), "dark")
    assert not [e for e in tmp_path.iterdir() if e.name.startswith(".tmp-")]
