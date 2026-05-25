from __future__ import annotations
import pytest

from codescope.analysis.session import ReviewSession
from codescope.analysis.finding import AggregatedFinding, Finding, Location, Severity
from codescope.output.markdown import MarkdownReporter
from codescope.output.review_report import build_summary


def _session_with_findings() -> ReviewSession:
    f1 = Finding(
        pattern_id="builtin/spring-data-1",
        pattern_name="Query Inside Loop",
        severity=Severity.HIGH,
        location=Location("OrderService.java", 20, 25),
        description="Repository call inside stream map.",
    )
    af = AggregatedFinding(
        pattern_id="builtin/spring-data-1",
        pattern_name="Query Inside Loop",
        severity=Severity.HIGH,
        instance_count=3,
        file_count=2,
        instances=[f1],
        fix_suggestion="Use findAllById().",
    )
    return ReviewSession(
        session_id="test-001",
        project_root="/project/my-service",
        hotspot_paths=["OrderService.java", "PaymentService.java"],
        aggregated_findings=[af],
        patterns_used=["builtin/spring-data-1"],
    )


def test_markdown_reporter_produces_heading():
    session = _session_with_findings()
    report = MarkdownReporter().render(session)
    assert "# Codebase Review" in report


def test_markdown_reporter_includes_pattern_name():
    session = _session_with_findings()
    report = MarkdownReporter().render(session)
    assert "Query Inside Loop" in report


def test_markdown_reporter_includes_fix():
    session = _session_with_findings()
    report = MarkdownReporter().render(session)
    assert "findAllById" in report


def test_markdown_reporter_includes_hotspot_table():
    session = _session_with_findings()
    report = MarkdownReporter().render(session)
    assert "OrderService.java" in report


def test_markdown_reporter_empty_session():
    session = ReviewSession(
        session_id="empty",
        project_root="/project/empty",
        hotspot_paths=[],
        aggregated_findings=[],
        patterns_used=[],
    )
    report = MarkdownReporter().render(session)
    assert "No findings" in report


def test_build_summary_counts_correctly():
    session = _session_with_findings()
    summary = build_summary(session)
    assert summary.hotspot_count == 2
    assert summary.pattern_count == 1
    assert summary.top_finding is not None
    assert summary.top_finding.pattern_name == "Query Inside Loop"
