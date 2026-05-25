from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path

from codescope.output.base import BaseReporter
from codescope.output.review_report import build_summary
from codescope.analysis.session import ReviewSession
from codescope.analysis.finding import AggregatedFinding


class MarkdownReporter(BaseReporter):
    def render(self, session: ReviewSession) -> str:
        summary = build_summary(session)
        date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        lines: list[str] = []

        lines += [
            f"# Codebase Review: {summary.project_name}",
            f"Generated: {date}  ·  Hot spots analysed: {summary.hotspot_count}",
            "",
        ]

        # Executive summary
        lines += ["## Executive Summary", ""]
        if not session.aggregated_findings:
            lines.append("No findings were identified in the analysed hot spots.")
        else:
            top = summary.top_finding
            lines.append(
                f"{summary.pattern_count} systematic issue(s) found across "
                f"{summary.hotspot_count} high-risk files."
            )
            if top:
                lines.append(
                    f"Most frequent: **{top.pattern_name}** "
                    f"({top.instance_count} instance{'s' if top.instance_count > 1 else ''} "
                    f"in {top.file_count} file{'s' if top.file_count > 1 else ''})."
                )
        lines.append("")

        # Systematic findings
        if session.aggregated_findings:
            lines += ["## Systematic Findings", ""]
            for rank, af in enumerate(session.aggregated_findings, 1):
                lines += _render_finding(rank, af)

        # Hot spot table
        if session.hotspot_paths:
            lines += [
                "## Hot Spot Files Analysed",
                "",
                "| # | File |",
                "|---|---|",
            ]
            for i, path in enumerate(session.hotspot_paths, 1):
                rel = _rel_path(path, session.project_root)
                lines.append(f"| {i} | `{rel}` |")
            lines.append("")

        # Pattern library section
        if session.patterns_used:
            lines += [
                "## Pattern Library",
                "",
                f"{len(session.patterns_used)} pattern(s) used in this review.",
            ]
            if session.patterns_created:
                lines.append(
                    f"{len(session.patterns_created)} new pattern(s) created: "
                    + ", ".join(f"`{p}`" for p in session.patterns_created)
                )
            lines.append("")

        return "\n".join(lines)


def _render_finding(rank: int, af: AggregatedFinding) -> list[str]:
    lines = [
        f"### {rank}. {af.pattern_name}  ·  "
        f"{af.instance_count} instance{'s' if af.instance_count > 1 else ''}  ·  "
        f"{af.file_count} file{'s' if af.file_count > 1 else ''}  ·  "
        f"{af.severity.value}",
        "",
        f"**Pattern:** `{af.pattern_id}`",
        "",
    ]

    if af.instances:
        lines.append("**Instances:**")
        lines.append("")
        for inst in af.instances:
            rel = Path(inst.location.file_path).name
            lines.append(f"- `{rel}:{inst.location.line_start}` — {inst.description}")
        lines.append("")

    if af.fix_suggestion:
        lines += [
            "**Suggested fix:**",
            "",
            f"```",
            af.fix_suggestion.strip(),
            "```",
            "",
        ]

    return lines


def _rel_path(path: str, root: str) -> str:
    try:
        return str(Path(path).relative_to(Path(root)))
    except ValueError:
        return path
