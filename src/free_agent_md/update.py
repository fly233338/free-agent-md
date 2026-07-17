from __future__ import annotations

import os
import posixpath
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

from .classify import classify_repository
from .github import GitHubClient, GitHubError, GitHubNotFound, iter_instruction_entries
from .heat import apply_heat
from .models import (
    Catalog,
    FileKind,
    FileRecord,
    HistoryPoint,
    RecordStatus,
    RepositoryHistory,
    RepositoryRecord,
    RunStats,
)
from .render import write_rendered
from .settings import Settings, load_overrides, load_settings
from .util import json_dump, parse_github_time, safe_repo_path, sha256_bytes, utcnow
from .validate import require_valid


OUTPUTS = ("snapshots", "data", "indexes", "README.md", "ARCHIVE.md")


def load_catalog(root: Path, *, now: datetime | None = None) -> Catalog:
    path = root / "data" / "catalog.json"
    if not path.exists():
        return Catalog(generated_at=now or utcnow())
    return Catalog.model_validate_json(path.read_text(encoding="utf-8"))


def load_histories(root: Path) -> dict[int, RepositoryHistory]:
    histories: dict[int, RepositoryHistory] = {}
    history_root = root / "data" / "history"
    if not history_root.exists():
        return histories
    for path in history_root.glob("*.json"):
        history = RepositoryHistory.model_validate_json(path.read_text(encoding="utf-8"))
        histories[history.repo_id] = history
    return histories


def _kind(path: str) -> FileKind:
    return {
        "agents.md": FileKind.AGENTS,
        "claude.md": FileKind.CLAUDE,
        "gemini.md": FileKind.GEMINI,
    }[PurePosixPath(path).name.lower()]


def _license(item: dict[str, Any]) -> str:
    value = item.get("license")
    if isinstance(value, dict) and isinstance(value.get("spdx_id"), str):
        return value["spdx_id"]
    return "NOASSERTION"


def _local_path(full_name: str, source_path: str) -> str:
    return f"snapshots/{full_name}/{source_path}"


def _resolve_blob(
    client: GitHubClient,
    full_name: str,
    entry: dict[str, Any],
    entries_by_path: dict[str, dict[str, Any]],
) -> tuple[str, int | None] | None:
    sha = entry.get("sha")
    if not isinstance(sha, str):
        return None
    mode = entry.get("mode")
    if mode != "120000":
        if not isinstance(mode, str) or not mode.startswith("100"):
            return None
        size = entry.get("size")
        return sha, size if isinstance(size, int) else None

    try:
        target_text = client.blob(full_name, sha).decode("utf-8")
    except (UnicodeDecodeError, GitHubError):
        return None
    if target_text.startswith(("/", "\\")):
        return None
    source_dir = posixpath.dirname(str(entry["path"]))
    target_path = safe_repo_path(posixpath.join(source_dir, target_text))
    if target_path is None:
        return None
    target = entries_by_path.get(target_path)
    if not target or target.get("type") != "blob" or target.get("mode") == "120000":
        return None
    target_sha = target.get("sha")
    target_size = target.get("size")
    if not isinstance(target_sha, str):
        return None
    return target_sha, target_size if isinstance(target_size, int) else None


def _discover_files(
    client: GitHubClient,
    stage: Path,
    settings: Settings,
    item: dict[str, Any],
    commit_sha: str,
    tree_sha: str,
    now: datetime,
    previous: RepositoryRecord | None,
) -> list[FileRecord]:
    full_name = str(item["full_name"])
    entries = client.scoped_tree(full_name, tree_sha, settings.scan_directories)
    entries_by_path = {
        str(entry["path"]): entry
        for entry in entries
        if isinstance(entry.get("path"), str)
    }
    previous_files = {file.source_path: file for file in previous.files} if previous else {}
    records: list[FileRecord] = []
    for entry in sorted(
        iter_instruction_entries(entries),
        key=lambda value: (str(value["path"]).count("/"), str(value["path"]).lower()),
    ):
        source_path = safe_repo_path(str(entry["path"]))
        if source_path is None:
            continue
        resolved = _resolve_blob(client, full_name, entry, entries_by_path)
        if resolved is None:
            continue
        blob_sha, declared_size = resolved
        if declared_size is not None and declared_size > settings.file_size_limit:
            continue

        local_path = _local_path(full_name, source_path)
        destination = stage.joinpath(*local_path.split("/"))
        old = previous_files.get(source_path)
        reused = False
        if old and old.blob_sha == blob_sha:
            old_path = stage.joinpath(*old.local_path.split("/"))
            if old_path.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                if old_path != destination:
                    shutil.copy2(old_path, destination)
                content = destination.read_bytes()
                reused = len(content) == old.size and sha256_bytes(content) == old.sha256
        if not reused:
            content = client.blob(full_name, blob_sha)
            if len(content) > settings.file_size_limit:
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        if len(content) > settings.file_size_limit:
            continue

        encoded_path = quote(source_path, safe="/")
        encoded_local = quote(local_path, safe="/")
        records.append(
            FileRecord(
                kind=_kind(source_path),
                source_path=source_path,
                local_path=local_path,
                commit_sha=commit_sha,
                blob_sha=blob_sha,
                sha256=sha256_bytes(content),
                size=len(content),
                raw_url=f"https://raw.githubusercontent.com/{settings.repository}/main/{encoded_local}",
                source_url=f"https://github.com/{full_name}/blob/{commit_sha}/{encoded_path}",
                first_seen_at=old.first_seen_at if old else now,
                last_seen_at=now,
            )
        )
    return records


def _record_from_item(
    item: dict[str, Any],
    files: list[FileRecord],
    commit_sha: str,
    now: datetime,
    previous: RepositoryRecord | None,
    settings: Settings,
    overrides: dict[str, str],
) -> RepositoryRecord:
    full_name = str(item["full_name"])
    description = item.get("description") if isinstance(item.get("description"), str) else None
    language = item.get("language") if isinstance(item.get("language"), str) else None
    topics = sorted(str(topic) for topic in item.get("topics", []) if isinstance(topic, str))
    return RepositoryRecord(
        repo_id=int(item["id"]),
        full_name=full_name,
        html_url=f"https://github.com/{full_name}",
        description=description,
        category=classify_repository(
            full_name, description, language, topics, settings.categories, overrides
        ),
        language=language,
        topics=topics,
        license=_license(item),
        stars=int(item.get("stargazers_count", 0)),
        pushed_at=parse_github_time(str(item["pushed_at"])),
        default_branch=str(item["default_branch"]),
        commit_sha=commit_sha,
        first_seen_at=previous.first_seen_at if previous else now,
        last_checked_at=now,
        files=files,
    )


def _prepare_stage(root: Path, stage: Path) -> None:
    for directory in ("snapshots", "data"):
        source = root / directory
        destination = stage / directory
        if source.exists():
            shutil.copytree(source, destination)
        else:
            destination.mkdir(parents=True)
    (stage / "indexes").mkdir(parents=True)


def _write_histories(
    stage: Path,
    histories: dict[int, RepositoryHistory],
    repositories: list[RepositoryRecord],
    now: datetime,
    days: int,
) -> None:
    cutoff = now - timedelta(days=days)
    history_root = stage / "data" / "history"
    history_root.mkdir(parents=True, exist_ok=True)
    for old_history in history_root.glob("*.json"):
        old_history.unlink()
    for repo in repositories:
        history = histories.get(
            repo.repo_id,
            RepositoryHistory(repo_id=repo.repo_id, full_name=repo.full_name),
        )
        history.full_name = repo.full_name
        history.points = [point for point in history.points if point.checked_at >= cutoff]
        point = HistoryPoint(
            checked_at=now,
            stars=repo.stars,
            pushed_at=repo.pushed_at,
            commit_sha=repo.commit_sha,
        )
        if history.points and history.points[-1].checked_at.date() == now.date():
            history.points[-1] = point
        else:
            history.points.append(point)
        histories[repo.repo_id] = history
    for history in histories.values():
        history.points = [point for point in history.points if point.checked_at >= cutoff]
        if history.points:
            json_dump(history_root / f"{history.repo_id}.json", history)


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _install_outputs(root: Path, stage: Path, outputs: tuple[str, ...]) -> None:
    backup = Path(tempfile.mkdtemp(prefix=".free-agent-md-backup-", dir=root.parent))
    installed: list[str] = []
    backed_up: list[str] = []
    try:
        for name in outputs:
            source = stage / name
            target = root / name
            old = backup / name
            if target.exists():
                old.parent.mkdir(parents=True, exist_ok=True)
                os.replace(target, old)
                backed_up.append(name)
            os.replace(source, target)
            installed.append(name)
    except Exception:
        for name in reversed(installed):
            _remove_path(root / name)
        for name in reversed(backed_up):
            os.replace(backup / name, root / name)
        raise
    finally:
        shutil.rmtree(backup, ignore_errors=True)


def _install_stage(root: Path, stage: Path) -> None:
    _install_outputs(root, stage, OUTPUTS)


def build_catalog(
    root: Path,
    stage: Path,
    client: GitHubClient,
    settings: Settings,
    now: datetime,
) -> Catalog:
    previous_catalog = load_catalog(root, now=now)
    histories = load_histories(root)
    overrides = load_overrides(root)
    allowed_categories = {rule.name for rule in settings.categories} | {"Other"}
    invalid_overrides = {
        full_name: category
        for full_name, category in overrides.items()
        if category not in allowed_categories
    }
    if invalid_overrides:
        raise ValueError(f"category overrides use unknown categories: {invalid_overrides}")
    previous_by_id = {repo.repo_id: repo for repo in previous_catalog.repositories}
    archived_by_id = {repo.repo_id: repo for repo in previous_catalog.archived}
    candidates = client.candidates(
        settings.search_tiers,
        today=now.date(),
        scan_limit=settings.scan_limit,
    )
    active: list[RepositoryRecord] = []
    seen_ids: set[int] = set()
    scanned = 0
    files_found = 0
    for item in candidates:
        repo_id = item.get("id")
        if not isinstance(repo_id, int) or not isinstance(item.get("full_name"), str):
            continue
        seen_ids.add(repo_id)
        previous = previous_by_id.get(repo_id) or archived_by_id.get(repo_id)
        if item.get("archived"):
            if previous:
                archived_by_id[repo_id] = previous.model_copy(
                    update={"status": RecordStatus.ARCHIVED, "last_checked_at": now}
                )
            continue
        branch = item.get("default_branch")
        if not isinstance(branch, str) or not isinstance(item.get("pushed_at"), str):
            continue
        scanned += 1
        commit_sha, tree_sha = client.branch_commit(str(item["full_name"]), branch)
        files = _discover_files(
            client, stage, settings, item, commit_sha, tree_sha, now, previous
        )
        if not files:
            if previous:
                deleted_files = [
                    file.model_copy(update={"status": RecordStatus.DELETED})
                    for file in previous.files
                ]
                archived_by_id[repo_id] = previous.model_copy(
                    update={
                        "status": RecordStatus.DELETED,
                        "last_checked_at": now,
                        "files": deleted_files,
                    }
                )
            continue
        if previous:
            current_paths = {file.source_path for file in files}
            files.extend(
                old.model_copy(update={"status": RecordStatus.DELETED})
                for old in previous.files
                if old.source_path not in current_paths
            )
        record = _record_from_item(
            item, files, commit_sha, now, previous, settings, overrides
        )
        active.append(record)
        files_found += sum(file.status == RecordStatus.ACTIVE for file in files)
        archived_by_id.pop(repo_id, None)

    for repo_id, previous in previous_by_id.items():
        if repo_id not in seen_ids:
            try:
                metadata = client.repository(previous.full_name)
                status = (
                    RecordStatus.ARCHIVED
                    if metadata.get("archived")
                    else RecordStatus.INACTIVE
                )
            except GitHubNotFound:
                status = RecordStatus.DELETED
            archived_by_id[repo_id] = previous.model_copy(
                update={"status": status, "last_checked_at": now}
            )

    apply_heat(active, histories, now)
    _write_histories(stage, histories, active, now, settings.history_days)
    active.sort(key=lambda repo: repo.full_name.lower())
    archived = sorted(archived_by_id.values(), key=lambda repo: repo.full_name.lower())
    catalog = Catalog(
        schema_version=settings.schema_version,
        generated_at=now,
        stats=RunStats(
            candidates=len(candidates),
            repositories_scanned=scanned,
            repositories_matched=len(active),
            files_found=files_found,
            api_requests=client.request_count,
        ),
        repositories=active,
        archived=archived,
    )
    json_dump(stage / "data" / "catalog.json", catalog)
    write_rendered(stage, catalog, settings)
    require_valid(stage, catalog, settings)
    return catalog


def run_update(
    root: Path,
    *,
    token: str | None = None,
    dry_run: bool = False,
    now: datetime | None = None,
    client: GitHubClient | None = None,
) -> Catalog:
    root = root.resolve()
    settings = load_settings(root)
    repository = os.getenv("GITHUB_REPOSITORY")
    if repository:
        settings = settings.model_copy(update={"repository": repository})
    now = now or utcnow()
    own_client = client is None
    github = client or GitHubClient(token)
    try:
        with tempfile.TemporaryDirectory(prefix=".free-agent-md-stage-", dir=root.parent) as temp:
            stage = Path(temp)
            _prepare_stage(root, stage)
            catalog = build_catalog(root, stage, github, settings, now)
            if not dry_run:
                _install_stage(root, stage)
            return catalog
    finally:
        if own_client:
            github.close()


def render_existing(root: Path) -> Catalog:
    root = root.resolve()
    settings = load_settings(root)
    repository = os.getenv("GITHUB_REPOSITORY")
    if repository:
        settings = settings.model_copy(update={"repository": repository})
    catalog = load_catalog(root)
    with tempfile.TemporaryDirectory(prefix=".free-agent-md-render-", dir=root.parent) as temp:
        stage = Path(temp)
        (stage / "indexes").mkdir()
        write_rendered(stage, catalog, settings)
        _install_outputs(root, stage, ("indexes", "README.md", "ARCHIVE.md"))
    return catalog
