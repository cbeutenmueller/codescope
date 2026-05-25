from __future__ import annotations


def namespace_id(pattern_id: str, library_name: str) -> str:
    """Prefix a pattern ID with its library name if not already prefixed."""
    if "/" in pattern_id:
        return pattern_id
    return f"{library_name}/{pattern_id}"


def strip_namespace(namespaced_id: str) -> tuple[str, str]:
    """Split 'library/id' into (library, id). Returns ('', id) if no slash."""
    if "/" in namespaced_id:
        library, _, base_id = namespaced_id.partition("/")
        return library, base_id
    return "", namespaced_id


def resolve_overrides(
    patterns: list,
    overrides: list[tuple[str, str]],
) -> list:
    """Apply explicit overrides: replace pattern A with pattern B.

    overrides is a list of (override_id, replacement_id) tuples.
    """
    override_map = {src: dst for src, dst in overrides}
    id_index = {p.namespaced_id: p for p in patterns}
    result = []
    for pattern in patterns:
        pid = pattern.namespaced_id
        if pid in override_map:
            replacement_id = override_map[pid]
            if replacement_id in id_index:
                continue  # drop the overridden pattern; replacement stays
        result.append(pattern)
    return result
