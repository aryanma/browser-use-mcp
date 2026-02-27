"""Coverage-focused tests for bootstrap and fallback paths."""

from __future__ import annotations

import importlib
import runpy
import sys
from types import SimpleNamespace

import pytest

from browser_use_mcp.browser_use import _to_status_code
from browser_use_mcp.smoke import PingResult, smoke_ping


def test_to_status_code_none_response() -> None:
    assert _to_status_code(None) is None


def test_to_status_code_status_code_fallback() -> None:
    response = SimpleNamespace(status_code=204)
    assert _to_status_code(response) == 204


def test_to_status_code_no_status_fields() -> None:
    response = object()
    assert _to_status_code(response) is None


@pytest.mark.asyncio
async def test_smoke_ping_returns_ping_result() -> None:
    result = await smoke_ping("hello")
    assert isinstance(result, PingResult)
    assert result.ok is True
    assert result.message == "hello"


def test_main_module_import_runs_load_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []

    def fake_load_dotenv() -> None:
        calls.append(True)

    monkeypatch.setattr("dotenv.load_dotenv", fake_load_dotenv)
    sys.modules.pop("browser_use_mcp.main", None)

    importlib.import_module("browser_use_mcp.main")

    assert calls == [True]


def test_main_dunder_main_executes_asyncio_run(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_server_main() -> None:
        return None

    captured: dict[str, object] = {}

    def fake_run(coro: object) -> None:
        captured["called"] = True
        # Close coroutine to avoid "was never awaited" warnings.
        coro.close()  # type: ignore[attr-defined]

    monkeypatch.setattr("browser_use_mcp.server.main", fake_server_main)
    monkeypatch.setattr("asyncio.run", fake_run)
    sys.modules.pop("browser_use_mcp.main", None)

    runpy.run_module("browser_use_mcp.main", run_name="__main__")

    assert captured.get("called") is True
