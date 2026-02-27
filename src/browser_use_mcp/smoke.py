"""Smoke tools for basic MCP handshake checks."""

from dedalus_mcp import tool
from dedalus_mcp.types import ToolAnnotations
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class PingResult:
    """Simple ping response."""

    ok: bool = True
    message: str = "pong"


@tool(
    description="Smoke test ping (no dispatch required)",
    tags=["smoke", "health"],
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
async def smoke_ping(message: str = "pong") -> PingResult:
    """Return a simple ping response."""
    return PingResult(message=message)


smoke_tools = [smoke_ping]
