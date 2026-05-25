from __future__ import annotations
from pathlib import Path

from codescope.indexer.index import FileIndex
from codescope.indexer.ast_extractor import AstExtractor
from codescope.indexer.walker import walk_files
from codescope.config import AppConfig


def build_index(project_root: Path, config: AppConfig) -> FileIndex:
    """Build (or incrementally update) the file index."""
    db_path = project_root / config.index.path / "codescope.db"
    index = FileIndex(db_path)
    extractor = AstExtractor()

    languages = set(config.index.languages)
    files = walk_files(project_root, config.index.exclude_globs, languages)

    for file_path in files:
        if config.index.incremental and index.is_indexed(file_path):
            continue
        record = extractor.extract(file_path)
        if record:
            index.upsert(record)

    return index
