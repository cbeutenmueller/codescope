from __future__ import annotations
import re
from pathlib import Path

_JAVA_IMPORT = re.compile(r"^\s*import\s+[\w.]+;", re.MULTILINE)
_JAVA_AUTOWIRED = re.compile(r"@(Autowired|Inject|Resource)\b")
_TS_IMPORT = re.compile(r"^\s*import\s+.+?\s+from\s+['\"]", re.MULTILINE)
_TS_CONSTRUCTOR_INJECT = re.compile(r"constructor\s*\([^)]{30,}\)")


def get_coupling_signals(file_path: str) -> float:
    """Return a coupling score: import count + DI injection count."""
    try:
        text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0.0

    path = file_path.lower()
    if path.endswith(".java"):
        imports = len(_JAVA_IMPORT.findall(text))
        di_params = len(_JAVA_AUTOWIRED.findall(text))
        return float(imports + di_params)
    elif path.endswith((".ts", ".tsx")):
        imports = len(_TS_IMPORT.findall(text))
        return float(imports)

    return 0.0
