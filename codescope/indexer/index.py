from __future__ import annotations
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    path TEXT PRIMARY KEY,
    language TEXT,
    indexed_at REAL,
    git_hash TEXT
);
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    name TEXT NOT NULL,
    annotations TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY (file_path) REFERENCES files(path) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    class_name TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL,
    annotations TEXT NOT NULL DEFAULT '[]',
    param_types TEXT NOT NULL DEFAULT '[]',
    param_count INTEGER NOT NULL DEFAULT 0,
    line_start INTEGER NOT NULL DEFAULT 0,
    line_end INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (file_path) REFERENCES files(path) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    import_path TEXT NOT NULL,
    FOREIGN KEY (file_path) REFERENCES files(path) ON DELETE CASCADE
);
"""


@dataclass
class MethodRecord:
    name: str
    class_name: str = ""
    annotations: list[str] = field(default_factory=list)
    param_types: list[str] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0


@dataclass
class ClassRecord:
    name: str
    annotations: list[str] = field(default_factory=list)


@dataclass
class FileRecord:
    path: str
    language: str
    classes: list[ClassRecord] = field(default_factory=list)
    methods: list[MethodRecord] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)


class FileIndex:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def upsert(self, record: FileRecord) -> None:
        c = self._conn
        import time

        c.execute(
            "INSERT OR REPLACE INTO files (path, language, indexed_at) VALUES (?, ?, ?)",
            (record.path, record.language, time.time()),
        )
        c.execute("DELETE FROM classes WHERE file_path = ?", (record.path,))
        c.execute("DELETE FROM methods WHERE file_path = ?", (record.path,))
        c.execute("DELETE FROM imports WHERE file_path = ?", (record.path,))

        for cls in record.classes:
            c.execute(
                "INSERT INTO classes (file_path, name, annotations) VALUES (?, ?, ?)",
                (record.path, cls.name, json.dumps(cls.annotations)),
            )
        for m in record.methods:
            c.execute(
                "INSERT INTO methods (file_path, class_name, name, annotations, param_types, param_count, line_start, line_end) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record.path,
                    m.class_name,
                    m.name,
                    json.dumps(m.annotations),
                    json.dumps(m.param_types),
                    len(m.param_types),
                    m.line_start,
                    m.line_end,
                ),
            )
        for imp in record.imports:
            c.execute(
                "INSERT INTO imports (file_path, import_path) VALUES (?, ?)",
                (record.path, imp),
            )
        c.commit()

    def files_with_annotation(self, annotation: str) -> list[str]:
        cur = self._conn.execute(
            "SELECT DISTINCT file_path FROM methods WHERE annotations LIKE ?",
            (f"%{annotation}%",),
        )
        return [row[0] for row in cur]

    def is_indexed(self, path: str) -> bool:
        cur = self._conn.execute("SELECT 1 FROM files WHERE path = ?", (path,))
        return cur.fetchone() is not None

    def close(self) -> None:
        self._conn.close()
