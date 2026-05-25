from __future__ import annotations
import json
import pytest

from codescope.llm.response_parser import parse_findings, _extract_json
from codescope.analysis.finding import Severity

_NAME_MAP = {
    "builtin/spring-data-1": "Query Inside Loop",
    "builtin/ng-rxjs-1": "Subscription Leak",
}


def test_parse_clean_json():
    raw = json.dumps(
        {
            "findings": [
                {
                    "pattern_id": "builtin/spring-data-1",
                    "line_start": 20,
                    "line_end": 25,
                    "description": "Repository call inside stream map",
                    "severity": "high",
                }
            ]
        }
    )
    findings = parse_findings(raw, "OrderService.java", _NAME_MAP)
    assert len(findings) == 1
    assert findings[0].severity == Severity.HIGH
    assert findings[0].location.line_start == 20
    assert findings[0].pattern_name == "Query Inside Loop"


def test_parse_empty_findings():
    raw = json.dumps({"findings": []})
    findings = parse_findings(raw, "Foo.java", _NAME_MAP)
    assert findings == []


def test_parse_json_in_markdown_fence():
    raw = '```json\n{"findings": [{"pattern_id": "builtin/ng-rxjs-1", "line_start": 5, "line_end": 10, "description": "leak", "severity": "high"}]}\n```'
    findings = parse_findings(raw, "items.ts", _NAME_MAP)
    assert len(findings) == 1


def test_parse_malformed_json_returns_empty():
    findings = parse_findings("not json at all", "Foo.java", _NAME_MAP)
    assert findings == []


def test_parse_unknown_severity_defaults_to_medium():
    raw = json.dumps(
        {
            "findings": [
                {
                    "pattern_id": "builtin/spring-data-1",
                    "line_start": 1,
                    "line_end": 2,
                    "description": "x",
                    "severity": "catastrophic",
                }
            ]
        }
    )
    findings = parse_findings(raw, "Foo.java", _NAME_MAP)
    assert findings[0].severity == Severity.MEDIUM


def test_extract_json_from_bare_object():
    text = 'Some preamble {"findings": []} trailing text'
    result = _extract_json(text)
    assert result == {"findings": []}


def test_parse_multiple_findings():
    raw = json.dumps(
        {
            "findings": [
                {
                    "pattern_id": "builtin/spring-data-1",
                    "line_start": 10,
                    "line_end": 15,
                    "description": "a",
                    "severity": "high",
                },
                {
                    "pattern_id": "builtin/ng-rxjs-1",
                    "line_start": 30,
                    "line_end": 35,
                    "description": "b",
                    "severity": "medium",
                },
            ]
        }
    )
    findings = parse_findings(raw, "Foo.java", _NAME_MAP)
    assert len(findings) == 2
