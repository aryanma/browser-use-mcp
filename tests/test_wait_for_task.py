"""Tests for task polling helper."""

from __future__ import annotations

import pytest

from browser_use_mcp import browser_use as mod

from .conftest import FakeDispatchContext, FakeDispatchResult, FakeHttpResponse


@pytest.mark.asyncio
async def test_wait_for_task_immediate_finish(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext(
        [
            FakeDispatchResult(
                success=True,
                response=FakeHttpResponse(
                    status=200,
                    body={"id": "task-1", "status": "finished"},
                ),
            )
        ]
    )
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    result = await mod.browser_use_wait_for_task("task-1", timeout_seconds=10, poll_interval_seconds=0.01)

    assert result.ok is True
    assert result.meta["polls"] == 1
    assert result.meta["finalStatus"] == "finished"


@pytest.mark.asyncio
async def test_wait_for_task_eventual_finish(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext(
        [
            FakeDispatchResult(success=True, response=FakeHttpResponse(status=200, body={"status": "started"})),
            FakeDispatchResult(success=True, response=FakeHttpResponse(status=200, body={"status": "started"})),
            FakeDispatchResult(success=True, response=FakeHttpResponse(status=200, body={"status": "finished"})),
        ]
    )
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    async def _no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(mod.asyncio, "sleep", _no_sleep)

    result = await mod.browser_use_wait_for_task("task-1", timeout_seconds=10, poll_interval_seconds=0.2)

    assert result.ok is True
    assert result.meta["polls"] == 3


@pytest.mark.asyncio
async def test_wait_for_task_dispatch_error_bubbles_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext([FakeDispatchResult(success=False, response=FakeHttpResponse(status=500), error=None)])
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    result = await mod.browser_use_wait_for_task("task-1", timeout_seconds=10, poll_interval_seconds=0.01)

    assert result.ok is False
    assert result.status_code == 500
    assert result.meta["polls"] == 1


@pytest.mark.asyncio
async def test_wait_for_task_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = FakeDispatchContext(
        [
            FakeDispatchResult(success=True, response=FakeHttpResponse(status=200, body={"status": "started"})),
            FakeDispatchResult(success=True, response=FakeHttpResponse(status=200, body={"status": "started"})),
            FakeDispatchResult(success=True, response=FakeHttpResponse(status=200, body={"status": "started"})),
        ]
    )
    monkeypatch.setattr(mod, "get_context", lambda: ctx)

    class FakeLoop:
        def __init__(self) -> None:
            self.current = 0.0

        def time(self) -> float:
            self.current += 0.6
            return self.current

    fake_loop = FakeLoop()

    async def _no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(mod.asyncio, "get_running_loop", lambda: fake_loop)
    monkeypatch.setattr(mod.asyncio, "sleep", _no_sleep)

    result = await mod.browser_use_wait_for_task("task-1", timeout_seconds=1, poll_interval_seconds=0.1)

    assert result.ok is False
    assert "Timeout waiting for task" in (result.error or "")
    assert result.meta["timeoutSeconds"] == 1
    assert result.meta["polls"] >= 1
    assert isinstance(result.meta["lastResult"], dict)
