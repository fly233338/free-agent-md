from __future__ import annotations

from free_agent_md.models import Catalog, RunStats
from free_agent_md.render import render_readme
from free_agent_md.settings import CategoryRule, Settings
from free_agent_md.validate import validate_catalog

from conftest import make_repo


def _settings() -> Settings:
    return Settings(
        repository="acme/index",
        scan_limit=300,
        file_size_limit=1024,
        readme_file_limit=1,
        search_tiers=[{"name": "x", "stars": ">=50", "active_days": 7}],
        categories=[CategoryRule(name="Developer Tools")],
    )


def test_readme_escapes_metadata_and_is_stably_sorted(now) -> None:
    lower = make_repo(now, repo_id=2, full_name="z|org/low", stars=10, heat=10)
    higher = make_repo(now, repo_id=1, full_name="a<script>/high", stars=20, heat=90)
    catalog = Catalog(generated_at=now, repositories=[lower, higher], stats=RunStats())
    rendered = render_readme(catalog, _settings())
    assert "a&lt;script&gt;/high" in rendered
    assert "z&#124;org/low" in rendered
    assert rendered.index("a&lt;script&gt;/high") < rendered.index("z&#124;org/low")


def test_readme_folds_repositories_after_category_limit(now) -> None:
    lower = make_repo(now, repo_id=2, full_name="acme/lower", heat=10)
    higher = make_repo(now, repo_id=1, full_name="acme/higher", heat=90)
    catalog = Catalog(generated_at=now, repositories=[lower, higher])
    settings = _settings().model_copy(update={"readme_category_limit": 1})
    rendered = render_readme(catalog, settings)
    details = rendered.index("<details>")
    assert rendered.index("acme/higher") < details < rendered.index("acme/lower")
    assert "<summary>Show 1 more repositories</summary>" in rendered


def test_validation_detects_hash_mismatch(tmp_path, now) -> None:
    repo = make_repo(now)
    snapshot = tmp_path / "snapshots" / "acme" / "tool" / "AGENTS.md"
    snapshot.parent.mkdir(parents=True)
    snapshot.write_bytes(b"x")
    catalog = Catalog(generated_at=now, repositories=[repo])
    errors = validate_catalog(tmp_path, catalog, _settings())
    assert any("hash mismatch" in error for error in errors)
