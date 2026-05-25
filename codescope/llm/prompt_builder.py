from __future__ import annotations
from codescope.patterns.schema import Pattern

_SYSTEM = """You are a senior software architect performing a code review.
Your task is to analyse the provided code for specific architectural and framework-semantic smells.
You must return a JSON object with a single key "findings" containing a list of findings.
Each finding must have:
  - pattern_id: string (the pattern ID from the list)
  - line_start: int
  - line_end: int
  - description: string (1-3 sentences explaining the specific instance)
  - severity: "low" | "medium" | "high" | "critical"

Only report genuine findings. Do not report false positives.
If there are no findings, return {"findings": []}.
"""


def build_analysis_prompt(
    file_path: str,
    code: str,
    patterns: list[Pattern],
    *,
    class_context: str = "",
) -> list[dict]:
    pattern_descriptions = _format_patterns(patterns)
    negative_examples = _format_negative_examples(patterns)

    user_content = f"""File: {file_path}

## Patterns to check
{pattern_descriptions}
{negative_examples}
## Code
```
{code}
```

Analyse the code for the patterns listed above. Return JSON."""

    if class_context:
        user_content = f"## Class context (summary)\n{class_context}\n\n" + user_content

    return [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": user_content},
    ]


def build_pattern_generation_prompt(description: str, language: str) -> list[dict]:
    system = """You are a code smell expert. Given a plain-language description of a code smell,
generate a YAML pattern entry for the CodeScope pattern library.
Return a valid YAML block (not JSON) with these fields:
id, name, category, language, severity, description, ast_hints, prompt_supplement, fix_template, tags.
The ast_hints must use only these keys:
  annotations_present, annotations_absent, method_call_pattern, parameter_type_present,
  parameter_type_absent, class_instantiation, min_param_count, max_param_count,
  contains_construct, scope, file_pattern, exclude_path.
"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Language: {language}\n\nSmell description:\n{description}"},
    ]


def _format_patterns(patterns: list[Pattern]) -> str:
    lines = []
    for p in patterns:
        lines.append(f"### {p.namespaced_id} — {p.name} [{p.severity}]")
        lines.append(p.description.strip())
        if p.prompt_supplement:
            lines.append(f"*Guidance:* {p.prompt_supplement.strip()}")
        lines.append("")
    return "\n".join(lines)


def _format_negative_examples(patterns: list[Pattern]) -> str:
    lines = []
    for p in patterns:
        if not p.negative_examples:
            continue
        lines.append(f"## Do NOT flag for {p.namespaced_id}:")
        for ex in p.negative_examples:
            lines.append(f"- {ex.reason}\n  ```\n  {ex.snippet.strip()}\n  ```")
    if lines:
        return "\n".join(lines) + "\n"
    return ""
