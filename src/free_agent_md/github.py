from __future__ import annotations

import base64
import email.utils
import time
from collections.abc import Callable, Iterator
from datetime import date, timedelta
from typing import Any
from urllib.parse import quote

import httpx

from .settings import SearchTier


class GitHubError(RuntimeError):
    pass


class GitHubNotFound(GitHubError):
    pass


class GitHubClient:
    def __init__(
        self,
        token: str | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        max_attempts: int = 5,
    ) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "free-agent-md/0.1",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(
            base_url="https://api.github.com",
            headers=headers,
            timeout=30,
            follow_redirects=True,
            transport=transport,
        )
        self._sleeper = sleeper
        self._max_attempts = max_attempts
        self.request_count = 0

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> GitHubClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _delay(self, response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return min(300.0, max(0.0, float(retry_after)))
            except ValueError:
                parsed = email.utils.parsedate_to_datetime(retry_after)
                return min(300.0, max(0.0, parsed.timestamp() - time.time()))
        reset = response.headers.get("X-RateLimit-Reset")
        if reset and response.status_code in {403, 429}:
            return min(300.0, max(1.0, float(reset) - time.time()))
        return min(60.0, float(2**attempt))

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        last: httpx.Response | None = None
        for attempt in range(self._max_attempts):
            self.request_count += 1
            try:
                response = self._client.request(method, path, **kwargs)
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt + 1 == self._max_attempts:
                    raise GitHubError(f"GitHub request failed: {path}") from exc
                self._sleeper(min(60.0, float(2**attempt)))
                continue
            last = response
            if response.status_code < 400:
                return response
            if response.status_code not in {403, 429, 500, 502, 503, 504}:
                break
            if attempt + 1 < self._max_attempts:
                self._sleeper(self._delay(response, attempt))
        assert last is not None
        message = last.text[:300].replace("\n", " ")
        if last.status_code == 404:
            raise GitHubNotFound(f"GitHub resource not found: {path}")
        raise GitHubError(f"GitHub returned {last.status_code} for {path}: {message}")

    def get_json(self, path: str, **params: Any) -> dict[str, Any]:
        value = self.request("GET", path, params=params).json()
        if not isinstance(value, dict):
            raise GitHubError(f"expected an object from {path}")
        return value

    def search(
        self,
        query: str,
        *,
        sort: str,
        limit: int = 100,
        per_page: int = 100,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page = 1
        incomplete_retries = 0
        while len(items) < limit:
            data = self.get_json(
                "/search/repositories",
                q=query,
                sort=sort,
                order="desc",
                per_page=min(per_page, limit - len(items)),
                page=page,
            )
            if data.get("incomplete_results") and incomplete_retries < 2:
                incomplete_retries += 1
                self._sleeper(float(2**incomplete_retries))
                continue
            if data.get("incomplete_results"):
                raise GitHubError(f"repository search remained incomplete for query: {query}")
            incomplete_retries = 0
            page_items = data.get("items", [])
            if not isinstance(page_items, list):
                raise GitHubError("repository search returned invalid items")
            items.extend(item for item in page_items if isinstance(item, dict))
            if len(page_items) < min(per_page, limit - len(items) + len(page_items)):
                break
            page += 1
        return items[:limit]

    def candidates(
        self,
        tiers: list[SearchTier],
        *,
        today: date,
        scan_limit: int,
        per_query_limit: int = 100,
    ) -> list[dict[str, Any]]:
        by_id: dict[int, dict[str, Any]] = {}
        for tier in tiers:
            pushed_after = today - timedelta(days=tier.active_days)
            query = f"stars:{tier.stars} pushed:>={pushed_after.isoformat()}"
            for sort in ("stars", "updated"):
                for item in self.search(query, sort=sort, limit=per_query_limit):
                    repo_id = item.get("id")
                    if isinstance(repo_id, int):
                        by_id.setdefault(repo_id, item)
        return list(by_id.values())[:scan_limit]

    def branch_commit(self, full_name: str, branch: str) -> tuple[str, str]:
        data = self.get_json(f"/repos/{full_name}/branches/{quote(branch, safe='')}")
        commit = data.get("commit", {})
        commit_sha = commit.get("sha")
        tree_sha = commit.get("commit", {}).get("tree", {}).get("sha")
        if not commit_sha or not tree_sha:
            if not isinstance(commit_sha, str):
                raise GitHubError(f"could not resolve default branch for {full_name}")
            commit_data = self.get_json(f"/repos/{full_name}/git/commits/{commit_sha}")
            tree_sha = commit_data.get("tree", {}).get("sha")
        if not isinstance(commit_sha, str) or not isinstance(tree_sha, str):
            raise GitHubError(f"could not resolve default branch for {full_name}")
        return commit_sha, tree_sha

    def repository(self, full_name: str) -> dict[str, Any]:
        return self.get_json(f"/repos/{full_name}")

    def tree(self, full_name: str, tree_sha: str) -> dict[str, Any]:
        return self.get_json(f"/repos/{full_name}/git/trees/{tree_sha}")

    def scoped_tree(
        self,
        full_name: str,
        root_sha: str,
        directories: list[str],
    ) -> list[dict[str, Any]]:
        root = self.tree(full_name, root_sha)
        if root.get("truncated"):
            raise GitHubError(f"root tree is truncated for {full_name}")
        root_entries = [item for item in root.get("tree", []) if isinstance(item, dict)]
        entries = list(root_entries)
        allowed = {directory.casefold() for directory in directories}
        for directory in root_entries:
            path = directory.get("path")
            sha = directory.get("sha")
            if (
                directory.get("type") != "tree"
                or not isinstance(path, str)
                or path.casefold() not in allowed
                or not isinstance(sha, str)
            ):
                continue
            child = self.tree(full_name, sha)
            if child.get("truncated"):
                raise GitHubError(f"configured directory tree is truncated: {full_name}/{path}")
            for item in child.get("tree", []):
                if isinstance(item, dict) and isinstance(item.get("path"), str):
                    entries.append({**item, "path": f"{path}/{item['path']}"})
        return entries

    def blob(self, full_name: str, sha: str) -> bytes:
        data = self.get_json(f"/repos/{full_name}/git/blobs/{sha}")
        if data.get("encoding") != "base64" or not isinstance(data.get("content"), str):
            raise GitHubError(f"unsupported blob encoding for {full_name}@{sha}")
        return base64.b64decode(data["content"], validate=False)


def iter_instruction_entries(entries: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    names = {"agents.md", "claude.md", "gemini.md"}
    for entry in entries:
        path = entry.get("path")
        if (
            isinstance(path, str)
            and path.rsplit("/", 1)[-1].lower() in names
            and entry.get("type") == "blob"
        ):
            yield entry
