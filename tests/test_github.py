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


def test_truncated_tree_falls_back_to_breadth_first_walk() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        recursive = request.url.params.get("recursive")
        if path.endswith("/root") and recursive == "1":
            return _response(request, 200, {"truncated": True, "tree": []})
        if path.endswith("/root"):
            return _response(
                request,
                200,
                {"tree": [{"path": "docs", "type": "tree", "sha": "sub", "mode": "040000"}]},
            )
        if path.endswith("/sub"):
            return _response(
                request,
                200,
                {"tree": [{"path": "AGENTS.md", "type": "blob", "sha": "file", "mode": "100644"}]},
            )
        raise AssertionError(path)

    with GitHubClient(transport=httpx.MockTransport(handler), sleeper=lambda _: None) as client:
        entries = client.walk_tree("acme/tool", "root")
    assert [entry["path"] for entry in entries] == ["docs", "docs/AGENTS.md"]
