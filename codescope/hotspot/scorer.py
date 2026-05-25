from __future__ import annotations
import math
from dataclasses import dataclass

from codescope.config import HotspotWeights


@dataclass
class FileSignals:
    path: str
    change_frequency: float = 0.0
    cyclomatic_complexity: float = 1.0
    dependency_count: float = 0.0
    recency_weight: float = 1.0
    loc: int = 0


@dataclass
class HotspotScore:
    path: str
    score: float
    signals: FileSignals


def compute_score(signals: FileSignals, weights: HotspotWeights) -> HotspotScore:
    """
    hotspot_score = (change_frequency * w_cf) * log(1 + complexity * w_cx)
                  * log(1 + deps * w_d) * (recency * w_r)

    Each signal is scaled by its weight before combining multiplicatively.
    Files with zero change_frequency score 0 — never changed = not a hot spot.
    """
    freq = signals.change_frequency * weights.change_frequency
    comp = math.log1p(signals.cyclomatic_complexity * weights.complexity)
    deps = math.log1p(signals.dependency_count * weights.dependencies)
    recency = signals.recency_weight * weights.recency

    score = freq * comp * deps * recency
    return HotspotScore(path=signals.path, score=score, signals=signals)
