from __future__ import annotations

import bisect
import math
from datetime import datetime, timedelta

from .models import RepositoryHistory, RepositoryRecord


def _percentiles(values: list[float]) -> list[float]:
    ordered = sorted(values)
    if not ordered:
        return []
    return [bisect.bisect_right(ordered, value) / len(ordered) for value in values]


def star_delta_7d(
    stars: int,
    history: RepositoryHistory | None,
    now: datetime,
) -> tuple[int, bool]:
    if history is None:
        return 0, True
    cutoff = now - timedelta(days=7)
    eligible = [point for point in history.points if point.checked_at <= cutoff]
    if not eligible:
        return 0, True
    baseline = max(eligible, key=lambda point: point.checked_at)
    return max(0, stars - baseline.stars), False


def apply_heat(
    repositories: list[RepositoryRecord],
    histories: dict[int, RepositoryHistory],
    now: datetime,
) -> None:
    if not repositories:
        return
    scales = _percentiles([math.log1p(repo.stars) for repo in repositories])
    deltas: list[int] = []
    cold: list[bool] = []
    for repo in repositories:
        delta, is_cold = star_delta_7d(repo.stars, histories.get(repo.repo_id), now)
        repo.stars_delta_7d = delta
        deltas.append(delta)
        cold.append(is_cold)
    trends = _percentiles([math.log1p(delta) for delta in deltas])
    for index, repo in enumerate(repositories):
        trend = scales[index] if cold[index] else trends[index]
        age_days = max(0.0, (now - repo.pushed_at).total_seconds() / 86400)
        activity = math.exp(-math.log(2) * age_days / 14)
        repo.heat = round(50 * scales[index] + 30 * trend + 20 * activity, 1)
