from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class FileKind(StrEnum):
    AGENTS = "AGENTS.md"
    CLAUDE = "CLAUDE.md"
    GEMINI = "GEMINI.md"


class RecordStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    INACTIVE = "inactive"


class FileRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: FileKind
    source_path: str
    local_path: str
    commit_sha: str
    blob_sha: str
    sha256: str
    size: int = Field(ge=0)
    raw_url: str
    source_url: str
    first_seen_at: datetime
    last_seen_at: datetime
    status: RecordStatus = RecordStatus.ACTIVE


class RepositoryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repo_id: int
    full_name: str
    html_url: str
    description: str | None = None
    category: str = "Other"
    language: str | None = None
    topics: list[str] = Field(default_factory=list)
    license: str = "NOASSERTION"
    stars: int = Field(ge=0)
    stars_delta_7d: int = Field(ge=0, default=0)
    pushed_at: datetime
    default_branch: str
    commit_sha: str
    heat: float = Field(ge=0, le=100, default=0)
    first_seen_at: datetime
    last_checked_at: datetime
    status: RecordStatus = RecordStatus.ACTIVE
    files: list[FileRecord] = Field(default_factory=list)


class RunStats(BaseModel):
    candidates: int = 0
    repositories_scanned: int = 0
    repositories_matched: int = 0
    files_found: int = 0
    api_requests: int = 0


class Catalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    generated_at: datetime
    stats: RunStats = Field(default_factory=RunStats)
    repositories: list[RepositoryRecord] = Field(default_factory=list)
    archived: list[RepositoryRecord] = Field(default_factory=list)


class HistoryPoint(BaseModel):
    checked_at: datetime
    stars: int = Field(ge=0)
    pushed_at: datetime
    commit_sha: str


class RepositoryHistory(BaseModel):
    repo_id: int
    full_name: str
    points: list[HistoryPoint] = Field(default_factory=list)
