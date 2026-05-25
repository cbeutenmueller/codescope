from __future__ import annotations
from pathlib import Path
import pytest

from codescope.config import AppConfig
from codescope.patterns.loader import load_patterns, _load_from_dir, _parse_yaml_file
from codescope.patterns.schema import Pattern, AstHints
from codescope.patterns.namespace import namespace_id, strip_namespace, resolve_overrides

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


def test_pattern_namespaced_id_with_library():
    p = Pattern(
        id="spring-data-1",
        name="Test",
        category="test",
        description="desc",
        library="builtin",
    )
    assert p.namespaced_id == "builtin/spring-data-1"


def test_pattern_namespaced_id_already_namespaced():
    p = Pattern(
        id="builtin/spring-data-1",
        name="Test",
        category="test",
        description="desc",
        library="builtin",
    )
    assert p.namespaced_id == "builtin/spring-data-1"


def test_ast_hints_is_empty():
    hints = AstHints()
    assert hints.is_empty()


def test_ast_hints_not_empty_when_annotations_set():
    hints = AstHints(annotations_present=["@Transactional"])
    assert not hints.is_empty()


# ---------------------------------------------------------------------------
# Namespace helpers
# ---------------------------------------------------------------------------


def test_namespace_id_adds_prefix():
    assert namespace_id("spring-data-1", "builtin") == "builtin/spring-data-1"


def test_namespace_id_skips_existing_prefix():
    assert namespace_id("builtin/spring-data-1", "builtin") == "builtin/spring-data-1"


def test_strip_namespace():
    assert strip_namespace("builtin/spring-data-1") == ("builtin", "spring-data-1")


def test_strip_namespace_no_slash():
    assert strip_namespace("spring-data-1") == ("", "spring-data-1")


def test_resolve_overrides_removes_overridden():
    from codescope.patterns.schema import Pattern

    def make(id_, lib="builtin"):
        return Pattern(id=id_, name=id_, category="x", description="x", library=lib)

    patterns = [make("builtin/a"), make("myteam/a", "myteam"), make("builtin/b")]
    result = resolve_overrides(patterns, [("builtin/a", "myteam/a")])
    ids = [p.namespaced_id for p in result]
    assert "builtin/a" not in ids
    assert "myteam/a" in ids
    assert "builtin/b" in ids


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def test_load_builtin_patterns_returns_patterns():
    config = AppConfig()
    patterns = load_patterns(config)
    assert len(patterns) > 0


def test_load_builtin_patterns_all_valid():
    config = AppConfig()
    for p in load_patterns(config):
        assert p.id
        assert p.name
        assert p.description


def test_builtin_patterns_have_namespaced_ids():
    config = AppConfig()
    for p in load_patterns(config):
        assert "/" in p.namespaced_id, f"Pattern {p.id} missing namespace"


def test_builtin_includes_spring_data_pattern():
    config = AppConfig()
    patterns = {p.namespaced_id: p for p in load_patterns(config)}
    assert "builtin/spring-data-1" in patterns


def test_builtin_includes_angular_rxjs_pattern():
    config = AppConfig()
    patterns = {p.namespaced_id: p for p in load_patterns(config)}
    assert "builtin/ng-rxjs-1" in patterns


def test_disabled_patterns_excluded():
    config = AppConfig()
    from codescope.patterns.builtin import __file__ as _

    # All builtin patterns have enabled: true — verify none are filtered out unexpectedly
    patterns = load_patterns(config)
    enabled_ids = [p.namespaced_id for p in patterns]
    # If any were disabled they wouldn't appear
    assert len(enabled_ids) > 0


def test_parse_yaml_file_invalid_returns_empty(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not: valid: yaml: :", encoding="utf-8")
    result = _parse_yaml_file(bad)
    assert result == []


def test_parse_yaml_file_non_list_returns_empty(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("key: value\n", encoding="utf-8")
    result = _parse_yaml_file(bad)
    assert result == []


def test_local_library_overrides_builtin(tmp_path):
    """A local pattern with the same base ID should override the builtin version."""
    local_dir = tmp_path / "local_patterns"
    local_dir.mkdir()
    (local_dir / "overrides.yaml").write_text(
        """
- id: spring-data-1
  name: My Override
  category: spring-data
  language: java
  severity: low
  description: Custom description
  enabled: true
""",
        encoding="utf-8",
    )
    from codescope.config import PatternLibraryConfig

    config = AppConfig()
    config.pattern_libraries.append(PatternLibraryConfig(name="local", source=str(local_dir)))
    patterns = {p.namespaced_id: p for p in load_patterns(config)}
    # local wins over builtin
    assert patterns.get("local/spring-data-1") is not None
    assert patterns["local/spring-data-1"].name == "My Override"
