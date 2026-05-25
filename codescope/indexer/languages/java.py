from __future__ import annotations
import re
from pathlib import Path

from codescope.indexer.index import FileRecord, ClassRecord, MethodRecord

_ANNOTATION = re.compile(r"@(\w+)")
_CLASS_DECL = re.compile(r"(?:public|private|protected|abstract|final|static|\s)*class\s+(\w+)")
_METHOD_DECL = re.compile(
    r"(?:public|private|protected|static|final|synchronized|\s)+"
    r"(?:\w+(?:<[^>]*>)?)\s+(\w+)\s*\(([^)]*)\)"
)
_IMPORT = re.compile(r"^\s*import\s+([\w.]+)\s*;", re.MULTILINE)
_PARAM_TYPE = re.compile(r"(?:@\w+\s+)?(?:final\s+)?(\w+(?:<[^>]*>)?)\s+\w+")


def extract(file_path: str) -> FileRecord:
    try:
        text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return FileRecord(path=file_path, language="java")

    classes: list[ClassRecord] = []
    methods: list[MethodRecord] = []
    imports: list[str] = []

    lines = text.splitlines()
    pending_annotations: list[str] = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Collect annotations on this line
        anns = _ANNOTATION.findall(stripped)
        if stripped.startswith("@"):
            pending_annotations.extend(anns)
            continue

        # Class declaration
        cls_match = _CLASS_DECL.search(stripped)
        if cls_match and ("class " in stripped):
            classes.append(
                ClassRecord(
                    name=cls_match.group(1),
                    annotations=list(pending_annotations),
                )
            )
            pending_annotations = []
            continue

        # Method declaration
        m_match = _METHOD_DECL.search(stripped)
        if m_match and "(" in stripped and not stripped.startswith("//"):
            params_raw = m_match.group(2)
            param_types = _parse_param_types(params_raw)
            class_name = classes[-1].name if classes else ""
            methods.append(
                MethodRecord(
                    name=m_match.group(1),
                    class_name=class_name,
                    annotations=list(pending_annotations),
                    param_types=param_types,
                    line_start=i + 1,
                    line_end=i + 1,
                )
            )
            pending_annotations = []
            continue

        if not stripped.startswith("@"):
            pending_annotations = []

    for m in _IMPORT.finditer(text):
        imports.append(m.group(1))

    return FileRecord(
        path=file_path,
        language="java",
        classes=classes,
        methods=methods,
        imports=imports,
    )


def _parse_param_types(params_raw: str) -> list[str]:
    if not params_raw.strip():
        return []
    types = []
    for param in params_raw.split(","):
        param = param.strip()
        m = _PARAM_TYPE.match(param)
        if m:
            types.append(m.group(1))
    return types
