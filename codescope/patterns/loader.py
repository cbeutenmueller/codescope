from __future__ import annotations
from pathlib import Path

import yaml

from codescope.config import AppConfig, PatternLibraryConfig
from codescope.patterns.schema import Pattern
from codescope.patterns.namespace import namespace_id, resolve_overrides

_BUILTIN_DIR = Path(__file__).parent / "builtin"


def load_patterns(config: AppConfig) -> list[Pattern]:
    """Load and merge patterns from all configured libraries.

    Libraries are resolved in config order; later entries win on ID conflict.
    """
    all_patterns: dict[str, Pattern] = {}

    for lib_cfg in config.pattern_libraries:
        for pattern in _load_library(lib_cfg):
            pid = namespace_id(pattern.id, lib_cfg.name)
            pattern = pattern.model_copy(update={"id": pid, "library": lib_cfg.name})
            all_patterns[pid] = pattern  # later entries overwrite earlier ones

    overrides = [(o.override, o.with_) for o in config.pattern_overrides]
    resolved = resolve_overrides(list(all_patterns.values()), overrides)
    return [p for p in resolved if p.enabled]


def _load_library(lib_cfg: PatternLibraryConfig) -> list[Pattern]:
    if lib_cfg.source == "builtin":
        return _load_from_dir(_BUILTIN_DIR)

    source_path = Path(lib_cfg.source).expanduser()
    if source_path.exists():
        return _load_from_dir(source_path)

    # Git-cloned libraries land in ~/.codescope/libraries/<name>
    cloned = Path.home() / ".codescope" / "libraries" / lib_cfg.name
    if cloned.exists():
        return _load_from_dir(cloned)

    return []


def _load_from_dir(directory: Path) -> list[Pattern]:
    patterns: list[Pattern] = []
    for yaml_file in sorted(directory.glob("**/*.yaml")):
        patterns.extend(_parse_yaml_file(yaml_file))
    return patterns


def _parse_yaml_file(path: Path) -> list[Pattern]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    result = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            result.append(Pattern.model_validate(item))
        except Exception:
            pass
    return result
