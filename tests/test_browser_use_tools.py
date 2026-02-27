"""Tool-level request mapping tests."""

from __future__ import annotations

import pytest

from browser_use_mcp import browser_use as mod

from .conftest import (
    FakeDispatchContext,
    FakeDispatchError,
    FakeDispatchResult,
    FakeHttpResponse,
)


@pytest.mark.asyncio
async def test_get_account_billing_dispatches_correct_request(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext(
        [
            FakeDispatchResult(
                success=True,
                response=FakeHttpResponse(status=200, body={"totalCreditsBalanceUsd": 1.23}),
            )
        ]
    )
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    result = await mod.browser_use_get_account_billing()

    assert result.ok is True
    assert result.status_code == 200
    assert result.data == {"totalCreditsBalanceUsd": 1.23}
    assert len(ctx.calls) == 1
    connection, request = ctx.calls[0]
    assert connection == "browser_use"
    assert request.method == mod.HttpMethod.GET
    assert request.path == "/billing/account"


@pytest.mark.asyncio
async def test_create_task_builds_expected_body(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext([FakeDispatchResult(success=True, response=FakeHttpResponse(status=202, body={"id": "t1"}))])
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    result = await mod.browser_use_create_task(
        task="Search docs",
        llm="browser-use-llm",
        session_id="s1",
        start_url="https://example.com",
        max_steps=12,
        structured_output='{"type":"object"}',
        metadata={"ticket": "123"},
        secrets={"k": "v"},
        allowed_domains=["example.com"],
        op_vault_id="vault-1",
        highlight_elements=True,
        flash_mode=True,
        thinking=False,
        vision="auto",
        system_prompt_extension="extra context",
    )

    assert result.ok is True
    assert result.status_code == 202
    _, request = ctx.calls[0]
    assert request.method == mod.HttpMethod.POST
    assert request.path == "/tasks"
    assert request.body == {
        "task": "Search docs",
        "llm": "browser-use-llm",
        "sessionId": "s1",
        "startUrl": "https://example.com",
        "maxSteps": 12,
        "structuredOutput": '{"type":"object"}',
        "metadata": {"ticket": "123"},
        "secrets": {"k": "v"},
        "allowedDomains": ["example.com"],
        "opVaultId": "vault-1",
        "highlightElements": True,
        "flashMode": True,
        "thinking": False,
        "vision": "auto",
        "systemPromptExtension": "extra context",
    }


@pytest.mark.asyncio
async def test_get_task(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext([FakeDispatchResult(success=True, response=FakeHttpResponse(status=200, body={"id": "t1"}))])
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    result = await mod.browser_use_get_task("task-123")

    assert result.ok is True
    _, request = ctx.calls[0]
    assert request.path == "/tasks/task-123"


@pytest.mark.asyncio
async def test_list_tasks_with_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext([FakeDispatchResult(success=True, response=FakeHttpResponse(status=200, body={"items": []}))])
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    result = await mod.browser_use_list_tasks(
        page_size=25,
        page_number=2,
        session_id="session-123",
        filter_by="started",
        after="2026-01-01T00:00:00Z",
        before="2026-01-02T00:00:00Z",
    )

    assert result.ok is True
    _, request = ctx.calls[0]
    assert request.path.startswith("/tasks?")
    assert "pageSize=25" in request.path
    assert "pageNumber=2" in request.path
    assert "sessionId=session-123" in request.path
    assert "filterBy=started" in request.path
    assert "after=2026-01-01T00:00:00Z" in request.path
    assert "before=2026-01-02T00:00:00Z" in request.path


@pytest.mark.asyncio
async def test_list_tasks_rejects_invalid_filter() -> None:
    with pytest.raises(ValueError, match="filter_by"):
        await mod.browser_use_list_tasks(filter_by="unknown")


@pytest.mark.asyncio
async def test_update_task_rejects_invalid_action() -> None:
    with pytest.raises(ValueError, match="action"):
        await mod.browser_use_update_task("task-1", "invalid")


@pytest.mark.asyncio
async def test_update_task_dispatches_valid_action(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext([FakeDispatchResult(success=True, response=FakeHttpResponse(status=200, body={"status": "paused"}))])
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    result = await mod.browser_use_update_task("task-1", "pause")

    assert result.ok is True
    _, request = ctx.calls[0]
    assert request.method == mod.HttpMethod.PATCH
    assert request.path == "/tasks/task-1"
    assert request.body == {"action": "pause"}


@pytest.mark.asyncio
async def test_get_task_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext([FakeDispatchResult(success=True, response=FakeHttpResponse(status=200, body={"downloadUrl": "u"}))])
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    result = await mod.browser_use_get_task_logs("task-logs")

    assert result.ok is True
    _, request = ctx.calls[0]
    assert request.path == "/tasks/task-logs/logs"


@pytest.mark.asyncio
async def test_get_session(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext([FakeDispatchResult(success=True, response=FakeHttpResponse(status=200, body={"id": "s1"}))])
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    result = await mod.browser_use_get_session("session-1")

    assert result.ok is True
    _, request = ctx.calls[0]
    assert request.path == "/sessions/session-1"


@pytest.mark.asyncio
async def test_update_session_default_action(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext([FakeDispatchResult(success=True, response=FakeHttpResponse(status=200, body={"status": "stopped"}))])
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    result = await mod.browser_use_update_session("session-1")

    assert result.ok is True
    _, request = ctx.calls[0]
    assert request.path == "/sessions/session-1"
    assert request.body == {"action": "stop"}


@pytest.mark.asyncio
async def test_update_session_invalid_action() -> None:
    with pytest.raises(ValueError, match="action"):
        await mod.browser_use_update_session("session-1", action="pause")


@pytest.mark.asyncio
async def test_list_profiles(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext([FakeDispatchResult(success=True, response=FakeHttpResponse(status=200, body={"items": []}))])
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    result = await mod.browser_use_list_profiles(page_size=20, page_number=3)

    assert result.ok is True
    _, request = ctx.calls[0]
    assert request.path == "/profiles?pageSize=20&pageNumber=3"


@pytest.mark.asyncio
async def test_create_profile_with_name(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext([FakeDispatchResult(success=True, response=FakeHttpResponse(status=201, body={"id": "p1"}))])
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    result = await mod.browser_use_create_profile("prod")

    assert result.ok is True
    _, request = ctx.calls[0]
    assert request.path == "/profiles"
    assert request.body == {"name": "prod"}


@pytest.mark.asyncio
async def test_get_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext([FakeDispatchResult(success=True, response=FakeHttpResponse(status=200, body={"id": "p1"}))])
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    result = await mod.browser_use_get_profile("profile-1")

    assert result.ok is True
    _, request = ctx.calls[0]
    assert request.path == "/profiles/profile-1"


@pytest.mark.asyncio
async def test_dispatch_failure_maps_error(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext(
        [
            FakeDispatchResult(
                success=False,
                response=FakeHttpResponse(status=429),
                error=FakeDispatchError(message="Rate limit"),
            )
        ]
    )
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    result = await mod.browser_use_get_account_billing()

    assert result.ok is False
    assert result.status_code == 429
    assert result.error == "Rate limit"
