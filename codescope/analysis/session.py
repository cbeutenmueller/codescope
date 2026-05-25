from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

from codescope.analysis.finding import AggregatedFinding, Finding, Location, Severity


@dataclass
class ReviewSession:
    session_id: str
    project_root: str
    started_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())
    hotspot_paths: list[str] = field(default_factory=list)
    aggregated_findings: list[AggregatedFinding] = field(default_factory=list)
    patterns_used: list[str] = field(default_factory=list)
    patterns_created: list[str] = field(default_factory=list)

    def save(self, sessions_dir: Path | None = None) -> Path:
        if sessions_dir is None:
            sessions_dir = Path.home() / ".codescope" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        path = sessions_dir / f"{self.session_id}.json"
        path.write_text(json.dumps(_serialise(self), indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, session_id: str, sessions_dir: Path | None = None) -> "ReviewSession":
        if sessions_dir is None:
            sessions_dir = Path.home() / ".codescope" / "sessions"
        path = sessions_dir / f"{session_id}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return _deserialise(data)


def _serialise(session: ReviewSession) -> dict:
    d = {
        "session_id": session.session_id,
        "project_root": session.project_root,
        "started_at": session.started_at,
        "hotspot_paths": session.hotspot_paths,
        "patterns_used": session.patterns_used,
        "patterns_created": session.patterns_created,
        "aggregated_findings": [_serialise_agg(af) for af in session.aggregated_findings],
    }
    return d


def _serialise_agg(af: AggregatedFinding) -> dict:
    return {
        "pattern_id": af.pattern_id,
        "pattern_name": af.pattern_name,
        "severity": af.severity.value,
        "instance_count": af.instance_count,
        "file_count": af.file_count,
        "fix_suggestion": af.fix_suggestion,
        "instances": [
            {
                "pattern_id": f.pattern_id,
                "pattern_name": f.pattern_name,
                "severity": f.severity.value,
                "file_path": f.location.file_path,
                "line_start": f.location.line_start,
                "line_end": f.location.line_end,
                "description": f.description,
                "fix_suggestion": f.fix_suggestion,
            }
            for f in af.instances
        ],
    }


def _deserialise(data: dict) -> ReviewSession:
    agg_findings = [_deserialise_agg(d) for d in data.get("aggregated_findings", [])]
    return ReviewSession(
        session_id=data["session_id"],
        project_root=data["project_root"],
        started_at=data.get("started_at", ""),
        hotspot_paths=data.get("hotspot_paths", []),
        aggregated_findings=agg_findings,
        patterns_used=data.get("patterns_used", []),
        patterns_created=data.get("patterns_created", []),
    )


def _deserialise_agg(d: dict) -> AggregatedFinding:
    instances = [
        Finding(
            pattern_id=i["pattern_id"],
            pattern_name=i["pattern_name"],
            severity=Severity(i["severity"]),
            location=Location(
                file_path=i["file_path"],
                line_start=i["line_start"],
                line_end=i["line_end"],
            ),
            description=i.get("description", ""),
            fix_suggestion=i.get("fix_suggestion", ""),
        )
        for i in d.get("instances", [])
    ]
    return AggregatedFinding(
        pattern_id=d["pattern_id"],
        pattern_name=d["pattern_name"],
        severity=Severity(d["severity"]),
        instance_count=d["instance_count"],
        file_count=d["file_count"],
        fix_suggestion=d.get("fix_suggestion", ""),
        instances=instances,
    )
