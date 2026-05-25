from __future__ import annotations
import fnmatch
from pathlib import Path

_LANGUAGE_EXTENSIONS: dict[str, tuple[str, ...]] = {
    "java": (".java",),
    "typescript": (".ts", ".tsx"),
}


def walk_files(
    root: Path,
    exclude_globs: list[str],
    languages: set[str] | None = None,
) -> list[str]:
    """Return absolute paths of all source files under root, respecting exclusions."""
    extensions: set[str] = set()
    if languages:
        for lang in languages:
            extensions.update(_LANGUAGE_EXTENSIONS.get(lang, ()))
    else:
        for exts in _LANGUAGE_EXTENSIONS.values():
            extensions.update(exts)

    result: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if extensions and path.suffix not in extensions:
            continue
        rel = path.relative_to(root).as_posix()
        if _is_excluded(rel, exclude_globs):
            continue
        result.append(str(path))

    return result


def _is_excluded(rel_path: str, globs: list[str]) -> bool:
    for pattern in globs:
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        # Also match against individual path segments
        for part in Path(rel_path).parts:
            if fnmatch.fnmatch(part, pattern.strip("*/")):
                return True
    return False


def detect_language(file_path: str) -> str | None:
    suffix = Path(file_path).suffix.lower()
    for lang, exts in _LANGUAGE_EXTENSIONS.items():
        if suffix in exts:
            return lang
    return None
