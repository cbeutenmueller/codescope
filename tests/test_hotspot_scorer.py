from __future__ import annotations
import math
import pytest

from codescope.hotspot.scorer import FileSignals, compute_score
from codescope.hotspot.ranker import rank_files
from codescope.config import AppConfig, HotspotWeights


def _weights() -> HotspotWeights:
    return HotspotWeights(change_frequency=1.0, complexity=0.8, dependencies=0.6, recency=0.4)


def test_compute_score_basic():
    signals = FileSignals(
        path="Foo.java",
        change_frequency=10.0,
        cyclomatic_complexity=5.0,
        dependency_count=3.0,
        recency_weight=0.9,
    )
    result = compute_score(signals, _weights())
    assert result.path == "Foo.java"
    assert result.score > 0


def test_zero_change_frequency_gives_zero_score():
    signals = FileSignals(
        path="Foo.java",
        change_frequency=0.0,
        cyclomatic_complexity=20.0,
        dependency_count=10.0,
        recency_weight=1.0,
    )
    result = compute_score(signals, _weights())
    assert result.score == 0.0


def test_higher_complexity_gives_higher_score():
    base = FileSignals(
        "A.java",
        change_frequency=5.0,
        cyclomatic_complexity=2.0,
        dependency_count=2.0,
        recency_weight=1.0,
    )
    high = FileSignals(
        "B.java",
        change_frequency=5.0,
        cyclomatic_complexity=20.0,
        dependency_count=2.0,
        recency_weight=1.0,
    )
    w = _weights()
    assert compute_score(high, w).score > compute_score(base, w).score


def test_higher_recency_gives_higher_score():
    old = FileSignals(
        "A.java",
        change_frequency=5.0,
        cyclomatic_complexity=5.0,
        dependency_count=2.0,
        recency_weight=0.1,
    )
    recent = FileSignals(
        "B.java",
        change_frequency=5.0,
        cyclomatic_complexity=5.0,
        dependency_count=2.0,
        recency_weight=0.9,
    )
    w = _weights()
    assert compute_score(recent, w).score > compute_score(old, w).score


def test_rank_files_returns_top_n(tmp_path):
    # Create a few dummy files
    for name in ("A.java", "B.java", "C.java", "D.java", "E.java"):
        (tmp_path / name).write_text("public class Foo {}", encoding="utf-8")

    config = AppConfig()
    config.review.top_n_hotspots = 3

    results = rank_files(
        [str(tmp_path / n) for n in ("A.java", "B.java", "C.java", "D.java", "E.java")],
        tmp_path,
        config,
    )
    assert len(results) <= 3


def test_rank_files_sorted_descending(tmp_path):
    (tmp_path / "A.java").write_text("class A {}", encoding="utf-8")
    (tmp_path / "B.java").write_text("class B {}", encoding="utf-8")
    config = AppConfig()
    config.review.top_n_hotspots = 10

    results = rank_files([str(tmp_path / "A.java"), str(tmp_path / "B.java")], tmp_path, config)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
