# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""MCP server entrypoint.

Cloud-only Browser Use wrapper for Dedalus MCP.
"""

from __future__ import annotations

import os

from dedalus_mcp import MCPServer
from dedalus_mcp.server import TransportSecuritySettings

from browser.cloud import browser_use_mcp
from tools import browser_tools


INSTRUCTIONS = """Browser Use Cloud MCP wrapper.

This server is cloud-only: every operation routes to Browser Use API v2.
Use it for:
- Account billing and credit visibility
- Task orchestration (create/get/stop/wait/run)
- Cloud sessions and public share links
- Remote browser sessions (CDP)
- File upload URL generation for tasks/browser sessions
- Profile management

Recommended flow:
1. Create or reuse a session/profile.
2. Capture and persist returned IDs (`session_id`, `task_id`, optional `cdp_url`).
3. Create task with explicit task prompt and optional guardrails.
4. Poll with bu_task_wait or use bu_task_run for one-shot execution.
5. Fetch logs/output URLs when needed.

This MCP server runs in stateless mode, so callers must pass IDs explicitly in
follow-up calls and must not assume server-side memory across requests.
"""


def create_server() -> MCPServer:
    """Create MCP server with cloud connection."""
    as_url = os.getenv("DEDALUS_AS_URL", "https://as.dedaluslabs.ai")
    return MCPServer(
        name="browser-use-mcp",
        version="1.0.0",
        instructions=INSTRUCTIONS,
        connections=[browser_use_mcp],
        http_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        streamable_http_stateless=True,
        authorization_server=as_url,
    )


async def main() -> None:
    """Start MCP server."""
    server = create_server()
    server.collect(*browser_tools)
    await server.serve(port=8080)
