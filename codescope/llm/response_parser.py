from __future__ import annotations
import json
import re

from codescope.analysis.finding import Finding, Location, Severity


def parse_findings(
    response: str,
    file_path: str,
    pattern_name_map: dict[str, str],
) -> list[Finding]:
    """Extract findings from a raw LLM JSON response string."""
    data = _extract_json(response)
    raw_findings = data.get("findings", [])
    if not isinstance(raw_findings, list):
        return []

    results = []
    for item in raw_findings:
        if not isinstance(item, dict):
            continue
        try:
            results.append(_parse_one(item, file_path, pattern_name_map))
        except (KeyError, ValueError):
            pass
    return results


def _parse_one(item: dict, file_path: str, pattern_name_map: dict[str, str]) -> Finding:
    pattern_id = str(item["pattern_id"])
    pattern_name = pattern_name_map.get(pattern_id, pattern_id)
    line_start = int(item.get("line_start", 1))
    line_end = int(item.get("line_end", line_start))

    raw_severity = str(item.get("severity", "medium")).lower()
    try:
        severity = Severity(raw_severity)
    except ValueError:
        severity = Severity.MEDIUM

    return Finding(
        pattern_id=pattern_id,
        pattern_name=pattern_name,
        severity=severity,
        location=Location(
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
        ),
        description=str(item.get("description", "")),
    )


def _extract_json(text: str) -> dict:
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find JSON block inside markdown code fences
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Find outermost { ... }
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return {"findings": []}
