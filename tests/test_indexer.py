from __future__ import annotations
from pathlib import Path
import pytest

from codescope.indexer.walker import walk_files, detect_language
from codescope.indexer.languages.java import extract as java_extract
from codescope.indexer.languages.typescript import extract as ts_extract
from codescope.indexer.index import FileIndex, FileRecord, ClassRecord, MethodRecord

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Walker
# ---------------------------------------------------------------------------


def test_detect_language_java():
    assert detect_language("Foo.java") == "java"


def test_detect_language_typescript():
    assert detect_language("foo.ts") == "typescript"
    assert detect_language("foo.tsx") == "typescript"


def test_detect_language_unknown():
    assert detect_language("foo.py") is None


def test_walk_files_finds_java(tmp_path):
    (tmp_path / "A.java").write_text("class A {}")
    (tmp_path / "B.py").write_text("pass")
    files = walk_files(tmp_path, [], {"java"})
    assert any("A.java" in f for f in files)
    assert not any("B.py" in f for f in files)


def test_walk_files_excludes_globs(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "target").mkdir()
    (tmp_path / "src" / "Main.java").write_text("class Main {}")
    (tmp_path / "target" / "Generated.java").write_text("class Generated {}")
    files = walk_files(tmp_path, ["**/target/**"], {"java"})
    assert any("Main.java" in f for f in files)
    assert not any("Generated.java" in f for f in files)


# ---------------------------------------------------------------------------
# Java extractor
# ---------------------------------------------------------------------------


def test_java_extract_finds_class(java_order_service):
    record = java_extract(str(java_order_service))
    class_names = [c.name for c in record.classes]
    assert "OrderService" in class_names


def test_java_extract_finds_methods(java_order_service):
    record = java_extract(str(java_order_service))
    method_names = [m.name for m in record.methods]
    assert "getOrdersForUser" in method_names


def test_java_extract_finds_imports(java_order_service):
    record = java_extract(str(java_order_service))
    assert any("springframework" in imp for imp in record.imports)


def test_java_extract_finds_annotations(java_order_service):
    record = java_extract(str(java_order_service))
    all_annotations = [a for m in record.methods for a in m.annotations]
    assert "Transactional" in all_annotations


# ---------------------------------------------------------------------------
# TypeScript extractor
# ---------------------------------------------------------------------------


def test_ts_extract_finds_class(angular_items_component):
    record = ts_extract(str(angular_items_component))
    class_names = [c.name for c in record.classes]
    assert "ItemsComponent" in class_names


def test_ts_extract_finds_decorators(angular_items_component):
    record = ts_extract(str(angular_items_component))
    all_decorators = [a for c in record.classes for a in c.annotations]
    assert "Component" in all_decorators


def test_ts_extract_finds_imports(angular_items_component):
    record = ts_extract(str(angular_items_component))
    assert any("angular/core" in imp for imp in record.imports)


# ---------------------------------------------------------------------------
# SQLite index
# ---------------------------------------------------------------------------


def test_file_index_upsert_and_query(tmp_path):
    idx = FileIndex(tmp_path / "test.db")
    record = FileRecord(
        path="/app/Foo.java",
        language="java",
        classes=[ClassRecord(name="Foo", annotations=["Service"])],
        methods=[MethodRecord(name="bar", class_name="Foo", annotations=["Transactional"])],
        imports=["org.springframework.stereotype.Service"],
    )
    idx.upsert(record)
    assert idx.is_indexed("/app/Foo.java")
    with_ann = idx.files_with_annotation("Transactional")
    assert "/app/Foo.java" in with_ann
    idx.close()


def test_file_index_upsert_replaces_stale(tmp_path):
    idx = FileIndex(tmp_path / "test.db")
    r1 = FileRecord(path="/app/Foo.java", language="java", imports=["org.old.Import"])
    r2 = FileRecord(path="/app/Foo.java", language="java", imports=["org.new.Import"])
    idx.upsert(r1)
    idx.upsert(r2)
    cur = idx._conn.execute("SELECT import_path FROM imports WHERE file_path = '/app/Foo.java'")
    imports = [row[0] for row in cur]
    assert "org.new.Import" in imports
    assert "org.old.Import" not in imports
    idx.close()
