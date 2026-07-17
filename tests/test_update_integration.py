from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from free_agent_md.models import RecordStatus
from free_agent_md.update import run_update


class FixtureGitHub:
    request_count = 12

    def __init__(self, now, *, entries: list[dict] | None = None, full_name: str = "acme/tool") -> None:
        self.item = {
            "id": 42,
            "full_name": full_name,
            "html_url": f"https://github.com/{full_name}",
            "description": "An AI command line developer tool",
            "language": "Python",
            "topics": ["ai", "cli"],
            "license": {"spdx_id": "Apache-2.0"},
            "stargazers_count": 500,
            "pushed_at": now.isoformat().replace("+00:00", "Z"),
            "default_branch": "main",
            "archived": False,
        }
        self.entries = entries if entries is not None else [
            {"path": "AGENTS.md", "type": "blob", "mode": "100644", "sha": "agents", "size": 6},
            {"path": "docs/ClAuDe.Md", "type": "blob", "mode": "100644", "sha": "claude", "size": 6},
            {"path": "g/GEMINI.md", "type": "blob", "mode": "120000", "sha": "link", "size": 9},
            {"path": "g/target.md", "type": "blob", "mode": "100644", "sha": "target", "size": 6},
            {"path": "huge/AGENTS.md", "type": "blob", "mode": "100644", "sha": "huge", "size": 2_000_000},
            {"path": "bad/CLAUDE.md", "type": "blob", "mode": "120000", "sha": "badlink", "size": 12},
        ]
        self.blobs = {
            "agents": b"agents",
            "claude": b"claud!",
            "link": b"target.md",
            "target": b"gemini",
            "badlink": b"../../escape",
        }
        self.fail = False

    def candidates(self, *_args, **_kwargs):
        return [self.item]

    def branch_commit(self, *_args):
        if self.fail:
            raise RuntimeError("fixture collection interrupted")
        return "c" * 40, "tree"

    def walk_tree(self, *_args):
        return self.entries

    def blob(self, _full_name, sha):
        return self.blobs[sha]


def _repository(tmp_path: Path) -> Path:
    source = Path(__file__).parents[1]
    shutil.copy2(source / "config.yml", tmp_path / "config.yml")
    (tmp_path / "config").mkdir()
    shutil.copy2(
        source / "config" / "category-overrides.yml",
        tmp_path / "config" / "category-overrides.yml",
    )
    (tmp_path / "README.md").write_text("old readme\n", encoding="utf-8")
    (tmp_path / "ARCHIVE.md").write_text("old archive\n", encoding="utf-8")
    return tmp_path


def _fingerprint(root: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for name in ("README.md", "ARCHIVE.md", "data", "indexes", "snapshots"):
        path = root / name
        if path.is_file():
            result[name] = path.read_bytes()
        elif path.exists():
            for child in sorted(value for value in path.rglob("*") if value.is_file()):
                result[child.relative_to(root).as_posix()] = child.read_bytes()
    return result


def test_update_finds_nested_case_variants_and_safe_symlink(tmp_path, now) -> None:
    root = _repository(tmp_path)
    catalog = run_update(root, client=FixtureGitHub(now), now=now)
    assert catalog.stats.repositories_matched == 1
    assert catalog.stats.files_found == 3
    assert [file.source_path for file in catalog.repositories[0].files] == [
        "AGENTS.md",
        "docs/ClAuDe.Md",
        "g/GEMINI.md",
    ]
    assert (root / "snapshots" / "acme" / "tool" / "g" / "GEMINI.md").read_bytes() == b"gemini"
    assert not (root / "snapshots" / "acme" / "tool" / "huge" / "AGENTS.md").exists()


def test_fixed_fixture_repeat_is_identical_and_dry_run_does_not_write(tmp_path, now) -> None:
    root = _repository(tmp_path)
    run_update(root, client=FixtureGitHub(now), now=now)
    first = _fingerprint(root)
    run_update(root, client=FixtureGitHub(now), now=now)
    assert _fingerprint(root) == first

    changed = FixtureGitHub(now)
    changed.item["stargazers_count"] = 999
    run_update(root, client=changed, now=now, dry_run=True)
    assert _fingerprint(root) == first


def test_corrupted_unchanged_snapshot_is_downloaded_again(tmp_path, now) -> None:
    root = _repository(tmp_path)
    run_update(root, client=FixtureGitHub(now), now=now)
    snapshot = root / "snapshots" / "acme" / "tool" / "AGENTS.md"
    snapshot.write_bytes(b"broken")
    run_update(root, client=FixtureGitHub(now), now=now)
    assert snapshot.read_bytes() == b"agents"


def test_rename_tracks_repository_id_and_preserves_first_seen(tmp_path, now) -> None:
    root = _repository(tmp_path)
    first = run_update(root, client=FixtureGitHub(now), now=now)
    renamed = run_update(root, client=FixtureGitHub(now, full_name="new-org/tool"), now=now)
    repo = renamed.repositories[0]
    assert repo.full_name == "new-org/tool"
    assert repo.first_seen_at == first.repositories[0].first_seen_at
    assert (root / "snapshots" / "new-org" / "tool" / "AGENTS.md").exists()


def test_removed_files_are_archived_and_snapshot_is_retained(tmp_path, now) -> None:
    root = _repository(tmp_path)
    run_update(root, client=FixtureGitHub(now), now=now)
    catalog = run_update(root, client=FixtureGitHub(now, entries=[]), now=now)
    assert catalog.repositories == []
    assert catalog.archived[0].status == RecordStatus.DELETED
    assert (root / "snapshots" / "acme" / "tool" / "AGENTS.md").exists()


def test_single_removed_file_is_archived_while_repository_stays_ranked(tmp_path, now) -> None:
    root = _repository(tmp_path)
    fixture = FixtureGitHub(now)
    run_update(root, client=fixture, now=now)
    remaining = [entry for entry in fixture.entries if entry["path"] != "docs/ClAuDe.Md"]
    catalog = run_update(root, client=FixtureGitHub(now, entries=remaining), now=now)
    repo = catalog.repositories[0]
    removed = next(file for file in repo.files if file.source_path == "docs/ClAuDe.Md")
    assert removed.status == RecordStatus.DELETED
    assert catalog.stats.files_found == 2
    assert "docs/ClAuDe.Md" in (root / "ARCHIVE.md").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "docs/ClAuDe.Md" not in readme


def test_collection_failure_leaves_last_success_untouched(tmp_path, now) -> None:
    root = _repository(tmp_path)
    run_update(root, client=FixtureGitHub(now), now=now)
    before = _fingerprint(root)
    failing = FixtureGitHub(now)
    failing.fail = True
    with pytest.raises(RuntimeError, match="interrupted"):
        run_update(root, client=failing, now=now)
    assert _fingerprint(root) == before


def test_repository_leaving_search_is_checked_for_upstream_archive(tmp_path, now) -> None:
    root = _repository(tmp_path)
    run_update(root, client=FixtureGitHub(now), now=now)

    archived = FixtureGitHub(now)
    archived.candidates = lambda *_args, **_kwargs: []
    archived.repository = lambda _full_name: {"archived": True}
    catalog = run_update(root, client=archived, now=now)
    assert catalog.repositories == []
    assert catalog.archived[0].status == RecordStatus.ARCHIVED
