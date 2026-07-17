from __future__ import annotations

from datetime import UTC, datetime

import pytest

from free_agent_md.models import FileKind, FileRecord, RepositoryRecord


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 7, 17, 3, 23, tzinfo=UTC)


def make_file(now: datetime, path: str = "AGENTS.md") -> FileRecord:
    return FileRecord(
        kind=FileKind.AGENTS,
        source_path=path,
        local_path=f"snapshots/acme/tool/{path}",
        commit_sha="c" * 40,
        blob_sha="b" * 40,
        sha256="0" * 64,
        size=1,
        raw_url=f"https://raw.githubusercontent.com/acme/index/main/snapshots/acme/tool/{path}",
        source_url=f"https://github.com/acme/tool/blob/{'c' * 40}/{path}",
        first_seen_at=now,
        last_seen_at=now,
    )


def make_repo(now: datetime, **updates: object) -> RepositoryRecord:
    values: dict[str, object] = {
        "repo_id": 1,
        "full_name": "acme/tool",
        "html_url": "https://github.com/acme/tool",
        "description": "developer tool",
        "category": "Developer Tools",
        "language": "Python",
        "topics": ["cli"],
        "license": "MIT",
        "stars": 100,
        "pushed_at": now,
        "default_branch": "main",
        "commit_sha": "c" * 40,
        "first_seen_at": now,
        "last_checked_at": now,
        "files": [make_file(now)],
    }
    values.update(updates)
    return RepositoryRecord.model_validate(values)
