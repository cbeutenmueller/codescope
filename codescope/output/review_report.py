from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from codescope.analysis.session import ReviewSession
from codescope.analysis.finding import AggregatedFinding


@dataclass
class ReportSummary:
    project_name: str
    file_count: int
    hotspot_count: int
    finding_count: int
    pattern_count: int
    top_finding: AggregatedFinding | None


def build_summary(session: ReviewSession) -> ReportSummary:
    top = session.aggregated_findings[0] if session.aggregated_findings else None
    return ReportSummary(
        project_name=Path(session.project_root).name if session.project_root else "unknown",
        file_count=len(
            {inst.location.file_path for af in session.aggregated_findings for inst in af.instances}
        ),
        hotspot_count=len(session.hotspot_paths),
        finding_count=sum(af.instance_count for af in session.aggregated_findings),
        pattern_count=len(session.aggregated_findings),
        top_finding=top,
    )
