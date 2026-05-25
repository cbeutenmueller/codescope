from __future__ import annotations
from pathlib import Path

from codescope.config import AppConfig
from codescope.hotspot.scorer import FileSignals, HotspotScore, compute_score
from codescope.hotspot.signals.git import get_git_signals
from codescope.hotspot.signals.complexity import get_complexity
from codescope.hotspot.signals.size import get_size_signals
from codescope.hotspot.signals.coupling import get_coupling_signals


def rank_files(
    file_paths: list[str],
    repo_root: Path,
    config: AppConfig,
) -> list[HotspotScore]:
    """Compute and rank hot spot scores for all given files."""
    scores: list[HotspotScore] = []

    for path in file_paths:
        freq, recency = get_git_signals(path, repo_root)
        complexity = get_complexity(path)
        size = get_size_signals(path)
        coupling = get_coupling_signals(path)

        signals = FileSignals(
            path=path,
            change_frequency=freq,
            cyclomatic_complexity=complexity,
            dependency_count=coupling,
            recency_weight=recency,
            loc=size.loc,
        )
        scores.append(compute_score(signals, config.review.hotspot_weights))

    scores.sort(key=lambda s: s.score, reverse=True)
    top_n = config.review.top_n_hotspots
    return scores[:top_n]
