from __future__ import annotations
from pathlib import Path

from codescope.indexer.index import FileRecord
from codescope.indexer.walker import detect_language


class AstExtractor:
    """Dispatches to language-specific extractors."""

    def extract(self, file_path: str) -> FileRecord | None:
        lang = detect_language(file_path)
        if lang is None:
            return None

        if lang == "java":
            from codescope.indexer.languages.java import extract

            return extract(file_path)
        elif lang == "typescript":
            from codescope.indexer.languages.typescript import extract

            return extract(file_path)

        return None
