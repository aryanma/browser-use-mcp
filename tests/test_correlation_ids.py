# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Unit tests for stateless correlation ID contracts."""

from __future__ import annotations

from http import HTTPStatus

from dedalus_mcp import HttpMethod
import pytest

from browser.types import CloudApiResult
from tools.browsers import bu_browser_session_create
from tools.sessions import bu_session_create
from tools.tasks import bu_task_create


@pytest.mark.asyncio
async def test_session_create_returns_session_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Session create should surface `session_id` at top-level."""

    async def fake_request(
        method: HttpMethod,
        path: str,
        *,
        body: dict[str, object] | None = None,
        query: dict[str, object] | None = None,
    ) -> CloudApiResult:
        assert path == "/api/v2/sessions"
        assert body is not None
        assert query is None
        assert method is HttpMethod.POST
        return CloudApiResult(success=True, status_code=HTTPStatus.OK, data={"id": "sess_123"})

    monkeypatch.setattr("tools.sessions.request", fake_request)
    result = await bu_session_create()

    assert result.success
    assert result.session_id == "sess_123"
    assert result.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_session_create_fails_when_id_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Session create should fail if upstream payload has no ID."""

    async def fake_request(
        method: HttpMethod,
        path: str,
        *,
        body: dict[str, object] | None = None,
        query: dict[str, object] | None = None,
    ) -> CloudApiResult:
        assert path == "/api/v2/sessions"
        assert body is not None
        assert query is None
        assert method is HttpMethod.POST
        return CloudApiResult(success=True, status_code=HTTPStatus.OK, data={"ok": True})

    monkeypatch.setattr("tools.sessions.request", fake_request)
    result = await bu_session_create()

    assert not result.success
    assert result.session_id is None
    assert result.error == "Session created but response did not include session_id"


@pytest.mark.asyncio
async def test_browser_session_create_returns_id_and_cdp(monkeypatch: pytest.MonkeyPatch) -> None:
    """Browser session create should surface `session_id` and `cdp_url`."""

    async def fake_request(
        method: HttpMethod,
        path: str,
        *,
        body: dict[str, object] | None = None,
        query: dict[str, object] | None = None,
    ) -> CloudApiResult:
        assert path == "/api/v2/browsers"
        assert body is not None
        assert query is None
        assert method is HttpMethod.POST
        return CloudApiResult(
            success=True,
            status_code=HTTPStatus.OK,
            data={"session": {"sessionId": "br_123", "cdpUrl": "wss://cdp.example/ws"}},
        )

    monkeypatch.setattr("tools.browsers.request", fake_request)
    result = await bu_browser_session_create()

    assert result.success
    assert result.session_id == "br_123"
    assert result.cdp_url == "wss://cdp.example/ws"
    assert result.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_task_create_returns_task_and_session_refs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Task create should return both task and session references."""

    async def fake_request(
        method: HttpMethod,
        path: str,
        *,
        body: dict[str, object] | None = None,
        query: dict[str, object] | None = None,
    ) -> CloudApiResult:
        assert path == "/api/v2/tasks"
        assert body is not None
        assert query is None
        assert method is HttpMethod.POST
        return CloudApiResult(
            success=True,
            status_code=HTTPStatus.OK,
            data={"task": {"id": "task_123", "sessionId": "sess_123"}},
        )

    monkeypatch.setattr("tools.tasks.request", fake_request)
    result = await bu_task_create(task="open docs")

    assert result.success
    assert result.task_id == "task_123"
    assert result.session_id == "sess_123"
