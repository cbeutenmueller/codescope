from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    def __gt__(self, other: "Severity") -> bool:
        order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        return order.index(self) > order.index(other)

    def __lt__(self, other: "Severity") -> bool:
        order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        return order.index(self) < order.index(other)


@dataclass
class Location:
    file_path: str
    line_start: int
    line_end: int

    def overlaps(self, other: "Location") -> bool:
        return (
            self.file_path == other.file_path
            and self.line_start <= other.line_end
            and other.line_start <= self.line_end
        )


@dataclass
class Finding:
    pattern_id: str
    pattern_name: str
    severity: Severity
    location: Location
    description: str
    fix_suggestion: str = ""
    snippet: str = ""
    false_positive: bool = False


@dataclass
class AggregatedFinding:
    pattern_id: str
    pattern_name: str
    severity: Severity
    instance_count: int
    file_count: int
    instances: list[Finding] = field(default_factory=list)
    fix_suggestion: str = ""

    @property
    def frequency(self) -> int:
        return self.instance_count
