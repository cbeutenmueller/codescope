from __future__ import annotations
import pytest

from codescope.analysis.finding import Finding, Location, Severity, AggregatedFinding
from codescope.analysis.aggregator import deduplicate, aggregate, _merge_overlapping


def _finding(pattern_id: str, file: str, start: int, end: int, severity=Severity.MEDIUM) -> Finding:
    return Finding(
        pattern_id=pattern_id,
        pattern_name=f"Pattern {pattern_id}",
        severity=severity,
        location=Location(file_path=file, line_start=start, line_end=end),
        description=f"Finding at {start}-{end}",
    )


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


def test_no_overlap_keeps_both():
    f1 = _finding("p1", "A.java", 10, 20)
    f2 = _finding("p1", "A.java", 30, 40)
    result = deduplicate([f1, f2])
    assert len(result) == 2


def test_overlapping_findings_merged():
    f1 = _finding("p1", "A.java", 10, 25)
    f2 = _finding("p1", "A.java", 20, 35)
    result = deduplicate([f1, f2])
    assert len(result) == 1
    assert result[0].location.line_start == 10
    assert result[0].location.line_end == 35


def test_merge_keeps_higher_severity():
    f1 = _finding("p1", "A.java", 10, 20, Severity.LOW)
    f2 = _finding("p1", "A.java", 15, 25, Severity.HIGH)
    result = _merge_overlapping([f1, f2])
    assert result[0].severity == Severity.HIGH


def test_different_patterns_not_merged():
    f1 = _finding("p1", "A.java", 10, 20)
    f2 = _finding("p2", "A.java", 15, 25)
    result = deduplicate([f1, f2])
    assert len(result) == 2


def test_different_files_not_merged():
    f1 = _finding("p1", "A.java", 10, 20)
    f2 = _finding("p1", "B.java", 10, 20)
    result = deduplicate([f1, f2])
    assert len(result) == 2


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def test_aggregate_groups_by_pattern():
    findings = [
        _finding("p1", "A.java", 10, 20),
        _finding("p1", "B.java", 5, 15),
        _finding("p2", "A.java", 50, 60),
    ]
    result = aggregate(findings)
    assert len(result) == 2
    by_id = {af.pattern_id: af for af in result}
    assert by_id["p1"].instance_count == 2
    assert by_id["p2"].instance_count == 1


def test_aggregate_counts_distinct_files():
    findings = [
        _finding("p1", "A.java", 10, 20),
        _finding("p1", "A.java", 30, 40),
        _finding("p1", "B.java", 10, 20),
    ]
    result = aggregate(findings)
    assert result[0].file_count == 2


def test_aggregate_sorted_by_frequency_descending():
    findings = [
        _finding("p1", "A.java", 1, 5),
        _finding("p2", "A.java", 10, 15),
        _finding("p2", "B.java", 10, 15),
        _finding("p2", "C.java", 10, 15),
    ]
    result = aggregate(findings)
    assert result[0].pattern_id == "p2"
    assert result[0].instance_count == 3


def test_aggregate_applies_fix_map():
    findings = [_finding("p1", "A.java", 1, 5)]
    result = aggregate(findings, fix_map={"p1": "Use X instead of Y."})
    assert result[0].fix_suggestion == "Use X instead of Y."


def test_aggregate_empty_returns_empty():
    assert aggregate([]) == []


def test_severity_ordering():
    assert Severity.LOW < Severity.MEDIUM
    assert Severity.MEDIUM < Severity.HIGH
    assert Severity.HIGH < Severity.CRITICAL


# ---------------------------------------------------------------------------
# Severity comparison
# ---------------------------------------------------------------------------


def test_severity_gt():
    assert Severity.HIGH > Severity.LOW
    assert not (Severity.LOW > Severity.HIGH)
