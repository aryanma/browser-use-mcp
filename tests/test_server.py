"""Server bootstrap tests."""

from __future__ import annotations

import pytest

from browser_use_mcp import server as server_mod


def test_create_server_uses_env_authorization_server(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeMCPServer:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setenv("DEDALUS_AS_URL", "https://as.example.test")
    monkeypatch.setattr(server_mod, "MCPServer", FakeMCPServer)

    server = server_mod.create_server()

    assert server.kwargs["name"] == "browser-use-mcp"
    assert server.kwargs["authorization_server"] == "https://as.example.test"
    assert len(server.kwargs["connections"]) == 1


@pytest.mark.asyncio
async def test_main_collects_and_serves(monkeypatch: pytest.MonkeyPatch) -> None:
    events: dict[str, object] = {}

    class FakeServer:
        def collect(self, *tools):
            events["tools_count"] = len(tools)

        async def serve(self, port: int) -> None:
            events["port"] = port

    def _create_server() -> FakeServer:
        return FakeServer()

    monkeypatch.setattr(server_mod, "create_server", _create_server)

    await server_mod.main()

    assert events["port"] == 8080
    assert isinstance(events["tools_count"], int)
    assert events["tools_count"] > 0
