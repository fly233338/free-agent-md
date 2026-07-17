from __future__ import annotations

from pathlib import Path

from .models import Catalog
from .settings import Settings
from .util import safe_repo_path, sha256_bytes


class ValidationError(ValueError):
    pass


def validate_catalog(root: Path, catalog: Catalog, settings: Settings) -> list[str]:
    errors: list[str] = []
    seen_repos: set[int] = set()
    current_ids = {repo.repo_id for repo in catalog.repositories}
    archived_ids = {repo.repo_id for repo in catalog.archived}
    overlap = current_ids.intersection(archived_ids)
    if overlap:
        errors.append(f"repositories are both current and archived: {sorted(overlap)}")

    expected_raw_prefix = f"https://raw.githubusercontent.com/{settings.repository}/main/"
    for repo in [*catalog.repositories, *catalog.archived]:
        if repo.repo_id in seen_repos:
            errors.append(f"duplicate repository id: {repo.repo_id}")
        seen_repos.add(repo.repo_id)
        seen_paths: set[str] = set()
        for item in repo.files:
            if item.source_path in seen_paths:
                errors.append(f"duplicate path in {repo.full_name}: {item.source_path}")
            seen_paths.add(item.source_path)
            if safe_repo_path(item.local_path) != item.local_path:
                errors.append(f"unsafe local path: {item.local_path}")
                continue
            local = root.joinpath(*item.local_path.split("/"))
            if not local.is_file():
                errors.append(f"missing snapshot: {item.local_path}")
                continue
            content = local.read_bytes()
            if len(content) != item.size:
                errors.append(f"size mismatch: {item.local_path}")
            if sha256_bytes(content) != item.sha256:
                errors.append(f"hash mismatch: {item.local_path}")
            if not item.raw_url.startswith(expected_raw_prefix):
                errors.append(f"unexpected raw URL: {item.raw_url}")
            if f"/blob/{item.commit_sha}/" not in item.source_url:
                errors.append(f"source URL is not commit-fixed: {item.source_url}")
            if item.size > settings.file_size_limit:
                errors.append(f"snapshot exceeds size limit: {item.local_path}")
    return errors


def require_valid(root: Path, catalog: Catalog, settings: Settings) -> None:
    errors = validate_catalog(root, catalog, settings)
    if errors:
        raise ValidationError("catalog validation failed:\n- " + "\n- ".join(errors))
