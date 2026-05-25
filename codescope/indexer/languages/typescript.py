from __future__ import annotations
import re
from pathlib import Path

from codescope.indexer.index import FileRecord, ClassRecord, MethodRecord

_DECORATOR = re.compile(r"@(\w+)")
_CLASS_DECL = re.compile(r"(?:export\s+)?(?:abstract\s+)?class\s+(\w+)")
_METHOD_DECL = re.compile(
    r"(?:public|private|protected|async|static|\s)*(\w+)\s*\(([^)]*)\)\s*(?::\s*\S+)?\s*\{"
)
_IMPORT = re.compile(r"""^\s*import\s+.+?\s+from\s+['"]([^'"]+)['"]""", re.MULTILINE)


def extract(file_path: str) -> FileRecord:
    try:
        text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return FileRecord(path=file_path, language="typescript")

    classes: list[ClassRecord] = []
    methods: list[MethodRecord] = []
    imports: list[str] = []

    lines = text.splitlines()
    pending_decorators: list[str] = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("@"):
            decs = _DECORATOR.findall(stripped)
            pending_decorators.extend(decs)
            continue

        cls_match = _CLASS_DECL.search(stripped)
        if cls_match and "class " in stripped:
            classes.append(
                ClassRecord(
                    name=cls_match.group(1),
                    annotations=list(pending_decorators),
                )
            )
            pending_decorators = []
            continue

        m_match = _METHOD_DECL.match(stripped)
        if m_match and not stripped.startswith("//"):
            class_name = classes[-1].name if classes else ""
            methods.append(
                MethodRecord(
                    name=m_match.group(1),
                    class_name=class_name,
                    annotations=list(pending_decorators),
                    param_types=[],
                    line_start=i + 1,
                    line_end=i + 1,
                )
            )
            pending_decorators = []
            continue

        # Only clear accumulated decorators on blank lines — multi-line decorator
        # bodies like @Component({...}) have non-@ content between decorator and class.
        if not stripped:
            pending_decorators = []

    for m in _IMPORT.finditer(text):
        imports.append(m.group(1))

    return FileRecord(
        path=file_path,
        language="typescript",
        classes=classes,
        methods=methods,
        imports=imports,
    )
