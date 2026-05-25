from __future__ import annotations
from codescope.analysis.finding import Finding, AggregatedFinding, Location, Severity


def deduplicate(findings: list[Finding]) -> list[Finding]:
    """Stage 1: merge overlapping instances of the same pattern within a file."""
    by_key: dict[tuple[str, str], list[Finding]] = {}
    for f in findings:
        key = (f.pattern_id, f.location.file_path)
        by_key.setdefault(key, []).append(f)

    result = []
    for group in by_key.values():
        result.extend(_merge_overlapping(group))
    return result


def aggregate(
    findings: list[Finding], fix_map: dict[str, str] | None = None
) -> list[AggregatedFinding]:
    """Stage 2: group by pattern_id, count instances, rank by frequency."""
    deduped = deduplicate(findings)
    by_pattern: dict[str, list[Finding]] = {}
    for f in deduped:
        by_pattern.setdefault(f.pattern_id, []).append(f)

    result = []
    for pid, instances in by_pattern.items():
        file_count = len({f.location.file_path for f in instances})
        max_sev = max((f.severity for f in instances), key=lambda s: list(Severity).index(s))
        fix = (fix_map or {}).get(pid, instances[0].fix_suggestion if instances else "")
        result.append(
            AggregatedFinding(
                pattern_id=pid,
                pattern_name=instances[0].pattern_name,
                severity=max_sev,
                instance_count=len(instances),
                file_count=file_count,
                instances=instances,
                fix_suggestion=fix,
            )
        )

    result.sort(key=lambda a: a.frequency, reverse=True)
    return result


def _merge_overlapping(findings: list[Finding]) -> list[Finding]:
    if not findings:
        return []
    sorted_f = sorted(findings, key=lambda f: f.location.line_start)
    merged = [sorted_f[0]]
    for current in sorted_f[1:]:
        last = merged[-1]
        if last.location.overlaps(current.location):
            # Keep higher severity; expand line range
            severity = current.severity if current.severity > last.severity else last.severity
            new_loc = Location(
                file_path=last.location.file_path,
                line_start=min(last.location.line_start, current.location.line_start),
                line_end=max(last.location.line_end, current.location.line_end),
            )
            desc = last.description
            if current.description and current.description != last.description:
                desc = f"{last.description} / {current.description}"
            merged[-1] = Finding(
                pattern_id=last.pattern_id,
                pattern_name=last.pattern_name,
                severity=severity,
                location=new_loc,
                description=desc,
                fix_suggestion=last.fix_suggestion or current.fix_suggestion,
                snippet=last.snippet,
            )
        else:
            merged.append(current)
    return merged
