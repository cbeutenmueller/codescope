from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SizeSignals:
    loc: int = 0
    non_blank_loc: int = 0


def get_size_signals(file_path: str) -> SizeSignals:
    try:
        text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return SizeSignals()

    lines = text.splitlines()
    loc = len(lines)
    non_blank = sum(1 for l in lines if l.strip())
    return SizeSignals(loc=loc, non_blank_loc=non_blank)
