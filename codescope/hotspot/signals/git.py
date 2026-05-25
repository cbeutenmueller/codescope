from __future__ import annotations
import math
from datetime import datetime, timezone
from pathlib import Path

try:
    from git import Repo, InvalidGitRepositoryError

    _GIT_AVAILABLE = True
except ImportError:
    _GIT_AVAILABLE = False


def get_git_signals(
    file_path: str,
    repo_root: Path,
    lookback_days: int = 180,
) -> tuple[float, float]:
    """Return (change_frequency, recency_weight) for a file.

    change_frequency: commits touching the file in the lookback window (raw count).
    recency_weight: decay based on days since last commit; 1.0 = today, → 0 as age → ∞.
    """
    if not _GIT_AVAILABLE:
        return 1.0, 1.0

    try:
        repo = Repo(repo_root, search_parent_directories=True)
    except (InvalidGitRepositoryError, Exception):
        return 1.0, 1.0

    rel_path = str(Path(file_path).relative_to(repo_root)).replace("\\", "/")
    now = datetime.now(tz=timezone.utc)
    cutoff = now.timestamp() - lookback_days * 86400

    commits = list(repo.iter_commits(paths=rel_path, since=f"{lookback_days} days ago"))
    change_frequency = float(len(commits))

    if not commits:
        return 0.0, 0.5

    last_ts = commits[0].committed_date
    age_days = max(0.0, (now.timestamp() - last_ts) / 86400)
    recency_weight = math.exp(-0.01 * age_days)  # half-life ≈ 69 days

    return change_frequency, recency_weight
