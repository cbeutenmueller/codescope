from __future__ import annotations
import tomllib
from pathlib import Path
import pytest
import tempfile

from codescope.config import AppConfig, load_config, _deep_merge


def test_default_config_has_expected_values():
    cfg = AppConfig()
    assert cfg.review.top_n_hotspots == 20
    assert cfg.review.max_tokens_per_call == 6000
    assert cfg.review.hotspot_weights.change_frequency == 1.0
    assert cfg.review.hotspot_weights.complexity == 0.8
    assert cfg.server.port == 8421
    assert "java" in cfg.index.languages
    assert "typescript" in cfg.index.languages


def test_default_config_has_builtin_library():
    cfg = AppConfig()
    names = [lib.name for lib in cfg.pattern_libraries]
    assert "builtin" in names


def test_load_config_from_toml(tmp_path):
    (tmp_path / ".codescope").mkdir()
    toml_content = """
[llm]
model = "my-model"
api_key = "sk-test"

[review]
top_n_hotspots = 10
"""
    (tmp_path / ".codescope" / "config.toml").write_text(toml_content, encoding="utf-8")
    cfg = load_config(tmp_path)
    assert cfg.llm.model == "my-model"
    assert cfg.review.top_n_hotspots == 10


def test_deep_merge_overrides_scalars():
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 99}}
    result = _deep_merge(base, override)
    assert result["a"] == 1
    assert result["b"]["c"] == 99
    assert result["b"]["d"] == 3


def test_deep_merge_adds_new_keys():
    base = {"a": 1}
    override = {"b": 2}
    result = _deep_merge(base, override)
    assert result == {"a": 1, "b": 2}


def test_llm_profile_selection():
    from codescope.config import LLMProfile

    cfg = AppConfig()
    cfg.llm.profiles["openai"] = LLMProfile(
        base_url="https://api.openai.com/v1",
        model="gpt-4o",
        api_key="sk-x",
    )
    profile = cfg.llm_profile("openai")
    assert profile.model == "gpt-4o"


def test_llm_profile_fallback_to_default():
    cfg = AppConfig()
    profile = cfg.llm_profile(None)
    assert profile is cfg.llm

    profile2 = cfg.llm_profile("nonexistent")
    assert profile2 is cfg.llm
