from __future__ import annotations

import json

import httpx
import pytest

from free_agent_md.github import GitHubClient, GitHubError, GitHubNotFound


def _response(request: httpx.Request, status: int, value: dict, **headers: str) -> httpx.Response:
    return httpx.Response(status, json=value, headers=headers, request=request)


def test_search_retries_incomplete_results_and_paginates() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        calls.append(page)
        if len(calls) == 1:
            return _response(request, 200, {"incomplete_results": True, "items": [{"id": 99}]})
        return _response(
            request,
            200,
            {"incomplete_results": False, "items": [{"id": page}]},
        )

    delays: list[float] = []
    with GitHubClient(transport=httpx.MockTransport(handler), sleeper=delays.append) as client:
        items = client.search("stars:>50", sort="stars", limit=2, per_page=1)
    assert [item["id"] for item in items] == [1, 2]
    assert calls == [1, 1, 2]
    assert delays == [2.0]


def test_rate_limit_retry_honors_retry_after() -> None:
    count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal count
        count += 1
        if count == 1:
            return _response(request, 429, {"message": "slow down"}, **{"Retry-After": "7"})
        return _response(request, 200, {"ok": True})

    delays: list[float] = []
    with GitHubClient(transport=httpx.MockTransport(handler), sleeper=delays.append) as client:
        assert client.get_json("/test") == {"ok": True}
    assert delays == [7.0]


def test_persistently_incomplete_search_fails_instead_of_publishing_partial_data() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _response(request, 200, {"incomplete_results": True, "items": []})

    with GitHubClient(transport=httpx.MockTransport(handler), sleeper=lambda _: None) as client:
        with pytest.raises(GitHubError, match="remained incomplete"):
            client.search("stars:>50", sort="stars")


def test_not_found_has_a_distinct_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _response(request, 404, {"message": "Not Found"})

    with GitHubClient(transport=httpx.MockTransport(handler), sleeper=lambda _: None) as client:
        with pytest.raises(GitHubNotFound):
            client.repository("gone/repository")


def test_scoped_tree_reads_root_and_direct_children_of_allowed_directories_only() -> None:
    requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        assert "recursive" not in request.url.params
        requested.append(path)
        if path.endswith("/root"):
            return _response(
                request,
                200,
                {
                    "tree": [
                        {"path": "AGENTS.md", "type": "blob", "sha": "root-file", "mode": "100644"},
                        {"path": "docs", "type": "tree", "sha": "docs", "mode": "040000"},
                        {"path": ".codex", "type": "tree", "sha": "codex", "mode": "040000"},
                    ]
                },
            )
        if path.endswith("/codex"):
            return _response(
                request,
                200,
                {
                    "tree": [
                        {"path": "CLAUDE.md", "type": "blob", "sha": "file", "mode": "100644"},
                        {"path": "nested", "type": "tree", "sha": "nested", "mode": "040000"},
                    ]
                },
            )
        raise AssertionError(path)

    with GitHubClient(transport=httpx.MockTransport(handler), sleeper=lambda _: None) as client:
        entries = client.scoped_tree("acme/tool", "root", [".codex"])
    assert [entry["path"] for entry in entries] == [
        "AGENTS.md",
        "docs",
        ".codex",
        ".codex/CLAUDE.md",
        ".codex/nested",
    ]
    assert requested == [
        "/repos/acme/tool/git/trees/root",
        "/repos/acme/tool/git/trees/codex",
    ]


def test_scoped_tree_rejects_truncated_root_instead_of_recursing() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "recursive" not in request.url.params
        return _response(request, 200, {"truncated": True, "tree": []})

    with GitHubClient(transport=httpx.MockTransport(handler), sleeper=lambda _: None) as client:
        with pytest.raises(GitHubError, match="root tree is truncated"):
            client.scoped_tree("acme/tool", "root", [".codex"])
