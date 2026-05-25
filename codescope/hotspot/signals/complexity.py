from __future__ import annotations
from pathlib import Path

try:
    import lizard

    _LIZARD_AVAILABLE = True
except ImportError:
    _LIZARD_AVAILABLE = False


def get_complexity(file_path: str) -> float:
    """Return the average cyclomatic complexity for the file.

    Falls back to 1.0 if lizard is unavailable or the file is unparseable.
    """
    if not _LIZARD_AVAILABLE:
        return 1.0

    try:
        result = lizard.analyze_file(file_path)
        if not result.function_list:
            return 1.0
        total = sum(fn.cyclomatic_complexity for fn in result.function_list)
        return total / len(result.function_list)
    except Exception:
        return 1.0


def get_max_complexity(file_path: str) -> float:
    """Return the maximum cyclomatic complexity across all functions in the file."""
    if not _LIZARD_AVAILABLE:
        return 1.0

    try:
        result = lizard.analyze_file(file_path)
        if not result.function_list:
            return 1.0
        return max(fn.cyclomatic_complexity for fn in result.function_list)
    except Exception:
        return 1.0
