from __future__ import annotations

from datetime import timedelta

from free_agent_md.classify import classify_repository
from free_agent_md.heat import apply_heat
from free_agent_md.models import HistoryPoint, RepositoryHistory
from free_agent_md.settings import CategoryRule

from conftest import make_repo


def test_classification_override_and_ambiguous_fallback() -> None:
    rules = [
        CategoryRule(name="AI & ML", topics=["ai"]),
        CategoryRule(name="Developer Tools", topics=["cli"]),
    ]
    assert (
        classify_repository("acme/x", None, None, ["ai"], rules, {"acme/x": "Web & Apps"})
        == "Web & Apps"
    )
    assert classify_repository("acme/x", None, None, ["ai", "cli"], rules, {}) == "Other"
    assert classify_repository("acme/x", "plain project", "Python", [], rules, {}) == "Other"


def test_heat_uses_scale_for_cold_start_and_history_for_trend(now) -> None:
    cold = make_repo(now, repo_id=1, stars=100)
    trending = make_repo(now, repo_id=2, full_name="acme/trending", stars=1000)
    histories = {
        2: RepositoryHistory(
            repo_id=2,
            full_name="acme/trending",
            points=[
                HistoryPoint(
                    checked_at=now - timedelta(days=8),
                    stars=900,
                    pushed_at=now - timedelta(days=1),
                    commit_sha="a" * 40,
                )
            ],
        )
    }
    apply_heat([cold, trending], histories, now)
    assert cold.stars_delta_7d == 0
    assert cold.heat == 60.0
    assert trending.stars_delta_7d == 100
    assert trending.heat == 100.0
