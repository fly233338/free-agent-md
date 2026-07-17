from __future__ import annotations

import json

from free_agent_md.cli import main
from free_agent_md.models import Catalog, RunStats


def test_dry_run_reports_estimated_api_requests(monkeypatch, capsys, tmp_path, now) -> None:
    catalog = Catalog(
        generated_at=now,
        stats=RunStats(candidates=2, repositories_scanned=2, api_requests=17),
    )
    monkeypatch.setattr("free_agent_md.cli.run_update", lambda *_args, **_kwargs: catalog)
    assert main(["--root", str(tmp_path), "dry-run"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["mode"] == "dry-run"
    assert output["estimated_api_requests"] == 17
