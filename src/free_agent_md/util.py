from __future__ import annotations

import hashlib
import json
import posixpath
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any


def utcnow() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_repo_path(path: str) -> str | None:
    normalized = posixpath.normpath(path.replace("\\", "/"))
    if normalized in {"", ".", ".."} or normalized.startswith("../"):
        return None
    candidate = PurePosixPath(normalized)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        return None
    return candidate.as_posix()


def parse_github_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
